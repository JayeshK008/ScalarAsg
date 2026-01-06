from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

@dataclass
class Task:
    """
    Task entity - fundamental unit of work.
    Maps to: tasks table
    """
    task_id: str
    name: str
    created_by: str
    project_id: Optional[str] = None
    section_id: Optional[str] = None
    parent_task_id: Optional[str] = None  # For subtasks
    description: Optional[str] = None
    assignee_id: Optional[str] = None  # NULL = unassigned
    priority: Optional[str] = None  # low, medium, high, urgent
    due_date: Optional[date] = None
    start_date: Optional[date] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dict for SQLite insertion."""
        return {
            'task_id': self.task_id,
            'project_id': self.project_id,
            'section_id': self.section_id,
            'parent_task_id': self.parent_task_id,
            'name': self.name,
            'description': self.description,
            'assignee_id': self.assignee_id,
            'created_by': self.created_by,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'completed': 1 if self.completed else 0,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat(),
            'modified_at': self.modified_at.isoformat() if self.modified_at else datetime.utcnow().isoformat()
        }
