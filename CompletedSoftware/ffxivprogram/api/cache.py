"""
CSV-based cache manager for API responses
"""
import os
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict
import config

class CacheManager:
    """Manages CSV-based caching for items, recipes, and market data"""
    
    def __init__(self):
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        os.makedirs(config.CACHE_DIR, exist_ok=True)
    
    def _is_cache_valid(self, filepath, max_age_seconds):
        """Check if cache file exists and is not stale"""
        if not os.path.exists(filepath):
            return False
        
        file_age = datetime.now().timestamp() - os.path.getmtime(filepath)
        return file_age < max_age_seconds
    
    # Item Cache Methods
    def load_items_cache(self) -> Optional[pd.DataFrame]:
        """Load items from cache if valid"""
        if self._is_cache_valid(config.ITEMS_CACHE, config.STATIC_DATA_EXPIRY):
            try:
                df = pd.read_csv(config.ITEMS_CACHE)
                print(f"[Cache] Loaded {len(df)} items from cache")
                return df
            except Exception as e:
                print(f"[Cache] Failed to load items cache: {e}")
        return None
    
    def save_items_cache(self, items_df: pd.DataFrame):
        """Save items to cache"""
        try:
            items_df.to_csv(config.ITEMS_CACHE, index=False)
            print(f"[Cache] Saved {len(items_df)} items to cache")
        except Exception as e:
            print(f"[Cache] Failed to save items cache: {e}")
    
    # Recipe Cache Methods
    def load_recipes_cache(self) -> Optional[pd.DataFrame]:
        """Load recipes from cache if valid"""
        if self._is_cache_valid(config.RECIPES_CACHE, config.STATIC_DATA_EXPIRY):
            try:
                df = pd.read_csv(config.RECIPES_CACHE)
                print(f"[Cache] Loaded {len(df)} recipes from cache")
                return df
            except Exception as e:
                print(f"[Cache] Failed to load recipes cache: {e}")
        return None
    
    def save_recipes_cache(self, recipes_df: pd.DataFrame):
        """Save recipes to cache"""
        try:
            recipes_df.to_csv(config.RECIPES_CACHE, index=False)
            print(f"[Cache] Saved {len(recipes_df)} recipes to cache")
        except Exception as e:
            print(f"[Cache] Failed to save recipes cache: {e}")
    
    # Market Data Cache Methods
    def load_market_data_cache(self, server: str) -> Optional[pd.DataFrame]:
        """Load market data from cache if valid"""
        if self._is_cache_valid(config.MARKET_DATA_CACHE, config.MARKET_DATA_EXPIRY):
            try:
                df = pd.read_csv(config.MARKET_DATA_CACHE)
                # Filter by server
                df = df[df['server'] == server]
                
                # Check if data is still fresh
                if not df.empty and 'last_updated' in df.columns:
                    df['last_updated'] = pd.to_datetime(df['last_updated'])
                    now = datetime.now()
                    df['age_seconds'] = (now - df['last_updated']).dt.total_seconds()
                    df = df[df['age_seconds'] < config.MARKET_DATA_EXPIRY]
                    df = df.drop('age_seconds', axis=1)
                
                if not df.empty:
                    print(f"[Cache] Loaded {len(df)} market data entries for {server}")
                    return df
            except Exception as e:
                print(f"[Cache] Failed to load market data cache: {e}")
        return None
    
    def save_market_data_cache(self, market_data_df: pd.DataFrame, server: str):
        """Save market data to cache, merging with existing data"""
        try:
            # Load existing cache
            existing_df = None
            if os.path.exists(config.MARKET_DATA_CACHE):
                try:
                    existing_df = pd.read_csv(config.MARKET_DATA_CACHE)
                except Exception:
                    pass
            
            # Remove old data for this server
            if existing_df is not None and not existing_df.empty:
                existing_df = existing_df[existing_df['server'] != server]
                # Combine with new data
                combined_df = pd.concat([existing_df, market_data_df], ignore_index=True)
            else:
                combined_df = market_data_df
            
            # Save combined data
            combined_df.to_csv(config.MARKET_DATA_CACHE, index=False)
            print(f"[Cache] Saved {len(market_data_df)} market data entries for {server}")
        except Exception as e:
            print(f"[Cache] Failed to save market data cache: {e}")
    
    def get_cached_market_data_for_item(self, item_id: int, server: str) -> Optional[Dict]:
        """Get cached market data for a specific item"""
        try:
            if not os.path.exists(config.MARKET_DATA_CACHE):
                return None
            
            df = pd.read_csv(config.MARKET_DATA_CACHE)
            df = df[(df['item_id'] == item_id) & (df['server'] == server)]
            
            if df.empty:
                return None
            
            # Check if data is fresh
            row = df.iloc[0]
            last_updated = pd.to_datetime(row['last_updated'])
            age_seconds = (datetime.now() - last_updated).total_seconds()
            
            if age_seconds < config.MARKET_DATA_EXPIRY:
                return row.to_dict()
            
        except Exception as e:
            print(f"[Cache] Error getting cached market data for item {item_id}: {e}")
        
        return None
    
    def clear_all_caches(self):
        """Clear all cache files"""
        for cache_file in [config.ITEMS_CACHE, config.RECIPES_CACHE, config.MARKET_DATA_CACHE]:
            try:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    print(f"[Cache] Cleared {cache_file}")
            except Exception as e:
                print(f"[Cache] Failed to clear {cache_file}: {e}")
