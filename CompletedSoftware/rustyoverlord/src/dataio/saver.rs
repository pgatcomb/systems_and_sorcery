use serde_json;
use crate::sim::gamestate::GameState;
use std::path::PathBuf;

pub fn save_game_state_to_json(base_path: &PathBuf, state: &GameState) {
    use std::fs;

    fs::create_dir_all(base_path)
        .expect("Failed to create save directory");

    let path = base_path.join("save.json");

    let json = serde_json::to_string_pretty(state)
        .expect("Failed to serialize game state");

    fs::write(path, json)
        .expect("Failed to write game state file");
}
