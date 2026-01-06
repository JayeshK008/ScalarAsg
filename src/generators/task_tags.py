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

from models.task_tag import TaskTag


class TaskTagGenerator:
    """
    Generates realistic task-tag associations.
    
    Strategy:
    - ~60% of tasks have at least one tag
    - Most tasks have 1-3 tags
    - Tags applied based on task properties (priority, type, etc.)
    - Some tags are more common than others
    """
    
    def __init__(self):
        pass
    
    def _should_have_tags(self, task_priority: Optional[str]) -> bool:
        """
        Decide if task should have tags.
        
        ~60% of tasks have tags, slightly higher for high priority.
        """
        base_prob = 0.60
        
        if task_priority in ['high', 'urgent']:
            base_prob = 0.70
        elif task_priority == 'low':
            base_prob = 0.50
        
        return random.random() < base_prob
    
    def _sample_num_tags(self) -> int:
        """
        Sample number of tags for a task.
        
        Distribution:
        - 1 tag: 50%
        - 2 tags: 30%
        - 3 tags: 15%
        - 4+ tags: 5%
        """
        return random.choices(
            [1, 2, 3, 4, 5],
            weights=[0.50, 0.30, 0.15, 0.04, 0.01]
        )[0]
    
    def _get_relevant_tags(self, task, tags: List, org_id: str) -> List:
        """
        Get tags relevant to this task based on its properties.
        """
        relevant_tags = []
        seen_tag_ids = set()  # Track by ID instead
        
        # Filter tags by organization
        org_tags = [t for t in tags if t.organization_id == org_id]
        
        if not org_tags:
            return []
        
        # Priority-based tags
        if task.priority:
            priority_tags = [t for t in org_tags if task.priority.lower() in t.name.lower()]
            for tag in priority_tags:
                if tag.tag_id not in seen_tag_ids:
                    relevant_tags.append(tag)
                    seen_tag_ids.add(tag.tag_id)
        
        # Name-based tags (keywords)
        task_name_lower = task.name.lower() if task.name else ""
        
        keywords_to_tags = {
            'bug': ['Bug', 'Critical', 'Urgent'],
            'fix': ['Bug', 'Maintenance'],
            'design': ['Design', 'UI/UX'],
            'feature': ['Feature', 'Enhancement'],
            'doc': ['Documentation'],
            'test': ['Testing', 'QA'],
            'deploy': ['Deployment', 'Production'],
            'research': ['Research', 'Investigation'],
            'review': ['Review', 'Feedback'],
            'meeting': ['Meeting', 'Discussion'],
            'planning': ['Planning', 'Strategy'],
            'urgent': ['Urgent', 'High Priority'],
            'blocked': ['Blocked'],
            'security': ['Security', 'Critical'],
            'performance': ['Performance', 'Optimization'],
        }
        
        for keyword, tag_names in keywords_to_tags.items():
            if keyword in task_name_lower:
                for tag_name in tag_names:
                    matching_tags = [t for t in org_tags if tag_name.lower() in t.name.lower()]
                    for tag in matching_tags:
                        if tag.tag_id not in seen_tag_ids:
                            relevant_tags.append(tag)
                            seen_tag_ids.add(tag.tag_id)
        
        # If no relevant tags found, use random tags
        if not relevant_tags:
            relevant_tags = random.sample(org_tags, min(10, len(org_tags)))
        
        return relevant_tags

    def _sample_created_at(self, task_created_at: datetime) -> datetime:
        """
        Sample tag assignment timestamp.
        Usually same day or within a few days of task creation.
        """
        days_after = random.choices(
            [0, 1, 2, 3, 7],
            weights=[0.60, 0.20, 0.10, 0.07, 0.03]
        )[0]
        
        created_at = task_created_at + timedelta(days=days_after)
        
        # Add random hours
        created_at = created_at + timedelta(hours=random.randint(0, 12))
        
        # Ensure not in future
        now = datetime.utcnow()
        if created_at > now:
            created_at = task_created_at
        
        return created_at
    
    def generate(self, tasks: List, tags: List) -> List[TaskTag]:
        """
        Generate task-tag associations.
        
        Args:
            tasks: List of Task objects
            tags: List of Tag objects
        
        Returns:
            List of TaskTag model instances
        """
        print(f"\nGenerating task-tag associations for {len(tasks):,} tasks and {len(tags):,} tags...")
        
        if not tags:
            print("⚠ No tags available, skipping task-tag generation")
            return []
        
        # Group tags by organization for faster lookup
        tags_by_org = defaultdict(list)
        for tag in tags:
            tags_by_org[tag.organization_id].append(tag)
        
        task_tags = []
        tasks_with_tags = 0
        
        for task in tasks:
            # Get organization from task (via project)
            # Assuming task has organization_id or we need to pass projects
            # For now, we'll just use all tags
            org_id = getattr(task, 'organization_id', None)
            
            if not org_id:
                # If task doesn't have org_id, skip or use all tags
                # We'll need to fix this based on your Task model
                org_tags = tags
            else:
                org_tags = tags_by_org.get(org_id, tags)
            
            # Decide if this task has tags
            if not self._should_have_tags(task.priority):
                continue
            
            tasks_with_tags += 1
            
            # Get relevant tags
            relevant_tags = self._get_relevant_tags(task, org_tags, org_id if org_id else tags[0].organization_id)
            
            if not relevant_tags:
                continue
            
            # Sample number of tags
            num_tags = min(self._sample_num_tags(), len(relevant_tags))
            
            # Sample tags
            selected_tags = random.sample(relevant_tags, num_tags)
            
            # Create TaskTag associations
            for tag in selected_tags:
                created_at = self._sample_created_at(task.created_at)
                
                task_tag = TaskTag(
                    task_tag_id=str(uuid.uuid4()),
                    task_id=task.task_id,
                    tag_id=tag.tag_id,
                    created_at=created_at
                )
                
                task_tags.append(task_tag)
            
            # Progress indicator
            if len(task_tags) % 10000 == 0 and len(task_tags) > 0:
                print(f"  Generated {len(task_tags):,} associations...")
        
        print(f" Generated {len(task_tags):,} task-tag associations")
        print(f"  - {tasks_with_tags:,} tasks have tags ({tasks_with_tags/len(tasks)*100:.1f}%)")
        
        return task_tags


def generate_task_tags(tasks: List, tags: List) -> List[TaskTag]:
    """
    Main entry point for task-tag generation.
    
    Args:
        tasks: List of Task objects
        tags: List of Tag objects
    
    Returns:
        List of TaskTag model instances
    """
    generator = TaskTagGenerator()
    task_tags = generator.generate(tasks, tags)
    
    # Log statistics
    print("\n" + "="*70)
    print("TASK-TAG ASSOCIATION SUMMARY")
    print("="*70)
    
    # Tags per task distribution
    tags_per_task = defaultdict(int)
    for tt in task_tags:
        tags_per_task[tt.task_id] += 1
    
    tag_count_dist = defaultdict(int)
    for task_id, count in tags_per_task.items():
        tag_count_dist[count] += 1
    
    print("\nTags per Task Distribution:")
    for num_tags in sorted(tag_count_dist.keys())[:10]:
        count = tag_count_dist[num_tags]
        pct = (count / len(tags_per_task)) * 100 if tags_per_task else 0
        print(f"  {num_tags} tag(s): {count:5,} tasks ({pct:5.1f}%)")
    
    # Average tags per task
    avg_tags = len(task_tags) / len(tags_per_task) if tags_per_task else 0
    print(f"\nAverage Tags per Task (with tags): {avg_tags:.2f}")
    
    # Most used tags
    tag_usage = defaultdict(int)
    for tt in task_tags:
        tag_usage[tt.tag_id] += 1
    
    print("\nMost Used Tags:")
    tag_dict = {t.tag_id: t for t in tags}
    for tag_id, count in sorted(tag_usage.items(), key=lambda x: x[1], reverse=True)[:10]:
        tag = tag_dict.get(tag_id)
        tag_name = tag.name if tag else "Unknown"
        pct = (count / len(task_tags)) * 100
        print(f"  {tag_name:25s}: {count:5,} tasks ({pct:5.1f}%)")
    
    print("="*70 + "\n")
    
    return task_tags


# ============================================================================
# Testing / Standalone Execution
# ============================================================================

if __name__ == "__main__":
    """
    Test task-tag generation.
    Run: python src/generators/task_tags.py
    """
    
    print("\n" + "="*70)
    print("TESTING TASK-TAG GENERATOR")
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
        
        task_tags = generate_task_tags(tasks, tags)
        
        # Validate
        print("\n" + "="*70)
        print("VALIDATION")
        print("="*70)
        
        # Check all reference valid tasks and tags
        task_ids = {t.task_id for t in tasks}
        tag_ids = {t.tag_id for t in tags}
        
        for tt in task_tags:
            assert tt.task_id in task_ids, f"Invalid task_id: {tt.task_id}"
            assert tt.tag_id in tag_ids, f"Invalid tag_id: {tt.tag_id}"
        print(" All task-tag associations reference valid tasks and tags")
        
        # Check timestamps
        task_dict = {t.task_id: t for t in tasks}
        for tt in task_tags:
            task = task_dict[tt.task_id]
            assert tt.created_at >= task.created_at, \
                f"Tag assigned before task creation: {tt.created_at} < {task.created_at}"
        print(" All timestamps consistent")
        
        # Check no duplicate associations
        associations = set()
        for tt in task_tags:
            key = (tt.task_id, tt.tag_id)
            assert key not in associations, f"Duplicate association: {key}"
            associations.add(key)
        print(" No duplicate task-tag associations")
        
        # Sample
        print("\nSample Task-Tag Association:")
        sample = random.choice(task_tags)
        print(json.dumps(sample.to_dict(), indent=2))
        
        print("\n ALL TESTS PASSED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
