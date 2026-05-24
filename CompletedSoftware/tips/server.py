# Server File for TIP version 7:00:00 5/2/2026

from pydantic import BaseModel, field_validator, Field
import csv
from typing import Any
from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
import secrets
import random
from math import log10
from pathlib import Path
import tomllib
from datetime import datetime
from escpos.printer import Win32Raw
CURRENCY_UNIT = "Cr"

tprinter = Win32Raw("Generic / Text Only")
ITEMS_FILENAME = 'items.tsv'
STORE_DIRECTORY = "stores"

class StockItem(BaseModel):
    """
    This item represents an available item for sale at a given store. It is a basemodel
    for protection of loading of the store class later.
    """
    item_name:str
    description:str
    stock:int
    price:float

    def adjust_stock(self, amount:int):
        self.stock = max(0, self.stock + amount)

class Store(BaseModel):
    id:int
    name:str
    max_rarity:int
    price_multiplier:float
    flags:list[str]
    taxes: float = Field(default_factory=float, init=False)
    inventory: dict[str, StockItem] = Field(default_factory=dict, init=False)

    def model_post_init(self, __context):
        self.taxes = self.calculate_taxes()

    # Most common condition is an item with a rarity of 0 (common) through 3 (very rare)
    def calculate_stock_available(self, item_price, item_rarity):
        item_price = max(1, item_price)

        if item_rarity < 4:
            price_tier = int(log10(item_price))
            match price_tier:
                case 0:  # 1–9
                    base = random.randint(5, 15)
                case 1:  # 10–99
                    base = random.randint(3, 12)
                case 2:  # 100–999
                    base = random.randint(2, 8)
                case 3:  # 1,000–9,999
                    base = random.randint(1, 4)
                case 4:  # 10,000–99,999
                    base = random.randint(1, 5)
                case _:
                    return 1

            return max(1, base - item_rarity)

        elif item_rarity == 4:  # Exotic
            return 2 if random.randint(1, 10) == 1 else 1

        else:  # Legendary / Mythic
            return 1

    def generate_stock(self, item_registry):
        # When generating, we're just going start with an empty store
        self.inventory.clear()
        rarity_penalty = {0 : 0.1, 1 : 0.3, 2 : 0.7, 3 : 0.9, 4: 0.98, 5 : 0.99, 6 : 0.995}
        items_added_to_store = 0
        total_items_in_store = 0
        self.inventory = {}
        for item in item_registry.items.keys():
            name = item
            description = item_registry.items[item].description
            #category = item_registry.items[item].category
            if "free_items" not in self.flags:
                base_cost = item_registry.items[item].base_cost * self.price_multiplier
                # Variable prices simply means each item has a range between 75-125% of the cost
                if "variable_prices" in self.flags:
                    base_cost *= (random.randrange(75,125) * 0.01)
                base_cost = round(base_cost)
            else:
                base_cost = 0
            rarity = item_registry.items[item].rarity
            tags = item_registry.items[item].tags
            #game_system = item_registry.items[item].game_system

            # Most common case for most games, unlimited stock and all items
            if "unlimited_stock" in self.flags and "all_items_available" in self.flags:
                stock_item_details = {"item_name" : name, "description" : description, "stock" : 999, "price" : base_cost}
                self.inventory[name] = StockItem(**stock_item_details)
                items_added_to_store += 1
                total_items_in_store += 999
            # We have everything _but_ we don't have unlimited quantity
            elif "all_items_available" in self.flags:
                stock = self.calculate_stock_available(base_cost, rarity)
                stock_item_details = {"item_name" : name, "description" : description, "stock" : stock, "price" : base_cost}
                self.inventory[name] = StockItem(**stock_item_details)
                items_added_to_store += 1
                total_items_in_store += stock
            # This store type has stock and items based on 'luck'
            else:
                # If we 'can' sell it based on rarity
                if rarity <= self.max_rarity:
                    if random.random() >= rarity_penalty[rarity]:
                        stock = self.calculate_stock_available(base_cost, rarity)
                        stock_item_details = {"item_name" : name, "description" : description, "stock" : stock, "price" : base_cost}
                        self.inventory[name] = StockItem(**stock_item_details)
                        items_added_to_store += 1
                        total_items_in_store += stock
               
        print(f"Added {items_added_to_store} for a total stock of {total_items_in_store}")

    def jitter_stock(self, item_registry):
        """When the flag 'volatile_stock' is set, we need to jumble the stock of items"""
        for item in self.inventory:
            real_item = item_registry.items[item]
            real_rarity = real_item.rarity
            real_cost = real_item.base_cost
            new_stock = self.calculate_stock_available(real_cost, real_rarity)
            self.inventory[item].stock = new_stock

    def get_current_price(self, item_name):
        if item_name in self.inventory:
            return self.inventory[item_name].price
        else:
            return -1
        
    def get_current_stock(self, item_name):
        if item_name in self.inventory:
            return self.inventory[item_name].stock
        else:
            return -1
        
    def calculate_taxes(self):
        tax = 0.0
        if "low_tax" in self.flags: 
            tax += 0.01
        if "med_tax" in self.flags: 
            tax += 0.10
        if "high_tax" in self.flags: 
            tax += 0.20
        return tax

    def checkout(self, cart):
        """
        Iterate through each item in the cart
        cost of each item is item count * item price (get from the StockItem)
        subtotal is the cost of all items added
        apply any taxes/fees based on flags for the store
        return if the operation was successful along with the totals
        Later, if the appropriate fields are set in the client, the printer will be triggered
        """
        pass

class Cart:
    """
    Cart class.  This holds the users cart and consists of CartItems

    """
    def __init__(self):
        self.cart_id = secrets.randbits(24)
        self.contents = {}

    def add_item(self, item):
        if item.name not in self.contents:
            self.contents[item.name] = item

    def remove_item(self, item_name: str):
        if item_name in self.contents:
            self.contents.pop(item_name)
    
    def adjust_quantity(self, item, qty):
        if item in self.contents:
            self.contents[item].quantity += qty

    def calculate_subtotal(self):
        subtotal = 0
        for item in self.contents:
            subtotal += round(self.contents[item].line_cost, 2)
        return subtotal
    
    def calculate_taxes(self, tax_percent):
        return round(self.calculate_subtotal() * tax_percent, 2)

    def calculate_total(self, tax_percent):
        return round(self.calculate_subtotal() + self.calculate_taxes(tax_percent), 2)


class CartItem:
    """This represents an item in the cart"""
    def __init__(self, name:str, price:float, quantity:int):
        self.name = name
        self.price = price
        self.quantity = quantity
        self.calculate_line_cost()

    def calculate_line_cost(self):
        return self.price * self.quantity
    
   
    """Quick helper so that the line can be quickly calculated"""
    @property
    def line_cost(self):
        return self.calculate_line_cost()
    
    def adjust_quantity(self, amount):
        # case one: We are adding more
        if amount > 0:
            self.quantity += amount
        # case two: We are subtracting some.
        elif amount < 0 and (abs(amount) < self.quantity):
            self.quantity -= abs(amount)  # Making sure we are subtracting a positive number!
        # case three: We are subtracting some so hard we get a negative number!
        else:
            self.quantity = 0
        
    
class Item(BaseModel):
    name: str
    description: str
    category: str
    base_cost: float
    rarity: int
    tags: list[str]
    game_system: str
    metadata: dict[str, Any]

    @field_validator('metadata', mode='before')
    @classmethod
    def parse_metadata(cls, v: Any) -> Any:
        if isinstance(v, str):
            if not v.strip(): 
                return {} # Handle empty metadata columns gracefully
                
            parsed_meta = {}
            try:
                for pair in v.split(";"):
                    if ":" in pair:
                        # Split on the FIRST colon only
                        key, val = pair.split(":", 1)
                        key, val = key.strip(), val.strip()
                        
                        # Sneaky type-casting: if it looks like an int, make it an int
                        # This makes your Use Boxes and encumbrance math MUCH easier later
                        parsed_meta[key] = int(val) if val.isdigit() else val
                        
                return parsed_meta
            except Exception as e:
                raise ValueError(f"Failed to parse metadata string '{v}': {e}")
        return v

    @field_validator('tags', mode='before')
    @classmethod
    def parse_tags(cls, v: Any) -> Any:
        if isinstance(v, str):
            # Let Pydantic handle the string-to-list splitting too!
            return [t.strip() for t in v.split(",") if t.strip()]
        return v

class ItemRegistry:
    def __init__(self):
        self.items: dict[str, Item] = {}

    def load_items_from_tsv(self, filename: str):
        loaded_items = 0
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file, delimiter='\t')
                for row in reader:
                    # We massage the keys to match the Pydantic model names
                    data = {
                        'name': row['item_name'],
                        'description': row['description'],
                        'category': row['category'],
                        'base_cost': row['cost'],
                        'rarity': row['rarity'],
                        'tags': row['tags'], 
                        'game_system': row['system'],
                        'metadata': row['metadata']
                    }
                    item = Item(**data)
                    self.items[item.name] = item
                    loaded_items += 1
            print(f"{loaded_items} items loaded.")
            
        except FileNotFoundError:
            print(f"CRITICAL: File not found: {filename}")
        except Exception as e:
            print(f"CRITICAL: An error occurred while loading items: {e}")

    def get(self, itemname: str):
        # Using .get() prevents KeyError if the item doesn't exist
        return self.items.get(itemname)

    def search(self, searchstring: str):
        pass

def run_tests():
    example_meta = "damage:1d6;range:close;enc:1"
    example_item = {
        "name": "short sword", 
        "description": "A pointy Sword", 
        "category": "weapon", 
        "base_cost": 20, 
        "rarity": 0, 
        "tags": "melee, pointy", # Testing string to list conversion 
        "game_system": "SWN Revised", 
        "metadata": example_meta
    }
    sword = Item(**example_item)
    assert sword.name == "short sword"
    assert sword.description == "A pointy Sword"
    assert sword.base_cost == 20.0
    assert sword.rarity == 0
    assert sword.tags == ["melee", "pointy"]
    assert sword.metadata == {'damage': '1d6', 'range': 'close', 'enc': 1} 
    test_stock_item_details = {"item_name" : "chair", "description" : "cool", "stock" : 15, "price" : 12.50}
    test_stock_item = StockItem(**test_stock_item_details)
    test_stock_item.adjust_stock(10)
    assert test_stock_item.stock == 25
    test_stock_item.adjust_stock(-99)
    assert test_stock_item.stock == 0

    test_store_details = {"id": 999, "name" : "Test Store", "max_rarity" : 6, "price_multiplier" : 1.0, "flags" : ["unlimited_stock", "all_items_available"]}
    test_store = Store(**test_store_details)
    test_store.generate_stock(registry)
    assert test_store.id == 999
    assert test_store.name == "Test Store"
    assert test_store.max_rarity == 6
    assert test_store.price_multiplier == 1.0
    assert "unlimited_stock" in test_store.flags
    assert test_store.taxes == 0
    assert len(test_store.inventory.items()) > 0
    test_store.flags = ["all_items_available", "variable_prices"]
    test_store.generate_stock(registry)
    assert len(test_store.inventory.items()) > 0
    test_store.flags = ["free_items"]
    test_store.generate_stock(registry)
    assert len(test_store.inventory.items()) > 0
    test_store.jitter_stock(registry)

    test_cart_item = CartItem("Test Item", 1.50, 1)
    assert test_cart_item.line_cost == 1.50
    test_cart_item.adjust_quantity(10)
    assert test_cart_item.quantity == 11
    test_cart_item.adjust_quantity(-10)
    assert test_cart_item.quantity == 1
    test_cart_item.adjust_quantity(-99)
    assert test_cart_item.quantity == 0

    test_cart = Cart()
    assert test_cart.cart_id > 0

    test_cart_item.quantity = 1
    test_cart.add_item(test_cart_item)
    assert test_cart.contents[test_cart_item.name].quantity==1
    test_cart.adjust_quantity(test_cart_item.name, 3)
    assert test_cart.contents[test_cart_item.name].quantity == 4

    assert test_cart.calculate_subtotal() == 6.0
    assert test_cart.calculate_taxes(0.1) == 0.6
    assert test_cart.calculate_taxes(0.0) == 0.0
    assert test_cart.calculate_total(0.1) == 6.6

    store_manager.get_all_stores()

    test_session_id = 9876543
    test_session_manager = SessionManager()
    test_session_manager.create_session("Tester", test_session_id)
    test_session_manager.set_active_store(test_session_id, test_store)
    test_session_manager.get_cart(test_session_id).add_item(test_cart_item)

    return True

class StoreManager:
    total_stores = 0
    def __init__(self):
        self.stores: dict[int, Store] = {}

    def load_stores(self, item_registry: ItemRegistry):
        # Scan the /stores/ directory for TOML files. Open them up and use this to populate
        # The stores list
        store_path = Path.cwd() / STORE_DIRECTORY
        for toml_file in store_path.glob("*.toml"):
            store_id = StoreManager.total_stores

            with toml_file.open("rb") as f:
                data = tomllib.load(f)

            store = Store(
                id=store_id,
                name=data["name"],
                max_rarity=data["max_rarity"],
                price_multiplier=data["price_multiplier"],
                flags=data.get("flags", [])
            )

            self.stores[store_id] = store
            store.generate_stock(item_registry)

            StoreManager.total_stores += 1

        print(f"Loaded {StoreManager.total_stores} stores from \\stores directory.")

    def remove_store(self, id):
        if id in self.stores:
            self.stores.po(id)
            print(f"Removed store {id}")

    def add_store(self, store):
        if type(store) == dict:
            self.stores[StoreManager.total_stores] = Store(**store)
        elif type(store) == Store:
            self.stores[StoreManager.total_stores] = store
        else:
            raise TypeError("Store is not properly formatted a store object")
        StoreManager.total_stores += 1

    def get_all_stores(self):
        print("ID        NAME")
        for store in self.stores:
            print(self.stores[store].id, self.stores[store].name)

class SessionManager:
    def __init__(self):
        self.active_sessions = {}

    def create_session(self, username:str, session_id:int):
        if session_id not in self.active_sessions:
            empty_cart = Cart()
            self.active_sessions[session_id] = {"username" : username, "cart" : empty_cart, "store" : None}
            print(f"Session ID {session_id} created")
        # Mathematically unlikely, but you never know!
        else:
            raise KeyError("Duplicate Session Detected")

    # returns that user cart
    def get_cart(self, session_id:int):
        return self.active_sessions[session_id]["cart"]
    
    #easily returns the username
    @property
    def username(self, session_id):
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]["username"]
        return "-"

    # Complex process of calculating totals, etc.
    def finalize_order(self, session_id):
        if session_id in self.active_sessions:
            pass

    def set_active_store(self, session_id, store):
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["store"] = store

    # Placeholde for printing later on
    def escprint(self):
        pass


# Get our 'master' data
store_manager = StoreManager()
registry = ItemRegistry()
session_manager = SessionManager()

def restore_cart_to_store(session_id: str):
    """Takes all items in a user's cart and puts them back in the store inventory."""
    session_data = session_manager.active_sessions.get(session_id)
    if not session_data: 
        return
        
    old_store = session_data.get("store")
    cart = session_data.get("cart")
    
    # If they have a store and a cart with items in it...
    if old_store and cart and cart.contents:
        for item_name, cart_item in cart.contents.items():
            # If the item exists in the store (it should!), put the stock back
            if item_name in old_store.inventory:
                old_store.inventory[item_name].adjust_stock(cart_item.quantity)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load data before the server starts taking requests
    registry.load_items_from_tsv(ITEMS_FILENAME)

    store_manager.load_stores(registry)
    if not run_tests():
        print("Tests failed")
        exit()
    yield
    # Clean up (if needed) when server shuts down
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

@app.get("/items")
async def get_all_items():
    """Returns the entire item registry as JSON."""
    return registry.items

@app.get("/items/{item_name}")
async def get_item(item_name: str):
    """Returns a single item by name."""
    item = registry.get(item_name)
    if item:
        return item
    return {"error": "Item not found"}

@app.post("/start-session")
async def start_session(username: str):
    token = secrets.token_hex(32)
    session_manager.create_session(username, token)
    return {
        "status": "connected",
        "session_id": token,
    }



class CartAddRequest(BaseModel):
    session_id: str
    item_name: str
    quantity: int

@app.post("/sessions/{session_id}/store/{store_id}")
async def set_session_store(session_id: str, store_id: int):
    if session_id not in session_manager.active_sessions:
        return {"error": "Invalid session"}
    
    # Put current cart items back on the shelf before leaving the store!
    restore_cart_to_store(session_id)
    
    store = store_manager.stores.get(store_id)
    session_manager.set_active_store(session_id, store)
    
    # Clear the cart for the new store
    session_manager.active_sessions[session_id]["cart"] = Cart()
    return {"status": "success"}

@app.post("/cart/remove")
async def remove_from_cart(req: CartAddRequest): # We can reuse the same request model
    session_data = session_manager.active_sessions.get(req.session_id)
    if not session_data: return {"error": "Invalid session"}
    
    cart = session_data["cart"]
    store = session_data["store"]
    
    if req.item_name in cart.contents:
        # Get the quantity they had in the cart
        qty_to_restore = cart.contents[req.item_name].quantity
        # Put it back in the store
        if store and req.item_name in store.inventory:
            store.inventory[req.item_name].adjust_stock(qty_to_restore)
        # Remove from cart
        cart.remove_item(req.item_name)
        
    return await get_cart_contents(req.session_id)


@app.post("/cart/add")
async def add_to_cart(req: CartAddRequest):
    """Validates stock and adds the item to the session's cart."""
    if req.session_id not in session_manager.active_sessions:
        return {"error": "Invalid session"}
        
    session_data = session_manager.active_sessions[req.session_id]
    store = session_data["store"]
    if not store:
        return {"error": "No store selected"}
        
    # Check if store has enough stock
    stock_qty = store.get_current_stock(req.item_name)
    if stock_qty != -1 and stock_qty < req.quantity:
        return {"error": "Not enough stock in store"}
        
    # NEW: Deduct from the store's shelf!
    store.inventory[req.item_name].adjust_stock(-req.quantity)
        
    price = store.get_current_price(req.item_name)
    cart = session_data["cart"]
    
    # Check if already in cart to just adjust quantity, else add new
    if req.item_name in cart.contents:
        # adjust_quantity inside the Cart class expects an object, not a string! 
        # Let's fix this slightly for your Cart architecture:
        cart.contents[req.item_name].adjust_quantity(req.quantity)
    else:
        new_item = CartItem(req.item_name, price, req.quantity)
        cart.add_item(new_item)
        
    return await get_cart_contents(req.session_id)

@app.get("/cart/{session_id}")
async def get_cart_contents(session_id: str):
    """Returns the cart items and all the math for the UI."""
    session_data = session_manager.active_sessions.get(session_id)
    if not session_data:
        return {"error": "Invalid session"}
        
    cart = session_data["cart"]
    store = session_data["store"]
    tax_rate = store.calculate_taxes() if store else 0.0
    
    return {
        "items": [
            {
                "name": item.name, 
                "price": item.price, 
                "quantity": item.quantity, 
                "total": item.line_cost
            }
            for item in cart.contents.values()
        ],
        "subtotal": cart.calculate_subtotal(),
        "taxes": cart.calculate_taxes(tax_rate),
        "total": cart.calculate_total(tax_rate)
    }

@app.post("/cart/cancel/{session_id}")
async def cancel_cart(session_id: str):
    """Empties the cart and puts everything back on the shelves."""
    if session_id not in session_manager.active_sessions:
         return {"error": "Invalid session"}
         
    restore_cart_to_store(session_id)
    session_manager.active_sessions[session_id]["cart"] = Cart()
    
    return await get_cart_contents(session_id)

@app.get("/stores")
async def get_stores():
    """Returns a list of all stores (id, name, taxes, flags)."""
    return [
        {
            "id": s.id, 
            "name": s.name, 
            "taxes": s.taxes, 
            "flags": s.flags
        } 
        for s in store_manager.stores.values()
    ]

@app.get("/stores/{store_id}/inventory")
async def get_store_inventory(store_id: int):
    store = store_manager.stores.get(store_id)
    if not store: return {"error": "Store not found"}
    
    output = {}
    for name, stock_item in store.inventory.items():
        # Get the "Full" item details from the registry
        full_item = registry.get(name)
        
        # Merge them: StockItem + Metadata/Tags
        item_dict = stock_item.model_dump()
        item_dict["metadata"] = full_item.metadata
        item_dict["tags"] = full_item.tags
        item_dict["category"] = full_item.category
        output[name] = item_dict
        
    return output

# Request model for the checkout
class CheckoutRequest(BaseModel):
    session_id: str
    print_receipt: bool
    print_stats: bool

def format_receipt_stats(item_name: str, registry: ItemRegistry, index: int):
    """Generates the stat text and 'use boxes' for the receipt."""
    full_item = registry.get(item_name)
    if not full_item: return ""
    
    meta = full_item.metadata
    lines = [f"{index}. {item_name}"]
    lines.append(f"{full_item.description}")
    
    if "dmg" in meta: lines.append(f"{meta['dmg']} Damage")
    if "enc" in meta: lines.append(f"{meta['enc']} enc")
    
    # The Use Boxes (1 box per 5 uses)
    if "uses" in meta:
        uses = int(meta["uses"])
        boxes = "[]" * (uses // 5)
        remainder = uses % 5
        if remainder: boxes += f"({remainder})"
        lines.append(f"{uses} uses {boxes}")
        
    return "\n".join(lines)

@app.post("/checkout")
async def checkout_cart(req: CheckoutRequest):
    """Finalizes the sale, clears the cart, and formats the receipt."""
    session_data = session_manager.active_sessions.get(req.session_id)
    if not session_data: return {"error": "Invalid session"}
    
    cart = session_data["cart"]
    store = session_data["store"]
    
    if not cart.contents:
        return {"error": "Cart is empty"}
        
    tax_rate = store.calculate_taxes() if store else 0.0
    
    # --- 1. GENERATE THE RECEIPT STRING ---
    receipt_lines = [
        f"{store.name.upper() if store else 'UNION DEPOT'}",
        "SALES RECEIPT",
        datetime.now().strftime("%m/%d/%Y %I:%M:%S %p"),
        "-" * 21
    ]
    
    total_qty = 0
    for item in cart.contents.values():
        receipt_lines.append(item.name.upper())
        receipt_lines.append(f"{item.quantity}X  {item.price:.2f}   {item.line_cost:.2f}")
        total_qty += item.quantity
        
    receipt_lines.append("-" * 20)
    receipt_lines.append(f"ITEMS SOLD: {total_qty}")
    receipt_lines.append(f"SUBTOTAL:   {CURRENCY_UNIT}{cart.calculate_subtotal():.0f}")
    receipt_lines.append(f"TAXES:        {CURRENCY_UNIT}{cart.calculate_taxes(tax_rate):.0f}")
    receipt_lines.append(f"TOTAL:      {CURRENCY_UNIT}{cart.calculate_total(tax_rate):.0f}")
    receipt_lines.append("\nTHANK YOU FOR SHOPPING")
    receipt_lines.append("WITH US\n")
    random_sayings = [
        "Yes, most of my merchandise was ripped from the hands of dead adventurers.",
        "No refunds!",
        "Catch-a-guuuun! Guh... never doing that again.",
        "If you shop anywhere else, I'll have you killed.",
        "Don't die! I need your business.",
        "A day without slaughter is like a day without sunshine.",
        "You can never be too rich, too good looking, or too well-armed.",
        "Capitalism, baby!",
        "Guns, glorious guns!",
        "When you think murder, think Marcus Munitions!",
        "You don't need to be a better shot, you just need to shoot more bullets.",
        "In a world of no guarantees, you can always count on Marcus guns.",
        "Heh-heh. Sold!",
        "May it serve you well!",
        "Now, get to killing!",
        "Guns: I've got them, you need them!",
        "If it took more than one shot, you weren't using a Jakobs.",
        "The love of money is the root of all money.",
        "Nobody does bullets better than Marcus Munitions.",
        "It's a fine day for capitalism!",
        "High quality, low prices, and no questions asked!",
        "Don't get killed! Your cash ain't worth a thing if you don't spend it!",
        "Remember - Marcus means quality at a great price!",
        "Looks like it works to me!",
        "I've got bullets with your name on them! Well, wait, that came out wrong."
    ]

    receipt_lines.append(random.choice(random_sayings))
    receipt_lines.append("\n")
    # Append the stats if the client requested them
    if req.print_stats:
        receipt_lines.append("..................")
        item_index = 1
        for item_name, cart_item in cart.contents.items():
            # If they bought 8 power cells, print 8 stat blocks!
            for _ in range(cart_item.quantity): 
                stats = format_receipt_stats(item_name, registry, item_index)
                if stats:
                    receipt_lines.append(stats)
                    receipt_lines.append("<-------------------->")
                item_index += 1

    final_receipt = "\n".join(receipt_lines)
    
    # --- 2. PRINTER LOGIC HOOK ---
    if req.print_receipt:
        # You will drop your python-escpos logic right here!
        tprinter.open()
        tprinter.set(align="center",custom_size=True, width=2, height=2)

        print("\n--- SENDING TO PRINTER ---")
        tprinter.text(final_receipt)
        print("--------------------------\n")
        tprinter.qr("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        tprinter.cut()
        tprinter.close()
    
    # --- 3. FINALIZE ---
    # We assign a brand new cart. 
    # Notice we DO NOT restore_cart_to_store(), because the items are bought!
    session_manager.active_sessions[req.session_id]["cart"] = Cart()
    
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)