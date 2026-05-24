use std::fs::File;
use sqlx::{SqlitePool, Executor};

pub async fn import_csv_to_sqlite(csv_path: &str, db_path: &str) -> Result<(), Box<dyn std::error::Error>> {
    // 1. Force-create a fresh, empty SQLite file on disk
    // If the file exists, we can remove it first, or just let SQLx connect
    let pool = SqlitePool::connect(&format!("sqlite://{}?mode=rwc", db_path)).await?;

    // 2. Open the CSV and grab headers
    let file = File::open(csv_path)?;
    let mut rdr = csv::Reader::from_reader(file);
    let headers = rdr.headers()?.clone();

    // 3. Dynamically craft the CREATE TABLE statement
    // We'll call our table "imported_data"
    let mut create_table_sql = String::from("CREATE TABLE IF NOT EXISTS imported_data (");
    let column_defs: Vec<String> = headers.iter()
        .map(|h| format!("`{}` TEXT", h.trim()))
        .collect();
    create_table_sql.push_str(&column_defs.join(", "));
    create_table_sql.push_str(");");

    pool.execute(create_table_sql.as_str()).await?;

    // 4. Start a blazing-fast transaction to batch write rows
    let mut tx = pool.begin().await?;
    
    // Build a reusable parameter placeholder string like: VALUES (?, ?, ?)
    let placeholders = vec!["?"; headers.len()].join(", ");
    let insert_sql = format!("INSERT INTO imported_data VALUES ({})", placeholders);

    for result in rdr.records() {
        let record = result?;
        let mut query = sqlx::query(&insert_sql);
        
        // Bind every field in the row dynamically
        for field in record.iter() {
            query = query.bind(field.trim().to_string());
        }
        
        // Execute the single row insert inside the transaction block
        query.execute(&mut *tx).await?;
    }

    // 5. Commit the transaction to disk completely
    tx.commit().await?;
    println!("Successfully loaded all rows into 'imported_data' table!");
    
    pool.close().await;
    Ok(())
}