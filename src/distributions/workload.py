import random
from typing import Dict


class WorkloadDistributions:
    """
    Controls how work is distributed across users and teams.
    Models:
    - How many tasks people get
    - How many they can finish
    - When tasks get reassigned
    - When overload happens
    """

    def __init__(self, benchmarks: Dict):
        self.benchmarks = benchmarks

        self.tasks_created_range = benchmarks["workload"]["tasks_created_per_employee_per_week_range"]
        self.tasks_completed_range = benchmarks["workload"]["tasks_completed_per_employee_per_week_range"]
        self.assignee_change_rate = benchmarks["workload"]["assignee_change_rate_range"]

        self.team_size_range = benchmarks["team_structure"]["avg_team_size_range"]

    # ----------------------------
    # Task creation
    # ----------------------------
    def sample_tasks_created(self) -> int:
        """
        How many new tasks a user receives this week.
        """
        low, high = self.tasks_created_range
        return random.randint(low, high)

    # ----------------------------
    # Task completion capacity
    # ----------------------------
    def sample_tasks_completed_capacity(self) -> int:
        """
        How many tasks a user is realistically able to complete this week.
        """
        low, high = self.tasks_completed_range

        # Use triangular distribution: most users are around the middle
        mode = (low + high) // 2
        return int(random.triangular(low, high, mode))

    # ----------------------------
    # Overload probability
    # ----------------------------
    def overload_ratio(self, created: int, capacity: int) -> float:
        """
        How overloaded a user is.
        >1.0 means tasks exceed capacity.
        """
        return created / max(1, capacity)

    def is_overloaded(self, created: int, capacity: int) -> bool:
        """
        Whether a user is overloaded enough to cause delays or reassignment.
        """
        ratio = self.overload_ratio(created, capacity)

        # Soft threshold: overloaded users don't instantly break
        return ratio > random.uniform(1.0, 1.5)

    # ----------------------------
    # Task reassignment
    # ----------------------------
    def should_reassign_task(self, overloaded: bool) -> bool:
        """
        Determines whether a task gets reassigned due to overload or churn.
        """
        low, high = self.assignee_change_rate
        base_prob = random.uniform(low, high)

        # Overloaded users are more likely to have tasks reassigned
        if overloaded:
            base_prob *= 1.5

        return random.random() < min(base_prob, 0.9)

    # ----------------------------
    # Team size
    # ----------------------------
    def sample_team_size(self) -> int:
        """
        Samples realistic team sizes.
        """
        low, high = self.team_size_range
        return random.randint(low, high)
