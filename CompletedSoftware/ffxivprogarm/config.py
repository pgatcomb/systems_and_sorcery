"""
Configuration constants for FFXIV Market Profit Analyzer
"""

# API Endpoints
TEAMCRAFT_ITEMS_URL = "https://raw.githubusercontent.com/ffxiv-teamcraft/ffxiv-teamcraft/staging/libs/data/src/lib/json/items.json"
TEAMCRAFT_RECIPES_URL = "https://raw.githubusercontent.com/ffxiv-teamcraft/ffxiv-teamcraft/staging/libs/data/src/lib/json/recipes.json"
TEAMCRAFT_RECIPES_PER_ITEM_URL = "https://raw.githubusercontent.com/ffxiv-teamcraft/ffxiv-teamcraft/staging/libs/data/src/lib/json/recipes-per-item.json"
TEAMCRAFT_RECIPE_LEVEL_TABLE_URL = "https://raw.githubusercontent.com/ffxiv-teamcraft/ffxiv-teamcraft/staging/libs/data/src/lib/json/recipe-level-table.json"

UNIVERSALIS_MARKETABLE_URL = "https://universalis.app/api/v2/marketable"
UNIVERSALIS_AGG_URL = "https://universalis.app/api/v2/aggregated/{dc}/{item}"
UNIVERSALIS_CURR_URL = "https://universalis.app/api/v2/{dc}/{item}?listings=40"

# Cache settings (CSV-based)
CACHE_DIR = "cache"
ITEMS_CACHE = "cache/items_cache.csv"
RECIPES_CACHE = "cache/recipes_cache.csv"
MARKET_DATA_CACHE = "cache/market_data_cache.csv"

# Cache expiry (in seconds)
STATIC_DATA_EXPIRY = 7 * 24 * 60 * 60  # 7 days for items/recipes
MARKET_DATA_EXPIRY = 60 * 60  # 1 hour for market data

# API rate limiting
REQUEST_TIMEOUT = 25
API_DELAY = 0.12  # seconds between requests

# Default settings
DEFAULT_SERVER = "Zalera"
DEFAULT_CRYSTAL_PRICE = 70.0
DEFAULT_CRYSTALS_PER_CRAFT = 5.0

# Crafter job codes (Teamcraft numeric IDs)
CRAFTER_JOBS = {
    8: "CRP",   # Carpenter
    9: "BSM",   # Blacksmith
    10: "ARM",  # Armorer
    11: "GSM",  # Goldsmith
    12: "LTW",  # Leatherworker
    13: "WVR",  # Weaver
    14: "ALC",  # Alchemist
    15: "CUL"   # Culinarian
}

# Filter defaults
DEFAULT_MIN_LEVEL = 1
DEFAULT_MAX_LEVEL = 100
DEFAULT_MIN_PROFIT = 1000
DEFAULT_MIN_VELOCITY = 0.5

# GUI settings
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800
RESULTS_REFRESH_BATCH = 50  # Update GUI every N items during data fetch

# Presets directory
PRESETS_DIR = "presets"
