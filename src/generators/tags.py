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

from models.tag import Tag


class TagGenerator:
    """
    Generates realistic tag library for organization.
    
    Strategy:
    - Common workflow tags (urgent, blocked, needs-review)
    - Priority tags (p0, p1, p2, p3)
    - Department-specific tags extracted from companies.json
    - Technical tags (bug, enhancement, documentation)
    """
    
    def __init__(self, research_dir: str = RESEARCH_DIR):
        self.research_dir = Path(research_dir)
        self._load_research_data()
        self._build_tag_library()
    
    def _load_research_data(self):
        """Load companies.json to extract department-specific tags."""
        companies_path = self.research_dir / "companies.json"
        with open(companies_path, 'r') as f:
            self.companies = json.load(f)
        
        print(f" Loaded {len(self.companies)} companies")
    
    def _extract_departments(self) -> List[str]:
        """Extract unique departments from companies' subindustries."""
        departments = set()
        
        for company in self.companies:
            subindustry = company.get('subindustry', '')
            
            if '->' in subindustry:
                dept_part = subindustry.split('->')[-1].strip()
                
                if ',' in dept_part:
                    parts = [p.strip() for p in dept_part.replace(' and ', ', ').split(',')]
                    departments.update(parts)
                elif ' and ' in dept_part:
                    parts = [p.strip() for p in dept_part.split(' and ')]
                    departments.update(parts)
                else:
                    departments.add(dept_part)
        
        return sorted(list(departments))
    
    def _extract_tech_tags(self) -> List[str]:
        """Extract technology/domain tags from companies' tags field."""
        tech_tags = set()
        
        for company in self.companies:
            company_tags = company.get('tags', [])
            for tag in company_tags:
                # Clean and add
                tag_clean = tag.strip().lower().replace(' ', '-')
                if tag_clean and len(tag_clean) <= 30:  # Reasonable length
                    tech_tags.add(tag_clean)
        
        return sorted(list(tech_tags))
    
    def _build_tag_library(self):
        """Build comprehensive tag library from research data."""
        
        # Core workflow tags (always present)
        self.core_tags = [
            'urgent',
            'blocked',
            'needs-review',
            'in-progress',
            'ready-for-qa',
            'on-hold',
            'waiting',
            'duplicate',
            'wont-fix',
            'help-wanted'
        ]
        
        # Priority tags
        self.priority_tags = [
            'p0', 'p1', 'p2', 'p3', 'p4',
            'critical', 'high-priority', 'low-priority'
        ]
        
        # Type tags
        self.type_tags = [
            'bug',
            'enhancement',
            'feature',
            'documentation',
            'refactor',
            'technical-debt',
            'chore',
            'question',
            'discussion'
        ]
        
        # Customer/business tags
        self.business_tags = [
            'customer-request',
            'internal',
            'external',
            'paid-feature',
            'beta',
            'experiment',
            'quick-win',
            'stretch-goal'
        ]
        
        # Extract department tags
        departments = self._extract_departments()
        self.department_tags = [dept.lower().replace(' ', '-') for dept in departments]
        
        # Extract tech tags from companies
        self.tech_tags = self._extract_tech_tags()
        
        # Combine all (sample subset for realism - not all companies use all tags)
        all_tags = (
            self.core_tags +
            self.priority_tags +
            self.type_tags +
            self.business_tags +
            self.department_tags[:15] +  # Top 15 departments
            list(self.tech_tags)[:20]    # Top 20 tech tags
        )
        
        # Remove duplicates, keep order
        seen = set()
        self.tag_library = []
        for tag in all_tags:
            if tag not in seen:
                seen.add(tag)
                self.tag_library.append(tag)
        
        print(f" Built tag library with {len(self.tag_library)} tags")
        print(f"  - {len(self.core_tags)} core workflow tags")
        print(f"  - {len(self.priority_tags)} priority tags")
        print(f"  - {len(self.type_tags)} type tags")
        print(f"  - {len(self.business_tags)} business tags")
        print(f"  - {len(self.department_tags)} department tags")
        print(f"  - {len(self.tech_tags)} tech tags extracted from companies")
    
    def _get_tag_color(self, tag_name: str) -> str:
        """
        Assign semantic color to tag based on name.
        
        Colors follow common conventions:
            - Red: urgent, critical, blocked, bug
            - Orange: needs-review, high-priority
            - Yellow: warning, in-progress
            - Green: ready, completed, enhancement
            - Blue: feature, documentation
            - Purple: experiment, beta
            - Gray: on-hold, wont-fix
        """
        tag_lower = tag_name.lower()
        
        # Red (urgent/critical)
        if any(word in tag_lower for word in ['urgent', 'critical', 'blocked', 'bug', 'p0']):
            return random.choice(['red', 'dark-red'])
        
        # Orange (attention needed)
        elif any(word in tag_lower for word in ['needs-review', 'high-priority', 'p1', 'waiting']):
            return random.choice(['orange', 'dark-orange'])
        
        # Yellow (in progress)
        elif any(word in tag_lower for word in ['in-progress', 'p2']):
            return random.choice(['yellow', 'light-orange'])
        
        # Green (positive/ready)
        elif any(word in tag_lower for word in ['ready', 'enhancement', 'feature', 'p3', 'p4']):
            return random.choice(['green', 'light-green'])
        
        # Blue (informational)
        elif any(word in tag_lower for word in ['documentation', 'question', 'discussion']):
            return random.choice(['blue', 'light-blue'])
        
        # Purple (experimental)
        elif any(word in tag_lower for word in ['experiment', 'beta', 'research']):
            return random.choice(['purple', 'light-purple'])
        
        # Gray (neutral/inactive)
        elif any(word in tag_lower for word in ['on-hold', 'wont-fix', 'duplicate', 'archived']):
            return random.choice(['gray', 'light-gray'])
        
        # Default: random from common set
        else:
            return random.choice(['blue', 'green', 'purple', 'teal', 'pink', 'brown'])
    
    def _sample_created_at(self, org_created_at: datetime) -> datetime:
        """
        Sample tag creation timestamp.
        Most tags created early in org history (setup phase).
        """
        # Most tags created in first month
        days_since_org = random.randint(0, 30)
        
        created_at = org_created_at + timedelta(days=days_since_org)
        
        # Add random hour
        hour = random.randint(8, 17)
        created_at = created_at.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        return created_at
    
    def generate(self, organization: Dict) -> List[Tag]:
        """
        Generate organization-wide tag library.
        
        Args:
            organization: Organization dict from organizations.py
        
        Returns:
            List of Tag model instances
        """
        org = organization['organization']
        
        print(f"\nGenerating tags for {org.name}...")
        
        tags = []
        
        for tag_name in self.tag_library:
            # Assign color
            color = self._get_tag_color(tag_name)
            
            # Sample creation time
            created_at = self._sample_created_at(org.created_at)
            
            # Create Tag instance
            tag = Tag(
                tag_id=str(uuid.uuid4()),
                organization_id=org.organization_id,
                name=tag_name,
                color=color,
                created_at=created_at
            )
            
            tags.append(tag)
        
        print(f" Generated {len(tags)} tags")
        
        return tags


def generate_tags(organization: Dict, research_dir: str = RESEARCH_DIR) -> List[Tag]:
    """
    Main entry point for tag generation.
    
    Args:
        organization: Organization dict from generate_organization()
        research_dir: Path to research/ directory
    
    Returns:
        List of Tag model instances
    
    Example:
        >>> from generators.organizations import generate_organization
        >>> org = generate_organization()
        >>> tags = generate_tags(org)
    """
    generator = TagGenerator(research_dir)
    tags = generator.generate(organization)
    
    # Log statistics
    print("\n" + "="*70)
    print("TAG GENERATION SUMMARY")
    print("="*70)
    
    # Color breakdown
    color_counts = defaultdict(int)
    for tag in tags:
        color_counts[tag.color] += 1
    
    print("\nTags by Color:")
    for color, count in sorted(color_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(tags)) * 100
        print(f"  {color:15s}: {count:3d} ({pct:5.1f}%)")
    
    # Sample tags
    print("\nSample Tags:")
    for tag in random.sample(tags, min(20, len(tags))):
        print(f"  {tag.name:30s} | {tag.color:15s}")
    
    print("="*70 + "\n")
    
    return tags


# ============================================================================
# Testing / Standalone Execution
# ============================================================================

if __name__ == "__main__":
    """
    Test tag generation.
    Run: python src/generators/tags.py
    """
    
    print("\n" + "="*70)
    print("TESTING TAG GENERATOR")
    print("="*70 + "\n")
    
    try:
        from organizations import generate_organization
        
        org_result = generate_organization(company_size=7000)
        tags = generate_tags(org_result)
        
        # Validate
        print("\n" + "="*70)
        print("VALIDATION")
        print("="*70)
        
        # Check all tags have names
        assert all(t.name for t in tags), "Missing tag names!"
        print(" All tags have names")
        
        # Check unique tag names
        tag_names = [t.name for t in tags]
        assert len(tag_names) == len(set(tag_names)), "Duplicate tag names!"
        print(" All tag names unique")
        
        # Check all have colors
        assert all(t.color for t in tags), "Missing colors!"
        print(" All tags have colors")
        
        # Check timestamps
        for tag in tags:
            assert tag.created_at >= org_result['organization'].created_at
        print(" All timestamps consistent")
        
        # Sample tag
        print("\nSample Tag:")
        sample = random.choice(tags)
        print(json.dumps(sample.to_dict(), indent=2))
        
        print("\n ALL TESTS PASSED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
