"""
Teamcraft API client for fetching item and recipe data
"""
import requests
import time
import pandas as pd
from typing import Dict, List, Optional, Tuple
import config
from models.item import Item
from models.recipe import Recipe

class TeamcraftAPI:
    """Client for fetching data from FFXIV Teamcraft"""
    
    def __init__(self):
        self.session = self._create_session()
        self.recipe_level_table = {}
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with headers"""
        s = requests.Session()
        s.headers.update({"User-Agent": "FFXIV-Market-Analyzer/1.0"})
        return s
    
    def _get_json(self, url: str) -> Optional[dict]:
        """Fetch JSON from URL with error handling"""
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[Teamcraft] Error fetching {url}: {e}")
            return None
    
    def load_recipe_level_table(self) -> Dict[int, int]:
        """Load recipe level table (rlvl ID -> actual level mapping)"""
        if self.recipe_level_table:
            return self.recipe_level_table
        
        print("[Teamcraft] Loading recipe level table...")
        data = self._get_json(config.TEAMCRAFT_RECIPE_LEVEL_TABLE_URL) or {}
        
        result = {}
        if isinstance(data, dict):
            for k, v in data.items():
                try:
                    rlvl_id = int(k)
                    # The key itself represents the recipe level
                    # The value contains crafting stats but not the level
                    result[rlvl_id] = rlvl_id
                except Exception:
                    continue
        
        self.recipe_level_table = result
        print(f"[Teamcraft] Loaded {len(result)} recipe level mappings")
        return result
    
    def load_items(self) -> List[Item]:
        """Load all items from Teamcraft"""
        print("[Teamcraft] Loading items...")
        data = self._get_json(config.TEAMCRAFT_ITEMS_URL) or {}
        
        items = []
        for item_id_str, item_data in data.items():
            try:
                item_id = int(item_id_str)
                name = item_data.get('en') or item_data.get('name') or f"Item {item_id}"
                item_level = item_data.get('ilvl', 0)
                can_be_hq = item_data.get('canBeHq', True)
                
                items.append(Item(item_id, name, item_level, can_be_hq))
            except Exception as e:
                continue
        
        print(f"[Teamcraft] Loaded {len(items)} items")
        return items
    
    def load_marketable_ids(self) -> set:
        """Load set of marketable item IDs from Universalis"""
        print("[Teamcraft] Loading marketable items list...")
        # Note: This is actually a Universalis endpoint but we keep it here for convenience
        data = self._get_json(config.UNIVERSALIS_MARKETABLE_URL) or []
        marketable = set(data)
        print(f"[Teamcraft] Loaded {len(marketable)} marketable item IDs")
        return marketable
    
    def load_recipes_per_item(self) -> Dict[int, List[int]]:
        """Load recipe IDs for each item"""
        print("[Teamcraft] Loading recipes-per-item mapping...")
        data = self._get_json(config.TEAMCRAFT_RECIPES_PER_ITEM_URL) or {}
        
        result = {}
        for item_id_str, recipe_ids in data.items():
            try:
                item_id = int(item_id_str)
                if isinstance(recipe_ids, list):
                    result[item_id] = [int(rid) for rid in recipe_ids if isinstance(rid, (int, str))]
            except Exception:
                continue
        
        print(f"[Teamcraft] Loaded recipes for {len(result)} items")
        return result
    
    def load_recipes(self) -> Dict[int, Recipe]:
        """Load all recipes from Teamcraft"""
        print("[Teamcraft] Loading recipes (this may take a moment)...")
        data = self._get_json(config.TEAMCRAFT_RECIPES_URL) or {}
        
        # Load recipe level table first
        rlvl_table = self.load_recipe_level_table()
        
        recipes = {}
        
        # Handle both dict and list formats
        if isinstance(data, dict):
            recipe_items = data.items()
        elif isinstance(data, list):
            recipe_items = [(r.get('id', i), r) for i, r in enumerate(data)]
        else:
            print("[Teamcraft] Unknown recipes data format")
            return recipes
        
        for recipe_id_key, recipe_data in recipe_items:
            try:
                if not isinstance(recipe_data, dict):
                    continue
                
                recipe_id = recipe_data.get('id', recipe_id_key)
                recipe_id = int(recipe_id)
                
                result_item_id = recipe_data.get('result', recipe_data.get('itemId', 0))
                result_item_id = int(result_item_id)
                
                # Get recipe level
                rlvl_raw = recipe_data.get('rlvl', 0)
                level = rlvl_table.get(int(rlvl_raw), int(rlvl_raw)) if rlvl_raw else 0
                
                job = recipe_data.get('job', 0)
                result_amount = recipe_data.get('yields', recipe_data.get('amount', 1))
                
                # Parse ingredients (materials)
                materials = []
                ingredients = recipe_data.get('ingredients', [])
                if isinstance(ingredients, list):
                    for ing in ingredients:
                        if isinstance(ing, dict):
                            ing_id = ing.get('id')
                            ing_amount = ing.get('amount', 1)
                            if ing_id:
                                materials.append([int(ing_id), int(ing_amount)])
                
                # Parse crystals
                crystals = []
                crystal_data = recipe_data.get('crystals', [])
                if isinstance(crystal_data, list):
                    for cryst in crystal_data:
                        if isinstance(cryst, dict):
                            cryst_id = cryst.get('id')
                            cryst_amount = cryst.get('amount', 1)
                            if cryst_id:
                                crystals.append([int(cryst_id), int(cryst_amount)])
                
                recipe = Recipe(
                    recipe_id=recipe_id,
                    result_item_id=result_item_id,
                    level=level,
                    job=job,
                    materials=materials,
                    crystals=crystals,
                    result_amount=result_amount
                )
                
                recipes[recipe_id] = recipe
                
            except Exception as e:
                continue
        
        print(f"[Teamcraft] Loaded {len(recipes)} recipes")
        return recipes
    
    def get_craftable_items(self) -> Tuple[List[Item], Dict[int, Recipe], set]:
        """
        Get all craftable items with their recipes
        Returns: (items_list, recipes_dict, marketable_ids_set)
        """
        # Load all data
        all_items = self.load_items()
        marketable_ids = self.load_marketable_ids()
        recipes_per_item = self.load_recipes_per_item()
        all_recipes = self.load_recipes()
        
        # Filter to craftable, marketable items
        craftable_items = []
        craftable_recipes = {}
        
        # Build a map of result_item_id -> recipe for faster lookup
        recipes_by_result = {}
        for recipe in all_recipes.values():
            recipes_by_result[recipe.result_item_id] = recipe
        
        for item in all_items:
            # Must be marketable and have a recipe
            if item.item_id not in marketable_ids:
                continue
            
            # Check if there's a recipe that produces this item
            if item.item_id in recipes_by_result:
                recipe = recipes_by_result[item.item_id]
                craftable_items.append(item)
                craftable_recipes[item.item_id] = recipe
        
        print(f"[Teamcraft] Found {len(craftable_items)} craftable, marketable items")
        return craftable_items, craftable_recipes, marketable_ids
