# Rust SQL Server

A lightweight HTTP bridge for SQLite databases, written in Rust. This tool provides an asynchronous REST API for querying SQLite databases, with optional automatic CSV-to-SQLite conversion.

## Features

- **HTTP API**: Exposes a RESTful endpoint (`PUT /query`) for executing SQL queries against a SQLite database
- **CSV Import**: Automatically converts CSV files to SQLite databases on startup
- **Dynamic Type Handling**: Properly converts SQLite types (INTEGER, REAL, BOOLEAN, TEXT) to JSON values in responses
- **Write Operation Support**: Handles INSERT, UPDATE, and DELETE operations with row count reporting
- **Parameterized Queries**: Supports parameterized queries to prevent SQL injection
- **Async/Await**: Built with Tokio and SQLx for high-performance asynchronous database operations

## Usage

### Command Line

```bash
# Start server with an existing SQLite database
cargo run -- dndmonsters.db

# Start server with a CSV file (will auto-convert to .db)
cargo run -- monsters.csv
```

**Default**: If no argument is provided, the server defaults to `dndmonsters.db`.

### API Endpoints

#### `GET /`

Health check endpoint. Returns a simple greeting message.

#### `PUT /query`

Execute SQL queries against the database.

**Request Body:**
```json
{
    "sql": "SELECT * FROM imported_data WHERE id = ?",
    "parameters": ["123"]
}
```

**Response (SELECT queries):**
```json
{
    "status": "success",
    "result": [
        {"id": 1, "name": "Goblin", ...},
        {"id": 2, "name": "Orc", ...}
    ]
}
```

**Response (INSERT/UPDATE/DELETE):**
```json
{
    "status": "success",
    "result": [
        {"message": "Success: 5 row(s) affected."}
    ]
}
```

**Error Response:**
```json
{
    "status": "error: <error message>",
    "result": []
}
```

### Server Configuration

- **Host**: `0.0.0.0:3000`
- **Database**: Specified via command line argument (SQLite file path)

## Architecture

- **`main.rs`**: Contains the Axum web server, request handlers, and CLI argument parsing
- **`lib.rs`**: Contains the `import_csv_to_sqlite()` function for CSV-to-SQLite conversion

## Dependencies

- `axum` - Web framework
- `sqlx` - Async database toolkit (SQLite)
- `tokio` - Async runtime
- `serde` / `serde_json` - JSON serialization
- `clap` - Command-line argument parsing
- `csv` - CSV file parsing

## Security Note

This tool provides **unrestricted** access to the hosted database. There is no authentication, authorization, or prevention of destructive commands (e.g., `DROP TABLE`). It is intended as a lightweight development/utility tool, not for production use with sensitive data.