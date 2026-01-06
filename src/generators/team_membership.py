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

from models.team_membership import TeamMembership


class TeamMembershipGenerator:
    """
    Generates team membership assignments.
    
    Strategy:
    - Users assigned to teams matching their department
    - Most users on 1-2 teams (realistic workload)
    - 1 team admin per team (first assigned member)
    - Rest are regular members
    - Uses benchmarks for team sizing
    """
    
    def __init__(self, research_dir: str = "../../research"):
        self.research_dir = Path(research_dir)
        self._load_benchmarks()
    
    def _load_benchmarks(self):
        """Load team size benchmarks."""
        benchmarks_path = self.research_dir / "benchmarks.json"
        with open(benchmarks_path, 'r') as f:
            benchmarks = json.load(f)
        
        team_structure = benchmarks.get('team_structure', {})
        self.avg_team_size_range = team_structure.get('avg_team_size_range', [6, 12])
        
        print(f" Team size range: {self.avg_team_size_range}")
    
    def _sample_team_size(self) -> int:
        """
        Sample realistic team size.
        Most teams have 7-9 people.
        """
        size = int(random.triangular(
            self.avg_team_size_range[0],  # min: 6
            self.avg_team_size_range[1],  # max: 12
            8.5  # mode: 8-9 people
        ))
        
        return size
    
    def _sample_teams_per_user(self) -> int:
        """
        Sample how many teams a user is on.
        
        Distribution:
            - 60% on 1 team
            - 30% on 2 teams
            - 8% on 3 teams
            - 2% on 4+ teams (cross-functional leads)
        """
        return random.choices(
            [1, 2, 3, 4],
            weights=[0.60, 0.30, 0.08, 0.02]
        )[0]
    
    def _sample_joined_at(self, user_created_at: datetime, team_created_at: datetime) -> datetime:
        """
        Sample when user joined team.
        Must be after both user and team creation.
        """
        # Start from latest of user/team creation
        earliest = max(user_created_at, team_created_at)
        
        # Ensure earliest is not in the future
        now = datetime.utcnow()
        if earliest > now:
            earliest = now - timedelta(days=1)
        
        # Calculate max possible delay (can't go past now)
        max_days_until_now = (now - earliest).days
        
        # User joins team within 0-30 days, but not past now
        days_delay = random.randint(0, min(30, max_days_until_now))
        
        joined_at = earliest + timedelta(days=days_delay)
        
        # Add random hour (business hours)
        hour = random.randint(8, 17)
        joined_at = joined_at.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        # Final safety check: ensure within bounds
        if joined_at < earliest:
            joined_at = earliest
        if joined_at > now:
            joined_at = now
        
        return joined_at

    def generate(self, teams: List, users: List) -> List[TeamMembership]:
        """
        Generate team membership assignments.
        
        Args:
            teams: List of Team objects from teams.py
            users: List of User objects from users.py
        
        Returns:
            List of TeamMembership model instances
        """
        print(f"\nGenerating team memberships for {len(teams)} teams and {len(users):,} users...")
        
        # Group users by department
        users_by_dept = defaultdict(list)
        for user in users:
            users_by_dept[user.department].append(user)
        
        # Track which users are already assigned to which teams
        user_team_assignments = defaultdict(set)  # user_id -> set of team_ids
        team_member_counts = defaultdict(int)  # team_id -> current member count
        
        memberships = []
        
        # Phase 1: Assign users to teams matching their department
        for team in teams:
            target_size = self._sample_team_size()
            
            # Get users from matching department
            matching_users = users_by_dept.get(team.team_type, [])
            
            if not matching_users:
                # Fallback: use any users if no matching department
                matching_users = users
            
            # Filter out users already on 4+ teams
            available_users = [
                u for u in matching_users
                if len(user_team_assignments[u.user_id]) < 4
            ]
            
            if not available_users:
                # If all users maxed out, use any available
                available_users = matching_users
            
            # Sample users for this team
            num_to_assign = min(target_size, len(available_users))
            
            # Prioritize users with fewer team assignments
            available_users.sort(key=lambda u: len(user_team_assignments[u.user_id]))
            
            selected_users = available_users[:num_to_assign]
            
            # First member is admin, rest are members
            for i, user in enumerate(selected_users):
                role = 'admin' if i == 0 else 'member'
                
                # Sample joined date
                joined_at = self._sample_joined_at(user.created_at, team.created_at)
                
                # Create membership
                membership = TeamMembership(
                    membership_id=str(uuid.uuid4()),
                    team_id=team.team_id,
                    user_id=user.user_id,
                    role=role,
                    joined_at=joined_at
                )
                
                memberships.append(membership)
                user_team_assignments[user.user_id].add(team.team_id)
                team_member_counts[team.team_id] += 1
        
        print(f" Generated {len(memberships):,} team memberships")
        
        # Statistics
        users_with_teams = len([u for u in users if user_team_assignments[u.user_id]])
        avg_teams_per_user = sum(len(teams) for teams in user_team_assignments.values()) / max(1, len(user_team_assignments))
        avg_members_per_team = sum(team_member_counts.values()) / max(1, len(team_member_counts))
        
        print(f"  - {users_with_teams:,} / {len(users):,} users assigned to teams ({users_with_teams/len(users)*100:.1f}%)")
        print(f"  - Avg {avg_teams_per_user:.2f} teams per user")
        print(f"  - Avg {avg_members_per_team:.1f} members per team")
        
        return memberships


def generate_team_memberships(teams: List, users: List, 
                              research_dir: str = "../../research") -> List[TeamMembership]:
    """
    Main entry point for team membership generation.
    
    Args:
        teams: List of Team objects from generate_teams()
        users: List of User objects from generate_users()
        research_dir: Path to research/ directory
    
    Returns:
        List of TeamMembership model instances
    
    Example:
        >>> from generators.organizations import generate_organization
        >>> from generators.users import generate_users
        >>> from generators.teams import generate_teams
        >>> org = generate_organization()
        >>> users = generate_users(org, target_count=7000)
        >>> teams = generate_teams(org, users)
        >>> memberships = generate_team_memberships(teams, users)
    """
    generator = TeamMembershipGenerator(research_dir)
    memberships = generator.generate(teams, users)
    
    # Log statistics
    print("\n" + "="*70)
    print("TEAM MEMBERSHIP SUMMARY")
    print("="*70)
    
    # Role breakdown
    role_counts = defaultdict(int)
    for membership in memberships:
        role_counts[membership.role] += 1
    
    print("\nMembership Roles:")
    for role, count in sorted(role_counts.items()):
        pct = (count / len(memberships)) * 100
        print(f"  {role:10s}: {count:6,} ({pct:5.1f}%)")
    
    # Teams per user distribution
    user_team_counts = defaultdict(int)
    for membership in memberships:
        user_team_counts[membership.user_id] += 1
    
    teams_per_user_dist = defaultdict(int)
    for user_id, count in user_team_counts.items():
        teams_per_user_dist[count] += 1
    
    print("\nTeams per User Distribution:")
    for num_teams in sorted(teams_per_user_dist.keys()):
        count = teams_per_user_dist[num_teams]
        pct = (count / len(user_team_counts)) * 100
        print(f"  {num_teams} team(s): {count:5,} users ({pct:5.1f}%)")
    
    print("="*70 + "\n")
    
    return memberships


# ============================================================================
# Testing / Standalone Execution
# ============================================================================

if __name__ == "__main__":
    """
    Test team membership generation.
    Run: python src/generators/team_memberships.py
    """
    
    print("\n" + "="*70)
    print("TESTING TEAM MEMBERSHIP GENERATOR")
    print("="*70 + "\n")
    
    try:
        from organizations import generate_organization
        from users import generate_users
        from teams import generate_teams
        
        org_result = generate_organization(company_size=7000)
        users = generate_users(org_result, target_count=500)
        teams = generate_teams(org_result, users)
        memberships = generate_team_memberships(teams, users)
        
        # Validate
        print("\n" + "="*70)
        print("VALIDATION")
        print("="*70)
        
        # Check no duplicate memberships (same user + team)
        membership_pairs = [(m.user_id, m.team_id) for m in memberships]
        assert len(membership_pairs) == len(set(membership_pairs)), "Duplicate memberships!"
        print(" No duplicate user-team pairs")
        
        # Check timestamps logical
        for membership in memberships:
            # Find user and team
            user = next(u for u in users if u.user_id == membership.user_id)
            team = next(t for t in teams if t.team_id == membership.team_id)
            
            assert membership.joined_at >= user.created_at
            assert membership.joined_at >= team.created_at
        print(" All timestamps consistent")
        
        # Check each team has at least one admin
        teams_with_admin = set()
        for membership in memberships:
            if membership.role == 'admin':
                teams_with_admin.add(membership.team_id)
        
        print(f" {len(teams_with_admin)} / {len(teams)} teams have admins")
        
        # Sample membership
        print("\nSample Membership:")
        sample = random.choice(memberships)
        print(json.dumps(sample.to_dict(), indent=2))
        
        print("\n ALL TESTS PASSED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
