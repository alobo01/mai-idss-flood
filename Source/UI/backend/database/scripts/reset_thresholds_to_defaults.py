#!/usr/bin/env python3
"""
Script to reset flood threshold configuration to default values.

This script resets the threshold_config table to the original default values
and provides a backup of the current configuration before resetting.

Usage:
    python backend/database/scripts/reset_thresholds_to_defaults.py [--backup] [--force]

Options:
    --backup    Create a backup of current thresholds before resetting
    --force     Reset without confirmation prompt
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db import get_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default threshold values
DEFAULT_THRESHOLDS = {
    'flood_minor': 16.0,
    'flood_moderate': 22.0,
    'flood_major': 28.0,
    'critical_probability': 0.8,
    'warning_probability': 0.6,
    'advisory_probability': 0.3
}

def backup_current_config(conn, backup_name: str = None):
    """Create a backup of the current threshold configuration."""
    if backup_name is None:
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        cursor = conn.cursor()

        # Get current configuration
        cursor.execute("""
            INSERT INTO threshold_config
            (config_name, flood_minor, flood_moderate, flood_major,
             critical_probability, warning_probability, advisory_probability, notes)
            SELECT
                %s, flood_minor, flood_moderate, flood_major,
                critical_probability, warning_probability, advisory_probability,
                'Backup created on ' || CURRENT_TIMESTAMP
            FROM threshold_config
            WHERE config_name = 'default'
        """, (backup_name,))

        conn.commit()
        logger.info(f"Created backup configuration: {backup_name}")

    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        conn.rollback()
        raise

def get_current_config(conn):
    """Get the current threshold configuration."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT flood_minor, flood_moderate, flood_major,
                   critical_probability, warning_probability, advisory_probability,
                   updated_at
            FROM threshold_config
            WHERE config_name = 'default'
        """)

        result = cursor.fetchone()
        if result:
            return {
                'flood_minor': result[0],
                'flood_moderate': result[1],
                'flood_major': result[2],
                'critical_probability': result[3],
                'warning_probability': result[4],
                'advisory_probability': result[5],
                'updated_at': result[6]
            }
        else:
            logger.warning("No current configuration found")
            return None

    except Exception as e:
        logger.error(f"Failed to get current configuration: {e}")
        return None

def reset_to_defaults(conn):
    """Reset thresholds to default values."""
    try:
        cursor = conn.cursor()

        # Update the default configuration
        cursor.execute("""
            UPDATE threshold_config
            SET
                flood_minor = %s,
                flood_moderate = %s,
                flood_major = %s,
                critical_probability = %s,
                warning_probability = %s,
                advisory_probability = %s,
                updated_by = 'reset_script',
                notes = 'Reset to default values on ' || CURRENT_TIMESTAMP
            WHERE config_name = 'default'
        """, (
            DEFAULT_THRESHOLDS['flood_minor'],
            DEFAULT_THRESHOLDS['flood_moderate'],
            DEFAULT_THRESHOLDS['flood_major'],
            DEFAULT_THRESHOLDS['critical_probability'],
            DEFAULT_THRESHOLDS['warning_probability'],
            DEFAULT_THRESHOLDS['advisory_probability']
        ))

        rows_affected = cursor.rowcount
        conn.commit()

        if rows_affected > 0:
            logger.info("Successfully reset thresholds to default values")
            return True
        else:
            logger.warning("No rows were updated - configuration may not exist")
            return False

    except Exception as e:
        logger.error(f"Failed to reset thresholds: {e}")
        conn.rollback()
        raise

def main():
    parser = argparse.ArgumentParser(description='Reset flood thresholds to default values')
    parser.add_argument('--backup', action='store_true',
                       help='Create a backup of current thresholds before resetting')
    parser.add_argument('--force', action='store_true',
                       help='Reset without confirmation prompt')

    args = parser.parse_args()

    try:
        # Connect to database
        conn = get_connection()
        logger.info("Connected to database")

        # Get current configuration
        current_config = get_current_config(conn)

        if current_config:
            print("\nCurrent threshold configuration:")
            print(f"  Minor flood level:     {current_config['flood_minor']} ft")
            print(f"  Moderate flood level:  {current_config['flood_moderate']} ft")
            print(f"  Major flood level:     {current_config['flood_major']} ft")
            print(f"  Critical probability:  {current_config['critical_probability']}")
            print(f"  Warning probability:   {current_config['warning_probability']}")
            print(f"  Advisory probability:  {current_config['advisory_probability']}")
            print(f"  Last updated:          {current_config['updated_at']}")

            print("\nDefault threshold configuration:")
            print(f"  Minor flood level:     {DEFAULT_THRESHOLDS['flood_minor']} ft")
            print(f"  Moderate flood level:  {DEFAULT_THRESHOLDS['flood_moderate']} ft")
            print(f"  Major flood level:     {DEFAULT_THRESHOLDS['flood_major']} ft")
            print(f"  Critical probability:  {DEFAULT_THRESHOLDS['critical_probability']}")
            print(f"  Warning probability:   {DEFAULT_THRESHOLDS['warning_probability']}")
            print(f"  Advisory probability:  {DEFAULT_THRESHOLDS['advisory_probability']}")
        else:
            print("No current configuration found. Will create default configuration.")

        if not args.force:
            response = input("\nDo you want to proceed with resetting to defaults? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("Operation cancelled.")
                return

        # Create backup if requested
        if args.backup and current_config:
            backup_name = f"backup_before_reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_current_config(conn, backup_name)

        # Reset to defaults
        success = reset_to_defaults(conn)

        if success:
            print("\n✅ Successfully reset thresholds to default values!")
            print("The system will now use the default threshold configuration.")
        else:
            print("\n❌ Failed to reset thresholds. Check the logs for details.")

    except Exception as e:
        logger.error(f"Script failed: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)

    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()