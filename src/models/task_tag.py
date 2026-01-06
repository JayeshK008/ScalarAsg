from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class TaskTag:
    """
    Many-to-many relationship: Task ↔ Tag
    Maps to: task_tags table
    """
    task_tag_id: str
    task_id: str
    tag_id: str
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dict for SQLite insertion."""
        return {
            'task_tag_id': self.task_tag_id,
            'task_id': self.task_id,
            'tag_id': self.tag_id,
            'created_at': self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat()
        }
