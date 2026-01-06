import json
import random
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.attachment import Attachment


class AttachmentGenerator:
    """
    Generates realistic attachments for tasks.
    
    Strategy:
    - ~40% of tasks have attachments
    - Most tasks have 1-2 attachments
    - File types vary by task type and department
    - Design tasks have images, engineering has docs/code, etc.
    """
    
    def __init__(self):
        self._define_file_templates()
    
    def _define_file_templates(self):
        """Define file name templates and types."""
        
        self.file_types = {
            'document': {
                'extensions': ['.pdf', '.docx', '.doc', '.txt', '.md'],
                'names': [
                    'requirements', 'specification', 'design_doc', 'proposal',
                    'report', 'notes', 'meeting_notes', 'brief', 'outline',
                    'documentation', 'readme', 'changelog', 'guide'
                ],
                'content_types': [
                    'application/pdf',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'application/msword',
                    'text/plain',
                    'text/markdown'
                ]
            },
            'image': {
                'extensions': ['.png', '.jpg', '.jpeg', '.gif', '.svg'],
                'names': [
                    'screenshot', 'mockup', 'design', 'wireframe', 'diagram',
                    'logo', 'icon', 'banner', 'illustration', 'photo',
                    'image', 'graphic', 'sketch', 'prototype'
                ],
                'content_types': [
                    'image/png',
                    'image/jpeg',
                    'image/gif',
                    'image/svg+xml'
                ]
            },
            'spreadsheet': {
                'extensions': ['.xlsx', '.xls', '.csv'],
                'names': [
                    'data', 'analysis', 'budget', 'metrics', 'report',
                    'forecast', 'plan', 'tracker', 'dashboard', 'export'
                ],
                'content_types': [
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'application/vnd.ms-excel',
                    'text/csv'
                ]
            },
            'presentation': {
                'extensions': ['.pptx', '.ppt', '.key'],
                'names': [
                    'presentation', 'slides', 'deck', 'pitch', 'demo',
                    'overview', 'review', 'update', 'kickoff'
                ],
                'content_types': [
                    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    'application/vnd.ms-powerpoint'
                ]
            },
            'code': {
                'extensions': ['.zip', '.tar.gz', '.json', '.xml', '.log'],
                'names': [
                    'code', 'patch', 'config', 'logs', 'dump',
                    'backup', 'export', 'data', 'payload', 'response'
                ],
                'content_types': [
                    'application/zip',
                    'application/gzip',
                    'application/json',
                    'application/xml',
                    'text/plain'
                ]
            }
        }
        
        # File type weights by department/task type
        self.type_weights_by_context = {
            'engineering': {
                'document': 0.30,
                'image': 0.20,
                'spreadsheet': 0.10,
                'presentation': 0.10,
                'code': 0.30
            },
            'design': {
                'document': 0.15,
                'image': 0.60,
                'spreadsheet': 0.05,
                'presentation': 0.15,
                'code': 0.05
            },
            'marketing': {
                'document': 0.25,
                'image': 0.40,
                'spreadsheet': 0.15,
                'presentation': 0.20,
                'code': 0.00
            },
            'sales': {
                'document': 0.30,
                'image': 0.10,
                'spreadsheet': 0.30,
                'presentation': 0.30,
                'code': 0.00
            },
            'product': {
                'document': 0.35,
                'image': 0.25,
                'spreadsheet': 0.20,
                'presentation': 0.15,
                'code': 0.05
            },
            'default': {
                'document': 0.35,
                'image': 0.25,
                'spreadsheet': 0.15,
                'presentation': 0.15,
                'code': 0.10
            }
        }
    
    def _should_have_attachments(self, task_priority: Optional[str]) -> bool:
        """
        Decide if task should have attachments.
        
        ~40% of tasks have attachments.
        Higher priority tasks slightly more likely.
        """
        base_prob = 0.40
        
        if task_priority in ['high', 'urgent']:
            base_prob = 0.50
        elif task_priority == 'low':
            base_prob = 0.30
        
        return random.random() < base_prob
    
    def _sample_num_attachments(self) -> int:
        """
        Sample number of attachments for a task.
        
        Distribution:
        - 1 attachment: 60%
        - 2 attachments: 25%
        - 3 attachments: 10%
        - 4+ attachments: 5%
        """
        return random.choices(
            [1, 2, 3, 4, 5],
            weights=[0.60, 0.25, 0.10, 0.04, 0.01]
        )[0]
    
    def _get_context(self, task_name: str) -> str:
        """Determine context from task name."""
        task_lower = task_name.lower() if task_name else ""
        
        if any(kw in task_lower for kw in ['design', 'ui', 'ux', 'mockup', 'wireframe']):
            return 'design'
        elif any(kw in task_lower for kw in ['code', 'develop', 'bug', 'fix', 'api', 'backend', 'frontend']):
            return 'engineering'
        elif any(kw in task_lower for kw in ['campaign', 'marketing', 'social', 'content', 'blog']):
            return 'marketing'
        elif any(kw in task_lower for kw in ['sales', 'deal', 'proposal', 'contract', 'pitch']):
            return 'sales'
        elif any(kw in task_lower for kw in ['product', 'feature', 'roadmap', 'requirement']):
            return 'product'
        else:
            return 'default'
    
    def _sample_file_type(self, context: str) -> str:
        """Sample file type based on context."""
        weights = self.type_weights_by_context.get(context, self.type_weights_by_context['default'])
        
        types = list(weights.keys())
        probs = list(weights.values())
        
        # Remove types with 0 probability
        types_probs = [(t, p) for t, p in zip(types, probs) if p > 0]
        if not types_probs:
            return 'document'
        
        types, probs = zip(*types_probs)
        return random.choices(types, weights=probs)[0]
    
    def _generate_filename(self, file_type: str) -> str:
        """Generate realistic filename."""
        template = self.file_types[file_type]
        
        name = random.choice(template['names'])
        ext = random.choice(template['extensions'])
        
        # Add version number sometimes
        if random.random() < 0.30:
            version = random.choice(['_v1', '_v2', '_v3', '_final', '_draft', '_updated'])
            name += version
        
        # Add date sometimes
        if random.random() < 0.20:
            name += f"_{random.randint(2023, 2025)}{random.randint(1,12):02d}{random.randint(1,28):02d}"
        
        return name + ext
    
    def _sample_file_size(self, file_type: str) -> int:
        """
        Sample file size in bytes.
        
        Different file types have different typical sizes.
        """
        size_ranges = {
            'document': (50_000, 5_000_000),        # 50KB - 5MB
            'image': (100_000, 10_000_000),         # 100KB - 10MB
            'spreadsheet': (20_000, 2_000_000),     # 20KB - 2MB
            'presentation': (500_000, 20_000_000),  # 500KB - 20MB
            'code': (10_000, 50_000_000)            # 10KB - 50MB
        }
        
        min_size, max_size = size_ranges.get(file_type, (50_000, 5_000_000))
        return random.randint(min_size, max_size)
    
    def _sample_content_type(self, file_type: str) -> str:
        """Sample content type (MIME type)."""
        template = self.file_types[file_type]
        return random.choice(template['content_types'])
    
    def _sample_created_at(self, task_created_at: datetime) -> datetime:
        """
        Sample attachment upload timestamp.
        Usually uploaded same day or within a few days of task creation.
        """
        days_after = random.choices(
            [0, 1, 2, 3, 7, 14],
            weights=[0.50, 0.20, 0.15, 0.08, 0.05, 0.02]
        )[0]
        
        created_at = task_created_at + timedelta(days=days_after)
        
        # Add random hours
        created_at = created_at + timedelta(hours=random.randint(0, 12))
        
        # Ensure not in future
        now = datetime.utcnow()
        if created_at > now:
            created_at = task_created_at
        
        return created_at
    
    def generate(self, tasks: List, users: List) -> List[Attachment]:
        """
        Generate attachments for tasks.
        
        Args:
            tasks: List of Task objects
            users: List of User objects
        
        Returns:
            List of Attachment model instances
        """
        print(f"\nGenerating attachments for {len(tasks):,} tasks...")
        
        if not users:
            print("⚠ No users available, skipping attachment generation")
            return []
        
        attachments = []
        tasks_with_attachments = 0
        
        for task in tasks:
            # Decide if this task has attachments
            if not self._should_have_attachments(task.priority):
                continue
            
            tasks_with_attachments += 1
            
            # Determine context
            context = self._get_context(task.name)
            
            # Sample number of attachments
            num_attachments = self._sample_num_attachments()
            
            # Generate attachments
            for _ in range(num_attachments):
                # Sample file type
                file_type = self._sample_file_type(context)
                
                # Generate filename
                filename = self._generate_filename(file_type)
                
                # Sample file size
                file_size = self._sample_file_size(file_type)
                
                # Sample content type
                content_type = self._sample_content_type(file_type)
                
                # Sample uploader (assignee or creator)
                uploader_id = None
                if task.assignee_id and random.random() < 0.70:
                    uploader_id = task.assignee_id
                elif task.created_by:
                    uploader_id = task.created_by
                else:
                    uploader_id = random.choice(users).user_id
                
                # Sample created timestamp
                created_at = self._sample_created_at(task.created_at)
                
                # Generate fake URL
                url = f"https://storage.asana.com/attachments/{uuid.uuid4()}/{filename}"
                
                # Create Attachment instance
                attachment = Attachment(
                    attachment_id=str(uuid.uuid4()),
                    task_id=task.task_id,
                    uploaded_by=uploader_id,
                    filename=filename,
                    file_type=content_type,
                    file_size_bytes=file_size,
                    storage_url=url,
                    created_at=created_at
                )

                attachments.append(attachment)
            
            # Progress indicator
            if len(attachments) % 10000 == 0 and len(attachments) > 0:
                print(f"  Generated {len(attachments):,} attachments...")
        
        print(f" Generated {len(attachments):,} attachments")
        print(f"  - {tasks_with_attachments:,} tasks have attachments ({tasks_with_attachments/len(tasks)*100:.1f}%)")
        
        return attachments


def generate_attachments(tasks: List, users: List) -> List[Attachment]:
    """
    Main entry point for attachment generation.
    
    Args:
        tasks: List of Task objects
        users: List of User objects
    
    Returns:
        List of Attachment model instances
    """
    generator = AttachmentGenerator()
    attachments = generator.generate(tasks, users)
    
    # Log statistics
    print("\n" + "="*70)
    print("ATTACHMENT GENERATION SUMMARY")
    print("="*70)

    # File type distribution
    type_counts = defaultdict(int)
    for att in attachments:
        # Infer type from file_type (was content_type)
        if 'image' in att.file_type:
            file_type = 'image'
        elif 'pdf' in att.file_type or 'word' in att.file_type or 'text' in att.file_type:
            file_type = 'document'
        elif 'spreadsheet' in att.file_type or 'excel' in att.file_type or 'csv' in att.file_type:
            file_type = 'spreadsheet'
        elif 'presentation' in att.file_type or 'powerpoint' in att.file_type:
            file_type = 'presentation'
        else:
            file_type = 'other'
        
        type_counts[file_type] += 1

    print("\nAttachments by File Type:")
    for file_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(attachments)) * 100
        print(f"  {file_type:15s}: {count:5,} ({pct:5.1f}%)")

    # Attachments per task
    atts_per_task = defaultdict(int)
    for att in attachments:
        atts_per_task[att.task_id] += 1

    att_count_dist = defaultdict(int)
    for task_id, count in atts_per_task.items():
        att_count_dist[count] += 1

    print("\nAttachments per Task Distribution:")
    for num_atts in sorted(att_count_dist.keys())[:10]:
        count = att_count_dist[num_atts]
        pct = (count / len(atts_per_task)) * 100
        print(f"  {num_atts} attachment(s): {count:5,} tasks ({pct:5.1f}%)")

    # Average attachments per task
    avg_atts = len(attachments) / len(atts_per_task) if atts_per_task else 0
    print(f"\nAverage Attachments per Task (with attachments): {avg_atts:.2f}")

    # Average file size (use file_size_bytes)
    avg_size = sum(att.file_size_bytes for att in attachments) / len(attachments) if attachments else 0
    print(f"Average File Size: {avg_size / 1_000_000:.2f} MB")

    # Sample attachment
    print("\nSample Attachment:")
    sample = random.choice(attachments)
    print(json.dumps(sample.to_dict(), indent=2))

    print("="*70 + "\n")

    return attachments



# ============================================================================
# Testing / Standalone Execution
# ============================================================================

if __name__ == "__main__":
    """
    Test attachment generation.
    Run: python src/generators/attachments.py
    """
    
    print("\n" + "="*70)
    print("TESTING ATTACHMENT GENERATOR")
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
        
        attachments = generate_attachments(tasks, users)
        
        # Validate
        print("\n" + "="*70)
        print("VALIDATION")
        print("="*70)

        # Check all have filenames
        assert all(att.filename for att in attachments), "Missing filenames!"
        print(" All attachments have filenames")

        # Check all have valid file sizes (use file_size_bytes)
        assert all(att.file_size_bytes > 0 for att in attachments), "Invalid file sizes!"
        print(" All attachments have valid file sizes")

        # Check all reference valid tasks
        task_ids = {t.task_id for t in tasks}
        for att in attachments:
            assert att.task_id in task_ids, f"Invalid task_id: {att.task_id}"
        print(" All attachments reference valid tasks")

        # Check timestamps
        task_dict = {t.task_id: t for t in tasks}
        for att in attachments:
            task = task_dict[att.task_id]
            assert att.created_at >= task.created_at, \
                f"Attachment before task: {att.created_at} < {task.created_at}"
        print(" All timestamps consistent")

        print("\n ALL TESTS PASSED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
