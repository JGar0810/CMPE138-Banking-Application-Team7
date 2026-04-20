# Banking Management System

SJSU CMPE 138 — Spring 2026 — Team 7

A CLI-based banking management system backed by a MySQL database. Supports customer accounts, transactions, loans, cards, and employee operations.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Python 3.10+](https://www.python.org/downloads/)

## Getting Started

### 1. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` if you want to change the default credentials.

### 2. Start the database

```bash
docker compose up
```

This pulls MySQL 8.0 and automatically runs the schema creation and sample data scripts on first start.

### 3. Verify the database is running

```bash
docker compose ps
```

### 4. Connect to the database (optional)

```bash
mysql -h 127.0.0.1 -P 3306 -u banking_user -p banking_pass banking_system
```

## Commands

<!-- TODO: update once the CLI commands are implemented -->

## Database Management

```bash
# Stop the database (data is preserved)
docker compose down

# Stop and wipe all data (re-runs init scripts on next start)
docker compose down -v

# View database logs
docker compose logs db
```
