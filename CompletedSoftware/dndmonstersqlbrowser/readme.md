# Monster Data SQL Browser

A specialized tool for executing SQLite queries against a comprehensive Dungeons & Dragons monster dataset. This application provides a lightweight interface for dungeon masters and developers to filter, analyze, and extract monster statistics using standard SQL syntax.

## Features

- **Full SQL Support**: Execute complex queries using standard SQLite syntax (SELECT, JOIN, WHERE, GROUP BY).
- **Statistical Analysis**: Easily calculate averages, find outliers, or group monsters by Challenge Rating (CR) and type.
- **Data Compatibility**: Integrated with the standardized monster data formats used throughout the tabletop software suite.

## Database Schema

The core data is stored in the `monsters` table with the following schema:

| Column | Type | Description |
| :--- | :--- | :--- |
| `monster_name` | TEXT | The unique name of the creature. |
| `hp` | INTEGER | Base Hit Points. |
| `ac` | INTEGER | Armor Class. |
| `attack_bonus` | INTEGER | Primary attack to-hit modifier. |
| `damage` | TEXT | Damage dice notation (e.g., "2d6+4"). |
| `challenge_rating` | REAL | The Challenge Rating (CR) for encounter scaling. |
| `flags` | TEXT | Semicolon or comma-separated traits (e.g., "undead;resistant_fire"). |

## Usage Examples

### Filter for Glass Cannons
Find high-CR monsters with high attack bonuses but low Hit Points:
```sql
SELECT monster_name, hp, attack_bonus, challenge_rating 
FROM monsters 
WHERE challenge_rating >= 10 AND hp < 100 
ORDER BY attack_bonus DESC;
```

### HP Benchmarking
Calculate the average Hit Points for every Challenge Rating:
```sql
SELECT challenge_rating, AVG(hp) as avg_hp 
FROM monsters 
GROUP BY challenge_rating 
ORDER BY challenge_rating ASC;
```

## Technical Requirements

- Python 3.8+
- SQLite3 compatible database engine
