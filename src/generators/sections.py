import json
import random
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.section import Section


class SectionGenerator:
    """
    Generates sections for each project based on project type.
    
    Strategy:
    - Different section patterns per project type
    - Sprint projects: Backlog, In Progress, Review, Done
    - Ongoing projects: To Do, In Progress, Done
    - Bug tracking: New, Triaged, In Progress, Fixed, Closed
    """
    
    def __init__(self, research_dir: str = "../../research"):
        self.research_dir = Path(research_dir)
        self._define_section_templates()
    
    def _define_section_templates(self):
        """Define section patterns for different project types."""
        self.section_templates = {
            'sprint': [
                "Backlog",
                "In Progress",
                "Review",
                "Done"
            ],
            'ongoing': [
                "To Do",
                "In Progress",
                "Done"
            ],
            'bug_tracking': [
                "New",
                "Triaged",
                "In Progress",
                "Fixed",
                "Closed"
            ],
            'campaign': [
                "Planning",
                "Creative",
                "Execution",
                "Analysis"
            ],
            'roadmap': [
                "Now",
                "Next",
                "Later",
                "Parking Lot"
            ],
            'default': [
                "To Do",
                "In Progress",
                "Done"
            ]
        }
        
        print(f" Loaded {len(self.section_templates)} section templates")
    
    def _get_sections_for_project(self, project_type: str) -> List[str]:
        """Get section names for a project type."""
        return self.section_templates.get(project_type, self.section_templates['default'])
    
    def _sample_created_at(self, project_created_at: datetime) -> datetime:
        """
        Sample section creation timestamp.
        Sections created same day or shortly after project creation.
        """
        now = datetime.utcnow()
        
        # Created 0-2 days after project
        days_after = random.randint(0, 2)
        created_at = project_created_at + timedelta(days=days_after)
        
        # Ensure not in future
        if created_at > now:
            created_at = project_created_at
        
        # Add random hour (business hours)
        hour = random.randint(8, 17)
        created_at = created_at.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        # ABSOLUTE FINAL CONSTRAINT: Ensure created_at >= project_created_at
        if created_at < project_created_at:
            created_at = project_created_at
        
        # ABSOLUTE FINAL CONSTRAINT: Ensure not in future
        if created_at > now:
            created_at = now - timedelta(hours=random.randint(1, 24))
        
        return created_at

    def generate(self, projects: List) -> List[Section]:
        """
        Generate sections for all projects.
        
        Args:
            projects: List of Project objects from projects.py
        
        Returns:
            List of Section model instances
        """
        print(f"\nGenerating sections for {len(projects):,} projects...")
        
        sections = []
        sections_per_project = defaultdict(int)
        
        for project in projects:
            # Get section names for this project type
            section_names = self._get_sections_for_project(project.project_type)
            
            # Create sections with sequential positions
            for position, section_name in enumerate(section_names):
                # Sample creation time
                created_at = self._sample_created_at(project.created_at)
                
                # Create Section instance
                section = Section(
                    section_id=str(uuid.uuid4()),
                    project_id=project.project_id,
                    name=section_name,
                    position=position,
                    created_at=created_at
                )
                
                sections.append(section)
                sections_per_project[project.project_id] += 1
        
        avg_sections = sum(sections_per_project.values()) / len(sections_per_project)
        
        print(f" Generated {len(sections):,} sections")
        print(f"  - Avg {avg_sections:.1f} sections per project")
        
        return sections


def generate_sections(projects: List, research_dir: str = "../../research") -> List[Section]:
    """
    Main entry point for section generation.
    
    Args:
        projects: List of Project objects from generate_projects()
        research_dir: Path to research/ directory
    
    Returns:
        List of Section model instances
    """
    generator = SectionGenerator(research_dir)
    sections = generator.generate(projects)
    
    # Log statistics
    print("\n" + "="*70)
    print("SECTION GENERATION SUMMARY")
    print("="*70)
    
    # Section name frequency
    name_counts = defaultdict(int)
    for section in sections:
        name_counts[section.name] += 1
    
    print("\nMost Common Section Names:")
    for name, count in sorted(name_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
        pct = (count / len(sections)) * 100
        print(f"  {name:20s}: {count:4d} ({pct:5.1f}%)")
    
    # Sections per project distribution
    sections_per_project = defaultdict(int)
    for section in sections:
        sections_per_project[section.project_id] += 1
    
    section_count_dist = defaultdict(int)
    for project_id, count in sections_per_project.items():
        section_count_dist[count] += 1
    
    print("\nSections per Project Distribution:")
    for num_sections in sorted(section_count_dist.keys()):
        count = section_count_dist[num_sections]
        pct = (count / len(sections_per_project)) * 100
        print(f"  {num_sections} sections: {count:4d} projects ({pct:5.1f}%)")
    
    print("="*70 + "\n")
    
    return sections


# ============================================================================
# Testing / Standalone Execution
# ============================================================================

if __name__ == "__main__":
    """
    Test section generation.
    Run: python src/generators/sections.py
    """
    
    print("\n" + "="*70)
    print("TESTING SECTION GENERATOR")
    print("="*70 + "\n")
    
    try:
        from organizations import generate_organization
        from users import generate_users
        from teams import generate_teams
        from projects import generate_projects
        
        org_result = generate_organization(company_size=7000)
        users = generate_users(org_result, target_count=500)
        teams = generate_teams(org_result, users)
        projects = generate_projects(org_result, teams, users)
        sections = generate_sections(projects)
        
        # Validate
        print("\n" + "="*70)
        print("VALIDATION")
        print("="*70)
        
        # Check all sections have names
        assert all(s.name for s in sections), "Missing section names!"
        print(" All sections have names")
        
        # Check positions are sequential per project
        sections_by_project = defaultdict(list)
        for section in sections:
            sections_by_project[section.project_id].append(section)
        
        for project_id, project_sections in sections_by_project.items():
            positions = sorted([s.position for s in project_sections])
            expected = list(range(len(project_sections)))
            assert positions == expected, f"Non-sequential positions for project {project_id}"
        print(" All section positions sequential")
        
        # Check timestamps
        project_dict = {p.project_id: p for p in projects}
        for section in sections:
            project = project_dict[section.project_id]
            assert section.created_at >= project.created_at
        print(" All timestamps consistent")
        
        # Sample section
        print("\nSample Section:")
        sample = random.choice(sections)
        print(json.dumps(sample.to_dict(), indent=2))
        
        print("\n ALL TESTS PASSED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
