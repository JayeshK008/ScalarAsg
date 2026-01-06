import json
import random
import uuid
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from config import RESEARCH_DIR

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.task import Task


class TaskGenerator:
    """
    Generates realistic task population.
    
    Strategy:
    - Uses benchmarks for completion rates (72% overall)
    - Tasks created/completed per employee per week (6-12 created, 3-6 completed)
    - Priority distribution (high 20%, medium 60%, low 20%)
    - Realistic task duration (1-30 days, avg 5.3 days)
    - Proper section distribution (more in "To Do" and "In Progress")
    """
    
    def __init__(self, research_dir: str = RESEARCH_DIR):
        self.research_dir = Path(research_dir)
        self._load_research_data()
    
    def _load_research_data(self):
        """Load benchmarks for task generation."""
        
        benchmarks_path = self.research_dir / "benchmarks.json"
        with open(benchmarks_path, 'r') as f:
            self.benchmarks = json.load(f)
        
        # Task completion metrics
        task_completion = self.benchmarks['task_completion']
        self.overall_completion_rate = task_completion['overall_rate']
        self.completion_by_priority = task_completion['by_priority']
        self.overdue_rate = task_completion['overdue_rate']
        
        # Workload metrics
        workload = self.benchmarks['workload']
        self.tasks_created_per_week_range = workload['tasks_created_per_employee_per_week_range']
        self.tasks_completed_per_week_range = workload['tasks_completed_per_employee_per_week_range']
        
        # Time metrics
        time_metrics = self.benchmarks['time_metrics']
        self.avg_task_duration = time_metrics['avg_task_duration_days']
        self.task_duration_range = time_metrics['avg_task_duration_days_range']
        
        print(f" Overall completion rate: {self.overall_completion_rate * 100}%")
        print(f" Overdue rate: {self.overdue_rate * 100}%")
        print(f" Avg task duration: {self.avg_task_duration} days")
    
    def _calculate_total_tasks(self, users: List, projects: List) -> int:
        """
        Calculate total tasks to generate based on benchmarks.
        
        Uses: 6-12 tasks created per employee per week over 6 months.
        """
        num_users = len(users)
        weeks = 26  # 6 months
        
        # Average tasks per week
        avg_tasks_per_week = (self.tasks_created_per_week_range[0] + 
                             self.tasks_created_per_week_range[1]) / 2
        
        total_tasks = int(num_users * avg_tasks_per_week * weeks)
        
        return total_tasks
    
    def _sample_priority(self) -> str:
        """
        Sample task priority.
        
        Distribution:
            - 20% high
            - 60% medium
            - 20% low
        """
        return random.choices(
            ['high', 'medium', 'low'],
            weights=[0.20, 0.60, 0.20]
        )[0]
    
    def _sample_status(self, priority: str, age_days: int) -> str:
        """
        Sample task status based on priority and age.
        
        Distribution varies by priority (from benchmarks):
            - High priority: 89% completion rate
            - Medium priority: 74% completion rate
            - Low priority: 58% completion rate
        """
        completion_rate = self.completion_by_priority.get(priority, 0.72)
        
        # Recent tasks more likely incomplete
        if age_days < 7:
            completion_rate *= 0.5  # Half as likely to be complete
        
        # Old tasks more likely complete
        if age_days > 60:
            completion_rate = min(0.95, completion_rate * 1.3)
        
        if random.random() < completion_rate:
            return 'completed'
        else:
            # Incomplete tasks
            return random.choices(
                ['in_progress', 'not_started'],
                weights=[0.40, 0.60]
            )[0]
    
    def _sample_task_duration(self) -> int:
        """
        Sample task duration in days.
        
        Distribution: Most tasks 1-14 days (from benchmarks).
        """
        # Use triangular distribution (most common around 3-7 days)
        duration = int(random.triangular(
            self.task_duration_range[0],   # min: 1
            self.task_duration_range[1],   # max: 30
            self.avg_task_duration         # mode: 5.3
        ))
        
        return max(1, duration)
    
    def _generate_task_name(self, project_type: str) -> str:
        """
        Generate realistic task name.
        
        For MVP: Use templates. Later: Use LLM.
        """
        # Task name templates by project type
        templates = {
            'sprint': [
                "Implement {} feature",
                "Fix {} bug",
                "Update {} documentation",
                "Review {} PR",
                "Test {} functionality",
                "Refactor {} module",
                "Deploy {} to production"
            ],
            'bug_tracking': [
                "Fix: {} not working properly",
                "Bug: {} throws error",
                "Issue: {} performance problem",
                "Critical: {} crashes",
                "Bug: {} displays incorrectly"
            ],
            'campaign': [
                "Design {} asset",
                "Write {} copy",
                "Review {} creative",
                "Launch {} campaign",
                "Analyze {} performance"
            ],
            'roadmap': [
                "Plan {} initiative",
                "Research {} approach",
                "Define {} requirements",
                "Evaluate {} options"
            ],
            'ongoing': [
                "Complete {} task",
                "Update {} system",
                "Review {} process",
                "Handle {} request",
                "Process {} items"
            ]
        }
        
        # Placeholder words
        placeholders = [
            "login", "payment", "dashboard", "API", "search", "notification",
            "user profile", "checkout", "analytics", "integration", "settings",
            "onboarding", "reporting", "authentication", "database", "UI"
        ]
        
        template_list = templates.get(project_type, templates['ongoing'])
        template = random.choice(template_list)
        placeholder = random.choice(placeholders)
        
        return template.format(placeholder)
    
    def _generate_task_description(self, task_name: str) -> Optional[str]:
        """
        Generate task description.
        
        For MVP: 40% have descriptions. Later: Use LLM.
        """
        # 60% have no description
        if random.random() < 0.60:
            return None
        
        # Simple description
        descriptions = [
            f"Work on {task_name.lower()}",
            f"Complete {task_name.lower()} as discussed",
            f"Need to {task_name.lower()} before end of sprint",
            f"Follow up on {task_name.lower()}",
            f"Important: {task_name.lower()}"
        ]
        
        return random.choice(descriptions)
    
    def _sample_created_at(self, project_created_at: datetime, 
                      assignee_created_at: datetime) -> datetime:
        """
        Sample task creation timestamp.
        Must be after both project and assignee creation.
        """
        earliest = max(project_created_at, assignee_created_at)
        now = datetime.utcnow()
        
        # Ensure earliest is not in the future
        if earliest > now:
            earliest = now - timedelta(days=random.randint(1, 30))
        
        # Tasks distributed over project lifetime
        days_available = (now - earliest).days
        
        if days_available > 0:
            days_offset = random.randint(0, days_available)
        else:
            days_offset = 0
        
        created_at = earliest + timedelta(days=days_offset)
        
        # Add random hour (business hours with some evening work)
        hour = random.choices(
            list(range(8, 21)),  # 8 AM - 8 PM
            weights=[1]*10 + [0.5]*3  # Less likely in evening
        )[0]
        
        # Build the datetime properly
        created_date = created_at.date()
        created_at = datetime.combine(created_date, datetime.min.time())
        created_at = created_at.replace(hour=hour, minute=random.randint(0, 59), 
                                    second=0, microsecond=0)
        
        # ABSOLUTE FINAL CONSTRAINTS
        # Ensure created_at >= earliest
        if created_at < earliest:
            created_at = earliest
        
        # Ensure created_at <= now
        if created_at > now:
            # Push back to a safe time
            created_at = now - timedelta(hours=random.randint(1, 48))
        
        # Final sanity check
        if created_at > now:
            created_at = now - timedelta(hours=1)
        
        return created_at

    def _sample_due_date(self, created_at: datetime, duration_days: int, 
                        priority: str) -> Optional[date]:
        """
        Sample task due date.
        
        80% of tasks have due dates.
        High priority tasks more likely to have due dates.
        """
        # Due date probability by priority
        has_due_date_prob = {
            'high': 0.95,
            'medium': 0.80,
            'low': 0.60
        }
        
        if random.random() > has_due_date_prob.get(priority, 0.80):
            return None
        
        # Due date = created + duration
        due_datetime = created_at + timedelta(days=duration_days)
        
        return due_datetime.date()
    
    def _sample_completed_at(self, created_at: datetime, due_date: Optional[date],
                            status: str) -> Optional[datetime]:
        """
        Sample task completion timestamp.
        
        Returns None if not completed.
        Completed tasks may be on-time or overdue (18% overdue from benchmarks).
        """
        if status != 'completed':
            return None
        
        now = datetime.utcnow()
        
        if due_date:
            due_datetime = datetime.combine(due_date, datetime.min.time())
            
            # 82% complete on time, 18% overdue
            if random.random() < (1 - self.overdue_rate):
                # Complete on time (between created and due)
                days_available = (due_datetime - created_at).days
                if days_available > 0:
                    completion_offset = random.randint(0, days_available)
                else:
                    completion_offset = 0
                
                completed_at = created_at + timedelta(days=completion_offset)
            else:
                # Complete overdue (1-14 days after due)
                overdue_days = random.randint(1, 14)
                completed_at = due_datetime + timedelta(days=overdue_days)
        else:
            # No due date: complete within 1-30 days of creation
            completion_offset = random.randint(1, 30)
            completed_at = created_at + timedelta(days=completion_offset)
        
        # Ensure not in future
        if completed_at > now:
            days_available = (now - created_at).days
            if days_available > 0:
                completion_offset = random.randint(0, days_available)
                completed_at = created_at + timedelta(days=completion_offset)
            else:
                completed_at = now - timedelta(hours=random.randint(1, 48))
        
        # Add random hour
        hour = random.randint(8, 20)
        completed_at = completed_at.replace(hour=hour, minute=random.randint(0, 59),
                                           second=0, microsecond=0)
        
        # ABSOLUTE FINAL CHECK: guarantee completed_at >= created_at
        if completed_at < created_at:
            # Force it to be after created_at
            completed_at = created_at + timedelta(hours=random.randint(1, 24))
        
        # ABSOLUTE FINAL CHECK: guarantee completed_at <= now
        # But also ensure it stays >= created_at
        if completed_at > now:
            # Check if we have room between created_at and now
            if now > created_at:
                # Yes, pick a time between them
                total_seconds = (now - created_at).total_seconds()
                if total_seconds > 3600:  # At least 1 hour gap
                    offset_seconds = random.randint(3600, int(total_seconds))
                    completed_at = created_at + timedelta(seconds=offset_seconds)
                else:
                    # Very small gap, just use created_at + a bit
                    completed_at = created_at + timedelta(seconds=int(total_seconds * 0.5))
            else:
                # created_at == now or created_at > now (shouldn't happen but handle it)
                completed_at = now
        
        # Ultra-final sanity check - if still broken, force it
        if completed_at < created_at:
            completed_at = created_at + timedelta(seconds=1)
        if completed_at > now:
            completed_at = now
        
        return completed_at

    
    def generate(self, projects: List, sections: List, users: List, 
                tags: List) -> List[Task]:
        """
        Generate tasks for all projects.
        
        Args:
            projects: List of Project objects
            sections: List of Section objects
            users: List of User objects
            tags: List of Tag objects
        
        Returns:
            List of Task model instances
        """
        # Calculate total tasks
        total_tasks = self._calculate_total_tasks(users, projects)
        
        print(f"\nGenerating {total_tasks:,} tasks for {len(projects):,} projects...")
        
        # Group sections by project
        sections_by_project = defaultdict(list)
        for section in sections:
            sections_by_project[section.project_id].append(section)
        
        # Group users by department for assignment
        users_by_dept = defaultdict(list)
        for user in users:
            users_by_dept[user.department].append(user)
        
        # Calculate tasks per project (weighted by team size)
        project_dict = {p.project_id: p for p in projects}
        active_projects = [p for p in projects if p.status in ['active', 'on_hold']]
        
        if not active_projects:
            active_projects = projects  # Fallback
        
        tasks_per_project = total_tasks // len(active_projects)
        
        tasks = []
        
        for project in active_projects:
            # Get sections for this project
            project_sections = sections_by_project.get(project.project_id, [])
            
            if not project_sections:
                continue  # Skip projects without sections
            
            # Get users from matching department
            team_users = users_by_dept.get(project_dict[project.project_id].owner_id, [])
            if not team_users:
                team_users = users  # Fallback
            
            # Generate tasks for this project
            for _ in range(tasks_per_project):
                # Sample task properties
                priority = self._sample_priority()
                duration_days = self._sample_task_duration()
                
                # Assign to user
                assignee = random.choice(team_users)
                
                # Sample creation time
                created_at = self._sample_created_at(project.created_at, assignee.created_at)
                
                # Calculate age
                age_days = (datetime.utcnow() - created_at).days
                
                # Sample status
                status = self._sample_status(priority, age_days)
                
                # Sample due date
                due_date = self._sample_due_date(created_at, duration_days, priority)
                
                # Sample completion time
                completed_at = self._sample_completed_at(created_at, due_date, status)
                
                # Generate name and description
                task_name = self._generate_task_name(project.project_type)
                description = self._generate_task_description(task_name)
                
                # Assign to section based on status
                if status == 'completed':
                    # Find "Done" or last section
                    section = next((s for s in project_sections if 'done' in s.name.lower()), 
                                  project_sections[-1])
                elif status == 'in_progress':
                    # Find "In Progress" or middle section
                    section = next((s for s in project_sections if 'progress' in s.name.lower()),
                                  project_sections[len(project_sections)//2])
                else:
                    # Find "To Do" / "Backlog" or first section
                    section = next((s for s in project_sections 
                                  if any(word in s.name.lower() for word in ['todo', 'backlog', 'new'])),
                                  project_sections[0])
                
                # Determine start_date based on status
                if status == 'not_started':
                    start_date = None
                else:
                    # Task started: set start_date between created and now
                    days_after_created = random.randint(0, min(3, age_days))
                    start_date = (created_at + timedelta(days=days_after_created)).date()

                # Create Task instance
                task = Task(
                    task_id=str(uuid.uuid4()),
                    project_id=project.project_id,
                    section_id=section.section_id,
                    assignee_id=assignee.user_id,
                    created_by=random.choice(team_users).user_id,
                    name=task_name,
                    description=description,
                    priority=priority,
                    due_date=due_date,
                    start_date=start_date,
                    completed=(status == 'completed'),
                    completed_at=completed_at,
                    created_at=created_at,
                    modified_at=completed_at if completed_at else created_at
                )

                
                tasks.append(task)
            
            # Progress indicator
            if len(tasks) % 10000 == 0:
                print(f"  Generated {len(tasks):,} / {total_tasks:,} tasks...")
        
        print(f" Generated {len(tasks):,} tasks")
        
        return tasks


def generate_tasks(projects: List, sections: List, users: List, tags: List,
                  research_dir: str = RESEARCH_DIR) -> List[Task]:
    """
    Main entry point for task generation.
    
    Args:
        projects: List of Project objects
        sections: List of Section objects
        users: List of User objects
        tags: List of Tag objects
        research_dir: Path to research/ directory
    
    Returns:
        List of Task model instances
    """
    generator = TaskGenerator(research_dir)
    tasks = generator.generate(projects, sections, users, tags)
    
    # Log statistics
    print("\n" + "="*70)
    print("TASK GENERATION SUMMARY")
    print("="*70)
    
    # Status breakdown (derived from completed field)
    completed_tasks = sum(1 for task in tasks if task.completed)
    incomplete_tasks = len(tasks) - completed_tasks
    
    print("\nTasks by Status:")
    print(f"  completed       : {completed_tasks:7,} ({completed_tasks/len(tasks)*100:5.1f}%)")
    print(f"  incomplete      : {incomplete_tasks:7,} ({incomplete_tasks/len(tasks)*100:5.1f}%)")
    
    # Priority breakdown
    priority_counts = defaultdict(int)
    for task in tasks:
        priority = task.priority if task.priority else 'none'
        priority_counts[priority] += 1
    
    print("\nTasks by Priority:")
    for priority, count in sorted(priority_counts.items()):
        pct = (count / len(tasks)) * 100
        print(f"  {priority:10s}: {count:7,} ({pct:5.1f}%)")
    
    # Completion stats
    total = len(tasks)
    completion_rate = (completed_tasks / total) * 100 if total > 0 else 0
    
    print(f"\nCompletion Rate: {completed_tasks:,} / {total:,} ({completion_rate:.1f}%)")
    
    # Due date stats
    with_due_date = sum(1 for t in tasks if t.due_date)
    due_date_pct = (with_due_date / total) * 100 if total > 0 else 0
    print(f"Tasks with Due Dates: {with_due_date:,} / {total:,} ({due_date_pct:.1f}%)")
    
    # Overdue stats (completed after due date)
    overdue = sum(1 for t in tasks 
                 if t.completed_at and t.due_date and 
                 t.completed_at.date() > t.due_date)
    overdue_pct = (overdue / completed_tasks) * 100 if completed_tasks > 0 else 0
    print(f"Overdue Completions: {overdue:,} / {completed_tasks:,} ({overdue_pct:.1f}%)")
    
    print("="*70 + "\n")
    
    return tasks


# ============================================================================
# Testing / Standalone Execution
# ============================================================================

if __name__ == "__main__":
    """
    Test task generation.
    Run: python src/generators/tasks.py
    """
    
    print("\n" + "="*70)
    print("TESTING TASK GENERATOR")
    print("="*70 + "\n")
    
    try:
        from organizations import generate_organization
        from users import generate_users
        from teams import generate_teams
        from projects import generate_projects
        from sections import generate_sections
        from tags import generate_tags
        
        org_result = generate_organization(company_size=7000)
        users = generate_users(org_result, target_count=100)  # Small for testing
        teams = generate_teams(org_result, users)
        projects = generate_projects(org_result, teams, users)
        sections = generate_sections(projects)
        tags = generate_tags(org_result)
        
        tasks = generate_tasks(projects, sections, users, tags)
        
        # Validate
        print("\n" + "="*70)
        print("VALIDATION")
        print("="*70)

        # Check all tasks have names
        assert all(t.name for t in tasks), "Missing task names!"
        print(" All tasks have names")

        # Check timestamps
        for task in tasks:
            assert task.created_at <= datetime.utcnow()
            if task.completed_at:
                assert task.completed_at >= task.created_at
                assert task.completed_at <= datetime.utcnow()
        print(" All timestamps consistent")

        # Check due dates
        for task in tasks:
            if task.due_date and task.completed_at:
                # Due date should be after creation
                assert task.due_date >= task.created_at.date()
        print(" All due dates logical")

        # Check completed flag matches completed_at
        for task in tasks:
            if task.completed:
                assert task.completed_at is not None, "Completed task missing completed_at!"
        print(" Completed flag consistent with completed_at")

        # Sample task
        print("\nSample Task:")
        sample = random.choice(tasks)
        print(json.dumps(sample.to_dict(), indent=2))

        print("\n ALL TESTS PASSED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
