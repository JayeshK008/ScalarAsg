from pathlib import Path

# Project root directory (parent of src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data directories
RESEARCH_DIR = PROJECT_ROOT / "research"
DATA_DIR = PROJECT_ROOT / "src/data"
# Ensure directories exist
RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
