from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

@dataclass
class Project:
    """
    Project entity - collection of tasks.
    Maps to: projects table
    """
    project_id: str
    organization_id: str
    name: str
    team_id: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[str] = None
    project_type: str = 'ongoing'  # sprint, ongoing, bug_tracking, campaign, roadmap
    privacy: str = 'team'  # public, team, private
    status: str = 'active'  # active, archived, completed, on_hold
    color: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dict for SQLite insertion."""
        return {
            'project_id': self.project_id,
            'organization_id': self.organization_id,
            'team_id': self.team_id,
            'name': self.name,
            'description': self.description,
            'owner_id': self.owner_id,
            'project_type': self.project_type,
            'privacy': self.privacy,
            'status': self.status,
            'color': self.color,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat()
        }
