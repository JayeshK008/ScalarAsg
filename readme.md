# Asana RL Simulator

This repository generates a realistic synthetic Asana-like workspace for a 5,000–10,000 employee B2B SaaS company. The goal is to create a research-grade environment for training and evaluating reinforcement-learning agents that interact with UI-based task management systems.

The codebase is organized for **reproducibility**, **config-driven runs**, and **clear separation** between research data collection, probability distributions, and synthetic data generation.

---

## Repository Structure

```text
asana-rl-simulator/
│
├── README.md
├── requirements.txt
├── schema.sql              # SQLite DDL for all tables
├── config.yaml             # Main generation config (company size, ranges, dates, etc.)
│
├── research/               # Real-world & derived research data (JSON)
│   ├── companies.json
│   ├── names.json
│   ├── job_titles.json
│   ├── task_patterns.json
│   ├── project_templates.json   # Manually derived (see research/README)
│   └── benchmarks.json          # Manually derived (see research/README)
│
├── src/
│   ├── main.py             # Orchestrates the full generation pipeline
│   ├── config.py           # Path configuration (PROJECT_ROOT, RESEARCH_DIR, DATA_DIR)
│   ├── database.py         # SQLite wrapper + schema loader + helpers
│   │
│   ├── scrapers/           # Phase 1: external data collection
│   │   ├── scrapper.py         # Scrapes YC, names, job titles, GitHub issues into research/

│   ├── models/             # Lightweight domain objects
│   │
│   ├── generators/         # Phase 2: synthetic data engines
│   │   ├── organizations.py
│   │   ├── users.py
│   │   ├── teams.py
│   │   ├── projects.py
│   │   ├── sections.py
│   │   ├── tasks.py
│   │   ├── comments.py
│   │   ├── tags.py
│   │   ├── custom_fields.py
│   │   └── (dependencies, attachments, task_tags, etc.)
│   │
│   ├── distributions/      # All probability/distributional logic
│   │   ├── time.py         # Sprint/project/task durations, offsets, slack
│   │   ├── workload.py     # Tasks per user, capacity, overload, reassignment
│   │   ├── completion.py   # Completion vs overdue vs reopen vs scope change
│   │   └── due_dates.py    # Deadline generation based on benchmarks
│   │
│   ├── validation/         # Sanity checks
└── data/
    ├── asana_simulation.db # Generated SQLite DB (output)
    └── generation.log      # Pipeline log
```

At a high level:

- `research/` holds JSONs derived from real-world sources and manual analysis.
- `distributions/` turns those benchmarks into reusable probability models.
- `generators/` uses the distributions + research data to produce concrete rows.
- `main.py` wires everything into a single reproducible pipeline that writes to SQLite.

---

## Installation

### 1. Create and activate environment

Using conda (recommended):

```bash
conda create -n asana-sim
conda activate asana-sim
```

### 2. Install dependencies

From the repo root:

```bash
pip install -r requirements.txt
```

---

## Configuration

### `config.yaml`

The main configuration file controls:

**Database path and schema**
- `database.path` (e.g., `data/asana_simulation.db`)
- `database.schema_path` (path to `schema.sql`)
- `database.reset_on_run` (drop + recreate tables on each run)

**Organization scale**
- `organization.company_size`

**Generation parameters**
- `users.target_count`, `active_ratio`
- `teams.min_team_size`, `max_team_size`
- `projects.projects_per_team_range`
- `tasks.tasks_per_project_range`, `completion_rate`

**Temporal window**
- `date_ranges.start_date`
- `date_ranges.end_date`

**Performance/logging**
- `performance.batch_size`
- `performance.log_level`
- `performance.show_progress`

### `config.py`

`src/config.py` centralizes project paths using `pathlib`:

- `PROJECT_ROOT`: repository root
- `RESEARCH_DIR`: `PROJECT_ROOT / "research"`
- `DATA_DIR`: `PROJECT_ROOT / "src/data"` (or `data/` depending on how you configure it)

Directories are created on import so runs are reproducible without manual setup.

---

## End-to-End Workflow

The pipeline is intentionally split into two phases:

1. **Phase 1: Research JSON generation**
2. **Phase 2: Synthetic Asana workspace generation**

---

## Phase 1: Generate research JSONs

Before you generate the SQLite database, you must populate `research/` with base JSONs.

From the repo root:

```bash
cd src/scrapers
python scrapper.py
```

What this does:

- Calls multiple public APIs and datasets.
- Writes the following files into `research/`:
  - `companies.json` (YC B2B SaaS company data)
  - `names.json` (first/last names)
  - `job_titles.json` (titles + departments + seniority)
  - `task_patterns.json` (issue/task naming patterns)

Two additional research artifacts are not scraped directly:

- `project_templates.json`
- `benchmarks.json`

These are curated manually from external reports and templates. The methodology and exact derivation are documented in a separate `research/README.md`.

After this step, `research/` contains all JSONs required by the distribution and generator modules.

---

## Phase 2: Run the generation pipeline

From the repo root:

```bash
python src/main.py
```

This will:

- Load `config.yaml`.
- Create or connect to the SQLite database at `database.path`.
- Apply `schema.sql` if needed.
- Run the generators in a fixed order:
  - organizations → users → teams → projects → sections → tags → tasks → dependencies → comments → attachments → custom fields → task-tags
- Run basic validation (e.g., foreign key checks).
- Log stats and timing to `data/generation.log`.

The final output is a single SQLite file you can inspect with any SQL client.

---

## CLI Options

`src/main.py` exposes a small CLI around the pipeline:

```bash
# Show help
python src/main.py --help
```

Key options:

- `--config PATH`  
  Use an alternate YAML config (default: `config.yaml`).

- `--reset`  
  Set `reset_on_run=True` for this invocation (drops existing tables before generation).

- `--company-size N`  
  Override `organization.company_size` from the command line.

- `--rem`  
  Remove (delete) the current database file and exit (no data generation).

Example:

```bash
# Regenerate everything for an 8000-person company, dropping previous tables:
python src/main.py --company-size 8000 --reset
```
if you get any error try deleting asana_simulation.db from src/data

## Pre-generated Database (Large File Notice)

For a company size of **5,000 employees**, the generated SQLite database is very large and exceeds typical GitHub file size limits.

Instead of committing it to the repository, the pre-generated database has been uploaded to [**Google Drive**](https://drive.google.com/file/d/1fdY1hSIuDdnI2PTOEdp4Fz_Eti8x3g9_/view?usp=drive_link).

If you want to regenerate the database yourself (for a different company size or configuration), follow the steps described above in **Phase 1** and **Phase 2**.

