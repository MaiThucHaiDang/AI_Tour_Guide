"""Push project to GitHub using API (no git binary needed)."""
import os, sys, json, base64, tempfile, shutil, mimetypes
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

TOKEN = "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"
REPO = "MaiThucHaiDang/AI_Tour_Guide"
BRANCH = "BTK"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import requests
from dulwich import porcelain
from dulwich.repo import Repo
from dulwich.objects import Blob, Tree, Commit
from dulwich.diff_tree import tree_changes

def get_default_branch_sha():
    r = requests.get(f"https://api.github.com/repos/{REPO}/git/refs/heads/main", headers={"Authorization": f"Bearer {TOKEN}"})
    if r.status_code == 200:
        return r.json()["object"]["sha"], "main"
    r = requests.get(f"https://api.github.com/repos/{REPO}/git/refs/heads/master", headers={"Authorization": f"Bearer {TOKEN}"})
    if r.status_code == 200:
        return r.json()["object"]["sha"], "master"
    print("Could not find default branch:", r.text)
    return None, None

def create_branch(sha, branch_name):
    r = requests.post(
        f"https://api.github.com/repos/{REPO}/git/refs",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"ref": f"refs/heads/{branch_name}", "sha": sha}
    )
    if r.status_code == 201:
        print(f"Created branch {branch_name}")
        return True
    if r.status_code == 422:
        print(f"Branch {branch_name} already exists")
        return True
    print(f"Failed to create branch: {r.text}")
    return False

walker = None

def push_via_dulwich():
    global TOKEN, REPO, BRANCH, PROJECT_ROOT
    tmpdir = tempfile.mkdtemp()
    try:
        # Init repo
        repo_dir = os.path.join(tmpdir, "repo")
        os.makedirs(repo_dir, exist_ok=True)
        
        # Try to clone via dulwich
        remote_url = f"https://x-access-token:{TOKEN}@github.com/{REPO}.git"
        
        print("Cloning repository...")
        try:
            repo = porcelain.clone(remote_url, repo_dir, depth=1)
        except Exception as e:
            print(f"Clone failed (trying init + fetch): {e}")
            repo = Repo.init(repo_dir)
            porcelain.fetch(repo, remote_url)
        
        # Check if BTK branch exists
        try:
            btk_ref = repo.refs[b"refs/remotes/origin/" + BRANCH.encode()]
            print(f"BTK branch found at {btk_ref.decode()}")
            # Checkout BTK
            porcelain.checkout_branch(repo, repo.refs[b"HEAD"], branch=BRANCH.encode())
        except KeyError:
            print(f"BTK branch not found, creating from main")
            # Create BTK from HEAD
            repo.refs[b"refs/heads/" + BRANCH.encode()] = repo.head()
        
        # Copy project files (excluding .venv, __pycache__, .git, node_modules)
        ignore_dirs = {".venv", "__pycache__", ".git", "node_modules", "scripts"}
        ignore_ext = {".pyc"}
        
        for root, dirs, files in os.walk(PROJECT_ROOT):
            rel = os.path.relpath(root, PROJECT_ROOT)
            if rel == ".":
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
            else:
                parts = rel.split(os.sep)
                if parts[0] in ignore_dirs:
                    dirs.clear()
                    continue
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for fname in files:
                if any(fname.endswith(ext) for ext in ignore_ext):
                    continue
                src = os.path.join(root, fname)
                dst = os.path.join(repo_dir, rel, fname) if rel != "." else os.path.join(repo_dir, fname)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    shutil.copy2(src, dst)
                except:
                    pass
        
        # Add all, commit, push
        porcelain.add(repo, repo_dir)
        
        # Check for changes
        status = porcelain.get_tree_changes(repo)
        if not any(status.values()):
            print("No changes to commit")
            return True
        
        porcelain.commit(repo, message="feat: update seed data, increase LLM tokens, remove word limit, add nearby attractions")
        
        print("Pushing to BTK...")
        push_result = porcelain.push(repo, remote_url, f"refs/heads/{BRANCH}")
        print(f"Push result: {push_result}")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    print(f"Pushing {PROJECT_ROOT} to {REPO}:{BRANCH}")
    
    # Try API first to ensure branch exists
    sha, default_branch = get_default_branch_sha()
    if sha:
        create_branch(sha, BRANCH)
    
    success = push_via_dulwich()
    if success:
        print("Success! Pushed to BTK branch.")
        sys.exit(0)
    else:
        # Fallback: use raw GitHub API
        print("Dulwich failed, trying GitHub API...")
        sys.exit(1)

