"""Add cascade delete constraints for location foreign keys

Revision ID: 8a9f5e3d2b1c
Revises: a9557239bffe
Create Date: 2025-01-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a9f5e3d2b1c'
down_revision: Union[str, Sequence[str], None] = 'a9557239bffe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add CASCADE DELETE to location foreign key constraints."""
    
    # Note: This migration will attempt to add CASCADE DELETE to foreign keys
    # If the constraints already exist without CASCADE, we need to drop and recreate them
    
    # SQL Server syntax for dropping and recreating constraints with CASCADE
    # This is designed to be safe - it will only modify constraints that exist
    
    try:
        # Provider run table - this is the main one causing issues
        op.execute("""
            IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK__provider___locat__02FC7413')
            BEGIN
                ALTER TABLE provider_run DROP CONSTRAINT FK__provider___locat__02FC7413
                ALTER TABLE provider_run ADD CONSTRAINT FK_provider_run_location_id 
                    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
            END
        """)
        
        # Other tables - add CASCADE if constraints exist
        tables_and_fks = [
            ('forecast_cache', 'forecast_cache_location_id_fkey'),
            ('observation_hourly', 'observation_hourly_location_id_fkey'),
            ('forecast_hourly', 'forecast_hourly_location_id_fkey'),
            ('aggregation_daily', 'aggregation_daily_location_id_fkey'),
            ('forecast_accuracy', 'forecast_accuracy_location_id_fkey'),
            ('trend_cache', 'trend_cache_location_id_fkey'),
            ('air_quality_hourly', 'air_quality_hourly_location_id_fkey'),
            ('astronomy_daily', 'astronomy_daily_location_id_fkey'),
        ]
        
        for table_name, constraint_name in tables_and_fks:
            op.execute(f"""
                IF EXISTS (SELECT 1 FROM sys.foreign_keys fk 
                          INNER JOIN sys.tables t ON fk.parent_object_id = t.object_id 
                          WHERE t.name = '{table_name}' AND fk.referenced_object_id = OBJECT_ID('locations'))
                BEGIN
                    -- Drop existing constraint (name may vary)
                    DECLARE @constraint_name NVARCHAR(256)
                    SELECT @constraint_name = fk.name 
                    FROM sys.foreign_keys fk 
                    INNER JOIN sys.tables t ON fk.parent_object_id = t.object_id 
                    WHERE t.name = '{table_name}' AND fk.referenced_object_id = OBJECT_ID('locations')
                    
                    IF @constraint_name IS NOT NULL
                    BEGIN
                        EXEC('ALTER TABLE {table_name} DROP CONSTRAINT ' + @constraint_name)
                        ALTER TABLE {table_name} ADD CONSTRAINT FK_{table_name}_location_id 
                            FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
                    END
                END
            """)
            
        # Location group members - already has CASCADE in model but ensure it's in DB
        op.execute("""
            IF EXISTS (SELECT 1 FROM sys.foreign_keys fk 
                      INNER JOIN sys.tables t ON fk.parent_object_id = t.object_id 
                      WHERE t.name = 'location_group_members' AND fk.referenced_object_id = OBJECT_ID('locations'))
            BEGIN
                DECLARE @constraint_name NVARCHAR(256)
                SELECT @constraint_name = fk.name 
                FROM sys.foreign_keys fk 
                INNER JOIN sys.tables t ON fk.parent_object_id = t.object_id 
                WHERE t.name = 'location_group_members' AND fk.referenced_object_id = OBJECT_ID('locations')
                
                -- Check if CASCADE is already enabled
                IF @constraint_name IS NOT NULL AND NOT EXISTS (
                    SELECT 1 FROM sys.foreign_keys 
                    WHERE name = @constraint_name AND delete_referential_action = 1  -- CASCADE
                )
                BEGIN
                    EXEC('ALTER TABLE location_group_members DROP CONSTRAINT ' + @constraint_name)
                    ALTER TABLE location_group_members ADD CONSTRAINT FK_location_group_members_location_id 
                        FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
                END
            END
        """)
        
    except Exception as e:
        # Migration is designed to be safe - if it fails, the manual cascade in the repository will handle it
        print(f"Migration warning: Could not update all FK constraints to CASCADE: {e}")
        print("Manual cascade deletion in LocationRepository will be used as fallback")


def downgrade() -> None:
    """Remove CASCADE DELETE from location foreign key constraints."""
    
    # This downgrade restores the original FK constraints without CASCADE
    # Note: This may cause the location deletion issue to return
    
    try:
        # Provider run table
        op.execute("""
            IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_provider_run_location_id')
            BEGIN
                ALTER TABLE provider_run DROP CONSTRAINT FK_provider_run_location_id
                ALTER TABLE provider_run ADD CONSTRAINT FK__provider___locat__02FC7413 
                    FOREIGN KEY (location_id) REFERENCES locations(id)
            END
        """)
        
        # Other tables - remove CASCADE
        tables = [
            'forecast_cache', 'observation_hourly', 'forecast_hourly',
            'aggregation_daily', 'forecast_accuracy', 'trend_cache',
            'air_quality_hourly', 'astronomy_daily', 'location_group_members'
        ]
        
        for table_name in tables:
            op.execute(f"""
                IF EXISTS (SELECT 1 FROM sys.foreign_keys fk 
                          INNER JOIN sys.tables t ON fk.parent_object_id = t.object_id 
                          WHERE t.name = '{table_name}' AND fk.referenced_object_id = OBJECT_ID('locations')
                          AND fk.delete_referential_action = 1)  -- CASCADE
                BEGIN
                    DECLARE @constraint_name NVARCHAR(256)
                    SELECT @constraint_name = fk.name 
                    FROM sys.foreign_keys fk 
                    INNER JOIN sys.tables t ON fk.parent_object_id = t.object_id 
                    WHERE t.name = '{table_name}' AND fk.referenced_object_id = OBJECT_ID('locations')
                    
                    IF @constraint_name IS NOT NULL
                    BEGIN
                        EXEC('ALTER TABLE {table_name} DROP CONSTRAINT ' + @constraint_name)
                        EXEC('ALTER TABLE {table_name} ADD CONSTRAINT FK_{table_name}_location_id_no_cascade 
                            FOREIGN KEY (location_id) REFERENCES locations(id)')
                    END
                END
            """)
            
    except Exception as e:
        print(f"Downgrade warning: Could not restore all FK constraints: {e}")