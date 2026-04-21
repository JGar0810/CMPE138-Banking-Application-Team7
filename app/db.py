from __future__ import annotations

import os
from typing import Optional

import mysql.connector
from dotenv import load_dotenv


def get_connection(database: Optional[str] = None):
    load_dotenv()
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "banking_user"),
        password=os.getenv("MYSQL_PASSWORD", "banking_pass"),
        database=database or os.getenv("MYSQL_DATABASE", "banking_system"),
        autocommit=False,
    )
