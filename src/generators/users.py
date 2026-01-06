import json
import random
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from collections import defaultdict
from config import RESEARCH_DIR
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.user import User


class UserGenerator:
    """
    Generates realistic user population for B2B SaaS company.
    
    Strategy:
    - Uses real names from US Census data (names.json)
    - Uses real job titles scraped from companies (job_titles.json)
    - Extracts department from subindustry mapping in companies.json
    - Staggers hiring over 6-month simulation period
    - Models realistic workload capacity and activity patterns
    """
    
    def __init__(self, research_dir: str = RESEARCH_DIR):
        self.research_dir = Path(research_dir)
        self._load_research_data()
        self._build_department_mapping()
    
    def _load_research_data(self):
        """Load all required research data."""
        
        # Load names
        names_path = self.research_dir / "names.json"
        
        if not names_path.exists():
            raise FileNotFoundError(f"names.json not found at {names_path}")
        
        with open(names_path, 'r') as f:
            names_data = json.load(f)
        
        print(f"\nDEBUG: names.json keys: {names_data.keys()}")
        print(f"DEBUG: first_names type: {type(names_data.get('first_names'))}")
        print(f"DEBUG: first_names length: {len(names_data.get('first_names', []))}")
        
        if 'first_names' in names_data and len(names_data['first_names']) > 0:
            print(f"DEBUG: first_names[0] = {names_data['first_names'][0]}")
        
        # Extract names based on structure
        first_names_raw = names_data.get('first_names', [])
        last_names_raw = names_data.get('last_names', [])
        
        # Handle different possible formats
        if first_names_raw and isinstance(first_names_raw[0], dict):
            # Format: [{"name": "Aaren", "gender": "male", ...}, ...]
            self.first_names = [item['name'] for item in first_names_raw if 'name' in item]
        elif first_names_raw and isinstance(first_names_raw[0], str):
            # Format: ["Aaren", "Aaron", ...]
            self.first_names = first_names_raw
        else:
            raise ValueError(f"Unknown first_names format: {first_names_raw[:2] if first_names_raw else 'empty'}")
        
        if last_names_raw and isinstance(last_names_raw[0], dict):
            # Format: [{"name": "SMITH", "count": "2376206", ...}, ...]
            self.last_names = [item['name'] for item in last_names_raw if 'name' in item]
        elif last_names_raw and isinstance(last_names_raw[0], str):
            # Format: ["SMITH", "JOHNSON", ...]
            self.last_names = last_names_raw
        else:
            raise ValueError(f"Unknown last_names format: {last_names_raw[:2] if last_names_raw else 'empty'}")
        
        if not self.first_names:
            raise ValueError("No first names loaded! Check names.json structure")
        if not self.last_names:
            raise ValueError("No last names loaded! Check names.json structure")
        
        # Load job titles
        job_titles_path = self.research_dir / "job_titles.json"
        with open(job_titles_path, 'r') as f:
            job_data = json.load(f)
            self.job_titles = job_data['job_titles']
        
        # Load companies to extract department types from subindustries
        companies_path = self.research_dir / "companies.json"
        with open(companies_path, 'r') as f:
            self.companies = json.load(f)
        
        print(f"\n Loaded {len(self.first_names)} first names")
        print(f" Loaded {len(self.last_names)} last names")
        print(f" Loaded {len(self.job_titles)} job titles")
        print(f" Loaded {len(self.companies)} companies")
    
    def _build_department_mapping(self):
        """
        Extract department types from companies' subindustries.
        
        Examples from companies.json:
            "B2B -> Engineering, Product and Design" → Engineering, Product, Design
            "B2B -> Human Resources" → Human Resources
            "B2B -> Marketing" → Marketing
            "B2B -> Sales" → Sales
        """
        departments = set()
        
        for company in self.companies:
            subindustry = company.get('subindustry', '')
            
            # Extract department after "->"
            if '->' in subindustry:
                dept_part = subindustry.split('->')[-1].strip()
                
                # Handle compound departments like "Engineering, Product and Design"
                if ',' in dept_part:
                    parts = [p.strip() for p in dept_part.replace(' and ', ', ').split(',')]
                    departments.update(parts)
                elif ' and ' in dept_part:
                    parts = [p.strip() for p in dept_part.split(' and ')]
                    departments.update(parts)
                else:
                    departments.add(dept_part)
        
        # Add fallback departments if none extracted
        if not departments:
            departments = {'Engineering', 'Product', 'Sales', 'Marketing', 'Operations', 'Customer Success'}
        
        # Clean up and standardize
        self.departments = sorted(list(departments))
        
        # Create keyword mapping from job titles to departments
        self.dept_keyword_map = {}
        for dept in self.departments:
            dept_lower = dept.lower()
            keywords = dept_lower.split()
            self.dept_keyword_map[dept] = keywords
        
        print(f"\n Extracted {len(self.departments)} unique departments:")
        for dept in self.departments[:10]:  # Show first 10
            print(f"  - {dept}")
        if len(self.departments) > 10:
            print(f"  ... and {len(self.departments) - 10} more")
    
    def _extract_department_from_title(self, job_title: str) -> str:
        """
        Extract department from job title using keyword matching.
        
        Examples:
            "Software Engineer" → "Engineering"
            "Account Executive" → "Sales"
            "Customer Success Manager" → "Human Resources" (closest match)
        """
        title_lower = job_title.lower()
        
        # Score each department based on keyword matches
        scores = {}
        for dept, keywords in self.dept_keyword_map.items():
            score = sum(1 for kw in keywords if kw in title_lower)
            if score > 0:
                scores[dept] = score
        
        if scores:
            # Return department with highest score
            return max(scores.items(), key=lambda x: x[1])[0]
        
        # Fallback: pick random department
        return random.choice(self.departments)
    
    def _sample_job_title_and_department(self) -> Tuple[str, str]:
        """
        Sample job title and extract department.
        Returns (job_title, department).
        """
        job_title = random.choice(self.job_titles)
        department = self._extract_department_from_title(job_title)
        return job_title, department
    
    def _generate_email(self, first_name: str, last_name: str, domain: str, 
                       used_emails: set) -> str:
        """
        Generate unique email address.
        
        Patterns:
            - firstname.lastname@domain.com (most common)
            - firstnamelastname@domain.com
            - firstname.lastname{number}@domain.com (if collision)
        """
        # Clean names (handle uppercase last names from census)
        first = first_name.lower().replace(' ', '').replace("'", '')
        last = last_name.lower().replace(' ', '').replace("'", '')
        
        # Try standard format first
        email = f"{first}.{last}@{domain}"
        
        if email not in used_emails:
            return email
        
        # Try without dot
        email = f"{first}{last}@{domain}"
        if email not in used_emails:
            return email
        
        # Add number suffix
        counter = 1
        while True:
            email = f"{first}.{last}{counter}@{domain}"
            if email not in used_emails:
                return email
            counter += 1
    
    def _sample_role(self) -> str:
        """
        Sample user role.
        
        Distribution:
            - 95% members
            - 4% admins
            - 1% limited (guests, contractors)
        """
        return random.choices(
            ['member', 'admin', 'limited'],
            weights=[0.95, 0.04, 0.01]
        )[0]
    
    def _sample_workload_capacity(self) -> float:
        """
        Sample workload capacity.
        
        Distribution: Normal(1.0, 0.2) truncated to [0.5, 2.0]
        - Most users at 1.0 (100% capacity)
        - Some part-time (0.5-0.8)
        - Some high performers (1.2-2.0)
        """
        capacity = random.gauss(1.0, 0.2)
        return max(0.5, min(2.0, capacity))
    
    def _sample_created_at(self, org_created_at: datetime, index: int, 
                          total_users: int) -> datetime:
        """
        Sample user creation timestamp (hire date).
        
        Strategy:
        - Spread hiring over 6-month period
        - Most hiring in first 3 months (company ramp-up)
        - Some recent hires in last month
        - Follows realistic hiring curve
        """
        days_since_org = 180  # 6 months
        
        # Early employees get earlier dates
        # Use beta distribution for realistic hiring curve
        # Most hiring early, tapers off
        progress = random.betavariate(2, 5)  # Skewed toward early dates
        
        days_offset = int(progress * days_since_org)
        
        created_at = org_created_at + timedelta(days=days_offset)
        
        # Add random hour (8 AM - 5 PM business hours)
        hour = random.randint(8, 17)
        created_at = created_at.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        return created_at
    
    def _sample_last_active(self, created_at: datetime) -> datetime:
        """
        Sample last active timestamp.
        
        Most users active in last 1-7 days.
        Some inactive (10% not active in 30+ days).
        """
        now = datetime.utcnow()
        
        # 90% active in last week
        if random.random() < 0.90:
            days_ago = random.randint(0, 7)
        else:
            # 10% inactive (30-90 days)
            days_ago = random.randint(30, 90)
        
        last_active = now - timedelta(days=days_ago)
        
        # Ensure last_active >= created_at
        if last_active < created_at:
            last_active = created_at + timedelta(days=random.randint(1, 7))
        
        return last_active
    
    def generate(self, organization: Dict, target_count: int = 7000) -> List[User]:
        """
        Generate user population.
        
        Args:
            organization: Organization dict from organizations.py
            target_count: Number of users to generate (5,000-10,000)
        
        Returns:
            List of User model instances
        """
        org = organization['organization']
        metadata = organization['metadata']
        
        users = []
        used_emails = set()
        
        print(f"\nGenerating {target_count:,} users for {org.name}...")
        
        for i in range(target_count):
            # Sample name
            first_name = random.choice(self.first_names)
            last_name = random.choice(self.last_names)
            
            # Capitalize properly (census data has uppercase last names)
            first_name = first_name.capitalize()
            last_name = last_name.capitalize()
            
            name = f"{first_name} {last_name}"
            
            # Generate email
            email = self._generate_email(first_name, last_name, org.domain, used_emails)
            used_emails.add(email)
            
            # Sample job title and department
            job_title, department = self._sample_job_title_and_department()
            
            # Sample role
            role = self._sample_role()
            
            # Sample workload capacity
            workload_capacity = self._sample_workload_capacity()
            
            # Sample timestamps
            created_at = self._sample_created_at(org.created_at, i, target_count)
            last_active_at = self._sample_last_active(created_at)
            
            # Determine if active (95% active, 5% inactive/left company)
            is_active = random.random() < 0.95
            
            # Create User instance
            user = User(
                user_id=str(uuid.uuid4()),
                organization_id=org.organization_id,
                email=email,
                name=name,
                role=role,
                department=department,
                job_title=job_title,
                photo_url=None,  # Could add gravatar URLs later
                is_active=is_active,
                workload_capacity=round(workload_capacity, 2),
                created_at=created_at,
                last_active_at=last_active_at if is_active else None
            )
            
            users.append(user)
            
            # Progress indicator
            if (i + 1) % 1000 == 0:
                print(f"  Generated {i + 1:,} / {target_count:,} users...")
        
        print(f" Generated {len(users):,} users")
        
        return users


def generate_users(organization: Dict, target_count: int = 7000, 
                   research_dir: str = RESEARCH_DIR) -> List[User]:
    """
    Main entry point for user generation.
    
    Args:
        organization: Organization dict from generate_organization()
        target_count: Number of users (default: 7000)
        research_dir: Path to research/ directory
    
    Returns:
        List of User model instances
    
    Example:
        >>> from generators.organizations import generate_organization
        >>> org = generate_organization(company_size=7000)
        >>> users = generate_users(org, target_count=7000)
        >>> print(f"Generated {len(users)} users")
    """
    generator = UserGenerator(research_dir)
    users = generator.generate(organization, target_count)
    
    # Log statistics
    print("\n" + "="*70)
    print("USER GENERATION SUMMARY")
    print("="*70)
    
    # Department breakdown
    dept_counts = defaultdict(int)
    for user in users:
        dept_counts[user.department] += 1
    
    print("\nDepartment Distribution:")
    for dept, count in sorted(dept_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(users)) * 100
        print(f"  {dept:30s}: {count:5,} ({pct:5.1f}%)")
    
    # Role breakdown
    role_counts = defaultdict(int)
    for user in users:
        role_counts[user.role] += 1
    
    print("\nRole Distribution:")
    for role, count in sorted(role_counts.items()):
        pct = (count / len(users)) * 100
        print(f"  {role:15s}: {count:5,} ({pct:5.1f}%)")
    
    # Activity stats
    active_count = sum(1 for u in users if u.is_active)
    print(f"\nActive Users: {active_count:,} / {len(users):,} ({active_count/len(users)*100:.1f}%)")
    
    # Sample users by department
    print("\nSample Users by Department:")
    shown_depts = set()
    for user in users[:50]:  # Check first 50 users
        if user.department not in shown_depts:
            print(f"  {user.name:25s} | {user.job_title:40s} | {user.department}")
            shown_depts.add(user.department)
            if len(shown_depts) >= 5:
                break
    
    print("="*70 + "\n")
    
    return users


# ============================================================================
# Testing / Standalone Execution
# ============================================================================

if __name__ == "__main__":
    """
    Test user generation.
    Run: python src/generators/users.py
    """
    
    print("\n" + "="*70)
    print("TESTING USER GENERATOR")
    print("="*70 + "\n")
    
    try:
        # First generate organization
        from organizations import generate_organization
        
        org_result = generate_organization(company_size=7000)
        
        # Generate users (small batch for testing)
        users = generate_users(org_result, target_count=100)
        
        # Validate
        print("\n" + "="*70)
        print("VALIDATION")
        print("="*70)
        
        # Check unique emails
        emails = [u.email for u in users]
        assert len(emails) == len(set(emails)), "Duplicate emails found!"
        print(" All emails unique")
        
        # Check all have valid departments
        assert all(u.department for u in users), "Missing departments!"
        print(" All users have departments")
        
        # Check all have valid job titles
        assert all(u.job_title for u in users), "Missing job titles!"
        print(" All users have job titles")
        
        # Check timestamps logical
        for user in users:
            assert user.created_at >= org_result['organization'].created_at
            if user.last_active_at:
                assert user.last_active_at >= user.created_at
        print(" All timestamps consistent")
        
        # Sample users
        print("\nSample Users:")
        for user in random.sample(users, min(3, len(users))):
            print(f"\n  Name: {user.name}")
            print(f"  Email: {user.email}")
            print(f"  Job Title: {user.job_title}")
            print(f"  Department: {user.department}")
            print(f"  Role: {user.role}")
            print(f"  Workload Capacity: {user.workload_capacity}")
            print(f"  Active: {user.is_active}")
        
        print("\n ALL TESTS PASSED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
