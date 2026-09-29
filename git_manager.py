import os
import sys
import argparse

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dulwich import porcelain
from dulwich.repo import Repo

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def init_and_commit(target_dir=ROOT_DIR, custom_msg=None):
    print("==================================================")
    print("GuardianFi Git Management Utility")
    print("==================================================")
    print(f"Target Directory: {target_dir}")
    
    # 1. Init repo
    git_dir = os.path.join(target_dir, ".git")
    if not os.path.exists(git_dir):
        repo = porcelain.init(target_dir)
        print("✓ Git repository initialized successfully.")
    else:
        repo = Repo(target_dir)
        print("✓ Existing Git repository loaded.")

    # 2. Configure user identity
    config = repo.get_config()
    config.set((b"user",), b"name", b"Kommanapalli Alivelu Manga Tayaru")
    config.set((b"user",), b"email", b"roadrollersayitshot@gmail.com")
    config.set((b"init",), b"defaultBranch", b"main")
    config.write_to_path()
    print("✓ Author: Kommanapalli Alivelu Manga Tayaru <roadrollersayitshot@gmail.com>")

    # 3. Collect files to add (respecting ignore rules)
    files_to_add = []
    for root, dirs, files in os.walk(target_dir):
        # Skip ignore directories
        if ".git" in dirs:
            dirs.remove(".git")
        if ".venv" in dirs:
            dirs.remove(".venv")
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
            
        for f in files:
            if f.startswith("~$") or f.endswith(".tmp") or f.endswith(".pyc"):
                continue
            rel_path = os.path.relpath(os.path.join(root, f), target_dir)
            files_to_add.append(rel_path)

    print(f"✓ Staging {len(files_to_add)} project files...")
    porcelain.add(repo, paths=files_to_add)

    # 4. Commit
    if custom_msg:
        commit_msg = custom_msg.encode("utf-8")
    else:
        commit_msg = (
            b"feat: Complete GuardianFi AI Autonomous Personal CFO platform\n\n"
            b"- Full-stack fiduciary financial intelligence application with zero-bloat Canvas 2D engine\n"
            b"- Dynamic Guardian Trust Score (0-900) & Debt Capacity Circuit Breaker\n"
            b"- Automated relational database synchronization (User data base.xlsx via Python openpyxl)\n"
            b"- Role-Based Access Control (Admin: roadrollersayitshot@gmail.com)\n"
            b"- Complete 10-slide Presentation Decks for AI QUEST & BIZIGNITE\n"
            b"- Print-ready high-resolution A3 Posters for AI QUEST & BIZIGNITE"
        )
    
    try:
        commit_id = porcelain.commit(
            repo,
            message=commit_msg,
            author=b"Kommanapalli Alivelu Manga Tayaru <roadrollersayitshot@gmail.com>",
            committer=b"Kommanapalli Alivelu Manga Tayaru <roadrollersayitshot@gmail.com>"
        )
        repo.refs[b"refs/heads/main"] = commit_id
        repo.refs.set_symbolic_ref(b"HEAD", b"refs/heads/main")
        print(f"✓ Commit created: {commit_id.decode('ascii')[:8]} on branch 'main'")
    except Exception as e:
        print(f"ℹ️ Working tree clean or up to date: {e}")

    return repo

def push_to_remote(remote_url, target_dir=ROOT_DIR):
    repo = Repo(target_dir)
    print(f"Pushing to remote repository: {remote_url}")
    try:
        porcelain.remote_add(repo, b"origin", remote_url.encode("utf-8"))
    except Exception:
        pass # already added
        
    try:
        porcelain.push(repo, remote_url.encode("utf-8"), b"refs/heads/main:refs/heads/main")
        print(f"✓ Successfully pushed branch 'main' to {remote_url}!")
    except Exception as e:
        print(f"⚠️ Push error: {e}")
        print("Note: If using GitHub, make sure to provide a Personal Access Token (PAT) in the URL:")
        print("Format: https://<TOKEN>@github.com/<USERNAME>/<REPO>.git")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GuardianFi Git Management")
    parser.add_argument("--push", help="Remote Git repository URL to push to")
    parser.add_argument("--message", "-m", help="Custom commit message")
    args = parser.parse_args()

    repo = init_and_commit(custom_msg=args.message)
    if args.push:
        push_to_remote(args.push)
    else:
        print("\n--------------------------------------------------")
        print("🚀 To push to your GitHub / GitLab repository, run:")
        print("  .venv\\Scripts\\python.exe git_manager.py --push https://<TOKEN>@github.com/<USERNAME>/<REPO>.git")
        print("--------------------------------------------------")
