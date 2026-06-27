"""
Plotcode DB Seed Script
Run once to register services, seed admin users, and verify setup.

Usage:
  cd plotcode/agents
  python seed_db.py
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# Add agent path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.state import get_state_store

store = get_state_store()
conn = None if store.use_mongodb else store._get_conn()
now = datetime.now(timezone.utc).isoformat()


def seed_services():
    """Register services (repositories) the AI can work on."""
    github_org = os.getenv("GITHUB_ORG", "")
    github_repo = os.getenv("GITHUB_DEFAULT_REPO", "plotcode-demo-api")
    repo_url = f"https://github.com/{github_org}/{github_repo}" if github_org else f"https://github.com/YOURUSERNAME/{github_repo}"

    services = [
        {
            "id": str(uuid.uuid4()),
            "name": "demo-api",
            "repo_url": repo_url,
            "default_branch": "main",
            "team_owner": "Platform Team",
            "tech_stack": "python,fastapi",
            "ci_workflow_path": ".github/workflows/ci.yml",
            "staging_env": os.getenv("STAGING_ENV_URL", "https://plotcode-demo-api-staging.onrender.com"),
            "production_env": os.getenv("PRODUCTION_ENV_URL", "https://plotcode-demo-api.onrender.com"),
            "is_active": 1,
        }
    ]

    if store.use_mongodb:
        db = store.db
        for svc in services:
            db.services.update_one({"name": svc["name"]}, {"$set": svc}, upsert=True)
            print(f"  [mongodb] service: {svc['name']} -> {svc['repo_url']}")
    else:
        for svc in services:
            existing = conn.execute("SELECT name FROM services WHERE name = ?", (svc["name"],)).fetchone()
            if existing:
                conn.execute(
                    """UPDATE services SET repo_url=?, staging_env=?, production_env=? WHERE name=?""",
                    (svc["repo_url"], svc["staging_env"], svc["production_env"], svc["name"])
                )
                print(f"  [updated] service: {svc['name']} -> {svc['repo_url']}")
            else:
                conn.execute(
                    """INSERT INTO services
                       (id, name, repo_url, default_branch, team_owner, tech_stack,
                        ci_workflow_path, staging_env, production_env, is_active)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        svc["id"], svc["name"], svc["repo_url"], svc["default_branch"],
                        svc["team_owner"], svc["tech_stack"], svc["ci_workflow_path"],
                        svc["staging_env"], svc["production_env"], svc["is_active"],
                    ),
                )
                print(f"  [created] service: {svc['name']} -> {svc['repo_url']}")
        conn.commit()


def seed_users():
    """Seed admin users from environment."""
    admin_ids = [
        uid.strip()
        for uid in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",")
        if uid.strip()
    ]

    if not admin_ids:
        print("  [skip] No ADMIN_TELEGRAM_IDS set in .env")
        return

    if store.use_mongodb:
        db = store.db
        for telegram_id in admin_ids:
            db.users.update_one(
                {"telegram_id": telegram_id},
                {"$set": {
                    "telegram_id": telegram_id,
                    "name": f"Admin ({telegram_id})",
                    "role": "admin",
                    "is_active": 1,
                    "created_at": now,
                    "updated_at": now
                }},
                upsert=True
            )
            print(f"  [mongodb] user {telegram_id} -> role=admin")
    else:
        for telegram_id in admin_ids:
            existing = conn.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
            if existing:
                conn.execute("UPDATE users SET role = 'admin' WHERE telegram_id = ?", (telegram_id,))
                print(f"  [updated] user {telegram_id} -> role=admin")
            else:
                conn.execute(
                    """INSERT INTO users (id, telegram_id, name, role, is_active, created_at, updated_at)
                       VALUES (?, ?, ?, 'admin', 1, ?, ?)""",
                    (str(uuid.uuid4()), telegram_id, f"Admin ({telegram_id})", now, now)
                )
                print(f"  [created] user {telegram_id} -> role=admin")
        conn.commit()


def verify_setup():
    """Verify environment and print a summary."""
    print("\n--- Environment Check ---")

    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    print(f"  TELEGRAM_BOT_TOKEN: {'[OK]' if token else '[MISSING]'}")

    gh_token = os.getenv("GITHUB_TOKEN", "")
    print(f"  GITHUB_TOKEN:       {'[OK]' if gh_token else '[MISSING] (needed for Git ops)'}")

    or_key = os.getenv("OPENROUTER_API_KEY", "")
    print(f"  OPENROUTER_API_KEY: {'[OK]' if or_key else '[MISSING]'}")

    webhook = os.getenv("PLOTCODE_WEBHOOK_URL", "")
    print(f"  PLOTCODE_WEBHOOK_URL: {webhook or '[MISSING] (set after ngrok)'}")

    admin_ids = os.getenv("ADMIN_TELEGRAM_IDS", "")
    print(f"  ADMIN_TELEGRAM_IDS: {admin_ids or '[MISSING]'}")

    print("\n--- Database ---")
    if store.use_mongodb:
        services = list(store.db.services.find())
        users = list(store.db.users.find())
    else:
        services = conn.execute("SELECT name, repo_url FROM services").fetchall()
        users = conn.execute("SELECT telegram_id, name, role FROM users").fetchall()

    for svc in services:
        print(f"  service: {svc['name']} -> {svc['repo_url']}")

    for u in users:
        print(f"  user: {u['telegram_id']} ({u['name']}) -> {u['role']}")

    print("\n--- Ready ---")
    print("  Run the bot: python telegram_bot.py")
    print("  Run the API: python api.py")
    print("  Poll worker: python main.py --poll")


if __name__ == "__main__":
    print("Seeding Plotcode database...\n")
    print("Services:")
    seed_services()
    print("\nUsers:")
    seed_users()
    verify_setup()
