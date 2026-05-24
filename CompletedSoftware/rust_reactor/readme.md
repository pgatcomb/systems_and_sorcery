# Rust Reactor Simulator

A high-fidelity nuclear reactor simulation written in Rust, featuring a grid-based thermal-hydraulic model and a RESTful API for real-time telemetry and control.

## Overview
This project simulates the internal thermodynamics and neutronics of a nuclear reactor core. It utilizes a 2D grid of components and a dual-loop cooling system to model heat generation, moderation, and heat rejection.

The system is split into two main parts:
1.  **Simulation Engine (`lib.rs`)**: A synchronous physics engine that handles the "ticks" of the reactor, calculating flux, temperature deltas, and coolant flow.
2.  **API Server (`main.rs`)**: An asynchronous `axum` web server that provides external access to the simulation state and allows for remote commanding.

## Core Features
- **Grid-Based Core**: Simulates individual components including Fuel Rods (LEU/HEU), Control Rods, Moderators, and Walls.
- **Neutronics Model**: Calculates effective flux based on neighboring moderation and absorption levels.
- **Thermodynamics**: Models heat transfer from fuel to primary coolant, and primary to secondary coolant via heat exchangers.
- **Dynamic Cooling**: Primary and secondary coolant loops with adjustable pump speeds and environmental cooling (including steam modifiers at boiling point).
- **Concurrency**: The simulation runs in a dedicated thread to ensure consistent timing (10Hz), while the API handles requests asynchronously.

## API Reference

The server listens on `http://localhost:3000` by default.

### Endpoints

*   `GET /`: Basic status check.
*   `GET /telemetry`: Returns the current state of the reactor in JSON format.
    - Includes: Tick count, loop temperatures/speeds, and individual component temperatures/positions.
*   `POST /command`: Sends a command to the reactor.

### Command Schema
Commands are sent as JSON objects. Supported commands include:

**SCRAM (Emergency Shutdown)**
```json
{"Scram": null}
```

**Set Control Rod Position**
```json
{
  "SetControlRodPosition": {
    "id": 7, 
    "position": 0.5
  }
}
```
*(Note: Use `"id": null` to target all control rods)*

**Set Pump Speed**
```json
{
  "SetPumpSpeed": {
    "loop_type": "Primary",
    "speed": 0.8
  }
}
```

## Running the Project
Ensure you have the Rust toolchain installed.

```bash
cargo run
```
