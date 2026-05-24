"""
Data processor for calculating profits and costs
"""
from typing import Dict, List, Optional, Tuple
import config
from models.item import Item
from models.recipe import Recipe
from models.market_data import MarketData

class DataProcessor:
    """Processes item data to calculate crafting costs and profits"""
    
    def __init__(self, items: Dict[int, Item], recipes: Dict[int, Recipe], 
                 market_data: Dict[int, MarketData], crystal_price: float = config.DEFAULT_CRYSTAL_PRICE):
        self.items = items
        self.recipes = recipes
        self.market_data = market_data
        self.crystal_price = crystal_price
        self._cost_cache = {}  # Cache for calculated material costs
    
    def get_crystal_cost(self, recipe: Recipe) -> float:
        """Calculate total crystal cost for a recipe"""
        total_crystals = sum(qty for crystal_id, qty in recipe.crystals)
        return total_crystals * self.crystal_price
    
    def get_material_cost(self, item_id: int, quantity: int = 1, depth: int = 0) -> float:
        """
        Recursively calculate material cost for an item
        
        Args:
            item_id: The item to calculate cost for
            quantity: How many of this item are needed
            depth: Recursion depth (to prevent infinite loops)
        
        Returns:
            Total cost in gil for the materials
        """
        # Prevent infinite recursion
        if depth > 10:
            return 0.0
        
        # Check cache
        cache_key = (item_id, quantity)
        if cache_key in self._cost_cache:
            return self._cost_cache[cache_key]
        
        # Get market price for this item
        market_price = None
        if item_id in self.market_data:
            md = self.market_data[item_id]
            market_price = md.min_listing or md.median_price
        
        # If item has no recipe, use market price
        if item_id not in self.recipes:
            cost = market_price * quantity if market_price else 0.0
            self._cost_cache[cache_key] = cost
            return cost
        
        recipe = self.recipes[item_id]
        
        # Calculate cost of crafting
        crafting_cost = 0.0
        
        # Add material costs (recursive)
        for mat_id, mat_qty in recipe.materials:
            mat_cost = self.get_material_cost(mat_id, mat_qty, depth + 1)
            crafting_cost += mat_cost
        
        # Add crystal cost
        crafting_cost += self.get_crystal_cost(recipe)
        
        # Adjust for recipe yield
        if recipe.result_amount > 1:
            crafting_cost = crafting_cost / recipe.result_amount
        
        # Choose cheaper option: craft or buy from market
        if market_price is not None:
            cost = min(crafting_cost, market_price) * quantity
        else:
            cost = crafting_cost * quantity
        
        self._cost_cache[cache_key] = cost
        return cost
    
    def calculate_profit(self, item_id: int) -> Tuple[float, float, float, float]:
        """
        Calculate profit metrics for an item
        
        Returns:
            (sale_price, material_cost, crystal_cost, profit)
        """
        # Get sale price
        sale_price = 0.0
        if item_id in self.market_data:
            md = self.market_data[item_id]
            sale_price = md.median_price or 0.0
        
        if sale_price == 0:
            return 0.0, 0.0, 0.0, 0.0
        
        # Get recipe
        if item_id not in self.recipes:
            return sale_price, 0.0, 0.0, 0.0
        
        recipe = self.recipes[item_id]
        
        # Calculate material cost
        material_cost = 0.0
        for mat_id, mat_qty in recipe.materials:
            mat_cost = self.get_material_cost(mat_id, mat_qty)
            material_cost += mat_cost
        
        # Calculate crystal cost
        crystal_cost = self.get_crystal_cost(recipe)
        
        # Adjust for recipe yield
        if recipe.result_amount > 1:
            material_cost = material_cost / recipe.result_amount
            crystal_cost = crystal_cost / recipe.result_amount
        
        # Calculate profit
        total_cost = material_cost + crystal_cost
        profit = sale_price - total_cost
        
        return sale_price, material_cost, crystal_cost, profit
    
    def get_roi_percentage(self, item_id: int) -> float:
        """Calculate ROI percentage for an item"""
        sale_price, material_cost, crystal_cost, profit = self.calculate_profit(item_id)
        total_cost = material_cost + crystal_cost
        
        if total_cost == 0:
            return 0.0
        
        return (profit / total_cost) * 100.0
    
    def get_shopping_list(self, item_id: int, quantity: int = 1) -> List[Tuple[int, str, int, float]]:
        """
        Generate shopping list for crafting an item
        
        Returns:
            List of (item_id, item_name, quantity_needed, cost_per_unit)
        """
        shopping_list = {}
        
        def collect_materials(item_id: int, qty: int, depth: int = 0):
            """Recursively collect materials needed"""
            if depth > 10:
                return
            
            # If item has no recipe, add to shopping list
            if item_id not in self.recipes:
                if item_id not in shopping_list:
                    shopping_list[item_id] = 0
                shopping_list[item_id] += qty
                return
            
            recipe = self.recipes[item_id]
            
            # Get market price for this item
            market_price = None
            crafting_cost = 0.0
            
            if item_id in self.market_data:
                md = self.market_data[item_id]
                market_price = md.min_listing or md.median_price
            
            # Calculate crafting cost
            for mat_id, mat_qty in recipe.materials:
                mat_cost = self.get_material_cost(mat_id, mat_qty)
                crafting_cost += mat_cost
            crafting_cost += self.get_crystal_cost(recipe)
            
            # If buying is cheaper than crafting, add to shopping list
            if market_price and market_price < crafting_cost:
                if item_id not in shopping_list:
                    shopping_list[item_id] = 0
                shopping_list[item_id] += qty
            else:
                # Otherwise, get materials for crafting
                for mat_id, mat_qty in recipe.materials:
                    collect_materials(mat_id, mat_qty * qty, depth + 1)
        
        collect_materials(item_id, quantity)
        
        # Convert to list with item names and prices
        result = []
        for mat_id, mat_qty in shopping_list.items():
            item_name = self.items[mat_id].name if mat_id in self.items else f"Item {mat_id}"
            
            cost_per_unit = 0.0
            if mat_id in self.market_data:
                md = self.market_data[mat_id]
                cost_per_unit = md.min_listing or md.median_price or 0.0
            
            result.append((mat_id, item_name, mat_qty, cost_per_unit))
        
        # Sort by item name
        result.sort(key=lambda x: x[1])
        return result
    
    def clear_cache(self):
        """Clear the material cost cache"""
        self._cost_cache.clear()
