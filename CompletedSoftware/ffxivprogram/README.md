# FFXIV Market Profit Analyzer

A comprehensive tool for analyzing Final Fantasy XIV marketboard data to identify profitable crafting opportunities.

## Features

- **Multi-Source Data Integration**: Pulls data from Teamcraft (recipes/items) and Universalis (market prices)
- **Advanced Filtering**: Filter by crafter job, recipe level, profit margins, and sale velocity
- **Profit Calculation**: Recursive material cost calculation with smart "craft vs buy" decisions
- **Filter Presets**: Save and load filter configurations for quick access
- **CSV Export**: Export results and shopping lists to CSV for use in Excel/LibreOffice
- **Shopping List Generator**: Automatically generates material lists for crafting
- **GUI Interface**: Clean, easy-to-use tkinter interface

## Installation

1. Install Python 3.8 or higher

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

```bash
python main.py
```

### First Time Setup

1. **Load Data**: Click "Refresh Data" button to download item and recipe data from Teamcraft and market data from Universalis
   - This may take several minutes on first run
   - Data is cached locally in CSV files to speed up subsequent loads

2. **Configure Filters**: 
   - Select your server (default: Zalera)
   - Adjust crystal price (default: 70 gil)
   - Check/uncheck crafter jobs you want to include
   - Set recipe level range
   - Set minimum profit threshold
   - Set minimum sale velocity

3. **Apply Filters**: Click "Apply Filters" to see filtered results

### Working with Results

- **Sort Results**: Click column headers to sort (sorted by profit by default)
- **View Details**: Click any item to see detailed cost breakdown and market data
- **Export Results**: Click "Export CSV" to save filtered results
- **Shopping List**: Select an item and click "Generate Shopping List" in detail panel

### Filter Presets

Save your favorite filter combinations as presets:

1. Configure your desired filters
2. Click "Save Current as Preset"
3. Enter a name for the preset
4. Use the dropdown and "Load" button to quickly apply saved presets

Default presets included:
- **High Profit All**: High-level items across all crafters with 5k+ profit
- **Quick Turnover**: Items with high sale velocity (5+ per day)
- **Carpenter 90+**: Level 90+ carpenter recipes only
- **Goldsmith 90+**: Level 90+ goldsmith recipes only

## Data Storage

All data is stored in portable CSV format:

- `cache/items_cache.csv` - Item data (refreshes after 7 days)
- `cache/recipes_cache.csv` - Recipe data (refreshes after 7 days)
- `cache/market_data_cache.csv` - Market prices (refreshes after 1 hour)
- `presets/*.json` - Filter presets

## Configuration

Edit `config.py` to customize:

- Default server
- Default crystal price
- Cache expiry times
- API rate limiting delays
- Default filter values
- Window size

## Tips for Best Results

1. **Refresh Market Data Regularly**: Market prices change frequently. Use the "Refresh Data" button to get current prices.

2. **Respect API Limits**: The app includes rate limiting (0.12s between requests) to avoid hitting Universalis API limits.

3. **Start Broad, Then Narrow**: Begin with loose filters to see all opportunities, then refine based on your capabilities.

4. **Check Sale Velocity**: High profit means nothing if items don't sell. Balance profit with velocity.

5. **Export for Analysis**: Use CSV export to analyze trends in Excel/LibreOffice over time.

## Project Structure

```
ffxivprogarm/
├── main.py                 # Application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Dependencies
├── README.md             # This file
│
├── models/               # Data models
│   ├── item.py
│   ├── recipe.py
│   └── market_data.py
│
├── api/                  # API clients
│   ├── teamcraft.py     # Teamcraft data fetching
│   ├── universalis.py   # Universalis market data
│   └── cache.py         # CSV caching layer
│
├── data/                # Data processing
│   ├── processor.py    # Profit calculations
│   └── filters.py      # Filter engine
│
├── storage/            # Storage utilities
│   ├── presets.py     # Filter preset management
│   └── export.py      # CSV export
│
├── gui/               # GUI components
│   └── main_window.py # Main application window
│
├── cache/            # Cached data (auto-generated)
└── presets/          # Filter presets (auto-generated)
```

## Known Limitations

- Market data fetching can take time due to API rate limits (avoid exceeding ~8 requests/second)
- Recipe data is based on Teamcraft's public data repository
- Material cost calculations assume you craft or buy at market price (doesn't account for gathering)
- Crystal costs are estimated using a configurable flat rate

## Troubleshooting

**"No items to display"**: Click "Refresh Data" to load data first

**"Failed to load data"**: Check internet connection; Teamcraft/Universalis APIs may be temporarily unavailable

**Slow initial load**: First run downloads all item/recipe data; subsequent runs use cached data

**"No market data"**: Some items may not have active market listings; adjust filters to exclude items without market data

## Credits

- Data provided by [FFXIV Teamcraft](https://ffxivteamcraft.com/)
- Market data from [Universalis](https://universalis.app/)
- Built with Python and tkinter

## License

This tool is for personal use. Please respect the terms of service for Teamcraft and Universalis APIs.
