import json
import random
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict
from config import RESEARCH_DIR

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.organization import Organization


class OrganizationGenerator:
    """
    Generates a single organization entity.
    Represents a 5,000-10,000 employee B2B SaaS company.
    """
    
    def __init__(self, research_dir: str = RESEARCH_DIR):
        self.research_dir = Path(research_dir)
        self._load_companies()
    
    def _load_companies(self):
        """Load scraped company data from research."""
        companies_path = self.research_dir / "companies.json"
        
        if not companies_path.exists():
            raise FileNotFoundError(
                f"companies.json not found at {companies_path}. "
                "Run the scraper first to populate research/ directory."
            )
        
        with open(companies_path, 'r') as f:
            self.companies = json.load(f)
        
        # Filter for companies in target size range (5,000-10,000 employees)
        # If none in exact range, pick larger companies we can scale down
        self.target_companies = [
            c for c in self.companies 
            if 3000 <= c.get('team_size', 0) <= 15000
        ]
        
        if not self.target_companies:
            # Fallback: use any companies with team_size data
            self.target_companies = [
                c for c in self.companies 
                if c.get('team_size', 0) > 1000
            ]
        
        print(f"Loaded {len(self.companies)} companies from research/")
        print(f"  → {len(self.target_companies)} in target size range")
    
    def _generate_domain(self, company_name: str) -> str:
        """
        Generate email domain from company name.
        
        Examples:
            "Asana" → "asana.com"
            "Notion Labs" → "notion.so"
            "Atlassian" → "atlassian.com"
        """
        # Clean company name
        name = company_name.lower()
        
        # Remove common suffixes
        for suffix in [' inc', ' inc.', ' corp', ' corporation', ' llc', ' ltd', ' limited']:
            name = name.replace(suffix, '')
        
        # Remove special characters, keep only alphanumeric
        name = ''.join(c for c in name if c.isalnum() or c == ' ')
        
        # Take first word or join first two words
        words = name.split()
        if len(words) == 1:
            domain_name = words[0]
        else:
            # Common patterns: "notion.so", "asana.com", "atlassian.com"
            domain_name = words[0]
        
        # Common TLDs for B2B SaaS
        tlds = ['com', 'io', 'so', 'app', 'co']
        weights = [0.70, 0.15, 0.05, 0.05, 0.05]  # .com is most common
        
        tld = random.choices(tlds, weights=weights)[0]
        
        return f"{domain_name}.{tld}"
    
    def _generate_org_id(self) -> str:
        """
        Generate organization ID in Asana's GID format.
        Asana uses numeric GIDs, but we'll use UUIDs for simplicity.
        """
        return str(uuid.uuid4())
    
    def _get_base_timestamp(self) -> datetime:
        """
        Get organization creation timestamp.
        Set to 6 months ago - this becomes the "base" for all other timestamps.
        Everything in the simulation happens after this date.
        """
        now = datetime.utcnow()
        six_months_ago = now - timedelta(days=180)
        
        # Set to start of business day (8 AM UTC)
        base_time = six_months_ago.replace(hour=8, minute=0, second=0, microsecond=0)
        
        return base_time
    
    def generate(self, company_size: int = None) -> Dict:
        """
        Generate a single organization.
        
        Args:
            company_size: Target employee count (5,000-10,000).
                         If None, randomly sampled from range.
        
        Returns:
            Dict with:
                - organization: Organization model instance
                - metadata: Additional context (target_size, founding_date, etc.)
        """
        # Sample target company size if not provided
        if company_size is None:
            company_size = random.randint(5000, 10000)
        
        # Select a company from scraped data
        # Prefer companies closer to target size
        if self.target_companies:
            company_data = random.choice(self.target_companies)
        else:
            raise ValueError(
                "No suitable companies found in research/companies.json. "
                "Ensure scraper collected B2B SaaS companies with team_size data."
            )
        
        company_name = company_data['name']
        domain = self._generate_domain(company_name)
        org_id = self._generate_org_id()
        created_at = self._get_base_timestamp()
        
        # Create Organization model instance
        organization = Organization(
            organization_id=org_id,
            name=company_name,
            domain=domain,
            is_organization=True,
            created_at=created_at
        )
        
        # Metadata for downstream generators
        metadata = {
            'target_employee_count': company_size,
            'actual_scraped_size': company_data.get('team_size'),
            'industry': company_data.get('industry'),
            'subindustry': company_data.get('subindustry'),
            'description': company_data.get('description'),
            'tags': company_data.get('tags', []),
            'founded_year': company_data.get('founded_year'),
            'website': company_data.get('website'),
            'simulation_start_date': created_at,
            'simulation_end_date': datetime.utcnow()
        }
        
        return {
            'organization': organization,
            'metadata': metadata
        }


def generate_organization(company_size: int = None, research_dir: str = RESEARCH_DIR) -> Dict:
    """
    Main entry point for organization generation.
    
    Args:
        company_size: Target employee count (5,000-10,000)
        research_dir: Path to research/ directory
    
    Returns:
        Dict with organization and metadata
    
    Example:
        >>> result = generate_organization(company_size=7000)
        >>> org = result['organization']
        >>> print(org.name, org.domain)
        Asana asana.com
    """
    generator = OrganizationGenerator(research_dir)
    result = generator.generate(company_size)
    
    # Log generation
    org = result['organization']
    meta = result['metadata']
    
    print("\n" + "="*70)
    print("ORGANIZATION GENERATED")
    print("="*70)
    print(f"Name:              {org.name}")
    print(f"Domain:            {org.domain}")
    print(f"Organization ID:   {org.organization_id}")
    print(f"Created At:        {org.created_at}")
    print(f"Target Employees:  {meta['target_employee_count']:,}")
    print(f"Industry:          {meta['industry']}")
    print(f"Subindustry:       {meta['subindustry']}")
    print(f"Simulation Period: {meta['simulation_start_date'].date()} to {meta['simulation_end_date'].date()}")
    print("="*70 + "\n")
    
    return result


# ============================================================================
# Testing / Standalone Execution
# ============================================================================

if __name__ == "__main__":
    """
    Test organization generation.
    Run: python src/generators/organizations.py
    """
    
    print("\n" + "="*70)
    print("TESTING ORGANIZATION GENERATOR")
    print("="*70 + "\n")
    
    try:
        # Generate organization
        result = generate_organization(company_size=7000)
        
        # Validate
        org = result['organization']
        org_dict = org.to_dict()
        
        print(" Organization model created")
        print(" to_dict() conversion works")
        
        print("\nGenerated organization dict:")
        print(json.dumps(org_dict, indent=2))
        
        print("\n ALL TESTS PASSED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
