"""
MongoDB Atlas State Store — production-grade, serverless.

Single backend: MongoDB Atlas (no SQLite fallback).
Collections:
  - requests      : Feature request lifecycle
  - audit_log     : Immutable event trail
  - users         : RBAC user records
  - services      : Registered GitHub repositories
  - ai_prompt_log : Every LLM prompt/response
"""

import os
import uuid
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

import pymongo
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.collection import Collection
from dotenv import load_dotenv

load_dotenv()

# ─── Connection ───────────────────────────────────────────────────────────────

_MONGO_URI = os.getenv("MONGODB_URI")
_MONGO_DB   = os.getenv("MONGODB_DB", "plotcode_db")

if not _MONGO_URI:
    raise EnvironmentError(
        "MONGODB_URI is not set. "
        "Please configure your MongoDB Atlas connection string in .env"
    )


# ─── Priority → SLA hours mapping ─────────────────────────────────────────────

SLA_HOURS: Dict[str, int] = {
    "P0": 4,
    "P1": 24,
    "P2": 72,
    "P3": 168,
}


class StateStore:
    """
    Production-grade MongoDB Atlas state store.
    Thread-safe via MongoClient's built-in connection pool.
    """

    def __init__(self):
        self.client: MongoClient = MongoClient(_MONGO_URI, serverSelectionTimeoutMS=8000)
        # Verify connectivity eagerly so misconfiguration surfaces at startup
        self.client.server_info()
        self.db = self.client[_MONGO_DB]
        self.db_type = "MongoDB Atlas"
        self._ensure_indexes()
        self._seed_defaults()

    # ─── Indexes & Seeds ──────────────────────────────────────────────────────

    def _ensure_indexes(self) -> None:
        """Create indexes for performance. Safe to call repeatedly (idempotent)."""
        # requests
        req: Collection = self.db.requests
        req.create_index("request_id", unique=True)
        req.create_index("status")
        req.create_index("priority")
        req.create_index("affected_service")
        req.create_index("feature_branch")
        req.create_index([("created_at", DESCENDING)])
        req.create_index([("title", TEXT), ("business_need", TEXT), ("expected_behavior", TEXT)])

        # audit_log
        al: Collection = self.db.audit_log
        al.create_index("request_id")
        al.create_index([("created_at", ASCENDING)])

        # users
        usr: Collection = self.db.users
        usr.create_index("telegram_id", unique=True, sparse=True)
        usr.create_index("slack_id",    unique=True, sparse=True)
        usr.create_index("email",       unique=True, sparse=True)

        # ai_prompt_log
        pl: Collection = self.db.ai_prompt_log
        pl.create_index("request_id")
        pl.create_index([("created_at", DESCENDING)])
        pl.create_index("agent_name")

        # services
        self.db.services.create_index("name", unique=True)

    def _seed_defaults(self) -> None:
        """Insert default service if the collection is empty."""
        if self.db.services.count_documents({}) == 0:
            self.db.services.insert_one({
                "id": str(uuid.uuid4()),
                "name": "demo-api",
                "repo_url": "https://github.com/Kamalesh1011/plotcode-demo-api",
                "default_branch": "main",
                "team_owner": "Platform Team",
                "tech_stack": "python,fastapi",
                "ci_workflow_path": ".github/workflows/ci.yml",
                "staging_env": os.getenv("STAGING_ENV_URL", ""),
                "production_env": os.getenv("PRODUCTION_ENV_URL", ""),
                "is_active": True,
                "created_at": _now(),
            })

    # ─── Internal helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _clean(doc: Optional[Dict]) -> Optional[Dict]:
        """Remove MongoDB's _id from returned documents."""
        if doc is None:
            return None
        doc = dict(doc)
        doc.pop("_id", None)
        return doc

    @staticmethod
    def _clean_list(docs) -> List[Dict]:
        return [StateStore._clean(d) for d in docs if d is not None]

    # ─── Request CRUD ─────────────────────────────────────────────────────────

    def create_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data.setdefault("id", str(uuid.uuid4()))
        now = _now()
        data.setdefault("created_at", now)
        data.setdefault("updated_at", now)
        data.setdefault("status", "submitted")
        data.setdefault("priority", "P2")

        # Auto-generate request_id
        if "request_id" not in data:
            count = self.db.requests.count_documents({}) + 1
            year = datetime.now(timezone.utc).year
            data["request_id"] = f"REQ-{year}-{count:04d}"

        # Compute SLA deadline
        priority = data.get("priority", "P2")
        hours = SLA_HOURS.get(priority, 72)
        data["sla_deadline"] = (
            datetime.now(timezone.utc) + timedelta(hours=hours)
        ).isoformat()

        self.db.requests.insert_one(data)
        return self.get_request(data["request_id"]) or data

    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        return self._clean(
            self.db.requests.find_one({"request_id": request_id})
        )

    def update_request(self, request_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        updates["updated_at"] = _now()
        self.db.requests.update_one(
            {"request_id": request_id},
            {"$set": updates}
        )
        return self.get_request(request_id) or {}

    def list_requests(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        service: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority
        if service:
            query["affected_service"] = service
        cursor = (
            self.db.requests.find(query)
            .sort("created_at", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        return self._clean_list(cursor)

    def search_requests(self, text: str) -> List[Dict[str, Any]]:
        """Full-text search across title, business_need, expected_behavior."""
        cursor = (
            self.db.requests.find(
                {"$text": {"$search": text}},
                {"score": {"$meta": "textScore"}}
            )
            .sort([("score", {"$meta": "textScore"})])
            .limit(50)
        )
        return self._clean_list(cursor)

    def get_request_by_branch_and_status(
        self, branch: str, statuses: List[str]
    ) -> Optional[Dict[str, Any]]:
        return self._clean(
            self.db.requests.find_one(
                {"feature_branch": branch, "status": {"$in": statuses}},
                sort=[("created_at", DESCENDING)]
            )
        )

    def bulk_update_status(
        self, request_ids: List[str], new_status: str, actor_id: str
    ) -> int:
        """Bulk-update status for a list of request IDs. Returns count updated."""
        result = self.db.requests.update_many(
            {"request_id": {"$in": request_ids}},
            {"$set": {"status": new_status, "updated_at": _now()}}
        )
        for rid in request_ids:
            self.log_audit(rid, "human", actor_id, "bulk_status_update", {
                "new_status": new_status
            })
        return result.modified_count

    def get_sla_breached_requests(self) -> List[Dict[str, Any]]:
        """Return all open requests whose SLA deadline has passed."""
        now = _now()
        terminal = {"closed", "deployed", "rejected"}
        cursor = self.db.requests.find({
            "sla_deadline": {"$lt": now},
            "sla_breach_alert_sent": {"$ne": True},
            "status": {"$nin": list(terminal)},
        })
        return self._clean_list(cursor)

    def mark_sla_alert_sent(self, request_id: str) -> None:
        self.db.requests.update_one(
            {"request_id": request_id},
            {"$set": {"sla_breach_alert_sent": True}}
        )

    def count_requests(self, query: Optional[Dict] = None) -> int:
        return self.db.requests.count_documents(query or {})

    # ─── Audit Log ────────────────────────────────────────────────────────────

    def log_audit(
        self,
        request_id: str,
        actor_type: str,
        actor_id: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "request_id": request_id,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "action": action,
            "details": details or {},
            "created_at": _now(),
        })

    def get_audit_log(self, request_id: str) -> List[Dict[str, Any]]:
        cursor = self.db.audit_log.find(
            {"request_id": request_id}
        ).sort("created_at", ASCENDING)
        return self._clean_list(cursor)

    def get_all_audit_logs(self, limit: int = 500) -> List[Dict[str, Any]]:
        cursor = self.db.audit_log.find().sort("created_at", DESCENDING).limit(limit)
        return self._clean_list(cursor)

    # ─── Prompt Log ───────────────────────────────────────────────────────────

    def log_prompt(
        self,
        request_id: str,
        agent_name: str,
        model: str,
        prompt: str,
        response: str,
        tokens_input: int = 0,
        tokens_output: int = 0,
        latency_ms: int = 0,
        success: bool = True,
        error_message: Optional[str] = None,
        confidence_score: Optional[float] = None,
        prompt_version: Optional[str] = None,
    ) -> None:
        self.db.ai_prompt_log.insert_one({
            "id": str(uuid.uuid4()),
            "request_id": request_id,
            "agent_name": agent_name,
            "model": model,
            "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest(),
            "prompt_preview": prompt[:2000],
            "response_hash": hashlib.sha256(response.encode()).hexdigest(),
            "response_preview": response[:2000],
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "latency_ms": latency_ms,
            "success": success,
            "error_message": error_message,
            "confidence_score": confidence_score,
            "prompt_version": prompt_version,
            "created_at": _now(),
        })

    def get_prompt_logs(
        self, request_id: Optional[str] = None, agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if request_id:
            query["request_id"] = request_id
        if agent_name:
            query["agent_name"] = agent_name
        cursor = self.db.ai_prompt_log.find(query).sort("created_at", DESCENDING).limit(limit)
        return self._clean_list(cursor)

    # ─── Metrics Aggregation ──────────────────────────────────────────────────

    def get_metrics(self) -> Dict[str, Any]:
        """Aggregate pipeline metrics for the dashboard."""
        total = self.db.requests.count_documents({})
        deployed = self.db.requests.count_documents({"status": "deployed"})
        closed   = self.db.requests.count_documents({"status": "closed"})
        rejected = self.db.requests.count_documents({"status": "rejected"})
        active   = total - deployed - closed - rejected

        # SLA compliance
        sla_breached = self.db.requests.count_documents({
            "sla_breach_alert_sent": True
        })
        sla_compliance = (
            round((1 - sla_breached / total) * 100, 1) if total > 0 else 100.0
        )

        # Status distribution
        pipeline_stage = list(self.db.requests.aggregate([
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": DESCENDING}}
        ]))

        # Priority breakdown
        priority_dist = list(self.db.requests.aggregate([
            {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
        ]))

        # Avg cycle time (days) for closed requests
        avg_cycle_ms = None
        closed_docs = list(self.db.requests.find(
            {"status": {"$in": ["closed", "deployed"]},
             "completed_at": {"$exists": True}},
            {"created_at": 1, "completed_at": 1}
        ))
        if closed_docs:
            deltas = []
            for doc in closed_docs:
                try:
                    t0 = datetime.fromisoformat(str(doc["created_at"]).replace("Z", "+00:00"))
                    t1 = datetime.fromisoformat(str(doc["completed_at"]).replace("Z", "+00:00"))
                    deltas.append((t1 - t0).total_seconds())
                except Exception:
                    pass
            if deltas:
                avg_cycle_ms = round(sum(deltas) / len(deltas) / 3600, 1)  # hours

        # AI prompt stats
        prompt_stats = list(self.db.ai_prompt_log.aggregate([
            {"$group": {
                "_id": "$agent_name",
                "total_calls": {"$sum": 1},
                "total_tokens_in": {"$sum": "$tokens_input"},
                "total_tokens_out": {"$sum": "$tokens_output"},
                "avg_latency_ms": {"$avg": "$latency_ms"},
                "success_rate": {"$avg": {"$cond": ["$success", 1, 0]}},
                "avg_confidence": {"$avg": "$confidence_score"},
            }},
            {"$sort": {"total_calls": DESCENDING}}
        ]))

        # Last 7 days volume
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        volume_7d = list(self.db.requests.aggregate([
            {"$match": {"created_at": {"$gte": seven_days_ago}}},
            {"$group": {
                "_id": {"$substr": ["$created_at", 0, 10]},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": ASCENDING}}
        ]))

        return {
            "total": total,
            "deployed": deployed,
            "closed": closed,
            "rejected": rejected,
            "active": active,
            "sla_compliance_pct": sla_compliance,
            "sla_breached": sla_breached,
            "avg_cycle_hours": avg_cycle_ms,
            "pipeline_stages": [{"status": s["_id"], "count": s["count"]} for s in pipeline_stage],
            "priority_distribution": [{"priority": p["_id"], "count": p["count"]} for p in priority_dist],
            "agent_performance": prompt_stats,
            "volume_7d": [{"date": v["_id"], "count": v["count"]} for v in volume_7d],
        }

    # ─── Services ─────────────────────────────────────────────────────────────

    def get_service(self, name: str) -> Optional[Dict[str, Any]]:
        return self._clean(self.db.services.find_one({"name": name, "is_active": True}))

    def list_services(self) -> List[Dict[str, Any]]:
        return self._clean_list(self.db.services.find({"is_active": True}))

    def upsert_service(self, data: Dict[str, Any]) -> None:
        data.setdefault("id", str(uuid.uuid4()))
        data.setdefault("is_active", True)
        data.setdefault("created_at", _now())
        self.db.services.update_one(
            {"name": data["name"]},
            {"$set": data},
            upsert=True
        )

    # ─── Users ────────────────────────────────────────────────────────────────

    def get_user(
        self,
        slack_id: Optional[str] = None,
        telegram_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if telegram_id:
            return self._clean(self.db.users.find_one({"telegram_id": telegram_id}))
        if slack_id:
            return self._clean(self.db.users.find_one({"slack_id": slack_id}))
        return None

    def create_user(self, user_data: Dict[str, Any]) -> None:
        key = {}
        if user_data.get("telegram_id"):
            key["telegram_id"] = user_data["telegram_id"]
        elif user_data.get("slack_id"):
            key["slack_id"] = user_data["slack_id"]
        else:
            key["id"] = user_data["id"]
        self.db.users.update_one(key, {"$setOnInsert": user_data}, upsert=True)

    def update_user_role(self, telegram_id: str, role: str) -> bool:
        result = self.db.users.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"role": role, "updated_at": _now()}}
        )
        return result.modified_count > 0

    def list_users(self) -> List[Dict[str, Any]]:
        return self._clean_list(self.db.users.find().sort("created_at", DESCENDING))

    # ─── Lifecycle ────────────────────────────────────────────────────────────

    def close(self) -> None:
        self.client.close()


# ─── Singleton ────────────────────────────────────────────────────────────────

_store: Optional[StateStore] = None


def get_state_store() -> StateStore:
    global _store
    if _store is None:
        _store = StateStore()
    return _store


# ─── Helper ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
