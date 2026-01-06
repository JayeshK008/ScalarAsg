import json
import random
from datetime import datetime
from collections import defaultdict
import sys
import os

# Adds the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from distributions.time import TimeDistributions
from distributions.workload import WorkloadDistributions
from distributions.completion import CompletionDistributions
from distributions.due_dates import DueDateDistributions
from config import RESEARCH_DIR

# -------------------------
# Load benchmarks from research/
# -------------------------

with open(RESEARCH_DIR/"/benchmarks.json") as f:
    BENCHMARKS = json.load(f)

# -------------------------
# Initialize distributions
# -------------------------

time_dist = TimeDistributions(BENCHMARKS)
workload_dist = WorkloadDistributions(BENCHMARKS)
completion_dist = CompletionDistributions(BENCHMARKS)
due_date_dist = DueDateDistributions(BENCHMARKS)

# -------------------------
# Run simulation
# -------------------------

N_TASKS = 50_000
now = datetime.utcnow()

stats = defaultdict(int)
durations = []
overdue = 0

for _ in range(N_TASKS):
    start = time_dist.sample_task_start(now)
    due = due_date_dist.compute_due_date(start)

    duration = (due - start).days
    durations.append(duration)

    completed, was_overdue = completion_dist.sample_completion(due, now)

    if completed:
        stats["completed"] += 1
    if was_overdue:
        overdue += 1


# -------------------------
# Compare against real world
# -------------------------

completion_rate = stats["completed"] / N_TASKS
overdue_rate = overdue / N_TASKS
avg_duration = sum(durations) / len(durations)

print("\n=== DISTRIBUTION VALIDATION REPORT ===\n")

print("Task completion:")
print("  Expected:", BENCHMARKS["task_completion"]["overall_rate"])
print("  Observed:", round(completion_rate, 3), "\n")

print("Overdue rate:")
print("  Expected:", BENCHMARKS["task_completion"]["overdue_rate"])
print("  Observed:", round(overdue_rate, 3), "\n")
