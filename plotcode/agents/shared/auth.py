"""
Production-grade authentication module.

Features:
  - JWT access + refresh tokens (HS256 signed)
  - Password hashing with bcrypt (passlib)
  - User storage in MongoDB (users collection with password_hash)
  - Admin user auto-seeding from env vars
  - GitHub OAuth integration
  - FastAPI dependencies for token-based route protection

Token lifecycle:
  - Access token: 30 minutes (short-lived)
  - Refresh token: 7 days (long-lived, used to mint new access tokens)
"""

import os
import time
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

import bcrypt
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

# ─── Configuration ─────────────────────────────────────────────────────────────

JWT_SECRET = os.getenv("JWT_SECRET") or secrets.token_hex(32)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Admin seeding (env-based bootstrap user)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "plotcode2024")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@plotcode.local")

# GitHub OAuth
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_OAUTH_REDIRECT_URI = os.getenv("GITHUB_OAUTH_REDIRECT_URI", "http://localhost:5173/auth/github/callback")

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_OAUTH_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:5173/auth/google/callback")

# ─── Password Hashing (bcrypt direct — no passlib) ────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly."""
    # bcrypt has a 72-byte limit; truncate to avoid ValueError
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        pw_bytes = plain.encode("utf-8")[:72]
        hash_bytes = hashed.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception:
        return False


# ─── JWT Tokens ────────────────────────────────────────────────────────────────

def create_access_token(data: Dict[str, Any]) -> str:
    """Create a short-lived JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc),
    })
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a long-lived JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),  # unique token ID for revocation tracking
    })
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify a JWT token. Returns payload or None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def create_token_pair(user: Dict[str, Any]) -> Dict[str, str]:
    """Create both access and refresh tokens for a user."""
    token_data = {
        "sub": str(user.get("id") or user.get("_id") or user.get("username")),
        "username": user.get("username", ""),
        "role": user.get("role", "requester"),
        "name": user.get("name", user.get("username", "")),
    }
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


# ─── User Store (MongoDB) ──────────────────────────────────────────────────────

class AuthStore:
    """Manages authenticated users in MongoDB (separate from Telegram RBAC users)."""

    def __init__(self, db):
        self.collection = db.auth_users
        self._ensure_indexes()
        self._seed_admin()

    def _ensure_indexes(self):
        self.collection.create_index("username", unique=True)
        self.collection.create_index("email", unique=True, sparse=True)
        self.collection.create_index("github_id", unique=True, sparse=True)
        self.collection.create_index("google_id", unique=True, sparse=True)

    def _seed_admin(self):
        """Seed the admin user from env vars if not present."""
        existing = self.collection.find_one({"username": ADMIN_USERNAME})
        if not existing:
            self.collection.insert_one({
                "id": str(uuid.uuid4()),
                "username": ADMIN_USERNAME,
                "email": ADMIN_EMAIL,
                "password_hash": hash_password(ADMIN_PASSWORD),
                "name": "Administrator",
                "role": "admin",
                "is_active": True,
                "github_id": None,
                "github_token": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

    @staticmethod
    def _clean(doc: Optional[Dict]) -> Optional[Dict]:
        if doc is None:
            return None
        doc = dict(doc)
        doc.pop("_id", None)
        doc.pop("password_hash", None)
        return doc

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify credentials and return user (without password hash) or None."""
        doc = self.collection.find_one({"username": username, "is_active": True})
        if not doc:
            return None
        if not verify_password(password, doc.get("password_hash", "")):
            return None
        return self._clean(doc)

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({"id": user_id})
        return self._clean(doc)

    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({"username": username})
        return self._clean(doc)

    def get_by_github_id(self, github_id: int) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({"github_id": github_id})
        return self._clean(doc)

    def create_user(self, username: str, password: str, email: str = "",
                    name: str = "", role: str = "requester") -> Dict[str, Any]:
        """Create a new authenticated user."""
        user_doc = {
            "id": str(uuid.uuid4()),
            "username": username,
            "email": email,
            "password_hash": hash_password(password),
            "name": name or username,
            "role": role,
            "is_active": True,
            "github_id": None,
            "github_token": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.collection.insert_one(user_doc)
        return self._clean(user_doc)

    def upsert_github_user(self, github_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update a user from GitHub OAuth data.
        Links GitHub account to existing user by email, or creates new.
        """
        github_id = github_data.get("id")
        email = github_data.get("email", "")
        username = github_data.get("login", f"github_{github_id}")
        name = github_data.get("name") or username
        token = github_data.get("access_token", "")

        # Check if GitHub user already linked
        existing = self.collection.find_one({"github_id": github_id})
        if existing:
            self.collection.update_one(
                {"github_id": github_id},
                {"$set": {
                    "github_token": token,
                    "name": name,
                    "email": email or existing.get("email", ""),
                }}
            )
            return self._clean(self.collection.find_one({"github_id": github_id}))

        # Check if email matches an existing user
        if email:
            existing = self.collection.find_one({"email": email})
            if existing:
                self.collection.update_one(
                    {"email": email},
                    {"$set": {
                        "github_id": github_id,
                        "github_token": token,
                    }}
                )
                return self._clean(self.collection.find_one({"email": email}))

        # Create new user from GitHub
        user_doc = {
            "id": str(uuid.uuid4()),
            "username": username,
            "email": email,
            "password_hash": None,  # OAuth users have no password
            "name": name,
            "role": "developer",  # Default role for GitHub users
            "is_active": True,
            "github_id": github_id,
            "github_token": token,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.collection.insert_one(user_doc)
        return self._clean(user_doc)

    def link_github(self, user_id: str, github_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Link a GitHub account to an existing user."""
        self.collection.update_one(
            {"id": user_id},
            {"$set": {
                "github_id": github_data.get("id"),
                "github_token": github_data.get("access_token", ""),
            }}
        )
        return self.get_by_id(user_id)

    def get_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({"google_id": google_id})
        return self._clean(doc)

    def upsert_google_user(self, google_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update a user from Google OAuth data.
        Links Google account to existing user by email, or creates new.
        """
        google_id = google_data.get("sub") or google_data.get("id")
        email = google_data.get("email", "")
        name = google_data.get("name") or email.split("@")[0] or "Google User"
        username = google_data.get("email", "").split("@")[0] or f"google_{google_id}"
        token = google_data.get("access_token", "")
        avatar = google_data.get("picture", "")

        # Check if Google user already linked
        existing = self.collection.find_one({"google_id": google_id})
        if existing:
            self.collection.update_one(
                {"google_id": google_id},
                {"$set": {
                    "google_token": token,
                    "name": name,
                    "avatar": avatar,
                }}
            )
            return self._clean(self.collection.find_one({"google_id": google_id}))

        # Check if email matches an existing user
        if email:
            existing = self.collection.find_one({"email": email})
            if existing:
                self.collection.update_one(
                    {"email": email},
                    {"$set": {
                        "google_id": google_id,
                        "google_token": token,
                        "avatar": avatar,
                    }}
                )
                return self._clean(self.collection.find_one({"email": email}))

        # Create new user from Google
        # Ensure username is unique
        base_username = username
        suffix = 1
        while self.collection.find_one({"username": username}):
            username = f"{base_username}_{suffix}"
            suffix += 1

        user_doc = {
            "id": str(uuid.uuid4()),
            "username": username,
            "email": email,
            "password_hash": None,  # OAuth users have no password
            "name": name,
            "role": "developer",
            "is_active": True,
            "github_id": None,
            "github_token": None,
            "google_id": google_id,
            "google_token": token,
            "avatar": avatar,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.collection.insert_one(user_doc)
        return self._clean(user_doc)

    def link_google(self, user_id: str, google_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Link a Google account to an existing user."""
        self.collection.update_one(
            {"id": user_id},
            {"$set": {
                "google_id": google_data.get("sub") or google_data.get("id"),
                "google_token": google_data.get("access_token", ""),
            }}
        )
        return self.get_by_id(user_id)

    def list_users(self) -> list:
        return [self._clean(doc) for doc in self.collection.find({})]

    def update_role(self, user_id: str, role: str) -> bool:
        result = self.collection.update_one(
            {"id": user_id}, {"$set": {"role": role}}
        )
        return result.modified_count > 0


# ─── GitHub OAuth Helpers ──────────────────────────────────────────────────────

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_USER_URL = "https://api.github.com/user"


def get_github_oauth_url(state: str = "") -> str:
    """Build the GitHub OAuth authorization URL."""
    import urllib.parse
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_OAUTH_REDIRECT_URI,
        "scope": "repo workflow read:user user:email",
        "state": state or secrets.token_hex(16),
    }
    return f"{GITHUB_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


def exchange_github_code(code: str) -> Optional[Dict[str, Any]]:
    """Exchange an OAuth code for a GitHub access token + user data."""
    import requests
    try:
        payload = {
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": GITHUB_OAUTH_REDIRECT_URI,
        }
        print(f"[auth] GitHub Token Exchange Request URI: {GITHUB_OAUTH_REDIRECT_URI}")
        print(f"[auth] GitHub Token Exchange Client ID: {GITHUB_CLIENT_ID}")
        resp = requests.post(GITHUB_TOKEN_URL, json=payload, headers={"Accept": "application/json"}, timeout=15)
        token_data = resp.json()

        if "error" in token_data:
            print(f"[auth] GitHub OAuth error response: {token_data}")
            return None

        access_token = token_data.get("access_token")
        if not access_token:
            print(f"[auth] GitHub OAuth: no access_token in response: {token_data}")
            return None

        # Fetch user profile
        resp = requests.get(GITHUB_API_USER_URL, headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }, timeout=15)
        user_data = resp.json()
        user_data["access_token"] = access_token
        return user_data
    except Exception as e:
        print(f"[auth] GitHub OAuth exchange failed: {e}")
        return None


# ─── Google OAuth Helpers ─────────────────────────────────────────────────────

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_API_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def get_google_oauth_url(state: str = "") -> str:
    """Build the Google OAuth authorization URL."""
    import urllib.parse
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state or secrets.token_hex(16),
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


def exchange_google_code(code: str) -> Optional[Dict[str, Any]]:
    """Exchange an OAuth code for a Google access token + user profile."""
    import requests
    try:
        payload = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
        }
        print(f"[auth] Google Token Exchange Request URI: {GOOGLE_OAUTH_REDIRECT_URI}")
        print(f"[auth] Google Token Exchange Client ID: {GOOGLE_CLIENT_ID}")
        resp = requests.post(GOOGLE_TOKEN_URL, data=payload, timeout=15)
        token_data = resp.json()

        if "error" in token_data:
            print(f"[auth] Google OAuth error response: {token_data}")
            return None

        access_token = token_data.get("access_token")
        if not access_token:
            print(f"[auth] Google OAuth: no access_token in response: {token_data}")
            return None

        # Fetch user profile from Google UserInfo endpoint
        resp = requests.get(GOOGLE_API_USERINFO_URL, headers={
            "Authorization": f"Bearer {access_token}",
        }, timeout=15)
        user_data = resp.json()
        user_data["access_token"] = access_token
        return user_data
    except Exception as e:
        print(f"[auth] Google OAuth exchange failed: {e}")
        return None


# ─── Singleton ─────────────────────────────────────────────────────────────────

_auth_store: Optional[AuthStore] = None


def get_auth_store() -> AuthStore:
    """Get the singleton AuthStore. Requires MongoDB to be initialized."""
    global _auth_store
    if _auth_store is None:
        from shared.state import get_state_store
        store = get_state_store()
        _auth_store = AuthStore(store.db)
    return _auth_store
