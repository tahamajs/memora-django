"""
Git Service for version control and GitHub sync.
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import git
from git import Repo, GitCommandError
from django.conf import settings
from django.utils import timezone
import requests

logger = logging.getLogger(__name__)


@dataclass
class GitConfig:
    """Git configuration."""
    username: str = "Local Notion User"
    email: str = "user@localnotion.com"
    repo_path: str = ""
    remote_name: str = "origin"
    branch: str = "main"


@dataclass
class GitHubConfig:
    """GitHub configuration."""
    username: str = ""
    token: str = ""
    repo_name: str = ""
    api_url: str = "https://api.github.com"


class GitService:
    """Service for Git operations."""
    
    _repo: Optional[Repo] = None
    _config: Optional[GitConfig] = None
    _github_config: Optional[GitHubConfig] = None
    _initialized: bool = False
    
    @classmethod
    def initialize(cls):
        """Initialize Git service and repository."""
        if cls._initialized:
            return
        
        # Set configuration
        cls._config = GitConfig(
            username=settings.GITHUB_USERNAME or "Local Notion User",
            email=f"{settings.GITHUB_USERNAME or 'user'}@localnotion.com",
            repo_path=str(settings.NOTES_DIR),
        )
        
        if settings.GITHUB_TOKEN:
            cls._github_config = GitHubConfig(
                username=settings.GITHUB_USERNAME or "",
                token=settings.GITHUB_TOKEN,
                repo_name=settings.GITHUB_REPO or "",
            )
        
        # Initialize repository
        cls._init_repo()
        cls._initialized = True
        logger.info("Git service initialized")
    
    @classmethod
    def _init_repo(cls):
        """Initialize or open Git repository."""
        repo_path = Path(cls._config.repo_path)
        repo_path.mkdir(parents=True, exist_ok=True)
        
        try:
            cls._repo = Repo(repo_path)
        except git.InvalidGitRepositoryError:
            cls._repo = Repo.init(repo_path)
            
            # Create initial .gitignore
            gitignore_path = repo_path / '.gitignore'
            if not gitignore_path.exists():
                gitignore_content = """
# Database files
*.db
*.sqlite
*.sqlite3

# Environment files
.env
.env.*

# Python cache
__pycache__/
*.pyc

# OS files
.DS_Store
Thumbs.db
"""
                gitignore_path.write_text(gitignore_content)
            
            # Initial commit
            cls._repo.index.add(['.gitignore'])
            cls._repo.index.commit("🎉 Initial commit: Local Notion Clone repository")
        
        # Configure user
        with cls._repo.config_writer() as config:
            config.set_value("user", "name", cls._config.username)
            config.set_value("user", "email", cls._config.email)
    
    @classmethod
    def get_repo(cls) -> Repo:
        """Get Git repository instance."""
        if not cls._repo:
            cls.initialize()
        return cls._repo
    
    @classmethod
    def save_note_as_markdown(cls, note) -> str:
        """
        Save a note as a Markdown file in the repository.
        
        Args:
            note: Note model instance
            
        Returns:
            str: Path to the saved file
        """
        notes_dir = Path(cls._config.repo_path) / 'notes'
        notes_dir.mkdir(exist_ok=True)
        
        # Create filename
        safe_title = cls._sanitize_filename(note.title or 'Untitled')
        filename = f"{note.id}_{safe_title}.md"
        filepath = notes_dir / filename
        
        # Build frontmatter
        frontmatter = {
            'id': str(note.id),
            'title': note.title,
            'tags': note.tag_list,
            'category': note.category.name if note.category else 'General',
            'status': note.status,
            'priority': note.priority,
            'created': note.created_at.isoformat() if note.created_at else '',
            'updated': note.updated_at.isoformat() if note.updated_at else '',
            'author': note.author.username if note.author else '',
            'version': note.version,
        }
        
        # Build markdown content
        content = "---\n"
        content += "\n".join([f"{k}: {json.dumps(v) if isinstance(v, list) else v}" 
                             for k, v in frontmatter.items()])
        content += "\n---\n\n"
        content += note.content or note.markdown_content or ''
        
        # Write file
        filepath.write_text(content, encoding='utf-8')
        
        return str(filepath)
    
    @classmethod
    def commit_note(cls, note, message: str = None) -> Optional[str]:
        """
        Commit a note to Git.
        
        Args:
            note: Note model instance
            message: Commit message (optional)
            
        Returns:
            str: Commit hash if successful, None otherwise
        """
        try:
            repo = cls.get_repo()
            
            # Save note as markdown
            cls.save_note_as_markdown(note)
            
            # Stage changes
            repo.index.add('*')
            
            # Create commit message
            if not message:
                action = "Updated" if note.version > 1 else "Created"
                message = f"{action}: {note.title} - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Commit
            commit = repo.index.commit(message)
            
            # Update note with commit hash
            note.git_commit_hash = commit.hexsha
            note.save(update_fields=['git_commit_hash'])
            
            # Create version record
            from apps.notes.models import NoteVersion
            NoteVersion.objects.create(
                note=note,
                version_number=note.version,
                title=note.title,
                content=note.content,
                commit_message=message,
                commit_hash=commit.hexsha,
                created_by=note.author,
            )
            
            logger.info(f"Committed note {note.id}: {commit.hexsha[:7]}")
            return commit.hexsha
            
        except Exception as e:
            logger.error(f"Failed to commit note {note.id}: {e}")
            return None
    
    @classmethod
    def get_note_history(cls, note) -> List[Dict[str, Any]]:
        """
        Get commit history for a note.
        
        Args:
            note: Note model instance
            
        Returns:
            List of commit information
        """
        try:
            repo = cls.get_repo()
            
            # Find the note file
            notes_dir = Path(cls._config.repo_path) / 'notes'
            note_files = list(notes_dir.glob(f"{note.id}_*.md"))
            
            if not note_files:
                return []
            
            note_path = str(note_files[0].relative_to(cls._config.repo_path))
            
            # Get commit history for the file
            commits = list(repo.iter_commits(paths=note_path))
            
            history = []
            for commit in commits:
                history.append({
                    'hash': commit.hexsha,
                    'short_hash': commit.hexsha[:7],
                    'message': commit.message.strip(),
                    'author': str(commit.author),
                    'date': commit.committed_datetime.isoformat(),
                    'stats': commit.stats.files.get(note_path, {}),
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get history for note {note.id}: {e}")
            return []
    
    @classmethod
    def get_repo_status(cls) -> Dict[str, Any]:
        """
        Get repository status.
        
        Returns:
            Dict with repository status information
        """
        try:
            repo = cls.get_repo()
            
            # Get current branch
            try:
                branch = repo.active_branch.name
            except TypeError:
                branch = "main"
            
            # Get status
            status = {
                'branch': branch,
                'is_dirty': repo.is_dirty(),
                'untracked_files': repo.untracked_files,
                'changed_files': [item.a_path for item in repo.index.diff(None)],
                'staged_files': [item.a_path for item in repo.index.diff('HEAD')],
                'last_commit': None,
                'total_commits': 0,
                'remote_configured': bool(cls._github_config),
            }
            
            # Get last commit info
            try:
                head_commit = repo.head.commit
                status['last_commit'] = {
                    'hash': head_commit.hexsha,
                    'short_hash': head_commit.hexsha[:7],
                    'message': head_commit.message.strip(),
                    'author': str(head_commit.author),
                    'date': head_commit.committed_datetime.isoformat(),
                }
                status['total_commits'] = len(list(repo.iter_commits()))
            except Exception:
                pass
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get repo status: {e}")
            return {'error': str(e)}
    
    @classmethod
    def configure_github(cls, username: str, token: str, repo_name: str):
        """
        Configure GitHub remote.
        
        Args:
            username: GitHub username
            token: Personal access token
            repo_name: Repository name
        """
        cls._github_config = GitHubConfig(
            username=username,
            token=token,
            repo_name=repo_name,
        )
        
        repo = cls.get_repo()
        remote_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
        
        try:
            # Check if remote exists
            try:
                origin = repo.remote('origin')
                origin.set_url(remote_url)
            except ValueError:
                repo.create_remote('origin', remote_url)
            
            logger.info(f"GitHub remote configured: {username}/{repo_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure GitHub: {e}")
            raise
    
    @classmethod
    def push_to_github(cls) -> bool:
        """
        Push changes to GitHub.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not cls._github_config or not cls._github_config.token:
            logger.warning("GitHub not configured")
            return False
        
        try:
            repo = cls.get_repo()
            origin = repo.remote('origin')
            origin.push()
            
            logger.info("Successfully pushed to GitHub")
            return True
            
        except Exception as e:
            logger.error(f"Failed to push to GitHub: {e}")
            return False
    
    @classmethod
    def pull_from_github(cls) -> bool:
        """
        Pull changes from GitHub.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not cls._github_config:
            logger.warning("GitHub not configured")
            return False
        
        try:
            repo = cls.get_repo()
            origin = repo.remote('origin')
            origin.pull()
            
            logger.info("Successfully pulled from GitHub")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pull from GitHub: {e}")
            return False
    
    @classmethod
    def sync_all_notes(cls) -> Dict[str, Any]:
        """
        Sync all notes to Git.
        
        Returns:
            Dict with sync results
        """
        from apps.notes.models import Note
        
        results = {
            'total': 0,
            'synced': 0,
            'failed': 0,
            'commit_hash': None,
        }
        
        try:
            notes = Note.objects.all()
            results['total'] = notes.count()
            
            for note in notes:
                try:
                    cls.save_note_as_markdown(note)
                    results['synced'] += 1
                except Exception as e:
                    logger.error(f"Failed to sync note {note.id}: {e}")
                    results['failed'] += 1
            
            # Commit all changes
            if results['synced'] > 0:
                commit_hash = cls.commit_all_changes()
                results['commit_hash'] = commit_hash
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to sync all notes: {e}")
            return {'error': str(e)}
    
    @classmethod
    def commit_all_changes(cls, message: str = None) -> Optional[str]:
        """
        Commit all changes in the repository.
        
        Args:
            message: Commit message
            
        Returns:
            str: Commit hash if successful
        """
        try:
            repo = cls.get_repo()
            
            if not repo.is_dirty():
                return None
            
            repo.index.add('*')
            
            if not message:
                message = f"📝 Batch update: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            commit = repo.index.commit(message)
            return commit.hexsha
            
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            return None
    
    @classmethod
    def create_backup_branch(cls, name: str = None) -> str:
        """
        Create a backup branch.
        
        Args:
            name: Branch name (default: backup-YYYYMMDD-HHMMSS)
            
        Returns:
            str: Branch name
        """
        if not name:
            name = f"backup-{timezone.now().strftime('%Y%m%d-%H%M%S')}"
        
        try:
            repo = cls.get_repo()
            current = repo.active_branch
            
            # Create and checkout new branch
            new_branch = repo.create_head(name)
            new_branch.checkout()
            
            # Commit any pending changes
            if repo.is_dirty():
                repo.index.add('*')
                repo.index.commit(f"💾 Backup: {name}")
            
            # Switch back to original branch
            current.checkout()
            
            return name
            
        except Exception as e:
            logger.error(f"Failed to create backup branch: {e}")
            raise
    
    @classmethod
    def get_file_content(cls, filepath: str, version: str = None) -> Optional[str]:
        """
        Get content of a file at a specific version.
        
        Args:
            filepath: Path to file in repository
            version: Git reference (commit hash, branch, tag)
            
        Returns:
            str: File content if found
        """
        try:
            repo = cls.get_repo()
            
            if version:
                commit = repo.commit(version)
                blob = commit.tree / filepath
            else:
                blob = (repo.head.commit.tree / filepath)
            
            return blob.data_stream.read().decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to get file content: {e}")
            return None
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for cross-platform compatibility.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename or 'untitled'