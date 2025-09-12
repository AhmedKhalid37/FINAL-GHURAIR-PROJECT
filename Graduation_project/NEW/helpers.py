import os
from pathlib import Path
from .config.database import DB_PATH

def get_db_name() -> str:
    """
    Returns the name of the database file.
    """
    return DB_PATH.name

def get_db_path() -> str:
    """
    Returns the absolute path to the database file.
    """
    return str(DB_PATH.resolve())