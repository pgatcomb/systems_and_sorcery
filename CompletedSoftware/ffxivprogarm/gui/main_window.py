"""
Main application window
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
from typing import List, Dict, Optional
import config
from models.item import Item
from models.recipe import Recipe
from models.market_data import MarketData
from api.teamcraft import TeamcraftAPI
from api.universalis import UniversalisAPI
from api.cache import CacheManager
from data.processor import DataProcessor
from data.filters import FilterEngine
from storage.presets import PresetManager
from storage.export import CSVExporter

class MainWindow:
    """Main application window with filters, results table, and details panel"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FFXIV Market Profit Analyzer")
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        
        # Initialize components
        self.teamcraft = TeamcraftAPI()
        self.universalis = UniversalisAPI()
        self.cache = CacheManager()
        self.preset_manager = PresetManager()
        self.exporter = CSVExporter()
        self.filter_engine = FilterEngine()
        
        # Data storage
        self.items: Dict[int, Item] = {}
        self.recipes: Dict[int, Recipe] = {}
        self.market_data: Dict[int, MarketData] = {}
        self.profit_data: Dict[int, tuple] = {}
        self.filtered_items: List[Item] = []
        self.selected_item: Optional[Item] = None
        
        # Server variable
        self.server_var = tk.StringVar(value=config.DEFAULT_SERVER)
        self.crystal_price_var = tk.DoubleVar(value=config.DEFAULT_CRYSTAL_PRICE)
        
        # Filter variables
        self.job_vars = {}
        for job_id, job_name in config.CRAFTER_JOBS.items():
            self.job_vars[job_id] = tk.BooleanVar(value=True)
        
        self.min_level_var = tk.IntVar(value=config.DEFAULT_MIN_LEVEL)
        self.max_level_var = tk.IntVar(value=config.DEFAULT_MAX_LEVEL)
        self.min_profit_var = tk.DoubleVar(value=config.DEFAULT_MIN_PROFIT)
        self.min_velocity_var = tk.DoubleVar(value=config.DEFAULT_MIN_VELOCITY)
        self.min_median_var = tk.DoubleVar(value=0)
        self.max_median_var = tk.DoubleVar(value=999999999)
        
        # Create UI
        self._create_ui()
        
        # Status
        self.data_loaded = False
        self.loading = False
        
        # Sorting state
        self.sort_column = 'Profit'
        self.sort_reverse = True
    
    def _create_ui(self):
        """Create the main UI layout"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create three-column layout
        # Left: Filters (250px)
        filter_frame = ttk.Frame(main_container, width=250)
        filter_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        filter_frame.pack_propagate(False)
        
        # Middle: Results table (expand)
        middle_frame = ttk.Frame(main_container)
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Right: Details (300px)
        detail_frame = ttk.Frame(main_container, width=300)
        detail_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(5, 0))
        detail_frame.pack_propagate(False)
        
        # Build each section
        self._create_filter_panel(filter_frame)
        self._create_results_panel(middle_frame)
        self._create_detail_panel(detail_frame)
    
    def _create_filter_panel(self, parent):
        """Create left filter panel"""
        # Title
        ttk.Label(parent, text="FILTERS", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Server selection
        ttk.Label(scrollable_frame, text="Server:").pack(anchor='w', pady=(5, 0))
        ttk.Entry(scrollable_frame, textvariable=self.server_var).pack(fill='x', pady=(0, 10))
        
        # Crystal price
        ttk.Label(scrollable_frame, text="Crystal Price (gil):").pack(anchor='w')
        ttk.Entry(scrollable_frame, textvariable=self.crystal_price_var).pack(fill='x', pady=(0, 10))
        
        # Crafter jobs
        ttk.Label(scrollable_frame, text="Crafter Jobs:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(5, 5))
        for job_id, job_name in sorted(config.CRAFTER_JOBS.items(), key=lambda x: x[1]):
            ttk.Checkbutton(scrollable_frame, text=job_name, 
                          variable=self.job_vars[job_id]).pack(anchor='w')
        
        # Level range
        ttk.Label(scrollable_frame, text="Recipe Level:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        
        level_frame = ttk.Frame(scrollable_frame)
        level_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(level_frame, text="Min:").pack(side='left')
        ttk.Entry(level_frame, textvariable=self.min_level_var, width=8).pack(side='left', padx=5)
        ttk.Label(level_frame, text="Max:").pack(side='left')
        ttk.Entry(level_frame, textvariable=self.max_level_var, width=8).pack(side='left', padx=5)
        
        # Profit threshold
        ttk.Label(scrollable_frame, text="Min Profit (gil):", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 0))
        ttk.Entry(scrollable_frame, textvariable=self.min_profit_var).pack(fill='x', pady=(0, 5))
        
        # Velocity threshold
        ttk.Label(scrollable_frame, text="Min Velocity (sales/day):", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 0))
        ttk.Entry(scrollable_frame, textvariable=self.min_velocity_var).pack(fill='x', pady=(0, 5))
        
        # Median price range
        ttk.Label(scrollable_frame, text="Median Price Range:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        
        median_frame = ttk.Frame(scrollable_frame)
        median_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(median_frame, text="Min:").pack(side='left')
        ttk.Entry(median_frame, textvariable=self.min_median_var, width=10).pack(side='left', padx=5)
        ttk.Label(median_frame, text="Max:").pack(side='left')
        ttk.Entry(median_frame, textvariable=self.max_median_var, width=10).pack(side='left', padx=5)
        
        # Apply filters button
        ttk.Button(scrollable_frame, text="Apply Filters", 
                  command=self._apply_filters).pack(fill='x', pady=10)
        
        # Presets section
        ttk.Label(scrollable_frame, text="Presets:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        
        preset_frame = ttk.Frame(scrollable_frame)
        preset_frame.pack(fill='x', pady=(0, 5))
        
        self.preset_combo = ttk.Combobox(preset_frame, state='readonly')
        self.preset_combo.pack(side='left', fill='x', expand=True)
        self._refresh_preset_list()
        
        ttk.Button(preset_frame, text="Load", width=6, 
                  command=self._load_preset).pack(side='left', padx=(5, 0))
        
        ttk.Button(scrollable_frame, text="Save Current as Preset", 
                  command=self._save_preset).pack(fill='x', pady=(0, 5))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_results_panel(self, parent):
        """Create center results panel"""
        # Top bar with title and buttons
        top_bar = ttk.Frame(parent)
        top_bar.pack(fill='x', pady=(0, 5))
        
        self.results_label = ttk.Label(top_bar, text="Results (0 items)", 
                                       font=('Arial', 12, 'bold'))
        self.results_label.pack(side='left')
        
        button_frame = ttk.Frame(top_bar)
        button_frame.pack(side='right')
        
        ttk.Button(button_frame, text="Refresh Data", 
                  command=self._refresh_data).pack(side='left', padx=2)
        ttk.Button(button_frame, text="Export CSV", 
                  command=self._export_csv).pack(side='left', padx=2)
        
        # Results table
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        vsb.pack(side='right', fill='y')
        
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        hsb.pack(side='bottom', fill='x')
        
        # Treeview
        columns = ('Name', 'Job', 'Level', 'Profit', 'ROI%', 'Median', 'Min', 'Velocity')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                                yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure columns
        self.tree.heading('Name', text='Name', command=lambda: self._sort_column('Name'))
        self.tree.heading('Job', text='Job', command=lambda: self._sort_column('Job'))
        self.tree.heading('Level', text='Lvl', command=lambda: self._sort_column('Level'))
        self.tree.heading('Profit', text='Profit', command=lambda: self._sort_column('Profit'))
        self.tree.heading('ROI%', text='ROI%', command=lambda: self._sort_column('ROI%'))
        self.tree.heading('Median', text='Median', command=lambda: self._sort_column('Median'))
        self.tree.heading('Min', text='Min', command=lambda: self._sort_column('Min'))
        self.tree.heading('Velocity', text='Vel/Day', command=lambda: self._sort_column('Velocity'))
        
        self.tree.column('Name', width=200)
        self.tree.column('Job', width=50, anchor='center')
        self.tree.column('Level', width=50, anchor='center')
        self.tree.column('Profit', width=90, anchor='e')
        self.tree.column('ROI%', width=70, anchor='e')
        self.tree.column('Median', width=90, anchor='e')
        self.tree.column('Min', width=90, anchor='e')
        self.tree.column('Velocity', width=70, anchor='e')
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection
        self.tree.bind('<<TreeviewSelect>>', self._on_item_selected)
        
        # Status bar
        self.status_label = ttk.Label(parent, text="Ready. Click 'Refresh Data' to load items.", 
                                     relief=tk.SUNKEN, anchor='w')
        self.status_label.pack(fill='x', pady=(5, 0))
    
    def _create_detail_panel(self, parent):
        """Create right detail panel"""
        ttk.Label(parent, text="ITEM DETAILS", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.detail_frame = ttk.Frame(canvas)
        
        self.detail_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.detail_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self._update_detail_panel(None)
    
    def _update_detail_panel(self, item: Optional[Item]):
        """Update detail panel with item information"""
        # Clear existing widgets
        for widget in self.detail_frame.winfo_children():
            widget.destroy()
        
        if not item:
            ttk.Label(self.detail_frame, text="Select an item to view details").pack(pady=20)
            return
        
        recipe = self.recipes.get(item.item_id)
        md = self.market_data.get(item.item_id)
        profit_info = self.profit_data.get(item.item_id, (0, 0, 0, 0))
        sale_price, material_cost, crystal_cost, profit = profit_info
        
        # Item name
        ttk.Label(self.detail_frame, text=item.name, 
                 font=('Arial', 11, 'bold'), wraplength=280).pack(anchor='w', pady=(0, 10))
        
        if recipe:
            job_name = config.CRAFTER_JOBS.get(recipe.job, f"Job{recipe.job}")
            ttk.Label(self.detail_frame, text=f"Job: {job_name}").pack(anchor='w')
            ttk.Label(self.detail_frame, text=f"Recipe Level: {recipe.level}").pack(anchor='w')
        
        # Market data
        if md:
            ttk.Label(self.detail_frame, text="\nMarket Data:", 
                     font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
            ttk.Label(self.detail_frame, text=f"Sale Price: {sale_price:,.0f} gil").pack(anchor='w')
            ttk.Label(self.detail_frame, text=f"Median Listing: {md.median_price:,.0f} gil" if md.median_price else "Median Listing: N/A").pack(anchor='w')
            ttk.Label(self.detail_frame, text=f"Min Listing: {md.min_listing:,.0f} gil" if md.min_listing else "Min Listing: N/A").pack(anchor='w')
            ttk.Label(self.detail_frame, text=f"Max Listing: {md.max_listing:,.0f} gil" if md.max_listing else "Max Listing: N/A").pack(anchor='w')
            ttk.Label(self.detail_frame, text=f"Velocity: {md.velocity:.2f}/day").pack(anchor='w')
            ttk.Label(self.detail_frame, text=f"Listings: {md.listing_count}").pack(anchor='w')
            
            # HQ vs NQ comparison
            if md.hq_price or md.nq_price:
                ttk.Label(self.detail_frame, text="\nHQ vs NQ Prices:", 
                         font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
                if md.hq_price:
                    ttk.Label(self.detail_frame, text=f"HQ Price: {md.hq_price:,.0f} gil").pack(anchor='w')
                if md.nq_price:
                    ttk.Label(self.detail_frame, text=f"NQ Price: {md.nq_price:,.0f} gil").pack(anchor='w')
                if md.hq_price and md.nq_price:
                    diff = md.hq_price - md.nq_price
                    diff_pct = (diff / md.nq_price * 100) if md.nq_price > 0 else 0
                    ttk.Label(self.detail_frame, text=f"HQ Premium: {diff:,.0f} gil ({diff_pct:.1f}%)").pack(anchor='w')
        
        # Crafting components
        if recipe and recipe.materials:
            ttk.Label(self.detail_frame, text="\nRequired Materials:", 
                     font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
            
            for mat_id, mat_qty in recipe.materials:
                mat_name = self.items.get(mat_id).name if mat_id in self.items else f"Item {mat_id}"
                mat_md = self.market_data.get(mat_id)
                mat_price = mat_md.min_listing if mat_md and mat_md.min_listing else (mat_md.median_price if mat_md else 0)
                mat_total = mat_price * mat_qty if mat_price else 0
                
                ttk.Label(self.detail_frame, 
                         text=f"  {mat_qty}x {mat_name} ({mat_total:,.0f} gil)",
                         wraplength=270).pack(anchor='w', padx=(10, 0))
            
            if recipe.crystals:
                ttk.Label(self.detail_frame, text="  Crystals:",
                         font=('Arial', 9, 'italic')).pack(anchor='w', padx=(10, 0), pady=(5, 0))
                for cryst_id, cryst_qty in recipe.crystals:
                    cryst_name = self.items.get(cryst_id).name if cryst_id in self.items else f"Crystal {cryst_id}"
                    ttk.Label(self.detail_frame, 
                             text=f"    {cryst_qty}x {cryst_name}",
                             wraplength=270).pack(anchor='w', padx=(10, 0))
        
        # Crafting costs
        ttk.Label(self.detail_frame, text="\nCrafting Cost:", 
                 font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Label(self.detail_frame, text=f"Materials: {material_cost:,.0f} gil").pack(anchor='w')
        ttk.Label(self.detail_frame, text=f"Crystals: {crystal_cost:,.0f} gil").pack(anchor='w')
        total_cost = material_cost + crystal_cost
        ttk.Label(self.detail_frame, text=f"Total Cost: {total_cost:,.0f} gil").pack(anchor='w')
        
        # Profit
        ttk.Label(self.detail_frame, text="\nProfit Analysis:", 
                 font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        ttk.Label(self.detail_frame, text=f"Profit: {profit:,.0f} gil", 
                 foreground='green' if profit > 0 else 'red').pack(anchor='w')
        roi = (profit / total_cost * 100) if total_cost > 0 else 0
        ttk.Label(self.detail_frame, text=f"ROI: {roi:.1f}%").pack(anchor='w')
        
        # Shopping list button
        ttk.Button(self.detail_frame, text="Generate Shopping List", 
                  command=lambda: self._generate_shopping_list(item)).pack(fill='x', pady=10)
    
    def _refresh_data(self):
        """Refresh data from APIs"""
        if self.loading:
            messagebox.showinfo("Loading", "Data is already being loaded. Please wait.")
            return
        
        self.loading = True
        self._set_status("Loading data from APIs...")
        
        # Run in thread to prevent GUI freeze
        thread = threading.Thread(target=self._load_data_thread)
        thread.daemon = True
        thread.start()
    
    def _load_data_thread(self):
        """Load data in background thread"""
        try:
            # Get craftable items from Teamcraft
            items_list, recipes_dict, marketable_ids = self.teamcraft.get_craftable_items()
            
            # Convert to dicts
            self.items = {item.item_id: item for item in items_list}
            self.recipes = recipes_dict
            
            self._set_status(f"Loaded {len(self.items)} craftable items. Fetching market data...")
            
            # Get market data from Universalis
            server = self.server_var.get()
            item_ids = list(self.items.keys())
            
            def progress(idx, total, item_id):
                if idx % 10 == 0:
                    self._set_status(f"Fetching market data: {idx}/{total}")
            
            self.market_data = self.universalis.get_market_data_batch(
                server, item_ids, progress_callback=progress)
            
            self._set_status("Calculating profits...")
            
            # Calculate profits
            processor = DataProcessor(self.items, self.recipes, self.market_data, 
                                    self.crystal_price_var.get())
            
            self.profit_data = {}
            for item_id in self.items.keys():
                self.profit_data[item_id] = processor.calculate_profit(item_id)
            
            self.data_loaded = True
            
            # Save data to cache
            self._save_session_data()
            
            self._set_status("Data loaded successfully. Applying filters...")
            
            # Apply filters
            self.root.after(0, self._apply_filters)
            
        except Exception as e:
            self._set_status(f"Error loading data: {e}")
            messagebox.showerror("Error", f"Failed to load data: {e}")
        finally:
            self.loading = False
    
    def _apply_filters(self):
        """Apply current filters to data"""
        if not self.data_loaded:
            messagebox.showinfo("No Data", "Please load data first by clicking 'Refresh Data'")
            return
        
        # Update filter engine
        enabled_jobs = {job_id for job_id, var in self.job_vars.items() if var.get()}
        self.filter_engine.set_job_filter(enabled_jobs)
        self.filter_engine.set_level_range(self.min_level_var.get(), self.max_level_var.get())
        self.filter_engine.set_profit_threshold(self.min_profit_var.get())
        self.filter_engine.set_velocity_threshold(self.min_velocity_var.get())
        
        # Get profit values only
        profit_values = {item_id: profit_info[3] for item_id, profit_info in self.profit_data.items()}
        
        # Filter items
        all_items = list(self.items.values())
        self.filtered_items = self.filter_engine.filter_items(
            all_items, self.recipes, self.market_data, profit_values)
        
        # Apply median price filter
        min_median = self.min_median_var.get()
        max_median = self.max_median_var.get()
        if min_median > 0 or max_median < 999999999:
            filtered_by_median = []
            for item in self.filtered_items:
                md = self.market_data.get(item.item_id)
                if md and md.median_price:
                    if min_median <= md.median_price <= max_median:
                        filtered_by_median.append(item)
            self.filtered_items = filtered_by_median
        
        # Update results table
        self._update_results_table()
        
        self._set_status(f"Showing {len(self.filtered_items)} items after filtering")
    
    def _update_results_table(self):
        """Update the results table with filtered items"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Sort items based on current sort column
        sorted_items = self._get_sorted_items()
        
        # Add items to tree
        for item in sorted_items:
            recipe = self.recipes.get(item.item_id)
            md = self.market_data.get(item.item_id)
            profit_info = self.profit_data.get(item.item_id, (0, 0, 0, 0))
            sale_price, material_cost, crystal_cost, profit = profit_info
            
            job_name = config.CRAFTER_JOBS.get(recipe.job, "") if recipe else ""
            level = recipe.level if recipe else 0
            roi = (profit / (material_cost + crystal_cost) * 100) if (material_cost + crystal_cost) > 0 else 0
            velocity = md.velocity if md else 0
            median_price = md.median_price if md and md.median_price else 0
            min_price = md.min_listing if md and md.min_listing else 0
            
            values = (
                item.name,
                job_name,
                level,
                f"{profit:,.0f}",
                f"{roi:.1f}",
                f"{median_price:,.0f}",
                f"{min_price:,.0f}",
                f"{velocity:.2f}"
            )
            
            self.tree.insert('', 'end', iid=str(item.item_id), values=values)
        
        # Update label
        self.results_label.config(text=f"Results ({len(sorted_items)} items)")
    
    def _get_sorted_items(self):
        """Get filtered items sorted by current sort column"""
        def get_sort_key(item):
            recipe = self.recipes.get(item.item_id)
            md = self.market_data.get(item.item_id)
            profit_info = self.profit_data.get(item.item_id, (0, 0, 0, 0))
            sale_price, material_cost, crystal_cost, profit = profit_info
            total_cost = material_cost + crystal_cost
            
            if self.sort_column == 'Name':
                return item.name.lower()
            elif self.sort_column == 'Job':
                return config.CRAFTER_JOBS.get(recipe.job, "") if recipe else ""
            elif self.sort_column == 'Level':
                return recipe.level if recipe else 0
            elif self.sort_column == 'Profit':
                return profit
            elif self.sort_column == 'ROI%':
                return (profit / total_cost * 100) if total_cost > 0 else 0
            elif self.sort_column == 'Median':
                return md.median_price if md and md.median_price else 0
            elif self.sort_column == 'Min':
                return md.min_listing if md and md.min_listing else 0
            elif self.sort_column == 'Velocity':
                return md.velocity if md else 0
            return 0
        
        return sorted(self.filtered_items, key=get_sort_key, reverse=self.sort_reverse)
    
    def _sort_column(self, col):
        """Sort tree by column"""
        # Toggle sort direction if clicking same column
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            # Default to descending for numeric columns, ascending for text
            self.sort_reverse = col != 'Name' and col != 'Job'
        
        # Re-populate table with new sort
        self._update_results_table()
    
    def _on_item_selected(self, event):
        """Handle item selection in tree"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_id = int(selection[0])
        item = self.items.get(item_id)
        self.selected_item = item
        self._update_detail_panel(item)
    
    def _generate_shopping_list(self, item: Item):
        """Generate and export shopping list for an item"""
        try:
            processor = DataProcessor(self.items, self.recipes, self.market_data, 
                                    self.crystal_price_var.get())
            
            shopping_list = processor.get_shopping_list(item.item_id, quantity=1)
            
            if not shopping_list:
                messagebox.showinfo("Shopping List", "No materials needed (or item has no recipe)")
                return
            
            # Ask for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"shopping_list_{item.name.replace(' ', '_')}.csv"
            )
            
            if filename:
                self.exporter.export_shopping_list(shopping_list, filename, item.name, 1)
                messagebox.showinfo("Success", f"Shopping list exported to {filename}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate shopping list: {e}")
    
    def _export_csv(self):
        """Export current filtered results to CSV"""
        if not self.filtered_items:
            messagebox.showinfo("No Data", "No items to export")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile="ffxiv_market_results.csv"
            )
            
            if filename:
                self.exporter.export_results(
                    self.filtered_items, self.recipes, self.market_data,
                    self.profit_data, filename, self.server_var.get())
                messagebox.showinfo("Success", f"Results exported to {filename}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")
    
    def _save_preset(self):
        """Save current filter settings as preset"""
        # Simple dialog for preset name
        name = tk.simpledialog.askstring("Save Preset", "Enter preset name:")
        if not name:
            return
        
        enabled_jobs = {job_id for job_id, var in self.job_vars.items() if var.get()}
        filter_config = self.preset_manager.create_filter_config(
            enabled_jobs,
            self.min_level_var.get(),
            self.max_level_var.get(),
            self.min_profit_var.get(),
            self.min_velocity_var.get()
        )
        
        if self.preset_manager.save_preset(name, filter_config):
            self._refresh_preset_list()
            messagebox.showinfo("Success", f"Preset '{name}' saved")
    
    def _load_preset(self):
        """Load selected preset"""
        preset_name = self.preset_combo.get()
        if not preset_name:
            return
        
        config_data = self.preset_manager.load_preset(preset_name)
        if not config_data:
            messagebox.showerror("Error", f"Failed to load preset '{preset_name}'")
            return
        
        # Apply preset to UI
        enabled_jobs = set(config_data.get('enabled_jobs', []))
        for job_id, var in self.job_vars.items():
            var.set(job_id in enabled_jobs)
        
        self.min_level_var.set(config_data.get('min_level', config.DEFAULT_MIN_LEVEL))
        self.max_level_var.set(config_data.get('max_level', config.DEFAULT_MAX_LEVEL))
        self.min_profit_var.set(config_data.get('min_profit', config.DEFAULT_MIN_PROFIT))
        self.min_velocity_var.set(config_data.get('min_velocity', config.DEFAULT_MIN_VELOCITY))
        
        messagebox.showinfo("Success", f"Loaded preset '{preset_name}'")
    
    def _refresh_preset_list(self):
        """Refresh the preset dropdown"""
        presets = self.preset_manager.list_presets()
        self.preset_combo['values'] = presets
        if presets:
            self.preset_combo.current(0)
    
    def _set_status(self, message: str):
        """Update status label (thread-safe)"""
        self.root.after(0, lambda: self.status_label.config(text=message))
    
    def _save_session_data(self):
        """Save current session data to cache files"""
        try:
            import pickle
            import os
            
            session_file = os.path.join(config.CACHE_DIR, 'session_data.pkl')
            os.makedirs(config.CACHE_DIR, exist_ok=True)
            
            session_data = {
                'items': self.items,
                'recipes': self.recipes,
                'market_data': self.market_data,
                'profit_data': self.profit_data,
                'server': self.server_var.get(),
                'crystal_price': self.crystal_price_var.get()
            }
            
            with open(session_file, 'wb') as f:
                pickle.dump(session_data, f)
            
            print(f"[Session] Saved session data to {session_file}")
        except Exception as e:
            print(f"[Session] Failed to save session data: {e}")
    
    def _load_session_data(self):
        """Load previous session data from cache files"""
        try:
            import pickle
            import os
            
            session_file = os.path.join(config.CACHE_DIR, 'session_data.pkl')
            
            if not os.path.exists(session_file):
                return False
            
            with open(session_file, 'rb') as f:
                session_data = pickle.load(f)
            
            self.items = session_data.get('items', {})
            self.recipes = session_data.get('recipes', {})
            self.market_data = session_data.get('market_data', {})
            self.profit_data = session_data.get('profit_data', {})
            
            # Update UI with saved server and crystal price
            saved_server = session_data.get('server')
            if saved_server:
                self.server_var.set(saved_server)
            
            saved_crystal_price = session_data.get('crystal_price')
            if saved_crystal_price:
                self.crystal_price_var.set(saved_crystal_price)
            
            if self.items:
                self.data_loaded = True
                self._set_status(f"Loaded cached data: {len(self.items)} items")
                self._apply_filters()
                print(f"[Session] Loaded session data from {session_file}")
                return True
            
            return False
        except Exception as e:
            print(f"[Session] Failed to load session data: {e}")
            return False
    
    def run(self):
        """Start the application"""
        # Create default presets if none exist
        if not self.preset_manager.list_presets():
            self.preset_manager.create_default_presets()
            self._refresh_preset_list()
        
        # Try to load cached session data
        if self._load_session_data():
            self._set_status("Loaded from cache. Click 'Refresh Data' to update market prices.")
        
        self.root.mainloop()
