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

from models.comment import Comment


class CommentGenerator:
    """
    Generates realistic comments on tasks.
    
    Strategy:
    - Not all tasks have comments (60% have 0 comments)
    - Comments from assignee, created_by, and team members
    - More comments on high priority and complex tasks
    - Comment timestamps between task creation and completion
    """
    
    def __init__(self):
        self._define_comment_templates()
    
    def _define_comment_templates(self):
        """Define comment text templates."""
        self.comment_templates = [
            "Working on this now",
            "Blocked by {}",
            "Need input from {}",
            "This is done",
            "Ready for review",
            "Can someone review this?",
            "Updated the approach",
            "Moving this to next sprint",
            "Completed and deployed",
            "Running into issues with {}",
            "Will handle this today",
            "This is more complex than expected",
            "Might need more time",
            "Almost done",
            "Waiting on {}",
            "Quick question about this",
            "Thanks for the update",
            "Looks good",
            "Approved",
            "Let's discuss this tomorrow",
            "Started working on this",
            "Made good progress",
            "Encountered a blocker",
            "Fixed the issue",
            "Needs more testing",
            "Updated the description",
            "Changed the approach",
            "This is ready now"
        ]
        
        self.blocking_items = [
            "another task", "the API", "testing", "deployment", 
            "code review", "design feedback", "requirements",
            "dependencies", "approval", "resources"
        ]
    
    def _should_have_comments(self, task_priority: str, task_completed: bool) -> bool:
        """
        Decide if task should have comments.
        
        Distribution:
            - 60% of tasks have 0 comments
            - High priority more likely to have comments
            - Completed tasks more likely to have comments
        """
        # Base probability: 40% have comments
        base_prob = 0.40
        
        # Adjust by priority
        if task_priority == 'high' or task_priority == 'urgent':
            base_prob = 0.60
        elif task_priority == 'low':
            base_prob = 0.25
        
        # Adjust by completion status
        if task_completed:
            base_prob *= 1.2
        
        return random.random() < min(0.80, base_prob)
    
    def _sample_num_comments(self, task_priority: str) -> int:
        """
        Sample number of comments for a task.
        
        Distribution:
            - Most tasks: 1-3 comments
            - High priority: can have up to 10 comments
        """
        if task_priority in ['high', 'urgent']:
            # More discussion on high priority
            return random.choices(
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                weights=[0.25, 0.25, 0.20, 0.12, 0.08, 0.04, 0.03, 0.02, 0.01, 0.01]
            )[0]
        elif task_priority == 'medium':
            return random.choices(
                [1, 2, 3, 4, 5],
                weights=[0.40, 0.30, 0.20, 0.08, 0.02]
            )[0]
        else:  # low or None
            return random.choices(
                [1, 2, 3],
                weights=[0.60, 0.30, 0.10]
            )[0]
    
    def _generate_comment_text(self) -> str:
        """Generate comment text from templates."""
        template = random.choice(self.comment_templates)
        
        # Fill in placeholders
        if '{}' in template:
            placeholder = random.choice(self.blocking_items)
            return template.format(placeholder)
        
        return template
    
    def _sample_created_at(self, task_created_at: datetime, 
                          task_completed_at: Optional[datetime],
                          comment_index: int, total_comments: int) -> datetime:
        """
        Sample comment creation timestamp.
        
        Comments distributed between task creation and completion (or now).
        """
        now = datetime.utcnow()
        
        # End time is completion or now
        end_time = task_completed_at if task_completed_at else now
        
        # Ensure end_time is after start_time
        if end_time <= task_created_at:
            end_time = task_created_at + timedelta(hours=random.randint(1, 48))
        
        # Ensure end_time not in future
        if end_time > now:
            end_time = now
        
        # Distribute comments evenly over time
        time_span = (end_time - task_created_at).total_seconds()
        
        if time_span <= 0:
            # Edge case: no time span
            return task_created_at + timedelta(minutes=random.randint(1, 60))
        
        if total_comments > 1:
            # Spread comments out
            progress = comment_index / (total_comments - 1)
        else:
            # Single comment: random time
            progress = random.random()
        
        # Add some randomness
        progress = max(0, min(1, progress + random.uniform(-0.1, 0.1)))
        
        offset_seconds = int(time_span * progress)
        created_at = task_created_at + timedelta(seconds=offset_seconds)
        
        # Final constraints
        if created_at < task_created_at:
            created_at = task_created_at + timedelta(hours=random.randint(1, 24))
        
        if created_at > now:
            created_at = now - timedelta(hours=random.randint(1, 24))
        
        # Ensure still >= task_created_at after adjustments
        if created_at < task_created_at:
            created_at = task_created_at + timedelta(minutes=random.randint(1, 60))
        
        return created_at
    
    def generate(self, tasks: List, users: List) -> List[Comment]:
        """
        Generate comments for tasks.
        
        Args:
            tasks: List of Task objects
            users: List of User objects
        
        Returns:
            List of Comment model instances
        """
        print(f"\nGenerating comments for {len(tasks):,} tasks...")
        
        # Group users by ID for quick lookup
        user_dict = {u.user_id: u for u in users}
        
        comments = []
        tasks_with_comments = 0
        
        for task in tasks:
            # Get priority (handle None)
            priority = task.priority if task.priority else 'medium'
            
            # Decide if this task has comments
            if not self._should_have_comments(priority, task.completed):
                continue
            
            tasks_with_comments += 1
            
            # Sample number of comments
            num_comments = self._sample_num_comments(priority)
            
            # Get relevant users (assignee, creator)
            relevant_users = []
            if task.assignee_id:
                relevant_users.append(task.assignee_id)
            if task.created_by:
                relevant_users.append(task.created_by)
            
            # Add random team members (same department)
            if task.assignee_id and task.assignee_id in user_dict:
                assignee = user_dict[task.assignee_id]
                dept_users = [u for u in users if u.department == assignee.department]
                relevant_users.extend([u.user_id for u in random.sample(dept_users, 
                                                                         min(3, len(dept_users)))])
            
            # Remove duplicates
            relevant_users = list(set(relevant_users))
            
            # Ensure we have at least one user
            if not relevant_users:
                relevant_users = [random.choice(users).user_id]
            
            # Generate comments
            for i in range(num_comments):
                # Sample author
                author_id = random.choice(relevant_users)
                
                # Generate text
                text = self._generate_comment_text()
                
                # Sample creation time
                created_at = self._sample_created_at(
                    task.created_at,
                    task.completed_at,
                    i,
                    num_comments
                )
                
                # Create Comment instance
                comment = Comment(
                    comment_id=str(uuid.uuid4()),
                    task_id=task.task_id,
                    user_id=author_id,
                    text=text,
                    created_at=created_at
                )
                
                comments.append(comment)
            
            # Progress indicator
            if len(comments) % 10000 == 0:
                print(f"  Generated {len(comments):,} comments...")
        
        print(f" Generated {len(comments):,} comments on {tasks_with_comments:,} tasks")
        print(f"  - {tasks_with_comments / len(tasks) * 100:.1f}% of tasks have comments")
        
        return comments


def generate_comments(tasks: List, users: List) -> List[Comment]:
    """
    Main entry point for comment generation.
    
    Args:
        tasks: List of Task objects
        users: List of User objects
    
    Returns:
        List of Comment model instances
    """
    generator = CommentGenerator()
    comments = generator.generate(tasks, users)
    
    # Log statistics
    print("\n" + "="*70)
    print("COMMENT GENERATION SUMMARY")
    print("="*70)
    
    # Comments per task distribution
    comments_per_task = defaultdict(int)
    for comment in comments:
        comments_per_task[comment.task_id] += 1
    
    comment_count_dist = defaultdict(int)
    for task_id, count in comments_per_task.items():
        comment_count_dist[count] += 1
    
    print("\nComments per Task Distribution:")
    for num_comments in sorted(comment_count_dist.keys())[:10]:
        count = comment_count_dist[num_comments]
        pct = (count / len(comments_per_task)) * 100 if comments_per_task else 0
        print(f"  {num_comments:2d} comment(s): {count:5,} tasks ({pct:5.1f}%)")
    
    # Average comments
    avg_comments = len(comments) / len(comments_per_task) if comments_per_task else 0
    print(f"\nAverage Comments per Task (with comments): {avg_comments:.2f}")
    
    # Sample comments
    print("\nSample Comments:")
    for comment in random.sample(comments, min(5, len(comments))):
        print(f"  '{comment.text}'")
    
    print("="*70 + "\n")
    
    return comments


# ============================================================================
# Testing / Standalone Execution
# ============================================================================

if __name__ == "__main__":
    """
    Test comment generation.
    Run: python src/generators/comments.py
    """
    
    print("\n" + "="*70)
    print("TESTING COMMENT GENERATOR")
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
        
        comments = generate_comments(tasks, users)
        
        # Validate
        print("\n" + "="*70)
        print("VALIDATION")
        print("="*70)

        # Check all comments have text
        assert all(c.text for c in comments), "Missing comment text!"
        print(" All comments have text")

        # Check timestamps
        task_dict = {t.task_id: t for t in tasks}
        for comment in comments:
            task = task_dict[comment.task_id]
            assert comment.created_at >= task.created_at, \
                f"Comment before task: {comment.created_at} < {task.created_at}"
            # Don't check against completion - comments can be added after
        print(" All timestamps consistent")

        # Sample comment
        print("\nSample Comment:")
        sample = random.choice(comments)
        print(json.dumps(sample.to_dict(), indent=2))

        print("\n ALL TESTS PASSED")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
