"""
database.py

Database utilities for creating and populating the Asana simulation database.
Handles SQLite connection, schema creation, batch inserts, and validation.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages SQLite database operations for the Asana simulation.
    
    Features:
    - Schema creation from SQL file
    - Batch inserts with transactions
    - Foreign key validation
    - Connection pooling
    - Error handling
    """
    
    def __init__(self, db_path: str = "data/asana_simulation.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create connection
        self.connection = None
        logger.info(f"DatabaseManager initialized with path: {self.db_path}")
    
    def connect(self):
        """Create database connection with optimizations."""
        if self.connection is None:
            self.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                isolation_level=None  # Autocommit mode for better control
            )
            
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
            
            # Performance optimizations
            self.connection.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
            self.connection.execute("PRAGMA synchronous = NORMAL")  # Faster writes
            self.connection.execute("PRAGMA cache_size = -64000")  # 64MB cache
            self.connection.execute("PRAGMA temp_store = MEMORY")  # In-memory temp tables
            
            logger.info("Database connection established with optimizations")
        
        return self.connection
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
    
    def execute_schema(self, schema_path: str = "schema.sql"):
        """
        Execute schema SQL file to create all tables.
        
        Args:
            schema_path: Path to schema SQL file
        """
        schema_file = Path(schema_path)
        
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        logger.info(f"Executing schema from: {schema_path}")
        
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        with self.get_cursor() as cursor:
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
            
            for statement in statements:
                try:
                    cursor.execute(statement)
                except sqlite3.Error as e:
                    logger.error(f"Error executing statement: {statement[:100]}...")
                    raise e
        
        self.connect().commit()
        logger.info(f" Schema created successfully ({len(statements)} statements)")
    
    def drop_all_tables(self):
        """Drop all tables (useful for reset)."""
        logger.warning("Dropping all tables...")
        
        with self.get_cursor() as cursor:
            # Get all table names
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Disable foreign keys temporarily
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # Drop each table
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                logger.info(f"  Dropped table: {table}")
            
            # Re-enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
        
        self.connect().commit()
        logger.info(f" Dropped {len(tables)} tables")
    
    def insert_batch(self, table: str, records: List[Dict[str, Any]], 
                    batch_size: int = 1000) -> int:
        """
        Batch insert records into a table.
        
        Args:
            table: Table name
            records: List of record dictionaries
            batch_size: Number of records per batch
        
        Returns:
            Number of records inserted
        """
        if not records:
            logger.warning(f"No records to insert into {table}")
            return 0
        
        logger.info(f"Inserting {len(records):,} records into {table}...")
        
        # Get column names from first record
        columns = list(records[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join(columns)
        
        insert_sql = f"""
            INSERT INTO {table} ({column_names})
            VALUES ({placeholders})
        """
        
        total_inserted = 0
        
        with self.get_cursor() as cursor:
            # Begin transaction
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                # Insert in batches
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    
                    # Convert records to tuples
                    values = [tuple(record[col] for col in columns) for record in batch]
                    
                    cursor.executemany(insert_sql, values)
                    total_inserted += len(batch)
                    
                    # Progress log every 10k records
                    if total_inserted % 10000 == 0:
                        logger.info(f"  Inserted {total_inserted:,} / {len(records):,} records...")
                
                # Commit transaction
                cursor.execute("COMMIT")
                logger.info(f" Inserted {total_inserted:,} records into {table}")
                
            except sqlite3.Error as e:
                cursor.execute("ROLLBACK")
                logger.error(f" Error inserting into {table}: {e}")
                raise e
        
        return total_inserted
    
    def insert_models(self, table: str, models: List[Any], 
                     batch_size: int = 1000) -> int:
        """
        Insert model instances (with to_dict() method) into a table.
        
        Args:
            table: Table name
            models: List of model instances with to_dict() method
            batch_size: Number of records per batch
        
        Returns:
            Number of records inserted
        """
        if not models:
            return 0
        
        # Convert models to dictionaries
        records = [model.to_dict() for model in models]
        
        return self.insert_batch(table, records, batch_size)
    
    def get_table_count(self, table: str) -> int:
        """Get number of rows in a table."""
        with self.get_cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
        
        return count
    
    def validate_foreign_keys(self) -> bool:
        """
        Validate all foreign key constraints.
        
        Returns:
            True if all constraints valid, False otherwise
        """
        logger.info("Validating foreign key constraints...")
        
        with self.get_cursor() as cursor:
            cursor.execute("PRAGMA foreign_key_check")
            violations = cursor.fetchall()
        
        if violations:
            logger.error(f" Found {len(violations)} foreign key violations:")
            for violation in violations[:10]:  # Show first 10
                logger.error(f"  {violation}")
            return False
        else:
            logger.info(" All foreign key constraints valid")
            return True
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with table counts and database info
        """
        stats = {
            'database_path': str(self.db_path),
            'database_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0,
            'created_at': datetime.now().isoformat(),
            'tables': {}
        }
        
        with self.get_cursor() as cursor:
            # Get all table names
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get count for each table
            for table in tables:
                try:
                    count = self.get_table_count(table)
                    stats['tables'][table] = count
                except sqlite3.Error:
                    stats['tables'][table] = 'error'
        
        stats['total_records'] = sum(v for v in stats['tables'].values() if isinstance(v, int))
        
        return stats
    
    def print_stats(self):
        """Print database statistics in a formatted way."""
        stats = self.get_database_stats()
        
        print("\n" + "="*70)
        print("DATABASE STATISTICS")
        print("="*70)
        print(f"Database: {stats['database_path']}")
        print(f"Size: {stats['database_size_mb']:.2f} MB")
        print(f"Total Records: {stats['total_records']:,}")
        print(f"\nTable Counts:")
        
        for table, count in sorted(stats['tables'].items()):
            if isinstance(count, int):
                print(f"  {table:30s}: {count:>10,}")
            else:
                print(f"  {table:30s}: {count:>10}")
        
        print("="*70 + "\n")
    
    def export_to_csv(self, table: str, output_path: str):
        """
        Export table to CSV file.
        
        Args:
            table: Table name
            output_path: Output CSV file path
        """
        import csv
        
        logger.info(f"Exporting {table} to {output_path}...")
        
        with self.get_cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table}")
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Write to CSV
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(cursor.fetchall())
        
        logger.info(f" Exported {table} to {output_path}")
    
    def vacuum(self):
        """Optimize database (reclaim space, rebuild indexes)."""
        logger.info("Vacuuming database...")
        with self.get_cursor() as cursor:
            cursor.execute("VACUUM")
        logger.info(" Database vacuumed")


# ============================================================================
# Convenience Functions
# ============================================================================

def create_database(db_path: str = "data/asana_simulation.db",
                   schema_path: str = "schema.sql",
                   reset: bool = False) -> DatabaseManager:
    """
    Create and initialize database.
    
    Args:
        db_path: Path to database file
        schema_path: Path to schema SQL file
        reset: If True, drop existing tables first
    
    Returns:
        DatabaseManager instance
    """
    db = DatabaseManager(db_path)
    db.connect()
    
    if reset:
        db.drop_all_tables()
    
    db.execute_schema(schema_path)
    
    return db


# ============================================================================
# Testing / Standalone Execution
# ============================================================================

if __name__ == "__main__":
    """
    Test database manager.
    Run: python src/database.py
    """
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*70)
    print("TESTING DATABASE MANAGER")
    print("="*70 + "\n")
    
    try:
        # Create test database
        db = DatabaseManager("data/test.db")
        db.connect()
        
        print(" Database connection successful")
        
        # Test creating a simple table
        with db.get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    value INTEGER
                )
            """)
        
        print(" Table creation successful")
        
        # Test batch insert
        test_records = [
            {'id': f'id_{i}', 'name': f'name_{i}', 'value': i}
            for i in range(100)
        ]
        
        db.insert_batch('test_table', test_records)
        print(" Batch insert successful")
        
        # Test count
        count = db.get_table_count('test_table')
        print(f" Table count: {count} records")
        
        # Test stats
        db.print_stats()
        
        # Cleanup
        db.close()
        Path("data/test.db").unlink()
        print(" Cleanup successful")
        
        print("\n ALL TESTS PASSED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
