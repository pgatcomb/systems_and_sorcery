mod dataio;
mod sim;

use dataio::loader::{load_definitions_and_meta, load_game_state_from_json};
use dataio::saver::save_game_state_to_json;
use dataio::validator::validate_definitions;
use dataio::meta::MetaData;
use sim::definitions::Definitions;
use sim::gamestate::{GameState, CommandType};
use sim::engine::Engine;

use std::path::PathBuf;
use std::process;
use std::sync::Arc;
use std::net::SocketAddr;


use tokio::sync::Mutex;
use axum::{Router,routing::{get, post},extract::State,Json};
use tower_http::cors::{CorsLayer};
use tower_http::cors::Any as CorsAny;


struct AppState {
    state: Mutex<GameState>,
    defs: Definitions,
    command_queue: Mutex<Vec<CommandType>>,
    meta: MetaData,
}

fn load_or_create_game_state(base_path: &PathBuf, defs: &Definitions) -> GameState {
    let path = base_path.join("save.json");

    if path.exists() {
        println!("Save found, loading...");
        if let Ok(state) = load_game_state_from_json(base_path) {
            return state;
        }
        println!("Failed to load save, creating new game state...");
    } else {
        println!("No save found, creating new game state...");
    }

    let state = GameState::new(defs);
    save_game_state_to_json(base_path, &state);
    state
}

#[tokio::main]
async fn main() {
    println!("Settle Sim version 0.1");
    // Meta is unused at this time, and will be implemented when we get the client going
    let (defs, meta) = load_definitions_and_meta();
    let _defs_copy_for_client = defs.clone();
    let validation_result = validate_definitions(&defs);
    if let Err(errors) = validation_result {
        println!("Validation failed! Fix the following issues:\n{}", errors.join("\n"));
        println!("Exiting");
        process::exit(1); 
    }
    let base_path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("saves");
    let state = load_or_create_game_state(&base_path, &defs);

    let app_state = Arc::new(AppState{
        state: Mutex::new(state),
        defs,
        command_queue: Mutex::new(Vec::new()),
        meta,
    });
    
    let cors = CorsLayer::new()
        .allow_origin(CorsAny)
        .allow_methods(CorsAny)
        .allow_headers(CorsAny);

    let app = Router::new()
        .route("/", get(|| async { "This is not the page you're looking for"}))
        .route("/state", get(get_state))
        .route("/order", post(order_handler))
        .route("/commit", post(commit_handler))
        .route("/meta", get(get_meta))
        .layer(cors)
        .with_state(app_state);
    let addr = SocketAddr::from(([127,0,0,1], 3000));
    println!("Server started on http://{}", addr);
    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();

}


async fn get_meta(State(app): State<Arc<AppState>>) -> Json<MetaData> {
    Json(app.meta.clone())
}


async fn get_state(State(app): State<Arc<AppState>>) -> Json<GameState>{
    let state = app.state.lock().await;
    Json(state.clone())
}

async fn order_handler(State(app): State<Arc<AppState>>, 
Json(cmd): Json<CommandType>) -> &'static str{
    let mut queue = app.command_queue.lock().await;
    queue.push(cmd);
    "Command received"
}

async fn commit_handler(State(app): State<Arc<AppState>>) -> &'static str{
    let mut state = app.state.lock().await;
    let mut queue = app.command_queue.lock().await;
    let commands = std::mem::take(&mut *queue);

    Engine::run_turn(&mut state, &app.defs, commands);
    "Turn Processed"
}


async fn _tick_handler(app: Arc<AppState>) {
    let mut state = app.state.lock().await;
    let mut queue = app.command_queue.lock().await;
    let commands = std::mem::take(&mut *queue);
    Engine::run_turn(&mut state, &app.defs, commands);
}

/*
async fn commit_handler(app: Arc<AppState>) {
    let mut state = app.state.lock().await;
    let mut queue = app.command_queue.lock().await;
    let commands = std::mem::take(&mut *queue);
    Engine::run_turn(&mut state, &app.defs, commands);
    todo!("Not yet implmented");
}
    */
/*
async fn order_handler(app: Arc<AppState>, cmd: CommandType) {
    let mut queue = app.command_queue.lock().await;
    queue.push(cmd);
    todo!("Not yet implmented");
}
*/
#[tokio::test]
async fn test_tick_handler_advances_turn() {
    let defs = Definitions::default();
    let state = GameState::new(&defs);
    let meta = MetaData::default();
    let command_queue = Mutex::new(Vec::new());
    let app = Arc::new(AppState {
        state: Mutex::new(state),
        defs,
        command_queue,
        meta,
    });
    _tick_handler(app.clone()).await;
    _tick_handler(app.clone()).await;
    let state = app.state.lock().await;
    assert_eq!(state.turn, 2);
}




