# TIPS Client version 07:00:00 5/2/2026
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.validation import Number
from textual.widgets import Button, TextArea, TabbedContent, TabPane, DataTable, Input, Header, Switch, Select, Label, Static
import httpx

class TipsClient(App):
    TITLE = "Tabletop Store Interface APP"
    SUB_TITLE = "Version 5/2/2026"
    CSS_PATH = "styles.tcss"
    session_id: str = ""
    server_url: str = ""
    current_items: dict = {}
    selected_item_name: str = ""
    current_store_id: int = -1
    selected_cart_item_name: str = ""

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(id="tabs"):
            with TabPane("Connections", id="tab_connections"):
                yield Input(placeholder="Player Name", id="player_name")
                yield Input("192.168.0.5:8000", id="server_ip", disabled=False)
                yield Button("Connect to server", id="button_connect")
                yield Label("After connecting, choose store below")
                yield Select([("Store 1", 1)], id="store_selection", disabled=True)
            with TabPane("Items", id="tabitems"):
                with Vertical(id="vertical_items"):
                    with Horizontal(id="itemfiltercontrols"):
                        yield Select([("Sort A-Z", 1), ("Sort Z-A", 2), ("Sort $-$$$", 3), ("Sort $$$-S", 4)], id="sort_option")
                        yield Input(placeholder="Search input", id="item_search_input")
                        yield Button("Filter/Sort", id="item_button_searchsort")
                    yield DataTable(id="items_datatable")
                    with Horizontal(id="item_details_and_add"):
                        with Horizontal():
                            yield TextArea("Select an item above for more details", disabled=False, id="item_details")
                            with Vertical():
                                yield Input("1", id="item_qty", type="integer", validators=[Number(minimum=1, maximum=100)])
                                yield Button("ADD", id="item_add_to_cart")
            with TabPane("Cart", id="tabcart"):
                with Vertical():
                    yield Static("Subtotal: $0 | Tax/Fees: $0 | Total: $0", id="totals")
                    yield DataTable(id="cart_items")
                    with Horizontal(id="cart_adjustments"):
                        yield Input("1", id="cart_item_qty", type="integer", validators=[Number(minimum=1, maximum=100)])
                        yield Button("Adjust", id="cart_adjust_quantity", variant="warning")
                        yield Button("Delete", id="cart_delete_item", variant="error")
                    with Horizontal(id="cart_finalization"):
                        with Vertical(id="printer_settings"):
                            with Horizontal():
                                yield Static("Print Receipt?", id="static_pr")
                                yield Switch(id="option_print_receipt", value=True)
                            with Horizontal():
                                yield Static("Include Stats?", id="static_is")
                                yield Switch(id="option_print_stats", value=True)
                        with Vertical(id="cart_commands"):
                            yield Button("COMPLETE ORDER", id="cart_complete_order", variant="success")
                            yield Button("Cancel Order", id="cart_cancel_order", variant="error")

    def on_mount(self):
        table = self.query_one("#items_datatable", DataTable)
        table.add_column("Item", width=30)
        table.add_column("Description", width=50)
        table.add_column("Price", width=20)
        table.add_column("Stock", width=20)
        table.cursor_type = "row"

        table = self.query_one("#cart_items", DataTable)
        table.add_column("Item", width=30)
        table.add_column("Qty", width=10)
        table.add_column("Price", width=15)
        table.add_column("Total", width=20)
        table.cursor_type = "row"

    def populate_items_table(self, items: dict):
        """Populates the items DataTable from a dict of items so we can sort them later"""
        table = self.query_one("#items_datatable", DataTable)
        table.clear()

        for item_name, item_data in items.items():
            table.add_row(
                item_data["item_name"],
                item_data["description"],
                f"{item_data['price']:.2f}",
                str(item_data["stock"]),
                key=item_name
            )


    async def connect_to_server(self, server_url: str, username: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"http://{server_url}/start-session",
                    params={"username": username},
                )
                response.raise_for_status()
        except httpx.RequestError as exc:
            self.notify(f"Network error: {exc}", severity="error")
            return False
        except httpx.HTTPStatusError as exc:
            self.notify(f"Server error: {exc}", severity="error")
            return False

        data = response.json()

        if data.get("status") != "connected":
            self.notify("Server rejected connection", severity="error")
            return False

        self.session_id = data["session_id"]
        self.server_url = server_url
        return True

    async def fetch_stores(self):
        """Gets the list of available stores from the server."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"http://{self.server_url}/stores")
                response.raise_for_status()
            
            stores = response.json()
            options = [(s["name"], s["id"]) for s in stores]
            
            select_widget = self.query_one("#store_selection", Select)
            select_widget.set_options(options)
            select_widget.disabled = False
            self.notify("Stores loaded. Please select one.")
        except Exception as e:
            self.notify(f"Failed to load stores: {e}", severity="error")

    async def load_items(self, store_id: int):
        """Fetches inventory for a specific store."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"http://{self.server_url}/stores/{store_id}/inventory")
                response.raise_for_status()
                
            self.current_items = response.json()
            
            table = self.query_one("#items_datatable", DataTable)
            table.clear()
            
            for item_name, item_data in self.current_items.items():
                table.add_row(
                    item_data["item_name"],
                    item_data["description"],
                    f"{item_data['price']:.2f}",
                    str(item_data["stock"]),
                    key=item_name
                )
            self.current_items = response.json()
            self.populate_items_table(self.current_items)
            self.notify("Inventory updated.")

        except Exception as e:
            self.notify(f"Error loading inventory: {e}", severity="error")

    def on_data_table_row_highlighted(self, event: DataTable.RowSelected):
        """Fires when a player clicks an item in the data tables."""
        if event.data_table.id == "items_datatable":
            item_name = event.row_key.value
            self.selected_item_name = item_name
            item_data = self.current_items.get(item_name)
            
            if item_data:
                tags = ", ".join(item_data.get("tags", []))
                meta = item_data.get("metadata", {})
                meta_string = "\n".join([f"{k.capitalize()}: {v}" for k, v in meta.items()])
                
                display_text = (
                    f"--- {item_data['item_name'].upper()} ---\n"
                    f"Category: {item_data['category'].capitalize()}\n"
                    f"Tags: {tags}\n\n"
                    f"STATS:\n{meta_string if meta_string else 'No special stats.'}"
                )
                
                details_box = self.query_one("#item_details", TextArea)
                details_box.text = display_text
        elif event.data_table.id == "cart_items":
            self.selected_cart_item_name = event.row_key.value

    async def on_select_changed(self, event: Select.Changed):
        if event.select.id == "store_selection" and event.value is not Select.BLANK:
            store_id = event.value 
            self.current_store_id = store_id
            
            async with httpx.AsyncClient() as client:
                await client.post(f"http://{self.server_url}/sessions/{self.session_id}/store/{store_id}")
            
            self.notify(f"Loading inventory for Store ID: {store_id}...")
            await self.load_items(store_id)
            await self.fetch_cart()
        elif event.select.id == "sort_option":
            self.do_item_sort()
 

    async def do_add_item_to_cart(self):
        if not self.selected_item_name:
            self.notify("Please select an item from the table first!", severity="warning")
            return
            
        qty_input = self.query_one("#item_qty").value
        qty = int(qty_input) if qty_input and qty_input.isdigit() else 1
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"http://{self.server_url}/cart/add",
                    json={
                        "session_id": self.session_id,
                        "item_name": self.selected_item_name,
                        "quantity": qty
                    }
                )
                data = response.json()
                
                if "error" in data:
                    self.notify(data["error"], severity="error")
                else:
                    self.notify(f"Added {qty}x {self.selected_item_name} to cart!", severity="success")
                    self.update_cart_ui(data)
                    if self.current_store_id != -1:
                        await self.load_items(self.current_store_id)
                            
        except Exception as e:
            self.notify(f"Failed to add to cart: {e}", severity="error")

    async def fetch_cart(self):
        """Pulls the current cart state from the server."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://{self.server_url}/cart/{self.session_id}")
                self.update_cart_ui(response.json())
        except Exception as e:
            self.notify(f"Error fetching cart: {e}", severity="error")

    def update_cart_ui(self, cart_data: dict):
        """Redraws the Cart table and math totals."""
        if "error" in cart_data: return
            
        table = self.query_one("#cart_items", DataTable)
        table.clear()
        
        for item in cart_data.get("items", []):
            table.add_row(
                item["name"],
                str(item["quantity"]),
                f"${item['price']:.2f}",
                f"${item['total']:.2f}",
                key=item["name"]
            )
            
        subtotal = cart_data.get("subtotal", 0)
        taxes = cart_data.get("taxes", 0)
        total = cart_data.get("total", 0)
        
        total_line = self.query_one("#totals", Static)
        total_line.update(f"Subtotal: ${subtotal:.2f} | Tax/Fees: ${taxes:.2f} | Total: ${total:.2f}")

    async def do_cancel_order(self):
        if not self.session_id: return
        self.notify("Cancelling order and returning items to shelves...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"http://{self.server_url}/cart/cancel/{self.session_id}")
                self.update_cart_ui(response.json())
                
            if self.current_store_id != -1:
                await self.load_items(self.current_store_id)
                
            self.notify("Order Cancelled.", severity="warning")
        except Exception as e:
            self.notify(f"Error cancelling: {e}", severity="error")


    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "item_search_input":
            self.do_item_sort()



    def do_item_sort(self):
        search_text = self.query_one("#item_search_input").value
        search_text = search_text.strip().lower()

        sort_option = self.query_one("#sort_option", Select).value

        # 1. Start from the master list
        items = self.current_items

        # 2. Apply search filter (if any)
        if search_text:
            filtered_items = {}
            for item_name, item in items.items():
                haystack = " ".join([
                    item.get("item_name", ""),
                    item.get("description", ""),
                    item.get("category", ""),
                    " ".join(item.get("tags", [])),
                ]).lower()

                if search_text in haystack:
                    filtered_items[item_name] = item
        else:
            filtered_items = dict(items)

        # 3. Sort
        sorted_items = list(filtered_items.items())

        if sort_option == 1:  # A-Z
            sorted_items.sort(key=lambda x: x[1]["item_name"].lower())

        elif sort_option == 2:  # Z-A
            sorted_items.sort(key=lambda x: x[1]["item_name"].lower(), reverse=True)

        elif sort_option == 3:  # $ -> $$$
            sorted_items.sort(key=lambda x: x[1]["price"])

        elif sort_option == 4:  # $$$ -> $
            sorted_items.sort(key=lambda x: x[1]["price"], reverse=True)

        # 4. Re-render
        self.populate_items_table(dict(sorted_items))

       # self.notify(f"Showing {len(sorted_items)} items")






    def do_adjust_cart_qty(self): self.notify("Adjusting quantity of selected item in cart")


    async def do_delete_cart_item(self):
            if not self.selected_cart_item_name:
                self.notify("Select an item in the cart to delete.", severity="warning")
                return
                
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"http://{self.server_url}/cart/remove",
                        json={
                            "session_id": self.session_id,
                            "item_name": self.selected_cart_item_name,
                            "quantity": 0 # Server ignores this for full removal
                        }
                    )
                    self.update_cart_ui(response.json())
                    
                    # Refresh inventory to see the stock return!
                    if self.current_store_id != -1:
                        await self.load_items(self.current_store_id)
                        
                    self.notify(f"Removed {self.selected_cart_item_name} from cart.")
                    self.selected_cart_item_name = "" # Reset selection
            except Exception as e:
                self.notify(f"Error removing item: {e}", severity="error")

    async def do_complete_order(self):
        if not self.session_id: return
        
        # Read the checkboxes on the UI
        print_receipt = self.query_one("#option_print_receipt", Switch).value
        print_stats = self.query_one("#option_print_stats", Switch).value
        
        self.notify("Processing Order...")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"http://{self.server_url}/checkout",
                    json={
                        "session_id": self.session_id,
                        "print_receipt": print_receipt,
                        "print_stats": print_stats
                    }
                )
                data = response.json()
                
                if "error" in data:
                    self.notify(data["error"], severity="error")
                else:
                    self.notify("Checkout Complete! Order finalized.", severity="success")
                    # Pull the new (empty) cart from the server to clear the UI
                    await self.fetch_cart()
        except Exception as e:
            self.notify(f"Checkout Failed: {e}", severity="error")

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "button_connect":
            username = self.query_one("#player_name").value
            server_ip = self.query_one("#server_ip").value
            self.notify("Connecting…")
            success = await self.connect_to_server(server_ip, username)
            if success:
                self.notify("Connected successfully")
                await self.fetch_stores()

        elif event.button.id == "item_button_searchsort":
            self.do_item_sort()
        elif event.button.id == "item_add_to_cart":
            await self.do_add_item_to_cart()
        elif event.button.id == "cart_adjust_quantity":
            self.do_adjust_cart_qty()
        elif event.button.id == "cart_delete_item":
            await self.do_delete_cart_item()
        elif event.button.id == "cart_complete_order":
            await self.do_complete_order()
        elif event.button.id == "cart_cancel_order":
            await self.do_cancel_order() # <--- THE MISSING AWAIT WAS HERE

if __name__ == "__main__":
    app = TipsClient()
    app.run()