use axum::{
    routing::{get, post},
    extract::State,
    Json, Router,serve,
};
//use serde::{Serialize, Deserialize};
use tokio::net::TcpListener;
//use tokio::task;
use std::sync::{Arc, RwLock};
use std::sync::mpsc;
use std::{thread, time};
use rust_reactor::*;

#[tokio::main]
async fn main(){
    //let mut wtr = csv::Writer::from_path("telemetry.csv").expect("Unable to open file");
    //wtr.write_record(["tick", "primary_coolant_temp", "secondary_coolant_temp", "core_temp"]).expect("Unable to write record to file");
    println!("Reactor Simulator Version 0.1");
    let (tx_tel, _rx_tel) = mpsc::channel();  // Telemetry TRANSMIT/RECEIVE channel
    let (tx_cmd, rx_cmd) = mpsc::channel();     //Command TRANSMIT/RECEIVE channel

    
    let telemetry_state = Arc::new(RwLock::new(ReactorTelemetry::default()));   // Set up pointer for our data and a lock so we know when we can safely read it
    let tel_state = telemetry_state.clone();                                         // Safety clone of the telemetry state so we can 'overwrite' it when it's ready for us to look at so our memory is isolated

    let _handle = thread::spawn(move || {
        let mut my_reactor = Reactor::new("Nuclear Reactor".to_string(), 7,7);

        loop {
            if let Ok(cmd) = rx_cmd.try_recv(){
                match cmd {
                    ReactorCommand::Shutdown => break,
                    other => {
                         let _ = my_reactor.handle_commands(other);
                    }
                };

            }
        my_reactor.tick().unwrap();
        let tel = my_reactor.get_telemetry();
        *tel_state.write().unwrap() = tel;
        tx_tel.send(()).unwrap();
        thread::sleep(time::Duration::from_millis(100));
        }

    });

    let app = Router::new()
        .route("/", get(|| async { "Reactor API is running. Use /telemetry or /command." }))
        .route("/telemetry", get(http_get_telemetry))
        .route("/command", post(http_post_command))
        .with_state((telemetry_state.clone(), tx_cmd.clone()));

    let listener = TcpListener::bind("0.0.0.0:3000").await.unwrap();
    println!("Server listening on http://localhost:3000");
    serve(listener, app).await.unwrap();
}

async fn http_get_telemetry(
    State((telemetry_state, _)): State<(Arc<RwLock<ReactorTelemetry>>, mpsc::Sender<ReactorCommand>)>
) -> Json<ReactorTelemetry> {
    let tel = telemetry_state.read().unwrap().clone();
    Json(tel)
}

async fn http_post_command(
    State((_, tx_cmd)): State<(Arc<RwLock<ReactorTelemetry>>, mpsc::Sender<ReactorCommand>)>,
    Json(cmd): Json<ReactorCommand>,
) {
    tx_cmd.send(cmd).unwrap();
}
