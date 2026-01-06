import json
import random
from datetime import datetime, timezone, timedelta
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

with open(RESEARCH_DIR+"/benchmarks.json") as f:
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
now = datetime.now(timezone.utc)  #  Fixed deprecation warning

stats = defaultdict(int)
durations = []
overdue_count = 0
completed_count = 0

for _ in range(N_TASKS):
    # Sample task creation time (random date in past 90 days)
    days_ago = random.randint(0, 90)
    task_created = now - timedelta(days=days_ago)
    
    # Sample task duration
    task_duration_days = time_dist.sample_task_duration()
    
    # Sample due date
    due_date = due_date_dist.compute_due_date(task_created)
    
    # Calculate actual duration
    duration = (due_date - task_created).days
    durations.append(duration)
    
    # Sample completion (using medium priority as default)
    priority = random.choice(['high', 'medium', 'low'])
    overloaded = random.random() < 0.3  # 30% overloaded
    is_overdue = due_date_dist.is_overdue()
    
    if completion_dist.will_complete(priority, overloaded, is_overdue):
        completed_count += 1
        stats["completed"] += 1
    
    if is_overdue:
        overdue_count += 1
        stats["overdue"] += 1

# -------------------------
# Compare against real world
# -------------------------

completion_rate = completed_count / N_TASKS
overdue_rate = overdue_count / N_TASKS
avg_duration = sum(durations) / len(durations)

print("\n=== DISTRIBUTION VALIDATION REPORT ===\n")

print("Task completion rate:")
print(f"  Expected: {BENCHMARKS['task_completion']['overall_rate']}")
print(f"  Observed: {round(completion_rate, 3)}")
diff = abs(completion_rate - BENCHMARKS['task_completion']['overall_rate'])
print(f"  Difference: {round(diff, 3)} ({' PASS' if diff < 0.05 else ' FAIL'})\n")

print("Overdue rate:")
print(f"  Expected: {BENCHMARKS['task_completion']['overdue_rate']}")
print(f"  Observed: {round(overdue_rate, 3)}")
diff = abs(overdue_rate - BENCHMARKS['task_completion']['overdue_rate'])
print(f"  Difference: {round(diff, 3)} ({' PASS' if diff < 0.05 else ' FAIL'})\n")

print("Avg task duration (days):")
print(f"  Expected: {BENCHMARKS['time_metrics']['avg_task_duration_days']}")
print(f"  Observed: {round(avg_duration, 2)}")
diff = abs(avg_duration - BENCHMARKS['time_metrics']['avg_task_duration_days'])
print(f"  Difference: {round(diff, 2)} days ({' PASS' if diff < 2 else ' FAIL'})\n")

# Additional stats
print("Additional statistics:")
print(f"  High priority completion: {stats.get('high_completed', 0)}")
print(f"  Medium priority completion: {stats.get('medium_completed', 0)}")
print(f"  Low priority completion: {stats.get('low_completed', 0)}")
