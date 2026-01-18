#!/usr/bin/env python3
"""
Database migration script to update DutyPlan model structure.
This script adds the new columns to support day-specific assignments.
"""

import sqlite3
from pathlib import Path

def migrate_database():
    """Migrate the database to support the new DutyPlan structure."""
    db_path = Path("dismissal_checker.db")
    
    if not db_path.exists():
        print("❌ Database file not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current table structure
        cursor.execute("PRAGMA table_info(duty_plans)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        # Add new columns if they don't exist
        if 'name' not in columns:
            print("Adding 'name' column...")
            cursor.execute("ALTER TABLE duty_plans ADD COLUMN name VARCHAR(120)")
        
        if 'is_daily_plan' not in columns:
            print("Adding 'is_daily_plan' column...")
            cursor.execute("ALTER TABLE duty_plans ADD COLUMN is_daily_plan BOOLEAN DEFAULT 0")
        
        # Update existing records to have names based on day_of_week
        print("Updating existing records...")
        cursor.execute("""
            UPDATE duty_plans 
            SET name = day_of_week || ' Plan'
            WHERE name IS NULL
        """)
        
        # Make day_of_week and supervisor nullable
        print("Making day_of_week and supervisor nullable...")
        # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
        
        # Create new table with updated structure
        cursor.execute("""
            CREATE TABLE duty_plans_new (
                id INTEGER PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                day_of_week VARCHAR(16),
                supervisor VARCHAR(120),
                team VARCHAR(255),
                is_daily_plan BOOLEAN DEFAULT 0 NOT NULL
            )
        """)
        
        # Copy data from old table
        cursor.execute("""
            INSERT INTO duty_plans_new (id, name, day_of_week, supervisor, team, is_daily_plan)
            SELECT id, 
                   COALESCE(name, day_of_week || ' Plan') as name,
                   day_of_week, 
                   supervisor, 
                   team, 
                   COALESCE(is_daily_plan, 0) as is_daily_plan
            FROM duty_plans
        """)
        
        # Drop old table and rename new one
        cursor.execute("DROP TABLE duty_plans")
        cursor.execute("ALTER TABLE duty_plans_new RENAME TO duty_plans")
        
        # Create unique index on name
        cursor.execute("CREATE UNIQUE INDEX idx_duty_plans_name ON duty_plans(name)")
        
        conn.commit()
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()