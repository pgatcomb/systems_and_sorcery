use axum::{
    extract::State,
    routing::{get, put},
    Router,
    Json,
};
use sqlx::{SqlitePool, Row, Column, TypeInfo};
use serde::{Serialize, Deserialize};
use serde_json::{Map, Value};
use clap::Parser;
use rustsqlserver::import_csv_to_sqlite;


#[tokio::main]
async fn main() {
    //let pool = SqlitePool::connect("dndmonsters.db").await.expect("Failed to connect to database");
    let arguments = Args::parse();
    let mut db_path = arguments.database.clone();
    if db_path.to_lowercase().ends_with(".csv") {
            let csv_path = &arguments.database;
            // Swap the extension: "monsters.csv" -> "monsters.db"
            let generated_db = db_path.replace(".csv", ".db");
            
            println!("CSV detected! Transforming '{}' into '{}'...", csv_path, generated_db);
            
            // Run our ingest engine (we'll build this next!)
            if let Err(err) = import_csv_to_sqlite(csv_path, &generated_db).await {
                eprintln!("Failed to import CSV: {}", err);
                std::process::exit(1);
            }
            
            db_path = generated_db; // Switch the server over to use the new file!
        }

    let connection_string = format!("sqlite://{}", db_path);
    let pool = SqlitePool::connect(&connection_string)
        .await
        .expect("Failed to connect to the database file");

    let shared_state = AppState { pool };
    let app = Router::new()
        .route("/", get(|| async { "Hi there. Did you do this right?" }))
        .route("/query", put(sql_query))
        .with_state(shared_state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn sql_query(State(state): State<AppState>, Json(payload): Json<QueryPayload>) -> Json<QueryResponse> {
    
    let mut query = sqlx::query(&payload.sql);
    for param in &payload.parameters {
        query = query.bind(param);
    }
    let sql_upper = payload.sql.trim().to_uppercase();
    let is_write = sql_upper.starts_with("INSERT") 
    || sql_upper.starts_with("UPDATE") 
    || sql_upper.starts_with("DELETE");

    if is_write {
    // 2. Execute the write operation
    match query.execute(&state.pool).await {
    Ok(result) => {
        let rows_changed = result.rows_affected();
        
        // We can return a helpful message in our JSON array
        let msg = serde_json::json!({
            "message": format!("Success: {} row(s) affected.", rows_changed)
        });

        Json(QueryResponse {
            status: "success".to_string(),
            result: vec![msg],
        })
    }
    Err(e) => {
        Json(QueryResponse {
            status: format!("error: {}", e),
            result: vec![],
        })
    }
    }
    } else {




    match query.fetch_all(&state.pool).await {
        Ok(sqlite_rows) => {
            let mut db_results = Vec::new();

            for row in sqlite_rows {
                let mut row_map = Map::new();

                // 🕵️ Inspect every column returned in this row
                for column in row.columns() {
                    let col_name = column.name().to_string();
                    let type_name = column.type_info().name();

                    // 🧬 Dynamically convert SQLite types to JSON values
                    let json_val = match type_name {
                        "INTEGER" | "BIGINT" => {
                            if let Ok(val) = row.try_get::<i64, _>(column.ordinal()) {
                                Value::from(val)
                            } else {
                                Value::Null
                            }
                        }
                        "REAL" | "DOUBLE" | "FLOAT" => {
                            if let Ok(val) = row.try_get::<f64, _>(column.ordinal()) {
                                Value::from(val)
                            } else {
                                Value::Null
                            }
                        }
                        "BOOLEAN" => {
                            if let Ok(val) = row.try_get::<bool, _>(column.ordinal()) {
                                Value::from(val)
                            } else {
                                Value::Null
                            }
                        }
                        _ => {
                            // Default everything else (TEXT, BLOB, etc.) to a String
                            if let Ok(val) = row.try_get::<String, _>(column.ordinal()) {
                                Value::from(val)
                            } else {
                                Value::Null
                            }
                        }
                    };

                    row_map.insert(col_name, json_val);
                }

                // Push our completed JSON row into the results array
                db_results.push(Value::Object(row_map));
            }

            Json(QueryResponse {
                status: "success".to_string(),
                result: db_results,
            })
        }
        Err(e) => {
            Json(QueryResponse {
                status: format!("error: {}", e),
                result: vec![],
            })
        }
    }
}
}

#[derive(Parser, Debug)]
#[command(name = "rustsqlserver", version = "1.0", about = "An HTTP bridge for SQLite")]
struct Args {
    #[arg(default_value="dndmonsters.db")]
    database: String,
}
#[derive(Clone)]
struct AppState{
    pool: SqlitePool,
}

#[derive(Deserialize)]
struct QueryPayload {
    sql: String,
    parameters: Vec<String>,
}

#[derive(Serialize)]
struct QueryResponse {
    status: String,
    result: Vec<serde_json::Value>,
}