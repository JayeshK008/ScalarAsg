from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class TeamMembership:
    """
    Many-to-many relationship: User ↔ Team
    Maps to: team_memberships table
    """
    membership_id: str
    team_id: str
    user_id: str
    role: str = 'member'  # admin, member
    joined_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dict for SQLite insertion."""
        return {
            'membership_id': self.membership_id,
            'team_id': self.team_id,
            'user_id': self.user_id,
            'role': self.role,
            'joined_at': self.joined_at.isoformat() if self.joined_at else datetime.utcnow().isoformat()
        }
