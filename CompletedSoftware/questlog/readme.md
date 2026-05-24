# Quest Log for TTRPGs

A simple, Streamlit-based quest tracking application designed for tabletop RPG players. This tool allows players to manage their quest progression through a clean, tabbed interface without requiring a dedicated Game Master interface.

## Features

- **Tabbed Interface**: Easily switch between **Active**, **Available**, and **Completed** quests.
- **Dynamic Availability**: Quests only appear in the "Available" tab once their prerequisites (specified by quest ID) are marked as "Completed".
- **Rich Quest Details**: View quest descriptions, quest givers, and difficulty levels.
- **Color-Coded Difficulty**: Difficulty levels (Trivial, Easy, Normal, Hard, Impossible) are visually distinct.
- **Reward Parsing**: Automatically formats complex reward strings (e.g., `credits:50|salvage:5`) into readable lists.
- **Sorting**: Organize quest lists by Name, Provider (Quest Giver), Type, or Difficulty rank.
- **Persistent Storage**: All progress is saved directly back to a `quests.csv` file.

## Installation

### Prerequisites

- Python 3.8+
- Streamlit
- Pandas

### Setup

1. Install the required dependencies:
   ```bash
   pip install streamlit pandas
   ```
2. Ensure `quests.csv` is in the same directory as `questlog.py`.

## Usage

Run the application using Streamlit:

```bash
streamlit run questlog.py
```

## Data Format (`quests.csv`)

The application reads from and writes to `quests.csv`. The file must contain the following columns:

| Column | Description |
| :--- | :--- |
| `id` | Unique identifier for the quest (used for prerequisites). |
| `name` | The title of the quest. |
| `description` | A detailed summary of the task. |
| `type` | Categorization (e.g., Main, Side, Faction). |
| `prereq` | The `id` of a quest that must be completed first. |
| `status` | Current state: `Available`, `Active`, or `Completed`. |
| `rewards` | Pipe-separated rewards with counts (e.g., `credits:100\|item:1`). |
| `quest_giver` | The NPC or entity providing the quest. |
| `difficulty` | Scaling: `trivial`, `easy`, `normal`, `hard`, `impossible`. |

### Reward Formatting Note
Rewards should be formatted as `Item Name:Quantity` and separated by a pipe `|`. 
*Example:* `Gold:100|Healing Potion:2`

## License
This project is open-source and intended for personal TTRPG use.
