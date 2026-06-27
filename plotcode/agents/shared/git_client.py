"""
Git and GitHub client for agent operations.
Handles cloning, branching, committing, and reading repo contents.
Supports automatic offline/local fallback when GITHUB_TOKEN is not set or invalid.
"""

import os
import shutil
import random
from typing import Optional, List, Dict, Any
from git import Repo, GitCommandError
from github import Github, Auth
from dotenv import load_dotenv

load_dotenv()


class GitClient:
    """Git/GitHub client for repository operations with local offline fallback."""

    def __init__(self, github_token: Optional[str] = None):
        self.token = github_token or os.getenv("GITHUB_TOKEN")
        self.org = os.getenv("GITHUB_ORG")
        self._gh: Optional[Github] = None
        self._workspace = os.path.abspath(os.getenv("AGENT_WORKSPACE", "./workspace/repos"))
        os.makedirs(self._workspace, exist_ok=True)

    def _get_github(self) -> Github:
        if self._gh is None:
            if not self.token or "personal_access_token" in self.token or len(self.token) < 5:
                raise ValueError("GITHUB_TOKEN not configured")
            auth = Auth.Token(self.token)
            self._gh = Github(auth=auth)
        return self._gh

    def _is_local_fallback(self) -> bool:
        """Check if we should run in local offline/fallback mode."""
        return (
            not self.token
            or "personal_access_token" in self.token
            or not self.org
            or "your-org" in self.org
            or len(self.org) < 2
        )

    def clone_repo(self, repo_url: str, repo_name: str) -> str:
        """Clone a repo into the workspace. Returns local path."""
        local_path = os.path.join(self._workspace, repo_name)
        
        # 1. Existing local git repo check
        if os.path.exists(os.path.join(local_path, ".git")):
            repo = Repo(local_path)
            if self._is_local_fallback():
                return local_path
            try:
                repo.remotes.origin.pull()
            except Exception as e:
                print(f"[git_client] Pull failed: {e}. Continuing offline.")
            return local_path

        # 2. Local fallback if no token or org
        if self._is_local_fallback():
            print(f"[git_client] Running in offline local mode for {repo_name}")
            os.makedirs(local_path, exist_ok=True)
            repo = Repo.init(local_path)
            
            # Copy all files from local plotcode-demo-api folder as initial codebase
            demo_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "plotcode-demo-api"))
            if os.path.exists(demo_src):
                for item in os.listdir(demo_src):
                    s = os.path.join(demo_src, item)
                    d = os.path.join(local_path, item)
                    if os.path.isdir(s):
                        if item != ".git" and item != "__pycache__":
                            shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)
            
            # Configure local git user for the workspace repo
            with repo.config_writer() as cw:
                cw.set_value("user", "name", "Plotcode Agent")
                cw.set_value("user", "email", "agent@plotcode.local")
                
            repo.index.add("*")
            repo.index.commit("Initial commit (local offline mode)")
            
            # Create dummy main branch if not exists
            if "main" not in repo.heads:
                repo.create_head("main")
            repo.git.checkout("main")
            
            try:
                repo.create_remote("origin", repo_url)
            except Exception:
                pass
            return local_path

        # 3. Standard online clone
        Repo.clone_from(repo_url, local_path)
        return local_path

    def create_branch(self, repo_name: str, branch_name: str, base_branch: str = "main") -> str:
        """Create a feature branch. Returns branch name."""
        local_path = os.path.join(self._workspace, repo_name)
        repo = Repo(local_path)
        
        if self._is_local_fallback():
            # Checkout base branch
            if base_branch not in repo.heads:
                # Fallback to master if main doesn't exist
                if "master" in repo.heads:
                    base_branch = "master"
                else:
                    repo.create_head(base_branch)
            repo.git.checkout(base_branch)
            
            # Create feature branch if not exists
            if branch_name in repo.heads:
                repo.git.branch("-D", branch_name)
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            return branch_name

        # Standard online branch creation
        try:
            repo.remotes.origin.fetch()
        except Exception:
            pass
        repo.git.checkout(base_branch)
        try:
            repo.remotes.origin.pull()
        except Exception:
            pass

        # Create and checkout new branch
        if branch_name in repo.heads:
            repo.git.branch("-D", branch_name)
        new_branch = repo.create_head(branch_name)
        new_branch.checkout()
        return branch_name

    def read_file(self, repo_name: str, path: str, branch: Optional[str] = None) -> str:
        """Read a file from the repo."""
        local_path = os.path.join(self._workspace, repo_name)
        repo = Repo(local_path)
        if branch:
            repo.git.checkout(branch)
        file_path = os.path.join(local_path, path)
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def write_file(self, repo_name: str, path: str, content: str) -> None:
        """Write content to a file in the repo."""
        local_path = os.path.join(self._workspace, repo_name)
        file_path = os.path.join(local_path, path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def commit(self, repo_name: str, message: str, files: Optional[List[str]] = None) -> str:
        """Stage and commit changes. Returns commit SHA."""
        local_path = os.path.join(self._workspace, repo_name)
        repo = Repo(local_path)
        
        # Configure config if not set
        with repo.config_writer() as cw:
            cw.set_value("user", "name", "Plotcode Agent")
            cw.set_value("user", "email", "agent@plotcode.local")
            
        if files:
            for f in files:
                repo.index.add([f])
        else:
            repo.index.add("*")
        commit = repo.index.commit(message)
        return commit.hexsha

    def push(self, repo_name: str, branch: Optional[str] = None) -> None:
        """Push current branch to origin."""
        if self._is_local_fallback():
            print(f"[git_client] Skipping git push in offline local mode for {repo_name}@{branch}")
            return
            
        local_path = os.path.join(self._workspace, repo_name)
        repo = Repo(local_path)
        try:
            origin = repo.remotes.origin
            if branch:
                origin.push(branch)
            else:
                origin.push()
        except Exception as e:
            print(f"[git_client] Push failed: {e}. Continuing.")

    def list_files(self, repo_name: str, path: str = "") -> List[str]:
        """List all tracked files in a path."""
        local_path = os.path.join(self._workspace, repo_name)
        repo = Repo(local_path)
        tree = repo.head.commit.tree
        if path:
            try:
                subtree = tree / path
                return [entry.path for entry in subtree]
            except KeyError:
                return []
        return [entry.path for entry in tree]

    def create_pull_request(self, repo_name: str, title: str, head: str, base: str, body: str) -> Dict[str, Any]:
        """Create a GitHub PR. Fallbacks to mock local PR if offline."""
        if self._is_local_fallback():
            pr_num = random.randint(10, 99)
            print(f"[git_client] Offline local mode: Simulated PR #{pr_num} created.")
            return {
                "number": pr_num,
                "html_url": f"https://github.com/local-mock/{repo_name}/pull/{pr_num}",
                "state": "open"
            }
            
        gh = self._get_github()
        repo = gh.get_repo(f"{self.org}/{repo_name}")
        pr = repo.create_pull(title=title, body=body, head=head, base=base)
        return {
            "number": pr.number,
            "html_url": pr.html_url,
            "state": pr.state
        }

    def get_repo_contents(self, repo_name: str, path: str, ref: str = "main") -> List[Dict[str, Any]]:
        """List contents of a directory via GitHub API or local path."""
        if self._is_local_fallback():
            local_path = os.path.join(self._workspace, repo_name, path)
            if not os.path.exists(local_path):
                return []
            items = []
            for name in os.listdir(local_path):
                full = os.path.join(local_path, name)
                is_dir = os.path.isdir(full)
                items.append({
                    "name": name,
                    "path": os.path.join(path, name),
                    "type": "dir" if is_dir else "file",
                    "sha": "local_sha",
                    "content": None
                })
            return items

        gh = self._get_github()
        repo = gh.get_repo(f"{self.org}/{repo_name}")
        contents = repo.get_contents(path, ref=ref)
        if not isinstance(contents, list):
            contents = [contents]
        return [
            {
                "name": c.name,
                "path": c.path,
                "type": c.type,
                "sha": c.sha,
                "content": c.content if c.type == "file" else None
            }
            for c in contents
        ]

    def get_file_via_api(self, repo_name: str, path: str, ref: str = "main") -> str:
        """Read a file's content via GitHub API or local workspace file."""
        if self._is_local_fallback():
            return self.read_file(repo_name, path, ref)

        gh = self._get_github()
        repo = gh.get_repo(f"{self.org}/{repo_name}")
        content = repo.get_contents(path, ref=ref)
        if hasattr(content, "content"):
            import base64
            return base64.b64decode(content.content).decode("utf-8")
        return ""

    def merge_pr(self, repo_name: str, pr_number: int, commit_title: Optional[str] = None) -> Dict[str, Any]:
        """Merge a pull request. Returns merge commit details."""
        if self._is_local_fallback():
            local_path = os.path.join(self._workspace, repo_name)
            repo = Repo(local_path)

            # Get current active branch (the feature branch) before switching
            feature_branch = repo.active_branch.name

            # Switch to main and merge the feature branch
            repo.git.checkout("main")
            repo.git.merge(feature_branch)
            sha = repo.head.commit.hexsha
            print(f"[git_client] Offline local mode: Merged feature branch '{feature_branch}' into main. SHA: {sha}")
            return {"sha": sha}

        gh = self._get_github()
        repo = gh.get_repo(f"{self.org}/{repo_name}")
        pr = repo.get_pull(pr_number)
        result = pr.merge(commit_title=commit_title or f"Merge PR #{pr_number}")
        return {"sha": result.sha}

    # ─── GitHub Checks API ────────────────────────────────────────────────

    def get_branch_sha(self, repo_name: str, branch: str) -> Optional[str]:
        """Get the latest commit SHA for a branch via GitHub API or local repo."""
        if self._is_local_fallback():
            local_path = os.path.join(self._workspace, repo_name)
            repo = Repo(local_path)
            try:
                if branch in repo.heads:
                    return repo.heads[branch].commit.hexsha
                # Fall back to active branch HEAD
                return repo.head.commit.hexsha
            except Exception:
                return None

        try:
            gh = self._get_github()
            repo = gh.get_repo(f"{self.org}/{repo_name}")
            ref = repo.get_branch(branch)
            return ref.commit.sha
        except Exception as e:
            print(f"[git_client] Failed to get branch SHA: {e}")
            return None

    def list_check_runs(self, repo_name: str, sha: str) -> List[Dict[str, Any]]:
        """
        List GitHub Actions check runs for a commit via the Checks API.
        Returns list of check run dicts with name, status, conclusion, url.
        """
        if self._is_local_fallback():
            # No CI checks in offline mode — return empty
            return []

        try:
            gh = self._get_github()
            repo = gh.get_repo(f"{self.org}/{repo_name}")
            checks = repo.get_check_runs(ref=sha)
            return [
                {
                    "id": cr.id,
                    "name": cr.name,
                    "status": cr.status,          # "queued" | "in_progress" | "completed"
                    "conclusion": cr.conclusion,  # "success" | "failure" | "neutral" | "cancelled" | None
                    "html_url": cr.html_url,
                    "started_at": str(cr.started_at) if cr.started_at else None,
                    "completed_at": str(cr.completed_at) if cr.completed_at else None,
                    "head_sha": cr.head_sha,
                }
                for cr in checks
            ]
        except Exception as e:
            print(f"[git_client] Failed to list check runs: {e}")
            return []

    def get_check_run_annotations(self, repo_name: str, check_run_id: int) -> List[Dict[str, Any]]:
        """
        Get annotations for a specific check run (error messages with file/line info).
        Requires the Checks API (GitHub Actions annotations).
        """
        if self._is_local_fallback():
            return []

        try:
            gh = self._get_github()
            repo = gh.get_repo(f"{self.org}/{repo_name}")
            annotations = repo.get_check_run_annotations(check_run_id)
            return [
                {
                    "path": ann.path,
                    "start_line": ann.start_line,
                    "end_line": ann.end_line,
                    "annotation_level": ann.annotation_level,  # "notice" | "warning" | "failure"
                    "message": ann.message,
                    "raw_details": ann.raw_details,
                }
                for ann in annotations
            ]
        except Exception as e:
            print(f"[git_client] Failed to get annotations for check {check_run_id}: {e}")
            return []

    def get_failed_check_logs(self, repo_name: str, branch: str) -> str:
        """
        High-level helper: fetch logs for failed CI check runs on a branch.
        Combines check run metadata + annotations into a readable log string.
        Returns a formatted string suitable for feeding to the LLM.
        """
        sha = self.get_branch_sha(repo_name, branch)
        if not sha:
            return f"Could not determine latest commit SHA for branch '{branch}' on repo '{repo_name}'."

        check_runs = self.list_check_runs(repo_name, sha)
        if not check_runs:
            return f"No CI check runs found for {repo_name}@{sha[:7]} (branch: {branch})."

        # Filter to failed/completed runs
        failed = [cr for cr in check_runs if cr.get("conclusion") in ("failure", "cancelled")]
        if not failed:
            completed = [cr for cr in check_runs if cr.get("status") == "completed"]
            if completed and all(cr.get("conclusion") == "success" for cr in completed):
                return ""  # All passed — no logs needed
            # Still in progress or no failures
            return f"CI checks for {repo_name}@{sha[:7]} are not failed. Statuses: " + \
                   ", ".join(f"{cr['name']}={cr['conclusion'] or cr['status']}" for cr in check_runs)

        # Build log output from failed checks + annotations
        log_parts = [f"CI Failure Report for {repo_name}@{sha[:7]} (branch: {branch})\n"]
        for cr in failed:
            log_parts.append(f"\n{'='*60}")
            log_parts.append(f"Check: {cr['name']}")
            log_parts.append(f"Conclusion: {cr['conclusion']}")
            log_parts.append(f"URL: {cr.get('html_url', 'N/A')}")
            if cr.get("completed_at"):
                log_parts.append(f"Completed: {cr['completed_at']}")

            # Fetch annotations for this failed check
            annotations = self.get_check_run_annotations(repo_name, cr["id"])
            if annotations:
                log_parts.append(f"\nAnnotations ({len(annotations)}):")
                for ann in annotations:
                    level = ann.get("annotation_level", "notice").upper()
                    path = ann.get("path", "?")
                    line = ann.get("start_line", "?")
                    msg = ann.get("message", "")
                    log_parts.append(f"  [{level}] {path}:{line} — {msg}")
            else:
                log_parts.append("\n(No annotations available — check the Actions log URL for details.)")

        return "\n".join(log_parts)

    def trigger_workflow(self, repo_name: str, workflow_filename: str,
                         ref: str, inputs: Optional[Dict[str, Any]] = None) -> bool:
        """
        Dispatch a GitHub Actions workflow with inputs.
        workflow_filename e.g. "deploy.yml", ref e.g. "main".
        Returns True if dispatch succeeded.
        """
        if self._is_local_fallback():
            print(f"[git_client] Offline mode: would trigger {workflow_filename} on {repo_name}@{ref}")
            return True

        try:
            gh = self._get_github()
            repo = gh.get_repo(f"{self.org}/{repo_name}")
            workflow = repo.get_workflow(workflow_filename)
            success = workflow.create_dispatch(ref=ref, inputs=inputs or {})
            if success:
                print(f"[git_client] Triggered {workflow_filename} on {repo_name}@{ref}")
            return success
        except Exception as e:
            print(f"[git_client] Failed to trigger workflow {workflow_filename}: {e}")
            return False


def get_git_client() -> GitClient:
    return GitClient()
