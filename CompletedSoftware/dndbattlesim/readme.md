# Dungeons & Dragons Combat Simulator

A high-performance D&D combat simulator written in Rust. This tool allows you to simulate thousands of simplified encounters between two teams of monsters to determine win probabilities and average outcomes.

## Features

*   **Parallel Simulation:** Uses `rayon` for parallel iteration over combatants and teams.
*   **Dice Engine:** Supports standard notation (e.g., `1d20+5`, `2d6-1`) with a robust parser.
*   **Data-Driven:** Load monster statistics from CSV and team compositions from JSON.

## Input Requirements

The simulator requires four command-line arguments:

1.  **Monster Data Path:** Path to a CSV file containing monster templates.
2.  **Team 1 Path:** Path to a JSON file defining the first team.
3.  **Team 2 Path:** Path to a JSON file defining the second team.
4.  **Iterations:** The number of full battles to simulate.

## Data Formats

### Monster CSV Format (`monsters.csv`)
The CSV file must include a header row. The fields are:
`monster_name,hp,ac,attack_bonus,damage,flags`

*   `monster_name`: String (must match names used in Team JSON).
*   `hp`: Integer (Hit Points).
*   `ac`: Integer (Armor Class).
*   `attack_bonus`: Integer added to the 1d20 attack roll.
*   `damage`: String dice notation (e.g., `2d8+4`).
*   `flags`: String for custom identifiers or future mechanics.

**Example:**
```csv
monster_name,hp,ac,attack_bonus,damage,flags
Goblin,7,15,4,1d6+2,goblinoid
Bugbear,27,16,4,2d8+2,goblinoid
```

### Team JSON Format (`team.json`)
Teams are defined by a name and a list of member names that correspond to entries in your CSV.

**Example:**
```json
{
  "team_name": "The Goblin Horde",
  "members": ["Goblin", "Goblin", "Bugbear"]
}
```

## How It Works

1.  **Initialization:** The simulator loads the monster templates into memory.
2.  **Instatiation:** Teams are built by cloning templates into `Combatant` instances.
3.  **Simulation Loop:**
    *   Each battle runs until one team has no living members (`is_any_alive`).
    *   Targeting is randomized among currently alive enemies.
    *   Attack rolls are checked against target AC; successful hits apply rolled damage.
4.  **Reporting:** Once the requested iterations are complete, the software outputs the win rate for each team.

## Development

### Prerequisites
*   Rust (Latest Stable)
*   Cargo

### Testing
To run the internal logic tests and verify the dice parser:
```bash
cargo test
```

## Performance Note
This simulator leverages `rayon` for parallel processing of team status checks and target selection, making it suitable for simulating very large scale battles or millions of iterations efficiently.
