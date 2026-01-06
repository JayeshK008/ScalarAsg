from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TaskDependency:
    """
    Task dependency (blocking relationship).
    
    Represents: "dependent_task is blocked by dependency_task"
    Example: Task B depends on Task A = Task A must complete before Task B can start
    
    Maps to: task_dependencies table
    """
    dependency_id: str
    dependent_task_id: str      # Task that is blocked
    dependency_task_id: str     # Task that blocks (must complete first)
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dict for SQLite insertion."""
        return {
            'dependency_id': self.dependency_id,
            'dependent_task_id': self.dependent_task_id,
            'dependency_task_id': self.dependency_task_id,
            'created_at': self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat()
        }
