from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Attachment:
    """
    File attachment on a task.
    Maps to: attachments table
    """
    attachment_id: str
    task_id: str
    uploaded_by: str
    filename: str
    file_type: Optional[str] = None  # image/png, application/pdf, etc.
    file_size_bytes: Optional[int] = None
    storage_url: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dict for SQLite insertion."""
        return {
            'attachment_id': self.attachment_id,
            'task_id': self.task_id,
            'uploaded_by': self.uploaded_by,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size_bytes': self.file_size_bytes,
            'storage_url': self.storage_url,
            'created_at': self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat()
        }
