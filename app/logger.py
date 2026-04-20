# SJSU CMPE 138 SPRING 2026 TEAM7

import logging
import os

os.makedirs("Log", exist_ok=True)

logging.basicConfig(
    filename="Log/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log_action(user, action, result):
    logging.info(f"USER: {user} | ACTION: {action} | RESULT: {result}")

def log_error(user, action, error):
    logging.error(f"USER: {user} | ACTION: {action} | ERROR: {error}")
