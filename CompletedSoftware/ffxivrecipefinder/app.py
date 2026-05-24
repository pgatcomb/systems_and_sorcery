import curses
import csv
import difflib
import json
import os
import requests
import io
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# --- DATA MODELS ---

@dataclass
class Ingredient:
    name: str
    quantity: int

@dataclass
class Recipe:
    name: str
    ingredients: Dict[str, int]  # Map of Item Name -> Quantity Needed
    output_qty: int = 1

# --- LOGIC LAYER ---

class CraftingEngine:
    def __init__(self):
        self.recipe_db: List[Recipe] = []
        self.inventory: Dict[str, int] = {}
        self.known_items: List[str] = []
        self.load_or_fetch_data()

    def load_or_fetch_data(self):
        file_path = "recipes.json"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for r_data in data:
                self.recipe_db.append(Recipe(
                    name=r_data["name"],
                    ingredients=r_data["ingredients"],
                    output_qty=r_data["output_qty"]
                ))
        except Exception as e:
            # Fallback or empty if file is corrupt
            pass

        self.known_items = list(set(
            [k for r in self.recipe_db for k in r.ingredients.keys()]
        ))

        self.load_inventory_from_csv()

    def load_inventory_from_csv(self):
        inventory_file = "user_inventory.csv"
        if not os.path.exists(inventory_file):
            return  # No file, nothing to do

        print(f"Found {inventory_file}, loading inventory...")
        loaded_count = 0
        try:
            with open(inventory_file, "r", encoding="utf-8", newline='') as f:
                # Use DictReader to handle columns by name, assuming headers "item" and "quantity"
                reader = csv.DictReader(f)
                for row in reader:
                    item_name = row.get("item", "").strip()
                    qty_str = row.get("quantity", "").strip()

                    if not item_name or not qty_str:
                        print(f"Warning: Skipping malformed row in {inventory_file}: {row}")
                        continue

                    try:
                        qty = int(qty_str)
                        self.add_to_inventory(item_name, qty)
                        loaded_count += 1
                    except ValueError:
                        print(f"Warning: Invalid quantity for '{item_name}' in {inventory_file}. Skipping.")
            print(f"Loaded {loaded_count} items from inventory file.")
        except Exception as e:
            print(f"Error loading inventory from {inventory_file}: {e}")

    def add_to_inventory(self, item_name: str, qty: int):
        # Fuzzy match to find the closest real item name
        matches = difflib.get_close_matches(item_name, self.known_items, n=1, cutoff=0.4)

        real_name = matches[0] if matches else item_name

        if real_name in self.inventory:
            self.inventory[real_name] += qty
        else:
            self.inventory[real_name] = qty
        return real_name

    def remove_from_inventory(self, item_name: str, qty: int):
        # Fuzzy match to find the closest real item name
        matches = difflib.get_close_matches(item_name, self.known_items, n=1, cutoff=0.4)

        real_name = matches[0] if matches else item_name

        if real_name in self.inventory:
            self.inventory[real_name] -= qty
            if self.inventory[real_name] <= 0:
                del self.inventory[real_name]
        return real_name

    def save_inventory_csv(self):
        inventory_file = "user_inventory.csv"
        try:
            with open(inventory_file, "w", encoding="utf-8", newline='') as f:
                fieldnames = ["item", "quantity"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for item_name, qty in self.inventory.items():
                    writer.writerow({"item": item_name, "quantity": qty})
            print(f"Saved inventory to {inventory_file}.")
        except Exception as e:
            print(f"Error saving inventory to {inventory_file}: {e}")

    def get_recommendations(self) -> List[str]:
        recommendations = []
        
        for recipe in self.recipe_db:
            craftable_count = float('inf')
            
            # Check if we have ingredients
            possible = True
            for ing_name, ing_qty in recipe.ingredients.items():
                if ing_name not in self.inventory:
                    possible = False
                    break
                
                # Calculate how many we can make based on this specific ingredient
                num_can_make = self.inventory[ing_name] // ing_qty
                if num_can_make == 0:
                    possible = False
                    break
                
                if num_can_make < craftable_count:
                    craftable_count = num_can_make
            
            if possible:
                recommendations.append(f"{recipe.name} (x{int(craftable_count)})")
                
        return recommendations

# --- UI LAYER (CURSES) ---

def draw_menu(stdscr, selected_row_idx, menu_items):
    h, w = stdscr.getmaxyx()
    for idx, row in enumerate(menu_items):
        x = w//2 - len(row)//2
        y = h//2 - len(menu_items)//2 + idx
        if idx == selected_row_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, x, row)
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, x, row)
    stdscr.refresh()

def input_screen(stdscr, engine: CraftingEngine):
    curses.echo()
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    stdscr.addstr(2, 2, "--- ADD INVENTORY ---")
    stdscr.addstr(4, 2, "Item Name: ")

    # Get Item Name
    item_name_bytes = stdscr.getstr(4, 13, 20)
    item_name = item_name_bytes.decode('utf-8')

    if not item_name:
        return

    stdscr.addstr(5, 2, "Quantity: ")
    qty_bytes = stdscr.getstr(5, 12, 5)
    try:
        qty = int(qty_bytes.decode('utf-8'))
    except ValueError:
        qty = 0

    # Process logic
    added_name = engine.add_to_inventory(item_name, qty)

    stdscr.addstr(7, 2, f"Added {qty} x {added_name}")
    stdscr.addstr(9, 2, "Press any key to return...")
    curses.noecho()
    stdscr.getch()

def remove_screen(stdscr, engine: CraftingEngine):
    curses.echo()
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    stdscr.addstr(2, 2, "--- REMOVE INVENTORY ---")
    stdscr.addstr(4, 2, "Item Name: ")

    # Get Item Name
    item_name_bytes = stdscr.getstr(4, 13, 20)
    item_name = item_name_bytes.decode('utf-8')

    if not item_name:
        return

    stdscr.addstr(5, 2, "Quantity: ")
    qty_bytes = stdscr.getstr(5, 12, 5)
    try:
        qty = int(qty_bytes.decode('utf-8'))
    except ValueError:
        qty = 0

    # Process logic
    removed_name = engine.remove_from_inventory(item_name, qty)

    stdscr.addstr(7, 2, f"Removed {qty} x {removed_name}")
    stdscr.addstr(9, 2, "Press any key to return...")
    curses.noecho()
    stdscr.getch()

def save_screen(stdscr, engine: CraftingEngine):
    curses.noecho()
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    stdscr.addstr(2, 2, "--- SAVE INVENTORY ---")

    # Process logic
    engine.save_inventory_csv()

    stdscr.addstr(4, 2, "Inventory saved to user_inventory.csv")
    stdscr.addstr(6, 2, "Press any key to return...")
    stdscr.getch()

def results_screen(stdscr, engine: CraftingEngine):
    curses.noecho()
    h, w = stdscr.getmaxyx()
    lines_to_show = h - 6  # Leave room for title, prompt, and margins
    if lines_to_show < 1:
        lines_to_show = 1

    recs = engine.get_recommendations()
    if not recs:
        lines = ["No recipes match your current inventory."]
    else:
        lines = [f"- {rec}" for rec in recs]

    lines.append("")  # Separator
    lines.append("--- CURRENT INVENTORY ---")
    lines.extend([f"{k}: {v}" for k, v in engine.inventory.items()])

    scroll_offset = 0
    while True:
        stdscr.clear()
        stdscr.addstr(1, 2, "--- CRAFTING RECOMMENDATIONS ---", curses.A_BOLD)

        for i in range(lines_to_show):
            if scroll_offset + i < len(lines):
                line = lines[scroll_offset + i]
                stdscr.addstr(3 + i, 2, line[:w-4])  # Truncate to fit width

        prompt_text = "Use up/down to scroll, enter to return to menu"
        stdscr.addstr(h-2, 2, prompt_text[:w-4])

        key = stdscr.getch()
        if key == curses.KEY_UP and scroll_offset > 0:
            scroll_offset -= 1
        elif key == curses.KEY_DOWN and scroll_offset < len(lines) - 1:
            scroll_offset += 1
        elif key in [10, 13]:  # Enter
            break

def main(stdscr, engine):
    # Setup colors
    curses.curs_set(0) # Hide cursor
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE) # Highlight
    
    menu_items = ['Add Inventory', 'View Recommendations', 'Remove Inventory', 'Save Inventory', 'Exit']
    current_row = 0

    while True:
        stdscr.clear()
        draw_menu(stdscr, current_row, menu_items)

        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_items) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            if current_row == 0:
                input_screen(stdscr, engine)
            elif current_row == 1:
                results_screen(stdscr, engine)
            elif current_row == 2:
                remove_screen(stdscr, engine)
            elif current_row == 3:
                save_screen(stdscr, engine)
            elif current_row == 4:
                break

if __name__ == "__main__":
    # Initialize engine first to handle data downloading before UI starts
    engine = CraftingEngine()
    curses.wrapper(main, engine)
