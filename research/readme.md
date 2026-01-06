# Research Basis for Simulation Parameters

This document explains how the values in `benchmarks.json` and `project_templates.json` were derived.  
The goal is not perfect precision, but to ensure all distributions are constrained by real organizational behavior.

## work_about_work_pct_range: [0.50, 0.60]
Source: Asana Anatomy of Work Index (2022–2024) reports ~58% of time spent on coordination.  
We model this as [0.50, 0.60] to allow org variance.

## strategic_work_pct_range: [0.10, 0.25]
Asana shows strategic work is ~10–20% of total time after removing coordination.  
So we use a bounded range.

## tasks_completed_per_employee_per_week: [3, 6]
Asana, RescueTime, and ClickUp show only a few meaningful tasks complete weekly.

## overdue_rate_range: [0.15, 0.30]
From Asana and Jira sprint spillover statistics.

## Sprint distribution
Parabol 2024 and Scrum.org surveys:
2 weeks ~60%, 3 weeks ~23%, 4 weeks ~10%, 1 week ~6%.

## avg_team_size_range: [6, 12]
From Scrum Guide, Spotify model, and Atlassian.

## Project durations
From Asana templates, Jira workflows, and SaaS playbooks.

## Completion by priority
High > Medium > Low completion follows Agile and issue-tracker data.

## Reopen & abandonment
From GitHub and Jira: 5–15% reopen, 10–30% dropped.
