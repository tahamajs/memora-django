import os
import json
from pathlib import Path
from datetime import datetime
from django.conf import settings
import git
import openai

class GitHubSyncService:
    _repo = None
    _config = {}
    
    @classmethod
    def get_repo(cls):
        if cls._repo is None:
            notes_dir = Path(settings.NOTES_DIR)
            notes_dir.mkdir(exist_ok=True)
            
            try:
                cls._repo = git.Repo(notes_dir)
            except git.InvalidGitRepositoryError:
                cls._repo = git.Repo.init(notes_dir)
                
                # Create .gitignore
                gitignore = notes_dir / '.gitignore'
                gitignore.write_text('*.db\n*.sqlite\n.env\n__pycache__/\n*.pyc\n')
        
        return cls._repo
    
    @classmethod
    def configure(cls, username, token, repo_name):
        cls._config = {
            'username': username,
            'token': token,
            'repo_name': repo_name
        }
        
        repo = cls.get_repo()
        remote_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
        
        try:
            origin = repo.remote('origin')
            origin.set_url(remote_url)
        except ValueError:
            repo.create_remote('origin', remote_url)
    
    @classmethod
    def save_note_as_markdown(cls, note):
        notes_dir = Path(settings.NOTES_DIR) / 'notes'
        notes_dir.mkdir(exist_ok=True)
        
        filename = f"{note.id}_{cls._sanitize_filename(note.title)}.md"
        filepath = notes_dir / filename
        
        content = f"""---
id: {note.id}
title: {note.title}
tags: {json.dumps(note.tags)}
category: {note.category}
created: {note.created_at.isoformat()}
updated: {note.updated_at.isoformat()}
---

{note.content}
"""
        filepath.write_text(content, encoding='utf-8')
        return filepath
    
    @classmethod
    def commit_note(cls, note):
        try:
            # Save note as markdown
            cls.save_note_as_markdown(note)
            
            repo = cls.get_repo()
            
            # Stage changes
            repo.index.add('*')
            
            # Commit
            commit_message = f"Update: {note.title} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            commit = repo.index.commit(commit_message)
            
            # Push if configured
            if cls._config:
                try:
                    origin = repo.remote('origin')
                    origin.push()
                except Exception as e:
                    print(f"Failed to push: {e}")
            
            # Update note with commit hash
            note.git_commit_hash = commit.hexsha
            note.save(update_fields=['git_commit_hash'])
            
            return commit.hexsha
        except Exception as e:
            print(f"Failed to commit note: {e}")
            return None
    
    @classmethod
    def pull_changes(cls):
        repo = cls.get_repo()
        origin = repo.remote('origin')
        origin.pull()
    
    @classmethod
    def get_status(cls):
        repo = cls.get_repo()
        return {
            'is_dirty': repo.is_dirty(),
            'active_branch': str(repo.active_branch),
            'untracked_files': repo.untracked_files
        }
    
    @staticmethod
    def _sanitize_filename(filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:100]

class AIService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
    
    def summarize_note(self, content):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Summarize this note in 2-3 sentences."},
                    {"role": "user", "content": content}
                ],
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate_tags(self, content):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Suggest 3-5 tags as a JSON array for this content."},
                    {"role": "user", "content": content}
                ],
                max_tokens=100
            )
            tags_text = response.choices[0].message.content
            return json.loads(tags_text)
        except:
            return ["general"]
    
    def improve_writing(self, content, style="professional"):
        prompts = {
            "professional": "Make this text more professional and polished.",
            "casual": "Make this text more casual and conversational.",
            "concise": "Make this text more concise and to the point.",
            "academic": "Make this text more academic and formal."
        }
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompts.get(style, prompts["professional"])},
                    {"role": "user", "content": content}
                ],
                max_tokens=len(content.split()) * 2
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    def research_assistant(self, query, context_notes):
        context = "\n\n".join([
            f"Note: {note.title}\nContent: {note.content[:500]}"
            for note in context_notes[:5]
        ])
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a research assistant. Provide analysis, key findings, sources, and methodology suggestions."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuery: {query}"}
                ],
                max_tokens=1000
            )
            return {"analysis": response.choices[0].message.content}
        except Exception as e:
            return {"error": str(e)}