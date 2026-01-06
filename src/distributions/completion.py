import random
from typing import Dict


class CompletionDistributions:
    """
    Controls whether tasks get completed, go overdue, get reopened,
    or fail due to overload and scope changes.
    """

    def __init__(self, benchmarks: Dict):
        self.benchmarks = benchmarks

        self.overall_completion = benchmarks["task_completion"]["overall_rate"]
        self.priority_rates = benchmarks["task_completion"]["by_priority"]
        self.overdue_rate = benchmarks["task_completion"]["overdue_rate"]

        self.on_time_rate = benchmarks["project_success"]["on_time_completion"]
        self.scope_change_rate = benchmarks["project_success"]["scope_change_rate"]

    # ----------------------------
    # Base completion probability
    # ----------------------------
    def base_completion_prob(self, priority: str) -> float:
        """
        Completion chance ignoring overload or delays.
        """
        return self.priority_rates.get(priority, self.overall_completion)

    # ----------------------------
    # Overdue probability
    # ----------------------------
    def is_overdue(self) -> bool:
        """
        Whether a task misses its due date.
        """
        return random.random() < self.overdue_rate

    # ----------------------------
    # Final completion
    # ----------------------------
    def will_complete(self, priority: str, overloaded: bool, overdue: bool) -> bool:
        """
        Whether a task ends up completed.
        """
        p = self.base_completion_prob(priority)

        # Overdue tasks are less likely to finish
        if overdue:
            p *= 0.6

        # Overloaded users drop more tasks
        if overloaded:
            p *= 0.7

        return random.random() < p

    # ----------------------------
    # Scope change & reopen
    # ----------------------------
    def has_scope_change(self) -> bool:
        """
        Whether a task or project changes after starting.
        """
        return random.random() < self.scope_change_rate

    def should_reopen(self) -> bool:
        """
        Whether a completed task gets reopened.
        """
        # Only a subset of scope changes cause reopen
        return random.random() < (self.scope_change_rate * 0.4)

    # ----------------------------
    # Project on-time completion
    # ----------------------------
    def project_on_time(self) -> bool:
        """
        Whether a project finishes on time.
        """
        return random.random() < self.on_time_rate
