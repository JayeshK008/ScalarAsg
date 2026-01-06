import sys
import logging
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager, create_database

# Import all generators
from generators.organizations import generate_organization
from generators.users import generate_users
from generators.teams import generate_teams
from generators.projects import generate_projects
from generators.sections import generate_sections
from generators.tags import generate_tags
from generators.tasks import generate_tasks
from generators.dependencies import generate_dependencies
from generators.comments import generate_comments
from generators.attachments import generate_attachments
from generators.custom_fields import generate_custom_fields
from generators.task_tags import generate_task_tags
from config import DATA_DIR
# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataGenerationPipeline:
    """
    Main pipeline for generating Asana simulation data.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize pipeline with configuration."""
        self.config = self._load_config(config_path)
        self.db = None
        self.start_time = None
        
        logger.info("DataGenerationPipeline initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Configuration loaded from {config_path}")
        return config
    
    def _setup_database(self):
        """Initialize database connection and schema."""
        logger.info("Setting up database...")
        
        db_config = self.config['database']
        
        self.db = create_database(
            db_path=db_config['path'],
            schema_path=db_config['schema_path'],
            reset=db_config.get('reset_on_run', False)
        )
        
        logger.info(" Database setup complete")
    
    def run(self):
        """Execute the complete data generation pipeline."""
        self.start_time = datetime.now()
        
        logger.info("\n" + "="*70)
        logger.info("ASANA SIMULATION DATA GENERATION PIPELINE")
        logger.info("="*70)
        logger.info(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Company Size: {self.config['organization']['company_size']:,}")
        
        try:
            # Setup database
            self._setup_database()
            
            # Step 1: Organizations
            logger.info("\n" + "="*70)
            logger.info("STEP 1: GENERATING ORGANIZATION")
            logger.info("="*70)
            
            company_size = self.config['organization']['company_size']
            org_result = generate_organization(company_size=company_size)
            
            # Insert organization (departments are just metadata, not stored)
            self.db.insert_models('organizations', [org_result['organization']])
            
            # Step 2: Users
            logger.info("\n" + "="*70)
            logger.info("STEP 2: GENERATING USERS")
            logger.info("="*70)
            
            target_count = self.config['users'].get('target_count')
            users = generate_users(org_result, target_count=target_count)
            
            self.db.insert_models('users', users)
            # Step 3: Teams
            logger.info("\n" + "="*70)
            logger.info("STEP 3: GENERATING TEAMS")
            logger.info("="*70)
            
            teams = generate_teams(org_result, users)
            
            self.db.insert_models('teams', teams)
            
            # Step 4: Projects
            
            logger.info("\n" + "="*70)
            logger.info("STEP 4: GENERATING PROJECTS")
            logger.info("="*70)
            
            projects = generate_projects(org_result, teams, users)
            
            self.db.insert_models('projects', projects)
            # Step 5: Sections
            logger.info("\n" + "="*70)
            logger.info("STEP 5: GENERATING SECTIONS")
            logger.info("="*70)
            
            sections = generate_sections(projects)
            
            self.db.insert_models('sections', sections)
            # Step 6: Tags
            logger.info("\n" + "="*70)
            logger.info("STEP 6: GENERATING TAGS")
            logger.info("="*70)
            
            tags = generate_tags(org_result)
            
            self.db.insert_models('tags', tags)
            # Step 7: Tasks
            logger.info("\n" + "="*70)
            logger.info("STEP 7: GENERATING TASKS")
            logger.info("="*70)
            
            tasks = generate_tasks(projects, sections, users, tags)
            
            self.db.insert_models('tasks', tasks)
            # Step 8: Dependencies
            logger.info("\n" + "="*70)
            logger.info("STEP 8: GENERATING TASK DEPENDENCIES")
            logger.info("="*70)
            
            dependencies = generate_dependencies(tasks)
            
            self.db.insert_models('task_dependencies', dependencies)
            # Step 9: Comments
            logger.info("\n" + "="*70)
            logger.info("STEP 9: GENERATING COMMENTS")
            logger.info("="*70)
            
            comments = generate_comments(tasks, users)
            
            self.db.insert_models('comments', comments)
            # Step 10: Attachments
            logger.info("\n" + "="*70)
            logger.info("STEP 10: GENERATING ATTACHMENTS")
            logger.info("="*70)
            
            attachments = generate_attachments(tasks, users)
            
            self.db.insert_models('attachments', attachments)
            # Step 11: Custom Fields
            logger.info("\n" + "="*70)
            logger.info("STEP 11: GENERATING CUSTOM FIELDS")
            logger.info("="*70)
            
            definitions, enum_options, values = generate_custom_fields(projects, teams, tasks)
            
            self.db.insert_models('custom_field_definitions', definitions)
            self.db.insert_models('custom_field_enum_options', enum_options)
            self.db.insert_models('custom_field_values', values)
            # Step 12: Task Tags
            logger.info("\n" + "="*70)
            logger.info("STEP 12: GENERATING TASK-TAG ASSOCIATIONS")
            logger.info("="*70)
            
            task_tags = generate_task_tags(tasks, tags)
            
            self.db.insert_models('task_tags', task_tags)
            
            # Validation
            logger.info("\n" + "="*70)
            logger.info("VALIDATING DATABASE")
            logger.info("="*70)
            
            if self.db.validate_foreign_keys():
                logger.info(" All foreign key constraints valid")
            else:
                logger.error(" Foreign key validation failed")
            
            # Optimize database
            logger.info("\nOptimizing database...")
            self.db.vacuum()
            
            # Print statistics
            self.db.print_stats()
            
            # Calculate duration
            end_time = datetime.now()
            duration = end_time - self.start_time
            
            logger.info("\n" + "="*70)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("="*70)
            logger.info(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Duration: {duration}")
            logger.info(f"Database: {self.config['database']['path']}")
            logger.info("="*70 + "\n")
            
        except Exception as e:
            logger.error("\n" + "="*70)
            logger.error("PIPELINE FAILED")
            logger.error("="*70)
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()
            logger.error("="*70 + "\n")
            raise e
        
        finally:
            # Close database
            if self.db:
                self.db.close()

def main():
    """Main entry point for CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate Asana simulation data",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Drop existing tables before generation'
    )
    parser.add_argument(
        '--rem',
        action='store_true',
        help='Remove (delete) the database file and exit (no generation)'
    )
    parser.add_argument(
        '--company-size',
        type=int,
        help='Override company size from config'
    )
    
    args = parser.parse_args()
    if args.rem:
        db_path = DATA_DIR/"asana_simulation.db"
        print(db_path)
        if db_path.exists():
            logger.info(f"Removing database: {db_path}")
            db_path.unlink()
            logger.info(" Database file deleted")
        else:
            logger.info("No database file found")
        return
    
    # Load config
    pipeline = DataGenerationPipeline(config_path=args.config)
    
    # Override config if provided
    if args.reset:
        pipeline.config['database']['reset_on_run'] = True
    
    if args.company_size:
        pipeline.config['organization']['company_size'] = args.company_size
    
    # Run pipeline
    pipeline.run()


if __name__ == "__main__":
    main()
