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

from models.dependency import TaskDependency


class DependencyGenerator:
    """
    Generates realistic task dependencies.
    
    Strategy:
    - ~10% of tasks have dependencies
    - Most tasks have 1 dependency, some have 2-3
    - Dependencies only within same project
    - No circular dependencies
    - Dependency task must be created before dependent task
    """
    
    def __init__(self):
        pass
    
    def _should_have_dependency(self) -> bool:
        """~10% of tasks have dependencies."""
        return random.random() < 0.10
    
    def _sample_num_dependencies(self) -> int:
        """
        Sample number of dependencies.
        
        Distribution:
        - 1 dependency: 70%
        - 2 dependencies: 20%
        - 3 dependencies: 10%
        """
        return random.choices([1, 2, 3], weights=[0.70, 0.20, 0.10])[0]
    
    def generate(self, tasks: List) -> List[TaskDependency]:
        """
        Generate task dependencies.
        
        Args:
            tasks: List of Task objects
        
        Returns:
            List of TaskDependency model instances
        """
        print(f"\nGenerating task dependencies for {len(tasks):,} tasks...")
        
        # Group tasks by project
        tasks_by_project = defaultdict(list)
        for task in tasks:
            tasks_by_project[task.project_id].append(task)
        
        # Sort tasks within each project by created_at
        for project_id in tasks_by_project:
            tasks_by_project[project_id].sort(key=lambda t: t.created_at)
        
        dependencies = []
        tasks_with_deps = 0
        
        # Track existing dependencies to avoid duplicates
        existing_deps = set()
        
        for project_id, project_tasks in tasks_by_project.items():
            if len(project_tasks) < 2:
                continue
            
            for i, dependent_task in enumerate(project_tasks):
                # Decide if this task has dependencies
                if not self._should_have_dependency():
                    continue
                
                tasks_with_deps += 1
                
                # Get potential blocker tasks (created before this task)
                potential_blockers = project_tasks[:i]
                
                if not potential_blockers:
                    continue
                
                # Sample number of dependencies
                num_deps = min(self._sample_num_dependencies(), len(potential_blockers))
                
                # Sample blocker tasks
                blocker_tasks = random.sample(potential_blockers, num_deps)
                
                # Create dependencies
                for blocker_task in blocker_tasks:
                    # Check for duplicate
                    dep_key = (dependent_task.task_id, blocker_task.task_id)
                    if dep_key in existing_deps:
                        continue
                    
                    existing_deps.add(dep_key)
                    
                    # Create dependency
                    dependency = TaskDependency(
                        dependency_id=str(uuid.uuid4()),
                        dependent_task_id=dependent_task.task_id,
                        dependency_task_id=blocker_task.task_id,
                        created_at=dependent_task.created_at + timedelta(hours=random.randint(1, 24))
                    )
                    
                    dependencies.append(dependency)
        
        print(f" Generated {len(dependencies):,} dependencies")
        print(f"  - {tasks_with_deps:,} tasks have dependencies ({tasks_with_deps/len(tasks)*100:.1f}%)")
        
        return dependencies


def generate_dependencies(tasks: List) -> List[TaskDependency]:
    """
    Main entry point for dependency generation.
    
    Args:
        tasks: List of Task objects
    
    Returns:
        List of TaskDependency model instances
    """
    generator = DependencyGenerator()
    dependencies = generator.generate(tasks)
    
    # Log statistics
    print("\n" + "="*70)
    print("TASK DEPENDENCY SUMMARY")
    print("="*70)
    
    # Dependencies per task
    deps_per_task = defaultdict(int)
    for dep in dependencies:
        deps_per_task[dep.dependent_task_id] += 1
    
    dep_count_dist = defaultdict(int)
    for task_id, count in deps_per_task.items():
        dep_count_dist[count] += 1
    
    print("\nDependencies per Task Distribution:")
    for num_deps in sorted(dep_count_dist.keys()):
        count = dep_count_dist[num_deps]
        pct = (count / len(deps_per_task)) * 100 if deps_per_task else 0
        print(f"  {num_deps} dependency(s): {count:5,} tasks ({pct:5.1f}%)")
    
    avg_deps = len(dependencies) / len(deps_per_task) if deps_per_task else 0
    print(f"\nAverage Dependencies per Task (with deps): {avg_deps:.2f}")
    
    print("="*70 + "\n")
    
    return dependencies


# ============================================================================
# Testing / Standalone Execution
# ============================================================================

if __name__ == "__main__":
    """
    Test dependency generation.
    Run: python src/generators/dependencies.py
    """
    
    print("\n" + "="*70)
    print("TESTING DEPENDENCY GENERATOR")
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
        
        dependencies = generate_dependencies(tasks)
        
        # Validate
        print("\n" + "="*70)
        print("VALIDATION")
        print("="*70)
        
        # Check all reference valid tasks
        task_ids = {t.task_id for t in tasks}
        for dep in dependencies:
            assert dep.dependent_task_id in task_ids, f"Invalid dependent_task_id"
            assert dep.dependency_task_id in task_ids, f"Invalid dependency_task_id"
        print(" All dependencies reference valid tasks")
        
        # Check no self-dependencies
        for dep in dependencies:
            assert dep.dependent_task_id != dep.dependency_task_id, "Self-dependency found!"
        print(" No self-dependencies")
        
        # Check timestamps
        task_dict = {t.task_id: t for t in tasks}
        for dep in dependencies:
            dependent = task_dict[dep.dependent_task_id]
            blocker = task_dict[dep.dependency_task_id]
            assert blocker.created_at <= dependent.created_at, \
                "Blocker created after dependent task!"
        print(" All dependency timestamps valid")
        
        # Sample
        print("\nSample Dependency:")
        sample = random.choice(dependencies)
        print(json.dumps(sample.to_dict(), indent=2))
        
        print("\n ALL TESTS PASSED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
