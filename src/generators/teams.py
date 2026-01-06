import json
import random
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict
from config import RESEARCH_DIR
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.team import Team


class TeamGenerator:
    """
    Generates realistic team structure for B2B SaaS company.
    
    Strategy:
    - Extracts department types from companies.json subindustries
    - Uses benchmarks for team size (6-12 people avg)
    - Creates multiple teams per department for large companies
    - Follows realistic naming patterns (Engineering - Platform, Engineering - Mobile)
    """
    
    def __init__(self, research_dir: str = RESEARCH_DIR):
        self.research_dir = Path(research_dir)
        self._load_research_data()
        self._extract_departments()
    
    def _load_research_data(self):
        """Load research data for team generation."""
        
        # Load companies for department extraction
        companies_path = self.research_dir / "companies.json"
        with open(companies_path, 'r') as f:
            self.companies = json.load(f)
        
        # Load benchmarks for team sizing
        benchmarks_path = self.research_dir / "benchmarks.json"
        with open(benchmarks_path, 'r') as f:
            self.benchmarks = json.load(f)
        
        # Extract team structure metrics
        team_structure = self.benchmarks.get('team_structure', {})
        self.avg_team_size_range = team_structure.get('avg_team_size_range', [6, 12])
        self.teams_per_100_employees_range = team_structure.get('teams_per_100_employees_range', [8, 15])
        
        print(f" Loaded {len(self.companies)} companies")
        print(f" Team size range: {self.avg_team_size_range}")
        print(f" Teams per 100 employees: {self.teams_per_100_employees_range}")
    
    def _extract_departments(self):
        """
        Extract unique department types from companies' subindustries.
        
        Examples:
            "B2B -> Engineering, Product and Design" → ["Engineering", "Product", "Design"]
            "B2B -> Human Resources" → ["Human Resources"]
            "B2B -> Marketing" → ["Marketing"]
        """
        departments = set()
        
        for company in self.companies:
            subindustry = company.get('subindustry', '')
            
            # Extract department after "->"
            if '->' in subindustry:
                dept_part = subindustry.split('->')[-1].strip()
                
                # Handle compound departments
                if ',' in dept_part:
                    parts = [p.strip() for p in dept_part.replace(' and ', ', ').split(',')]
                    departments.update(parts)
                elif ' and ' in dept_part:
                    parts = [p.strip() for p in dept_part.split(' and ')]
                    departments.update(parts)
                else:
                    departments.add(dept_part)
        
        # Add core departments if missing (fallback)
        core_departments = {
            'Engineering', 'Product', 'Sales', 'Marketing', 
            'Customer Success', 'Operations', 'Finance', 'Human Resources'
        }
        departments.update(core_departments)
        
        self.departments = sorted(list(departments))
        
        print(f"\n Extracted {len(self.departments)} unique departments:")
        for dept in self.departments:
            print(f"  - {dept}")
    
    def _get_team_specializations(self, department: str) -> List[str]:
        """
        Get realistic team specializations/subdivisions for a department.
        
        Examples:
            Engineering → ["Platform", "Mobile", "Backend", "Frontend", "Infrastructure"]
            Sales → ["Enterprise", "SMB", "Partnerships"]
            Marketing → ["Growth", "Content", "Product Marketing", "Brand"]
        """
        specializations = {
            'Engineering': [
                'Platform', 'Mobile', 'Backend', 'Frontend', 'Infrastructure',
                'Data', 'Security', 'DevOps', 'API', 'Core', 'Growth'
            ],
            'Product': [
                'Core Product', 'Growth', 'Platform', 'Mobile', 'Enterprise',
                'Analytics', 'Integrations'
            ],
            'Design': [
                'Product Design', 'UX Research', 'Brand Design', 'Marketing Design'
            ],
            'Sales': [
                'Enterprise', 'Mid-Market', 'SMB', 'Partnerships', 'Inside Sales',
                'Sales Development', 'Account Management'
            ],
            'Marketing': [
                'Growth', 'Content', 'Product Marketing', 'Brand', 'Demand Generation',
                'Events', 'Communications', 'Performance Marketing'
            ],
            'Customer Success': [
                'Enterprise', 'SMB', 'Onboarding', 'Support', 'Solutions'
            ],
            'Operations': [
                'Business Operations', 'Revenue Operations', 'IT', 'Facilities'
            ],
            'Finance': [
                'Accounting', 'FP&A', 'Revenue', 'Payroll'
            ],
            'Human Resources': [
                'Recruiting', 'People Operations', 'Talent', 'Compensation'
            ],
            'Legal': [
                'Contracts', 'Compliance', 'Privacy'
            ],
            'Data': [
                'Analytics', 'Data Engineering', 'Data Science', 'Business Intelligence'
            ],
            'Security': [
                'InfoSec', 'Compliance', 'Privacy'
            ]
        }
        
        # Return specializations for department, or generic subdivisions
        if department in specializations:
            return specializations[department]
        else:
            # Generic subdivisions
            return ['Team A', 'Team B', 'Team C']
    
    def _calculate_teams_needed(self, num_employees: int) -> int:
        """
        Calculate number of teams needed based on employee count.
        Uses benchmarks: 8-15 teams per 100 employees.
        """
        # Sample from benchmark range
        teams_per_100 = random.uniform(
            self.teams_per_100_employees_range[0],
            self.teams_per_100_employees_range[1]
        )
        
        teams_needed = int((num_employees / 100) * teams_per_100)
        
        # Ensure minimum teams
        return max(10, teams_needed)
    
    def _sample_team_size(self) -> int:
        """
        Sample realistic team size.
        Uses benchmarks: 6-12 people per team (most common 7-9).
        """
        # Weight toward middle of range (7-9 people)
        size = int(random.triangular(
            self.avg_team_size_range[0],  # min: 6
            self.avg_team_size_range[1],  # max: 12
            8.5  # mode: 8-9 people
        ))
        
        return size
    
    def _distribute_teams_by_department(self, total_teams: int) -> Dict[str, int]:
        """
        Distribute teams across departments based on typical B2B SaaS structure.
        
        Typical distribution:
            - Engineering: 30-40%
            - Sales: 20-25%
            - Customer Success: 15-20%
            - Product: 8-12%
            - Marketing: 8-10%
            - Operations: 5-8%
            - Others: 5-10%
        """
        distribution = {
            'Engineering': 0.35,
            'Sales': 0.22,
            'Customer Success': 0.18,
            'Product': 0.10,
            'Marketing': 0.09,
            'Operations': 0.06
        }
        
        # Allocate teams
        dept_teams = {}
        allocated = 0
        
        for dept in self.departments:
            if dept in distribution:
                count = int(total_teams * distribution[dept])
            else:
                # Other departments get fewer teams
                count = max(1, int(total_teams * 0.02))
            
            dept_teams[dept] = max(1, count)  # At least 1 team per dept
            allocated += dept_teams[dept]
        
        # Distribute remaining teams to Engineering (largest dept)
        remaining = total_teams - allocated
        if 'Engineering' in dept_teams and remaining > 0:
            dept_teams['Engineering'] += remaining
        
        return dept_teams
    
    def _sample_team_privacy(self) -> str:
        """
        Sample team privacy setting.
        
        Distribution:
            - 85% public (most teams)
            - 12% private (sensitive teams)
            - 3% secret (executive, security, legal)
        """
        return random.choices(
            ['public', 'private', 'secret'],
            weights=[0.85, 0.12, 0.03]
        )[0]
    
    def _sample_created_at(self, org_created_at: datetime, team_index: int, 
                          total_teams: int) -> datetime:
        """
        Sample team creation timestamp.
        
        Strategy:
        - Core teams (Engineering, Sales) created early
        - Most teams created in first 3 months
        - Specialized teams created later
        """
        days_since_org = 180  # 6 months
        
        # Early teams get earlier dates
        progress = random.betavariate(1.5, 4)  # Skewed toward early dates
        days_offset = int(progress * days_since_org)
        
        created_at = org_created_at + timedelta(days=days_offset)
        
        # Add random hour (business hours)
        hour = random.randint(8, 17)
        created_at = created_at.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        return created_at
    
    def generate(self, organization: Dict, users: List) -> List[Team]:
        """
        Generate team structure.
        
        Args:
            organization: Organization dict from organizations.py
            users: List of User objects from users.py
        
        Returns:
            List of Team model instances
        """
        org = organization['organization']
        num_employees = len(users)
        
        # Calculate teams needed
        total_teams = self._calculate_teams_needed(num_employees)
        
        print(f"\nGenerating teams for {num_employees:,} employees...")
        print(f"Target: {total_teams} teams ({total_teams / (num_employees/100):.1f} per 100 employees)")
        
        # Distribute teams by department
        dept_teams = self._distribute_teams_by_department(total_teams)
        
        teams = []
        team_index = 0
        
        for department in self.departments:
            num_teams_for_dept = dept_teams.get(department, 0)
            
            if num_teams_for_dept == 0:
                continue
            
            specializations = self._get_team_specializations(department)
            
            # Create teams for this department
            for i in range(num_teams_for_dept):
                # Team naming
                if num_teams_for_dept == 1:
                    # Single team: just department name
                    team_name = department
                else:
                    # Multiple teams: add specialization
                    if i < len(specializations):
                        specialization = specializations[i]
                    else:
                        # Cycle through specializations
                        specialization = specializations[i % len(specializations)]
                        if i >= len(specializations):
                            specialization = f"{specialization} {i // len(specializations) + 1}"
                    
                    team_name = f"{department} - {specialization}"
                
                # Sample team properties
                privacy = self._sample_team_privacy()
                created_at = self._sample_created_at(org.created_at, team_index, total_teams)
                
                # Generate description
                description = f"{department} team focused on {team_name.split(' - ')[-1] if ' - ' in team_name else 'core operations'}"
                
                # Create Team instance
                team = Team(
                    team_id=str(uuid.uuid4()),
                    organization_id=org.organization_id,
                    name=team_name,
                    team_type=department,
                    description=description,
                    privacy=privacy,
                    created_at=created_at
                )
                
                teams.append(team)
                team_index += 1
            
            if num_teams_for_dept > 0:
                print(f"   Created {num_teams_for_dept} {department} teams")
        
        print(f"\n Generated {len(teams)} teams total")
        
        return teams


def generate_teams(organization: Dict, users: List, 
                   research_dir: str = RESEARCH_DIR) -> List[Team]:
    """
    Main entry point for team generation.
    
    Args:
        organization: Organization dict from generate_organization()
        users: List of User objects from generate_users()
        research_dir: Path to research/ directory
    
    Returns:
        List of Team model instances
    
    Example:
        >>> from generators.organizations import generate_organization
        >>> from generators.users import generate_users
        >>> org = generate_organization()
        >>> users = generate_users(org, target_count=7000)
        >>> teams = generate_teams(org, users)
    """
    generator = TeamGenerator(research_dir)
    teams = generator.generate(organization, users)
    
    # Log statistics
    print("\n" + "="*70)
    print("TEAM GENERATION SUMMARY")
    print("="*70)
    
    # Department breakdown
    dept_counts = defaultdict(int)
    for team in teams:
        dept_counts[team.team_type] += 1
    
    print("\nTeams by Department:")
    for dept, count in sorted(dept_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(teams)) * 100
        print(f"  {dept:30s}: {count:3d} ({pct:5.1f}%)")
    
    # Privacy breakdown
    privacy_counts = defaultdict(int)
    for team in teams:
        privacy_counts[team.privacy] += 1
    
    print("\nPrivacy Distribution:")
    for privacy, count in sorted(privacy_counts.items()):
        pct = (count / len(teams)) * 100
        print(f"  {privacy:10s}: {count:3d} ({pct:5.1f}%)")
    
    # Sample teams
    print("\nSample Teams:")
    for team in random.sample(teams, min(10, len(teams))):
        print(f"  {team.name:50s} | {team.privacy:8s} | {team.team_type}")
    
    print("="*70 + "\n")
    
    return teams


# ============================================================================
# Testing / Standalone Execution
# ============================================================================

if __name__ == "__main__":
    """
    Test team generation.
    Run: python src/generators/teams.py
    """
    
    print("\n" + "="*70)
    print("TESTING TEAM GENERATOR")
    print("="*70 + "\n")
    
    try:
        # Generate organization and users first
        from organizations import generate_organization
        from users import generate_users
        
        org_result = generate_organization(company_size=7000)
        users = generate_users(org_result, target_count=500)  # Small batch for testing
        
        # Generate teams
        teams = generate_teams(org_result, users)
        
        # Validate
        print("\n" + "="*70)
        print("VALIDATION")
        print("="*70)
        
        # Check all teams have names
        assert all(t.name for t in teams), "Missing team names!"
        print(" All teams have names")
        
        # Check all teams have valid team_type
        assert all(t.team_type for t in teams), "Missing team types!"
        print(" All teams have types")
        
        # Check timestamps logical
        for team in teams:
            assert team.created_at >= org_result['organization'].created_at
        print(" All timestamps consistent")
        
        # Check organization_id matches
        for team in teams:
            assert team.organization_id == org_result['organization'].organization_id
        print(" All teams linked to organization")
        
        # Sample team details
        print("\nSample Team Details:")
        sample = random.choice(teams)
        print(json.dumps(sample.to_dict(), indent=2))
        
        print("\n ALL TESTS PASSED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
