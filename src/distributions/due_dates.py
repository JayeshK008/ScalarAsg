import random
from datetime import timedelta


class DueDateDistributions:
    """
    Controls how aggressive or realistic deadlines are.
    Models:
    - How long tasks are supposed to take
    - How often deadlines are too short
    - How overdue happens
    """

    def __init__(self, benchmarks):
        self.benchmarks = benchmarks

        self.avg_task_days = benchmarks["time_metrics"]["avg_task_duration_days"]
        self.sprint_length = benchmarks["time_metrics"]["sprint_duration"]
        self.project_median = benchmarks["time_metrics"]["project_duration_median"]

        self.overdue_rate = benchmarks["task_completion"]["overdue_rate"]

    # ----------------------------
    # Task duration targets
    # ----------------------------
    def sample_task_duration_days(self) -> int:
        """
        How long a task is expected to take.
        Most tasks are near average, some are much longer.
        """
        return max(
            1,
            int(random.lognormvariate(mu=1.2, sigma=0.6) * (self.avg_task_days / 4))
        )

    # ----------------------------
    # Due date generation
    # ----------------------------
    def compute_due_date(self, start_date):
        """
        Assigns a due date based on task difficulty and deadline pressure.
        """
        expected = self.sample_task_duration_days()

        # Some deadlines are too aggressive
        if random.random() < self.overdue_rate:
            expected *= random.uniform(0.4, 0.7)   # unrealistic deadline
        else:
            expected *= random.uniform(0.9, 1.3)

        return start_date + timedelta(days=max(1, int(expected)))

    # ----------------------------
    # Sprint deadlines
    # ----------------------------
    def sprint_due_date(self, sprint_start):
        """
        End of sprint deadline.
        """
        return sprint_start + timedelta(days=self.sprint_length)

    # ----------------------------
    # Project deadlines
    # ----------------------------
    def project_due_date(self, project_start):
        """
        When the project is supposed to finish.
        """
        jitter = random.uniform(0.7, 1.5)
        return project_start + timedelta(days=int(self.project_median * jitter))
    
    def is_overdue(self) -> bool:
        """
        Whether a task misses its due date.
        Uses the overdue_rate from benchmarks.
        """
        return random.random() < self.overdue_rate