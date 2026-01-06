import json
import random
import uuid
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.custom_field import CustomFieldDefinition, CustomFieldEnumOption, CustomFieldValue


class CustomFieldGenerator:
    """
    Generates realistic custom fields for projects and their values on tasks.
    
    Strategy:
    - Define field definitions per project
    - Create enum options for enum fields
    - Populate values on ~70% of tasks
    """
    
    def __init__(self):
        self._define_field_templates()
    
    def _define_field_templates(self):
        """Define custom field templates by project/team type."""
        
        self.common_fields = [
            {
                'name': 'Status',
                'field_type': 'enum',
                'description': 'Current status of the task',
                'is_required': False,
                'options': [
                    {'value': 'Not Started', 'color': '#d3d3d3'},
                    {'value': 'In Progress', 'color': '#4a90e2'},
                    {'value': 'Blocked', 'color': '#e2472f'},
                    {'value': 'Complete', 'color': '#6bc950'}
                ]
            },
            {
                'name': 'Priority',
                'field_type': 'enum',
                'description': 'Task priority level',
                'is_required': False,
                'options': [
                    {'value': 'Low', 'color': '#d3d3d3'},
                    {'value': 'Medium', 'color': '#ffa500'},
                    {'value': 'High', 'color': '#e2472f'},
                    {'value': 'Urgent', 'color': '#8b0000'}
                ]
            },
            {
                'name': 'Effort',
                'field_type': 'enum',
                'description': 'Estimated effort required',
                'is_required': False,
                'options': [
                    {'value': 'Small', 'color': '#6bc950'},
                    {'value': 'Medium', 'color': '#ffa500'},
                    {'value': 'Large', 'color': '#e2472f'},
                    {'value': 'Extra Large', 'color': '#8b0000'}
                ]
            }
        ]
        
        self.engineering_fields = [
            {
                'name': 'Story Points',
                'field_type': 'number',
                'description': 'Estimated complexity in story points',
                'is_required': False,
                'options': None
            },
            {
                'name': 'Sprint',
                'field_type': 'text',
                'description': 'Sprint identifier',
                'is_required': False,
                'options': None
            },
            {
                'name': 'Environment',
                'field_type': 'enum',
                'description': 'Target deployment environment',
                'is_required': False,
                'options': [
                    {'value': 'Development', 'color': '#4a90e2'},
                    {'value': 'Staging', 'color': '#ffa500'},
                    {'value': 'Production', 'color': '#e2472f'}
                ]
            },
            {
                'name': 'Component',
                'field_type': 'enum',
                'description': 'System component',
                'is_required': False,
                'options': [
                    {'value': 'Frontend', 'color': '#4a90e2'},
                    {'value': 'Backend', 'color': '#6bc950'},
                    {'value': 'Database', 'color': '#ffa500'},
                    {'value': 'API', 'color': '#9b59b6'},
                    {'value': 'Infrastructure', 'color': '#e74c3c'}
                ]
            },
            {
                'name': 'Bug Severity',
                'field_type': 'enum',
                'description': 'Severity level for bugs',
                'is_required': False,
                'options': [
                    {'value': 'Critical', 'color': '#8b0000'},
                    {'value': 'High', 'color': '#e2472f'},
                    {'value': 'Medium', 'color': '#ffa500'},
                    {'value': 'Low', 'color': '#d3d3d3'}
                ]
            }
        ]
        
        self.marketing_fields = [
            {
                'name': 'Campaign Type',
                'field_type': 'enum',
                'description': 'Type of marketing campaign',
                'is_required': False,
                'options': [
                    {'value': 'Email', 'color': '#4a90e2'},
                    {'value': 'Social', 'color': '#3b5998'},
                    {'value': 'Content', 'color': '#6bc950'},
                    {'value': 'Paid Ads', 'color': '#ffa500'},
                    {'value': 'Events', 'color': '#9b59b6'}
                ]
            },
            {
                'name': 'Channel',
                'field_type': 'enum',
                'description': 'Marketing channel',
                'is_required': False,
                'options': [
                    {'value': 'LinkedIn', 'color': '#0077b5'},
                    {'value': 'Twitter', 'color': '#1da1f2'},
                    {'value': 'Facebook', 'color': '#3b5998'},
                    {'value': 'Instagram', 'color': '#e1306c'},
                    {'value': 'Blog', 'color': '#6bc950'},
                    {'value': 'Email', 'color': '#ffa500'}
                ]
            },
            {
                'name': 'Budget',
                'field_type': 'number',
                'description': 'Campaign budget in USD',
                'is_required': False,
                'options': None
            },
            {
                'name': 'Target Audience',
                'field_type': 'enum',
                'description': 'Target customer segment',
                'is_required': False,
                'options': [
                    {'value': 'Enterprise', 'color': '#8b0000'},
                    {'value': 'SMB', 'color': '#ffa500'},
                    {'value': 'Startup', 'color': '#6bc950'},
                    {'value': 'Developer', 'color': '#4a90e2'},
                    {'value': 'General', 'color': '#d3d3d3'}
                ]
            }
        ]
        
        self.sales_fields = [
            {
                'name': 'Deal Stage',
                'field_type': 'enum',
                'description': 'Current deal stage',
                'is_required': False,
                'options': [
                    {'value': 'Prospecting', 'color': '#d3d3d3'},
                    {'value': 'Qualified', 'color': '#4a90e2'},
                    {'value': 'Proposal', 'color': '#ffa500'},
                    {'value': 'Negotiation', 'color': '#e2472f'},
                    {'value': 'Closed Won', 'color': '#6bc950'},
                    {'value': 'Closed Lost', 'color': '#8b0000'}
                ]
            },
            {
                'name': 'Deal Value',
                'field_type': 'number',
                'description': 'Estimated deal value in USD',
                'is_required': False,
                'options': None
            },
            {
                'name': 'Account Tier',
                'field_type': 'enum',
                'description': 'Account size tier',
                'is_required': False,
                'options': [
                    {'value': 'Enterprise', 'color': '#8b0000'},
                    {'value': 'Mid-Market', 'color': '#ffa500'},
                    {'value': 'SMB', 'color': '#6bc950'}
                ]
            },
            {
                'name': 'Lead Source',
                'field_type': 'enum',
                'description': 'Origin of the lead',
                'is_required': False,
                'options': [
                    {'value': 'Inbound', 'color': '#6bc950'},
                    {'value': 'Outbound', 'color': '#4a90e2'},
                    {'value': 'Referral', 'color': '#ffa500'},
                    {'value': 'Partner', 'color': '#9b59b6'},
                    {'value': 'Event', 'color': '#e74c3c'}
                ]
            }
        ]
        
        self.product_fields = [
            {
                'name': 'Feature Area',
                'field_type': 'enum',
                'description': 'Product feature area',
                'is_required': False,
                'options': [
                    {'value': 'Core', 'color': '#4a90e2'},
                    {'value': 'Integrations', 'color': '#6bc950'},
                    {'value': 'Analytics', 'color': '#ffa500'},
                    {'value': 'Admin', 'color': '#9b59b6'},
                    {'value': 'Mobile', 'color': '#e74c3c'}
                ]
            },
            {
                'name': 'User Impact',
                'field_type': 'enum',
                'description': 'Impact on users',
                'is_required': False,
                'options': [
                    {'value': 'High', 'color': '#e2472f'},
                    {'value': 'Medium', 'color': '#ffa500'},
                    {'value': 'Low', 'color': '#d3d3d3'}
                ]
            },
            {
                'name': 'Release',
                'field_type': 'text',
                'description': 'Target release version',
                'is_required': False,
                'options': None
            }
        ]
        
        self.design_fields = [
            {
                'name': 'Design Phase',
                'field_type': 'enum',
                'description': 'Current design phase',
                'is_required': False,
                'options': [
                    {'value': 'Research', 'color': '#d3d3d3'},
                    {'value': 'Wireframes', 'color': '#4a90e2'},
                    {'value': 'Mockups', 'color': '#ffa500'},
                    {'value': 'Prototype', 'color': '#9b59b6'},
                    {'value': 'Final', 'color': '#6bc950'}
                ]
            },
            {
                'name': 'Design Type',
                'field_type': 'enum',
                'description': 'Type of design work',
                'is_required': False,
                'options': [
                    {'value': 'UI', 'color': '#4a90e2'},
                    {'value': 'UX', 'color': '#6bc950'},
                    {'value': 'Branding', 'color': '#e74c3c'},
                    {'value': 'Illustration', 'color': '#ffa500'},
                    {'value': 'Motion', 'color': '#9b59b6'}
                ]
            }
        ]
        
        # Map project types to relevant fields
        self.fields_by_project_type = {
            'sprint': self.common_fields + self.engineering_fields[:3],
            'bug_tracking': self.common_fields + [self.engineering_fields[4]],
            'campaign': self.common_fields + self.marketing_fields,
            'roadmap': self.common_fields + self.product_fields,
            'ongoing': self.common_fields[:2]
        }
    
    def _get_fields_for_project(self, project_type: str, team_type: str) -> List[Dict]:
        """Get relevant custom fields for a project."""
        fields = self.fields_by_project_type.get(project_type, self.common_fields[:2])
        
        team_lower = team_type.lower()
        
        if 'engineering' in team_lower or 'product' in team_lower:
            for field in self.engineering_fields[:2]:
                if field not in fields:
                    fields.append(field)
        elif 'marketing' in team_lower:
            for field in self.marketing_fields[:2]:
                if field not in fields:
                    fields.append(field)
        elif 'sales' in team_lower:
            for field in self.sales_fields[:2]:
                if field not in fields:
                    fields.append(field)
        elif 'design' in team_lower:
            for field in self.design_fields[:1]:
                if field not in fields:
                    fields.append(field)
        
        num_fields = random.randint(2, min(5, len(fields)))
        selected_fields = random.sample(fields, num_fields)
        
        return selected_fields
    
    def generate(self, projects: List, teams: List, tasks: List) -> Tuple[List, List, List]:
        """
        Generate custom field definitions, enum options, and values.
        
        Returns:
            Tuple of (definitions, enum_options, values)
        """
        print(f"\nGenerating custom fields for {len(projects):,} projects...")
        
        team_dict = {t.team_id: t for t in teams}
        
        definitions = []
        enum_options = []
        values = []
        
        # Track field_id to options mapping
        field_to_options = {}
        
        # Generate field definitions per project
        for project in projects:
            team = team_dict.get(project.team_id)
            if not team:
                continue
            
            field_templates = self._get_fields_for_project(project.project_type, team.team_type)
            
            for position, template in enumerate(field_templates):
                field_id = str(uuid.uuid4())
                
                created_at = project.created_at + timedelta(days=random.randint(0, 2))
                if created_at > datetime.utcnow():
                    created_at = project.created_at
                
                definition = CustomFieldDefinition(
                    field_id=field_id,
                    project_id=project.project_id,
                    name=template['name'],
                    field_type=template['field_type'],
                    description=template['description'],
                    is_required=template['is_required'],
                    position=position,
                    created_at=created_at
                )
                
                definitions.append(definition)
                
                # Create enum options if enum type
                if template['field_type'] == 'enum' and template['options']:
                    field_to_options[field_id] = []
                    for opt_position, opt_template in enumerate(template['options']):
                        option_id = str(uuid.uuid4())
                        
                        enum_option = CustomFieldEnumOption(
                            option_id=option_id,
                            field_id=field_id,
                            value=opt_template['value'],
                            color=opt_template.get('color'),
                            position=opt_position
                        )
                        
                        enum_options.append(enum_option)
                        field_to_options[field_id].append(option_id)
        
        print(f" Generated {len(definitions):,} field definitions")
        print(f" Generated {len(enum_options):,} enum options")
        
        # Generate values for tasks
        print(f"\nPopulating custom field values on {len(tasks):,} tasks...")
        
        # Group definitions by project
        defs_by_project = defaultdict(list)
        for defn in definitions:
            defs_by_project[defn.project_id].append(defn)
        
        for task in tasks:
            task_defs = defs_by_project.get(task.project_id, [])
            if not task_defs:
                continue
            
            # ~70% of tasks have custom field values
            if random.random() > 0.70:
                continue
            
            # Fill 60-100% of available fields
            num_to_fill = random.randint(int(len(task_defs) * 0.6), len(task_defs))
            fields_to_fill = random.sample(task_defs, num_to_fill)
            
            for field_def in fields_to_fill:
                value_id = str(uuid.uuid4())
                
                # Sample value based on type
                if field_def.field_type == 'enum':
                    option_ids = field_to_options.get(field_def.field_id, [])
                    if option_ids:
                        value = CustomFieldValue(
                            value_id=value_id,
                            task_id=task.task_id,
                            field_id=field_def.field_id,
                            value_enum_option_id=random.choice(option_ids),
                            created_at=task.created_at + timedelta(hours=random.randint(1, 48))
                        )
                        values.append(value)
                
                elif field_def.field_type == 'number':
                    # Story Points: 1-13, Budget/Deal: 1000-100000
                    if 'story' in field_def.name.lower() or 'point' in field_def.name.lower():
                        num_val = random.choice([1, 2, 3, 5, 8, 13])
                    elif 'budget' in field_def.name.lower() or 'value' in field_def.name.lower():
                        num_val = random.randint(1000, 100000)
                    else:
                        num_val = random.randint(1, 100)
                    
                    value = CustomFieldValue(
                        value_id=value_id,
                        task_id=task.task_id,
                        field_id=field_def.field_id,
                        value_number=float(num_val),
                        created_at=task.created_at + timedelta(hours=random.randint(1, 48))
                    )
                    values.append(value)
                
                elif field_def.field_type == 'text':
                    # Sprint: "Sprint 23", Release: "v2.4.1"
                    if 'sprint' in field_def.name.lower():
                        text_val = f"Sprint {random.randint(1, 50)}"
                    elif 'release' in field_def.name.lower():
                        text_val = f"v{random.randint(1,5)}.{random.randint(0,10)}.{random.randint(0,20)}"
                    else:
                        text_val = f"Value {random.randint(1, 100)}"
                    
                    value = CustomFieldValue(
                        value_id=value_id,
                        task_id=task.task_id,
                        field_id=field_def.field_id,
                        value_text=text_val,
                        created_at=task.created_at + timedelta(hours=random.randint(1, 48))
                    )
                    values.append(value)
                
                elif field_def.field_type == 'date':
                    # Random date within project timeframe
                    date_val = task.created_at.date() + timedelta(days=random.randint(0, 90))
                    value = CustomFieldValue(
                        value_id=value_id,
                        task_id=task.task_id,
                        field_id=field_def.field_id,
                        value_date=date_val,
                        created_at=task.created_at + timedelta(hours=random.randint(1, 48))
                    )
                    values.append(value)
                
                elif field_def.field_type == 'checkbox':
                    value = CustomFieldValue(
                        value_id=value_id,
                        task_id=task.task_id,
                        field_id=field_def.field_id,
                        value_checkbox=random.choice([True, False]),
                        created_at=task.created_at + timedelta(hours=random.randint(1, 48))
                    )
                    values.append(value)
        
        print(f" Generated {len(values):,} custom field values")
        
        return definitions, enum_options, values


def generate_custom_fields(projects: List, teams: List, tasks: List) -> Tuple[List, List, List]:
    """
    Main entry point for custom field generation.
    
    Returns:
        Tuple of (definitions, enum_options, values)
    """
    generator = CustomFieldGenerator()
    definitions, enum_options, values = generator.generate(projects, teams, tasks)
    
    # Log statistics
    print("\n" + "="*70)
    print("CUSTOM FIELD GENERATION SUMMARY")
    print("="*70)
    
    # Type breakdown
    type_counts = defaultdict(int)
    for defn in definitions:
        type_counts[defn.field_type] += 1
    
    print("\nField Definitions by Type:")
    for field_type, count in sorted(type_counts.items()):
        pct = (count / len(definitions)) * 100
        print(f"  {field_type:10s}: {count:5,} ({pct:5.1f}%)")
    
    # Name frequency
    name_counts = defaultdict(int)
    for defn in definitions:
        name_counts[defn.name] += 1
    
    print("\nMost Common Field Names:")
    for name, count in sorted(name_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        pct = (count / len(definitions)) * 100
        print(f"  {name:25s}: {count:4,} ({pct:5.1f}%)")
    
    # Values statistics
    tasks_with_values = len(set(v.task_id for v in values))
    total_tasks = len(tasks)
    print(f"\nTasks with Custom Field Values: {tasks_with_values:,} / {total_tasks:,} ({tasks_with_values/total_tasks*100:.1f}%)")
    
    avg_values_per_task = len(values) / tasks_with_values if tasks_with_values > 0 else 0
    print(f"Average Values per Task (with values): {avg_values_per_task:.1f}")
    
    print("="*70 + "\n")
    
    return definitions, enum_options, values


# ============================================================================
# Testing / Standalone Execution
# ============================================================================

if __name__ == "__main__":
    """Test custom field generation."""
    
    print("\n" + "="*70)
    print("TESTING CUSTOM FIELD GENERATOR")
    print("="*70 + "\n")
    
    try:
        from organizations import generate_organization
        from users import generate_users
        from teams import generate_teams
        from projects import generate_projects
        from sections import generate_sections
        from tags import generate_tags
        from tasks import generate_tasks
        
        org_result = generate_organization(company_size=7000)
        users = generate_users(org_result, target_count=100)
        teams = generate_teams(org_result, users)
        projects = generate_projects(org_result, teams, users)
        sections = generate_sections(projects)
        tags = generate_tags(org_result)
        tasks = generate_tasks(projects, sections, users, tags)
        
        definitions, enum_options, values = generate_custom_fields(projects, teams, tasks)
        
        # Validate
        print("\n" + "="*70)
        print("VALIDATION")
        print("="*70)
        
        assert all(d.name for d in definitions), "Missing field names!"
        print(" All definitions have names")
        
        assert all(d.field_type for d in definitions), "Missing field types!"
        print(" All definitions have types")
        
        # Check enum options reference valid fields
        field_ids = {d.field_id for d in definitions}
        for opt in enum_options:
            assert opt.field_id in field_ids, f"Invalid field_id in enum option!"
        print(" All enum options reference valid fields")
        
        # Check values reference valid tasks and fields
        task_ids = {t.task_id for t in tasks}
        for val in values:
            assert val.task_id in task_ids, f"Invalid task_id in value!"
            assert val.field_id in field_ids, f"Invalid field_id in value!"
        print(" All values reference valid tasks and fields")
        
        # Sample
        print("\nSample Field Definition:")
        sample_def = random.choice(definitions)
        print(json.dumps(sample_def.to_dict(), indent=2))
        
        print("\nSample Value:")
        sample_val = random.choice(values)
        print(json.dumps(sample_val.to_dict(), indent=2))
        
        print("\n ALL TESTS PASSED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
