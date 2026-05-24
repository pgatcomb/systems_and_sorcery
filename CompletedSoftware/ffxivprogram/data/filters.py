"""
Filter engine for item filtering
"""
from typing import List, Set, Optional
import config
from models.item import Item
from models.recipe import Recipe
from models.market_data import MarketData

class FilterEngine:
    """Applies filters to item lists"""
    
    def __init__(self):
        self.enabled_jobs = set(config.CRAFTER_JOBS.keys())  # All enabled by default
        self.min_level = config.DEFAULT_MIN_LEVEL
        self.max_level = config.DEFAULT_MAX_LEVEL
        self.min_profit = config.DEFAULT_MIN_PROFIT
        self.min_velocity = config.DEFAULT_MIN_VELOCITY
        self.exclude_no_market_data = True
    
    def set_job_filter(self, job_ids: Set[int]):
        """Set which crafter jobs to include"""
        self.enabled_jobs = job_ids
    
    def set_level_range(self, min_level: int, max_level: int):
        """Set recipe level range"""
        self.min_level = min_level
        self.max_level = max_level
    
    def set_profit_threshold(self, min_profit: float):
        """Set minimum profit threshold"""
        self.min_profit = min_profit
    
    def set_velocity_threshold(self, min_velocity: float):
        """Set minimum sale velocity"""
        self.min_velocity = min_velocity
    
    def passes_filter(self, item: Item, recipe: Recipe, market_data: Optional[MarketData], 
                     profit: float) -> bool:
        """
        Check if an item passes all active filters
        
        Args:
            item: The item to check
            recipe: The recipe for the item
            market_data: Market data for the item (can be None)
            profit: Calculated profit for the item
        
        Returns:
            True if item passes all filters
        """
        # Job filter
        if recipe.job not in self.enabled_jobs:
            return False
        
        # Level filter
        if recipe.level < self.min_level or recipe.level > self.max_level:
            return False
        
        # Market data filter
        if self.exclude_no_market_data and (market_data is None or not market_data.median_price):
            return False
        
        # Profit filter
        if profit < self.min_profit:
            return False
        
        # Velocity filter
        if market_data:
            if market_data.velocity < self.min_velocity:
                return False
        
        return True
    
    def filter_items(self, items: List[Item], recipes: dict, market_data: dict, 
                    profit_data: dict) -> List[Item]:
        """
        Filter a list of items based on current filter settings
        
        Args:
            items: List of items to filter
            recipes: Dict mapping item_id -> Recipe
            market_data: Dict mapping item_id -> MarketData
            profit_data: Dict mapping item_id -> profit value
        
        Returns:
            Filtered list of items
        """
        filtered = []
        
        for item in items:
            # Get associated data
            recipe = recipes.get(item.item_id)
            if not recipe:
                continue
            
            md = market_data.get(item.item_id)
            profit = profit_data.get(item.item_id, 0.0)
            
            # Apply filters
            if self.passes_filter(item, recipe, md, profit):
                filtered.append(item)
        
        return filtered
    
    def get_job_name(self, job_id: int) -> str:
        """Get job abbreviation from job ID"""
        return config.CRAFTER_JOBS.get(job_id, f"Job{job_id}")
    
    def reset_to_defaults(self):
        """Reset all filters to default values"""
        self.enabled_jobs = set(config.CRAFTER_JOBS.keys())
        self.min_level = config.DEFAULT_MIN_LEVEL
        self.max_level = config.DEFAULT_MAX_LEVEL
        self.min_profit = config.DEFAULT_MIN_PROFIT
        self.min_velocity = config.DEFAULT_MIN_VELOCITY
        self.exclude_no_market_data = True
