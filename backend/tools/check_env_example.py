#!/usr/bin/env python3
"""
Environment consistency checker for WeatherAI backend.

Verifies that all fields in AppSettings are documented in .env.example
and vice versa (with some exceptions for extra keys).
"""

import argparse
import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import after path modification to avoid import errors
# ruff: noqa: E402
from app.core.config import AppSettings


def get_settings_fields() -> set[str]:
    """Extract field names from AppSettings class."""
    fields = set()

    # Get all field definitions from AppSettings
    for field_name, field_info in AppSettings.model_fields.items():
        # Use the alias if it exists, otherwise use the field name
        alias = field_info.alias if field_info.alias else field_name
        fields.add(alias.upper())

    return fields


def get_env_example_fields(env_example_path: Path) -> set[str]:
    """Extract variable names from .env.example file."""
    fields = set()

    if not env_example_path.exists():
        return fields

    with open(env_example_path) as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Extract variable name (everything before =)
            if '=' in line:
                var_name = line.split('=')[0].strip()
                fields.add(var_name)

    return fields


def check_consistency(fix: bool = False) -> bool:
    """
    Check consistency between AppSettings and .env.example.

    Args:
        fix: If True, attempt to fix inconsistencies by updating .env.example

    Returns:
        bool: True if consistent (or fixed), False if inconsistencies found
    """
    backend_dir = Path(__file__).parent.parent
    env_example_path = backend_dir / '.env.example'

    settings_fields = get_settings_fields()
    env_fields = get_env_example_fields(env_example_path)

    # Ignore extra keys that are not yet integrated into settings
    ignore_extra = {
        'DB_SCHEMA_CORE',
        'DB_SCHEMA_RAG',
        'DATABASE_URL',  # Legacy, derived from other fields
        'APP_ENV',       # Legacy field name
        'DEV_FALLBACK',  # Legacy field
    }

    # Find missing and extra fields
    missing_in_env = settings_fields - env_fields
    extra_in_env = env_fields - settings_fields - ignore_extra

    has_issues = bool(missing_in_env or extra_in_env)

    if missing_in_env:
        print(f"❌ Missing from .env.example: {sorted(missing_in_env)}")

    if extra_in_env:
        print(f"⚠️  Extra in .env.example (not in AppSettings): {sorted(extra_in_env)}")

    if not has_issues:
        print("✅ .env.example is consistent with AppSettings")
        return True

    if fix:
        return fix_env_example(env_example_path, missing_in_env)

    return False


def fix_env_example(env_example_path: Path, missing_fields: set[str]) -> bool:
    """
    Add missing fields to .env.example with placeholder values.

    Args:
        env_example_path: Path to .env.example file
        missing_fields: Set of field names to add

    Returns:
        bool: True if successful
    """
    if not missing_fields:
        return True

    print(f"🔧 Adding missing fields to {env_example_path}")

    # Default values for common missing fields
    default_values = {
        'DB_SCHEMA_CORE': 'core',
        'DB_SCHEMA_RAG': 'rag',
    }

    additions = []
    for field in sorted(missing_fields):
        default_value = default_values.get(field, '')
        additions.append(f"\n# {field}\n{field}={default_value}")

    # Append to file
    with open(env_example_path, 'a') as f:
        f.write('\n'.join(additions))

    print(f"✅ Added {len(missing_fields)} missing fields")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check consistency between AppSettings and .env.example"
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help="Attempt to fix inconsistencies by updating .env.example"
    )

    args = parser.parse_args()

    try:
        is_consistent = check_consistency(fix=args.fix)
        sys.exit(0 if is_consistent else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
