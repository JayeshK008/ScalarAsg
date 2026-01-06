from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Section:
    """
    Section within a project (e.g., To Do, In Progress, Done).
    Maps to: sections table
    """
    section_id: str
    project_id: str
    name: str
    position: int
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dict for SQLite insertion."""
        return {
            'section_id': self.section_id,
            'project_id': self.project_id,
            'name': self.name,
            'position': self.position,
            'created_at': self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat()
        }
