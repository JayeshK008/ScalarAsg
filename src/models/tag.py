from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Tag:
    """
    Tag entity - labels that can be applied across projects.
    Maps to: tags table
    """
    tag_id: str
    organization_id: str
    name: str
    color: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dict for SQLite insertion."""
        return {
            'tag_id': self.tag_id,
            'organization_id': self.organization_id,
            'name': self.name,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat()
        }
