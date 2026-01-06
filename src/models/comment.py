from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Comment:
    """
    Comment/Story on a task.
    Maps to: comments table
    """
    comment_id: str
    task_id: str
    user_id: str
    text: str
    is_pinned: bool = False
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dict for SQLite insertion."""
        return {
            'comment_id': self.comment_id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'text': self.text,
            'is_pinned': 1 if self.is_pinned else 0,
            'created_at': self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat()
        }
