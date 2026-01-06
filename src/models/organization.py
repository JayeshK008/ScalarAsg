from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Organization:
    """
    Top-level container for workspace.
    Maps to: organizations table
    """
    organization_id: str
    name: str
    domain: str
    is_organization: bool = True
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dict for SQLite insertion."""
        return {
            'organization_id': self.organization_id,
            'name': self.name,
            'domain': self.domain,
            'is_organization': 1 if self.is_organization else 0,
            'created_at': self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat()
        }
