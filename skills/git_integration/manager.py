import os
import subprocess
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CommitInfo:
    hash: str
    message: str
    author: str
    date: str
    files_changed: int
    insertions: int
    deletions: int

@dataclass
class BranchInfo:
    name: str
    is_current: bool
    is_remote: bool
    ahead: int
    behind: int

@dataclass
class PRInfo:
    number: int
    title: str
    body: str
    author: str
    state: str
    created_at: str
    updated_at: str
    branch: str
    base_branch: str

class GitManager:
    def __init__(self, work_dir: str = None):
        self.work_dir = Path(work_dir).expanduser() if work_dir else Path.cwd()
        self._ensure_git()
    
    def _ensure_git(self):
        """Ensure git is installed"""
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
        except:
            raise RuntimeError("Git is not installed")
    
    def _run_git(self, args: List[str], cwd: str = None, check: bool = True) -> Tuple[str, str, int]:
        """Run git command"""
        work_dir = Path(cwd).expanduser() if cwd else self.work_dir
        
        result = subprocess.run(
            ['git'] + args,
            cwd=work_dir,
            capture_output=True,
            text=True
        )
        
        if check and result.returncode != 0:
            raise RuntimeError(f"Git error: {result.stderr}")
        
        return result.stdout, result.stderr, result.returncode
    
    def is_repo(self, path: str = None) -> bool:
        """Check if directory is a git repository"""
        try:
            self._run_git(['rev-parse', '--git-dir'], cwd=path, check=False)
            return True
        except:
            return False
    
    def init_repo(self, path: str, bare: bool = False) -> bool:
        """Initialize a new git repository"""
        try:
            args = ['init']
            if bare:
                args.append('--bare')
            args.append(path)
            
            self._run_git(args, cwd='/')
            
            # Create initial .gitignore
            gitignore_path = Path(path) / '.gitignore'
            if not gitignore_path.exists():
                gitignore_path.write_text(self._default_gitignore())
            
            return True
        except Exception as e:
            print(f"Error initializing repo: {e}")
            return False
    
    def clone(self, url: str, path: str = None, branch: str = None) -> bool:
        """Clone a repository"""
        try:
            args = ['clone']
            if branch:
                args.extend(['-b', branch])
            args.append(url)
            if path:
                args.append(path)
            
            self._run_git(args, cwd='/')
            return True
        except Exception as e:
            print(f"Error cloning repo: {e}")
            return False
    
    def get_status(self, path: str = None) -> Dict:
        """Get repository status"""
        try:
            stdout, _, _ = self._run_git(['status', '--porcelain', '-b'], cwd=path)
            
            lines = stdout.strip().split('\n')
            branch_line = lines[0] if lines else ''
            
            # Parse branch info
            branch_match = re.search(r'## (.+)\.\.\.(.*)', branch_line)
            branch = branch_match.group(1) if branch_match else 'unknown'
            remote = branch_match.group(2) if branch_match and branch_match.group(2) else None
            
            # Parse file status
            staged = []
            unstaged = []
            untracked = []
            
            for line in lines[1:]:
                if not line.strip():
                    continue
                
                status = line[:2]
                filename = line[3:]
                
                if status[0] != ' ' and status[0] != '?':
                    staged.append({'status': status[0], 'file': filename})
                if status[1] != ' ':
                    unstaged.append({'status': status[1], 'file': filename})
                if status == '??':
                    untracked.append(filename)
            
            return {
                'branch': branch,
                'remote': remote,
                'ahead': 0,  # TODO: parse from branch_line
                'behind': 0,
                'staged': staged,
                'unstaged': unstaged,
                'untracked': untracked,
                'is_clean': len(staged) == 0 and len(unstaged) == 0 and len(untracked) == 0
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_branches(self, path: str = None, remote: bool = False) -> List[BranchInfo]:
        """List branches"""
        try:
            args = ['branch', '-vv']
            if remote:
                args.append('-a')
            
            stdout, _, _ = self._run_git(args, cwd=path)
            
            branches = []
            for line in stdout.strip().split('\n'):
                if not line.strip():
                    continue
                
                is_current = line.startswith('*')
                name = line[2:].split()[0] if not remote else line.strip()
                
                # Parse ahead/behind
                ahead = 0
                behind = 0
                match = re.search(r'\[.+?:(?: ahead (\d+))?(?:,)?(?: behind (\d+))?\]', line)
                if match:
                    ahead = int(match.group(1)) if match.group(1) else 0
                    behind = int(match.group(2)) if match.group(2) else 0
                
                branches.append(BranchInfo(
                    name=name,
                    is_current=is_current,
                    is_remote=remote,
                    ahead=ahead,
                    behind=behind
                ))
            
            return branches
        except Exception as e:
            return []
    
    def create_branch(self, name: str, from_branch: str = None, path: str = None) -> bool:
        """Create and checkout a new branch"""
        try:
            args = ['checkout', '-b', name]
            if from_branch:
                args.append(from_branch)
            
            self._run_git(args, cwd=path)
            return True
        except Exception as e:
            print(f"Error creating branch: {e}")
            return False
    
    def checkout(self, branch: str, path: str = None, create: bool = False) -> bool:
        """Checkout a branch"""
        try:
            args = ['checkout']
            if create:
                args.append('-b')
            args.append(branch)
            
            self._run_git(args, cwd=path)
            return True
        except Exception as e:
            print(f"Error checking out branch: {e}")
            return False
    
    def add(self, files: List[str] = None, all_files: bool = False, path: str = None) -> bool:
        """Stage files"""
        try:
            args = ['add']
            if all_files:
                args.append('.')
            elif files:
                args.extend(files)
            else:
                args.append('.')
            
            self._run_git(args, cwd=path)
            return True
        except Exception as e:
            print(f"Error adding files: {e}")
            return False
    
    def commit(self, message: str, path: str = None, amend: bool = False) -> bool:
        """Create a commit"""
        try:
            args = ['commit', '-m', message]
            if amend:
                args.append('--amend')
            
            self._run_git(args, cwd=path)
            return True
        except Exception as e:
            print(f"Error creating commit: {e}")
            return False
    
    def smart_commit(self, path: str = None, custom_message: str = None) -> Dict:
        """AI-powered commit with auto-generated message"""
        try:
            status = self.get_status(path)
            
            if status.get('is_clean'):
                return {'success': False, 'message': 'No changes to commit'}
            
            # Get diff stats
            stdout, _, _ = self._run_git(['diff', '--cached', '--stat'], cwd=path)
            
            # Stage all if nothing staged
            if not status.get('staged'):
                self.add(all_files=True, path=path)
            
            # Generate commit message
            if custom_message:
                message = custom_message
            else:
                message = self._generate_commit_message(status, stdout)
            
            # Create commit
            self.commit(message, path)
            
            return {
                'success': True,
                'message': message,
                'files_changed': len(status.get('staged', [])) + len(status.get('unstaged', []))
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generate_commit_message(self, status: Dict, diff_stat: str) -> str:
        """Generate commit message based on changes"""
        staged = status.get('staged', [])
        unstaged = status.get('unstaged', [])
        
        all_files = [f['file'] for f in staged + unstaged]
        
        # Detect change type
        if any('test' in f.lower() for f in all_files):
            prefix = "test"
        elif any(f.endswith('.md') or 'readme' in f.lower() for f in all_files):
            prefix = "docs"
        elif any('fix' in f.lower() or 'bug' in f.lower() for f in all_files):
            prefix = "fix"
        elif any('feature' in f.lower() or 'add' in f.lower() for f in all_files):
            prefix = "feat"
        else:
            prefix = "chore"
        
        # Generate description
        if len(all_files) == 1:
            desc = f"update {Path(all_files[0]).name}"
        elif len(all_files) <= 3:
            desc = f"update {', '.join(Path(f).name for f in all_files)}"
        else:
            desc = f"update {len(all_files)} files"
        
        return f"{prefix}: {desc}"
    
    def get_log(self, limit: int = 10, path: str = None, branch: str = None) -> List[CommitInfo]:
        """Get commit history"""
        try:
            args = ['log', f'-{limit}', '--pretty=format:%H|%s|%an|%ad|%d', '--date=short']
            if branch:
                args.append(branch)
            
            stdout, _, _ = self._run_git(args, cwd=path)
            
            commits = []
            for line in stdout.strip().split('\n'):
                if '|' not in line:
                    continue
                
                parts = line.split('|')
                if len(parts) >= 4:
                    commits.append(CommitInfo(
                        hash=parts[0][:7],
                        message=parts[1],
                        author=parts[2],
                        date=parts[3],
                        files_changed=0,
                        insertions=0,
                        deletions=0
                    ))
            
            return commits
        except Exception as e:
            return []
    
    def get_diff(self, path: str = None, staged: bool = False, 
                file: str = None, commit1: str = None, commit2: str = None) -> str:
        """Get diff"""
        try:
            args = ['diff']
            if staged:
                args.append('--cached')
            if file:
                args.append(file)
            if commit1 and commit2:
                args.extend([commit1, commit2])
            
            stdout, _, _ = self._run_git(args, cwd=path)
            return stdout
        except Exception as e:
            return f"Error: {e}"
    
    def push(self, remote: str = 'origin', branch: str = None, 
            path: str = None, force: bool = False) -> bool:
        """Push to remote"""
        try:
            args = ['push']
            if force:
                args.append('--force-with-lease')
            args.append(remote)
            if branch:
                args.append(branch)
            
            self._run_git(args, cwd=path)
            return True
        except Exception as e:
            print(f"Error pushing: {e}")
            return False
    
    def pull(self, remote: str = 'origin', branch: str = None, path: str = None) -> bool:
        """Pull from remote"""
        try:
            args = ['pull']
            if remote:
                args.append(remote)
            if branch:
                args.append(branch)
            
            self._run_git(args, cwd=path)
            return True
        except Exception as e:
            print(f"Error pulling: {e}")
            return False
    
    def fetch(self, remote: str = 'origin', path: str = None) -> bool:
        """Fetch from remote"""
        try:
            self._run_git(['fetch', remote], cwd=path)
            return True
        except Exception as e:
            print(f"Error fetching: {e}")
            return False
    
    def merge(self, branch: str, path: str = None, no_ff: bool = False) -> Dict:
        """Merge a branch"""
        try:
            args = ['merge']
            if no_ff:
                args.append('--no-ff')
            args.append(branch)
            
            stdout, stderr, code = self._run_git(args, cwd=path, check=False)
            
            if code != 0:
                if 'CONFLICT' in stdout or 'CONFLICT' in stderr:
                    return {
                        'success': False,
                        'has_conflicts': True,
                        'message': 'Merge conflicts detected',
                        'conflicts': self._get_conflicts(path)
                    }
                return {'success': False, 'error': stderr}
            
            return {'success': True, 'message': 'Merge successful'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_conflicts(self, path: str = None) -> List[str]:
        """Get list of conflicted files"""
        try:
            stdout, _, _ = self._run_git(['diff', '--name-only', '--diff-filter=U'], cwd=path)
            return [f for f in stdout.strip().split('\n') if f]
        except:
            return []
    
    def stash(self, message: str = None, path: str = None) -> bool:
        """Stash changes"""
        try:
            args = ['stash', 'push']
            if message:
                args.extend(['-m', message])
            
            self._run_git(args, cwd=path)
            return True
        except Exception as e:
            print(f"Error stashing: {e}")
            return False
    
    def stash_pop(self, index: int = 0, path: str = None) -> bool:
        """Pop stash"""
        try:
            args = ['stash', 'pop']
            if index > 0:
                args.append(f'stash@{{{index}}}')
            
            self._run_git(args, cwd=path)
            return True
        except Exception as e:
            print(f"Error popping stash: {e}")
            return False
    
    def get_remotes(self, path: str = None) -> List[Dict]:
        """List remote repositories"""
        try:
            stdout, _, _ = self._run_git(['remote', '-v'], cwd=path)
            
            remotes = {}
            for line in stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    url = parts[1]
                    remotes[name] = url
            
            return [{'name': k, 'url': v} for k, v in remotes.items()]
        except Exception as e:
            return []
    
    def add_remote(self, name: str, url: str, path: str = None) -> bool:
        """Add remote repository"""
        try:
            self._run_git(['remote', 'add', name, url], cwd=path)
            return True
        except Exception as e:
            print(f"Error adding remote: {e}")
            return False
    
    def create_pr(self, repo: str, title: str, body: str, 
                 head_branch: str, base_branch: str = 'main') -> Dict:
        """Create pull request using gh CLI"""
        try:
            # Check if gh CLI is installed
            subprocess.run(['gh', '--version'], capture_output=True, check=True)
            
            # Create PR
            cmd = [
                'gh', 'pr', 'create',
                '--repo', repo,
                '--title', title,
                '--body', body,
                '--head', head_branch,
                '--base', base_branch
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'url': result.stdout.strip(),
                    'message': 'PR created successfully'
                }
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_prs(self, repo: str, state: str = 'open') -> List[Dict]:
        """List pull requests"""
        try:
            cmd = ['gh', 'pr', 'list', '--repo', repo, '--state', state, '--json', 'number,title,author,state,createdAt,headRefName,baseRefName']
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                import json
                return json.loads(result.stdout)
            else:
                return []
        except Exception as e:
            return []
    
    def review_pr(self, repo: str, pr_number: int, action: str = 'view') -> Dict:
        """Review a PR"""
        try:
            if action == 'view':
                cmd = ['gh', 'pr', 'view', str(pr_number), '--repo', repo]
            elif action == 'checkout':
                cmd = ['gh', 'pr', 'checkout', str(pr_number), '--repo', repo]
            elif action == 'merge':
                cmd = ['gh', 'pr', 'merge', str(pr_number), '--repo', repo, '--squash']
            elif action == 'close':
                cmd = ['gh', 'pr', 'close', str(pr_number), '--repo', repo]
            else:
                return {'success': False, 'error': 'Unknown action'}
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def analyze_diff(self, path: str = None) -> Dict:
        """Analyze code diff for review"""
        try:
            # Get diff stats
            stdout, _, _ = self._run_git(['diff', '--cached', '--stat'], cwd=path)
            
            # Get changed files
            stdout2, _, _ = self._run_git(['diff', '--cached', '--name-only'], cwd=path)
            files = [f for f in stdout2.strip().split('\n') if f]
            
            # Analyze each file
            analysis = {
                'files_changed': len(files),
                'files': [],
                'summary': stdout,
                'suggestions': []
            }
            
            for file in files:
                # Get file diff
                diff, _, _ = self._run_git(['diff', '--cached', file], cwd=path)
                
                file_analysis = {
                    'file': file,
                    'lines_added': diff.count('\n+'),
                    'lines_removed': diff.count('\n-'),
                    'issues': []
                }
                
                # Check for common issues
                if 'TODO' in diff or 'FIXME' in diff:
                    file_analysis['issues'].append('Contains TODO/FIXME comments')
                if 'print(' in diff and file.endswith('.py'):
                    file_analysis['issues'].append('Contains debug print statements')
                if 'debugger' in diff.lower():
                    file_analysis['issues'].append('Contains debugger statements')
                
                analysis['files'].append(file_analysis)
            
            return analysis
        except Exception as e:
            return {'error': str(e)}
    
    def _default_gitignore(self) -> str:
        """Default .gitignore content"""
        return """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Environment variables
.env
.env.local
.env.*.local

# Logs
*.log
logs/

# Database
*.db
*.sqlite
*.sqlite3
"""

class GitHubActions:
    """GitHub Actions workflow manager"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.workflows_dir = self.repo_path / '.github' / 'workflows'
    
    def create_workflow(self, name: str, content: str) -> bool:
        """Create a GitHub Actions workflow"""
        try:
            self.workflows_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_file = self.workflows_dir / f"{name}.yml"
            workflow_file.write_text(content)
            
            return True
        except Exception as e:
            print(f"Error creating workflow: {e}")
            return False
    
    def create_python_ci(self) -> bool:
        """Create Python CI workflow"""
        workflow = """name: Python CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest black flake8
    
    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    
    - name: Format check with black
      run: |
        black --check .
    
    - name: Test with pytest
      run: |
        pytest
"""
        return self.create_workflow('python-ci', workflow)
