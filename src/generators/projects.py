import json
import random
import uuid
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import List, Dict, Tuple
from collections import defaultdict
from config import RESEARCH_DIR
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.project import Project


class ProjectGenerator:
    """
    Generates realistic project structure for B2B SaaS company.
    
    Strategy:
    - Uses project templates from research
    - 3-5 projects per team (active + archived)
    - Varies by project type (sprint, campaign, bug tracking, etc.)
    - Realistic timeline and completion patterns
    """
    
    def __init__(self, research_dir: str = RESEARCH_DIR):
        self.research_dir = Path(research_dir)
        self._load_research_data()
    
    def _load_research_data(self):
        """Load research data for project generation."""
        
        # Load project templates
        templates_path = self.research_dir / "project_templates.json"
        
        if templates_path.exists():
            with open(templates_path, 'r') as f:
                data = json.load(f)
                
                print(f"\nDEBUG: project_templates.json type: {type(data)}")
                
                # Handle different possible structures
                if isinstance(data, list):
                    # Direct list of templates
                    self.templates = data
                    print(f"DEBUG: Loaded list with {len(data)} items")
                    if data:
                        print(f"DEBUG: First template keys: {data[0].keys()}")
                elif isinstance(data, dict):
                    print(f"DEBUG: Dict keys: {list(data.keys())}")
                    
                    if 'templates' in data:
                        self.templates = data['templates']
                    elif 'project_types' in data:
                        self.templates = data['project_types']
                    else:
                        # Try to extract templates from dict values
                        # Maybe structure is: {"sprint": {...}, "ongoing": {...}}
                        print("⚠ Converting dict structure to template list")
                        self.templates = []
                        for key, value in data.items():
                            if isinstance(value, dict):
                                template = value.copy()
                                if 'type' not in template:
                                    template['type'] = key
                                self.templates.append(template)
                        
                        if not self.templates:
                            print(f"⚠ Could not parse project_templates.json structure")
                            self._create_fallback_templates()
                            return
                else:
                    print(f"⚠ Unknown data type: {type(data)}")
                    self._create_fallback_templates()
                    return
                
                # Validate templates have required keys
                if self.templates:
                    sample = self.templates[0]
                    print(f"DEBUG: Sample template keys: {list(sample.keys())}")
                    
                    # Ensure all templates have 'type' key
                    for i, template in enumerate(self.templates):
                        if 'type' not in template:
                            print(f"⚠ Template {i} missing 'type' key, keys: {list(template.keys())}")
                            self._create_fallback_templates()
                            return
            
            print(f" Loaded {len(self.templates)} project templates")
        else:
            # Fallback: create basic templates
            print("⚠ project_templates.json not found, using fallback templates")
            self._create_fallback_templates()
        
        # Load benchmarks
        benchmarks_path = self.research_dir / "benchmarks.json"
        with open(benchmarks_path, 'r') as f:
            self.benchmarks = json.load(f)
        
        # Extract project metrics
        self.sprint_duration = self.benchmarks['time_metrics']['sprint_duration']
        self.project_duration_median = self.benchmarks['time_metrics']['project_duration_median']
        self.project_duration_ranges = self.benchmarks['time_metrics']['project_duration_days_range']
        
        print(f" Sprint duration: {self.sprint_duration} days")
        print(f" Project median duration: {self.project_duration_median} days")

    def _create_fallback_templates(self):
        """Create basic project templates if file doesn't exist."""
        self.templates = [
            {
                "type": "sprint",
                "weight": 0.35,
                "duration_days_range": [10, 21],
                "typical_sections": ["Backlog", "In Progress", "Review", "Done"]
            },
            {
                "type": "ongoing",
                "weight": 0.25,
                "duration_days_range": [60, 365],
                "typical_sections": ["To Do", "In Progress", "Done"]
            },
            {
                "type": "bug_tracking",
                "weight": 0.15,
                "duration_days_range": [30, 180],
                "typical_sections": ["New", "Triaged", "In Progress", "Fixed", "Closed"]
            },
            {
                "type": "campaign",
                "weight": 0.15,
                "duration_days_range": [30, 90],
                "typical_sections": ["Planning", "Creative", "Execution", "Analysis"]
            },
            {
                "type": "roadmap",
                "weight": 0.10,
                "duration_days_range": [90, 365],
                "typical_sections": ["Now", "Next", "Later", "Parking Lot"]
            }
        ]
    
    def _sample_project_type(self) -> Dict:
        """Sample project type based on template weights."""
        types = [t['type'] for t in self.templates]
        weights = [t['weight'] for t in self.templates]
        
        selected_type = random.choices(types, weights=weights)[0]
        
        return next(t for t in self.templates if t['type'] == selected_type)
    
    def _generate_project_name(self, project_type: str, team_type: str) -> str:
        """
        Generate realistic project name.
        
        For MVP: Use templates. Later: Use LLM.
        
        Examples:
            Engineering + sprint → "Q1 2026 Sprint 1"
            Marketing + campaign → "Product Launch Campaign"
            Engineering + bug_tracking → "Backend Bug Tracker"
        """
        # Name patterns by type
        if project_type == 'sprint':
            quarter = random.choice(['Q1', 'Q2', 'Q3', 'Q4'])
            year = random.choice([2025, 2026])
            sprint_num = random.randint(1, 12)
            return f"{team_type} {quarter} {year} Sprint {sprint_num}"
        
        elif project_type == 'campaign':
            campaigns = [
                f"{team_type} Product Launch",
                f"{team_type} Growth Campaign",
                f"Holiday Campaign {random.randint(1, 4)}",
                f"{team_type} Brand Awareness",
                f"Lead Generation {random.choice(['Q1', 'Q2', 'Q3', 'Q4'])}"
            ]
            return random.choice(campaigns)
        
        elif project_type == 'bug_tracking':
            return f"{team_type} Bug Tracker"
        
        elif project_type == 'roadmap':
            year = random.choice([2025, 2026])
            return f"{team_type} {year} Roadmap"
        
        elif project_type == 'ongoing':
            ongoing_names = [
                f"{team_type} Operations",
                f"{team_type} Daily Tasks",
                f"{team_type} Backlog",
                f"{team_type} Workspace"
            ]
            return random.choice(ongoing_names)
        
        else:
            return f"{team_type} {project_type.replace('_', ' ').title()} Project"
    
    def _generate_project_description(self, project_name: str, project_type: str) -> str:
        """
        Generate project description.
        
        For MVP: Simple templates. Later: Use LLM.
        """
        # 20% have no description
        if random.random() < 0.20:
            return None
        
        descriptions = {
            'sprint': f"Sprint project for {project_name}. Track tasks and deliverables for this sprint cycle.",
            'campaign': f"Marketing campaign project. Plan, execute, and measure campaign performance.",
            'bug_tracking': f"Track and resolve bugs and technical issues.",
            'roadmap': f"Product roadmap planning and prioritization.",
            'ongoing': f"Ongoing operational tasks and maintenance work."
        }
        
        return descriptions.get(project_type, f"Project workspace for {project_name}")
    
    def _sample_project_status(self, project_type: str, age_days: int) -> str:
        """
        Sample project status based on type and age.
        
        Distribution:
            - 50% active
            - 30% completed
            - 15% archived
            - 5% on_hold
        """
        # Recent projects more likely active
        if age_days < 30:
            weights = [0.75, 0.10, 0.10, 0.05]  # Mostly active
        elif age_days < 90:
            weights = [0.50, 0.30, 0.15, 0.05]  # Normal distribution
        else:
            # Old projects more likely completed/archived
            weights = [0.20, 0.50, 0.25, 0.05]
        
        return random.choices(
            ['active', 'completed', 'archived', 'on_hold'],
            weights=weights
        )[0]
    
    def _sample_project_privacy(self) -> str:
        """
        Sample project privacy.
        
        Distribution:
            - 80% team (most common)
            - 15% public
            - 5% private (sensitive projects)
        """
        return random.choices(
            ['team', 'public', 'private'],
            weights=[0.80, 0.15, 0.05]
        )[0]
    
    def _sample_project_color(self) -> str:
        """Sample project color for visual identification."""
        colors = [
            'blue', 'green', 'red', 'yellow', 'purple', 'orange',
            'pink', 'teal', 'brown', 'gray', 'light-blue', 'light-green'
        ]
        return random.choice(colors)
    
    def _sample_project_dates(self, org_created_at: datetime, 
                             team_created_at: datetime,
                             template: Dict) -> Tuple[date, date, datetime]:
        """
        Sample project start, due, and completion dates.
        
        Returns: (start_date, due_date, completed_at)
        """
        # Project starts after team creation
        earliest = max(org_created_at, team_created_at)
        now = datetime.utcnow()
        
        # Sample start date (distributed over org history)
        days_since_earliest = (now - earliest).days
        start_offset = random.randint(0, max(1, days_since_earliest))
        
        start_datetime = earliest + timedelta(days=start_offset)
        start_date = start_datetime.date()
        
        # Sample duration from template range
        duration_range = template.get('duration_days_range', [14, 90])
        duration = random.randint(duration_range[0], duration_range[1])
        
        due_date = start_date + timedelta(days=duration)
        
        return start_date, due_date
    
    def _sample_completed_at(self, start_date: date, due_date: date, 
                        status: str) -> datetime:
        """
        Sample completion timestamp if project is completed.
        
        Returns None if not completed.
        """
        if status not in ['completed', 'archived']:
            return None
        
        # Completed between start and due date (or slightly after)
        start_dt = datetime.combine(start_date, datetime.min.time())
        due_dt = datetime.combine(due_date, datetime.min.time())
        
        now = datetime.utcnow()
        
        # 70% complete on time, 30% complete late
        if random.random() < 0.70:
            # Completed on time (between start and due)
            total_days = (due_dt - start_dt).days
            if total_days > 0:
                completion_offset = random.randint(int(total_days * 0.5), total_days)
            else:
                completion_offset = 0
            completed_at = start_dt + timedelta(days=completion_offset)
        else:
            # Completed late (up to 50% overrun after due date)
            overrun_days = random.randint(1, max(1, int((due_dt - start_dt).days * 0.5)))
            completed_at = due_dt + timedelta(days=overrun_days)
        
        # Ensure not in future
        if completed_at > now:
            # Complete it somewhere between start and now
            days_available = (now - start_dt).days
            if days_available > 0:
                completion_offset = random.randint(0, days_available)
                completed_at = start_dt + timedelta(days=completion_offset)
            else:
                # Start date is very recent, complete it now
                completed_at = now - timedelta(hours=random.randint(1, 48))
        
        # Add random hour (business hours)
        hour = random.randint(8, 17)
        completed_at = completed_at.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        # ABSOLUTE FINAL CONSTRAINT: Ensure completed_at >= start_date
        # This handles all edge cases including hour replacement pushing it back
        if completed_at.date() < start_date:
            # Force it to be on or after start_date
            completed_at = datetime.combine(start_date, datetime.min.time())
            completed_at = completed_at.replace(hour=random.randint(8, 17), minute=0, second=0, microsecond=0)
        
        # ABSOLUTE FINAL CONSTRAINT: Ensure not in future
        if completed_at > now:
            completed_at = now - timedelta(hours=random.randint(1, 48))
            completed_at = completed_at.replace(hour=random.randint(8, 17), minute=0, second=0, microsecond=0)
        
        return completed_at

    def _sample_created_at(self, start_date: date) -> datetime:
        """Sample project creation timestamp (usually few days before start)."""
        start_dt = datetime.combine(start_date, datetime.min.time())
        
        # Created 0-14 days before start
        days_before = random.randint(0, 14)
        created_at = start_dt - timedelta(days=days_before)
        
        # Add random hour
        hour = random.randint(8, 17)
        created_at = created_at.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        return created_at
    
    def generate(self, organization: Dict, teams: List, users: List) -> List[Project]:
        """
        Generate projects for all teams.
        
        Args:
            organization: Organization dict from organizations.py
            teams: List of Team objects from teams.py
            users: List of User objects from users.py
        
        Returns:
            List of Project model instances
        """
        org = organization['organization']
        
        # Calculate projects per team (3-5 projects per team)
        projects_per_team_range = [3, 5]
        
        print(f"\nGenerating projects for {len(teams)} teams...")
        
        projects = []
        
        for team in teams:
            num_projects = random.randint(projects_per_team_range[0], projects_per_team_range[1])
            
            # Get team members to assign as project owners
            team_users = [u for u in users if u.department == team.team_type]
            if not team_users:
                team_users = users  # Fallback
            
            for _ in range(num_projects):
                # Sample project type
                template = self._sample_project_type()
                project_type = template['type']
                
                # Generate name and description
                project_name = self._generate_project_name(project_type, team.team_type)
                description = self._generate_project_description(project_name, project_type)
                
                # Sample dates
                start_date, due_date = self._sample_project_dates(
                    org.created_at, 
                    team.created_at, 
                    template
                )
                
                # Calculate age
                age_days = (datetime.utcnow().date() - start_date).days
                
                # Sample status
                status = self._sample_project_status(project_type, age_days)
                
                # Sample completion date if applicable
                completed_at = self._sample_completed_at(start_date, due_date, status)
                
                # Sample project owner (active team member)
                owner = random.choice(team_users)
                
                # Sample other properties
                privacy = self._sample_project_privacy()
                color = self._sample_project_color()
                created_at = self._sample_created_at(start_date)
                
                # Create Project instance
                project = Project(
                    project_id=str(uuid.uuid4()),
                    organization_id=org.organization_id,
                    team_id=team.team_id,
                    name=project_name,
                    description=description,
                    owner_id=owner.user_id,
                    project_type=project_type,
                    privacy=privacy,
                    status=status,
                    color=color,
                    start_date=start_date,
                    due_date=due_date,
                    completed_at=completed_at,
                    created_at=created_at
                )
                
                projects.append(project)
        
        print(f" Generated {len(projects):,} projects")
        print(f"  - Avg {len(projects) / len(teams):.1f} projects per team")
        
        return projects


def generate_projects(organization: Dict, teams: List, users: List,
                     research_dir: str = RESEARCH_DIR) -> List[Project]:
    """
    Main entry point for project generation.
    
    Args:
        organization: Organization dict from generate_organization()
        teams: List of Team objects from generate_teams()
        users: List of User objects from generate_users()
        research_dir: Path to research/ directory
    
    Returns:
        List of Project model instances
    """
    generator = ProjectGenerator(research_dir)
    projects = generator.generate(organization, teams, users)
    
    # Log statistics
    print("\n" + "="*70)
    print("PROJECT GENERATION SUMMARY")
    print("="*70)
    
    # Type breakdown
    type_counts = defaultdict(int)
    for project in projects:
        type_counts[project.project_type] += 1
    
    print("\nProjects by Type:")
    for ptype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(projects)) * 100
        print(f"  {ptype:20s}: {count:4d} ({pct:5.1f}%)")
    
    # Status breakdown
    status_counts = defaultdict(int)
    for project in projects:
        status_counts[project.status] += 1
    
    print("\nProjects by Status:")
    for status, count in sorted(status_counts.items()):
        pct = (count / len(projects)) * 100
        print(f"  {status:15s}: {count:4d} ({pct:5.1f}%)")
    
    # Privacy breakdown
    privacy_counts = defaultdict(int)
    for project in projects:
        privacy_counts[project.privacy] += 1
    
    print("\nProjects by Privacy:")
    for privacy, count in sorted(privacy_counts.items()):
        pct = (count / len(projects)) * 100
        print(f"  {privacy:10s}: {count:4d} ({pct:5.1f}%)")
    
    # Sample projects
    print("\nSample Projects:")
    for project in random.sample(projects, min(5, len(projects))):
        print(f"  {project.name:50s} | {project.project_type:15s} | {project.status}")
    
    print("="*70 + "\n")
    
    return projects


# ============================================================================
# Testing / Standalone Execution
# ============================================================================

if __name__ == "__main__":
    """
    Test project generation.
    Run: python src/generators/projects.py
    """
    
    print("\n" + "="*70)
    print("TESTING PROJECT GENERATOR")
    print("="*70 + "\n")
    
    try:
        from organizations import generate_organization
        from users import generate_users
        from teams import generate_teams
        
        org_result = generate_organization(company_size=7000)
        users = generate_users(org_result, target_count=500)
        teams = generate_teams(org_result, users)
        projects = generate_projects(org_result, teams, users)
        
        # Validate
        print("\n" + "="*70)
        print("VALIDATION")
        print("="*70)
        
        # Check all projects have names
        assert all(p.name for p in projects), "Missing project names!"
        print(" All projects have names")
        
        # Check dates logical
        for project in projects:
            assert project.start_date <= project.due_date
            if project.completed_at:
                assert project.completed_at.date() >= project.start_date
        print(" All dates logical")
        
        # Check timestamps
        for project in projects:
            assert project.created_at <= datetime.combine(project.start_date, datetime.max.time())
        print(" All timestamps consistent")
        
        # Sample project
        print("\nSample Project:")
        sample = random.choice(projects)
        print(json.dumps(sample.to_dict(), indent=2))
        
        print("\n ALL TESTS PASSED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
