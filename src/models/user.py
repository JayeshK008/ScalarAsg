from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    """
    User entity with role and workload capacity.
    Maps to: users table
    """
    user_id: str
    organization_id: str
    email: str
    name: str
    role: str = 'member'  # admin, member, guest, limited
    department: Optional[str] = None
    job_title: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: bool = True
    workload_capacity: float = 1.0  # 0.0-2.0
    created_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dict for SQLite insertion."""
        return {
            'user_id': self.user_id,
            'organization_id': self.organization_id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'department': self.department,
            'job_title': self.job_title,
            'photo_url': self.photo_url,
            'is_active': 1 if self.is_active else 0,
            'workload_capacity': self.workload_capacity,
            'created_at': self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat(),
            'last_active_at': self.last_active_at.isoformat() if self.last_active_at else None
        }
