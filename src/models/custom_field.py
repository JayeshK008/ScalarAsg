from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


@dataclass
class CustomFieldDefinition:
    """
    Custom field definition at project level.
    Maps to: custom_field_definitions table
    """
    field_id: str
    project_id: str
    name: str
    field_type: str  # text, number, enum, date, checkbox, user
    description: Optional[str] = None
    is_required: bool = False
    position: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dict for SQLite insertion."""
        return {
            'field_id': self.field_id,
            'project_id': self.project_id,
            'name': self.name,
            'field_type': self.field_type,
            'description': self.description,
            'is_required': 1 if self.is_required else 0,
            'position': self.position,
            'created_at': self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat()
        }


@dataclass
class CustomFieldEnumOption:
    """
    Enum options for custom fields (e.g., Priority: High/Medium/Low).
    Maps to: custom_field_enum_options table
    """
    option_id: str
    field_id: str
    value: str
    color: Optional[str] = None
    position: Optional[int] = None
    
    def to_dict(self):
        """Convert to dict for SQLite insertion."""
        return {
            'option_id': self.option_id,
            'field_id': self.field_id,
            'value': self.value,
            'color': self.color,
            'position': self.position
        }


@dataclass
class CustomFieldValue:
    """
    Actual value of a custom field on a specific task.
    Maps to: custom_field_values table
    """
    value_id: str
    task_id: str
    field_id: str
    value_text: Optional[str] = None
    value_number: Optional[float] = None
    value_date: Optional[date] = None
    value_checkbox: Optional[bool] = None
    value_enum_option_id: Optional[str] = None
    value_user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dict for SQLite insertion."""
        return {
            'value_id': self.value_id,
            'task_id': self.task_id,
            'field_id': self.field_id,
            'value_text': self.value_text,
            'value_number': self.value_number,
            'value_date': self.value_date.isoformat() if self.value_date else None,
            'value_checkbox': 1 if self.value_checkbox else 0 if self.value_checkbox is not None else None,
            'value_enum_option_id': self.value_enum_option_id,
            'value_user_id': self.value_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat()
        }
