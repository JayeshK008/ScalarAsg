from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Team:
    """
    Team entity - groups of users within organization.
    Maps to: teams table
    """
    team_id: str
    organization_id: str
    name: str
    team_type: str  # Engineering, Marketing, Product, Operations, Sales
    description: Optional[str] = None
    privacy: str = 'public'  # public, private, secret
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dict for SQLite insertion."""
        return {
            'team_id': self.team_id,
            'organization_id': self.organization_id,
            'name': self.name,
            'description': self.description,
            'team_type': self.team_type,
            'privacy': self.privacy,
            'created_at': self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat()
        }
