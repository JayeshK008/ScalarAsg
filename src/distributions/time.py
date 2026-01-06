import random
from datetime import timedelta
from typing import Dict


class TimeDistributions:
    """
    Controls all time-related stochastic behavior:
    - Sprint lengths
    - Project durations
    - Task durations
    - Time gaps between events

    All values are sampled from benchmarks.json distributions.
    """

    def __init__(self, benchmarks: Dict):
        self.benchmarks = benchmarks
        self.sprint_dist = benchmarks["sprint_dynamics"]["sprint_length_days_distribution"]
        self.project_ranges = benchmarks["time_metrics"]["project_duration_days_range"]
        self.task_duration_range = benchmarks["time_metrics"]["avg_task_duration_days_range"]

    # ----------------------------
    # Sprint length
    # ----------------------------
    def sample_sprint_length(self) -> int:
        """
        Samples a sprint length based on real-world Scrum distributions.
        Returns length in days.
        """
        choices = []
        weights = []

        for k, v in self.sprint_dist.items():
            if k.endswith("_days"):
                days = int(k.replace("_days", ""))
            else:
                continue
            choices.append(days)
            weights.append(v)

        return random.choices(choices, weights=weights, k=1)[0]

    # ----------------------------
    # Project duration
    # ----------------------------
    def sample_project_duration(self, project_type: str) -> int:
        """
        Samples project duration based on project category.
        """
        project_type = project_type.lower()

        if project_type in ["sprint", "engineering"]:
            low, high = self.project_ranges["short_projects"]
        elif project_type in ["campaign", "marketing"]:
            low, high = self.project_ranges["medium_projects"]
        elif project_type in ["infrastructure", "platform"]:
            low, high = self.project_ranges["long_projects"]
        else:
            low, high = self.project_ranges["medium_projects"]

        return int(random.uniform(low, high))

    # ----------------------------
    # Task duration
    # ----------------------------
    def sample_task_duration(self) -> int:
        """
        Samples how long a task takes to complete.
        Uses a skewed distribution (most tasks are short, some are long).
        """
        low, high = self.task_duration_range

        # Beta distribution skews toward shorter tasks
        alpha = 2
        beta = 5

        frac = random.betavariate(alpha, beta)
        return max(1, int(low + frac * (high - low)))

    # ----------------------------
    # Task scheduling inside projects
    # ----------------------------
    def sample_task_start_offset(self, project_duration: int) -> int:
        """
        When during a project a task is scheduled to start.
        Earlier tasks more likely than late tasks.
        """
        # Bias toward earlier part of project
        alpha = 2
        beta = 4
        frac = random.betavariate(alpha, beta)

        return int(frac * project_duration)

    # ----------------------------
    # Deadline slack
    # ----------------------------
    def sample_deadline_slack(self) -> int:
        """
        How much buffer time is added to a due date.
        Models real-world padding and uncertainty.
        """
        # Most tasks have small slack, some have big buffers
        return int(random.expovariate(1 / 2))  # mean ~2 days

    # ----------------------------
    # Utility
    # ----------------------------
    def add_days(self, dt, days: int):
        return dt + timedelta(days=days)
