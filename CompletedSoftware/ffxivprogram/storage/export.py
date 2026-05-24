"""
CSV export functionality
"""
import pandas as pd
from datetime import datetime
from typing import List, Dict
import config

class CSVExporter:
    """Handles exporting data to CSV files"""
    
    def export_results(self, items: List, recipes: Dict, market_data: Dict, 
                      profit_data: Dict, filename: str, server: str) -> bool:
        """
        Export filtered results to CSV
        
        Args:
            items: List of Item objects to export
            recipes: Dict mapping item_id -> Recipe
            market_data: Dict mapping item_id -> MarketData
            profit_data: Dict mapping item_id -> (sale_price, material_cost, crystal_cost, profit)
            filename: Output CSV filename
            server: Server name
        
        Returns:
            True if export was successful
        """
        try:
            rows = []
            
            for item in items:
                recipe = recipes.get(item.item_id)
                if not recipe:
                    continue
                
                md = market_data.get(item.item_id)
                profit_info = profit_data.get(item.item_id, (0, 0, 0, 0))
                sale_price, material_cost, crystal_cost, profit = profit_info
                
                # Calculate ROI
                total_cost = material_cost + crystal_cost
                roi = (profit / total_cost * 100) if total_cost > 0 else 0.0
                
                # Get job name
                job_name = config.CRAFTER_JOBS.get(recipe.job, f"Job{recipe.job}")
                
                row = {
                    'Item ID': item.item_id,
                    'Name': item.name,
                    'Job': job_name,
                    'Recipe Level': recipe.level,
                    'Sale Price': round(sale_price, 2) if sale_price else 0,
                    'Material Cost': round(material_cost, 2) if material_cost else 0,
                    'Crystal Cost': round(crystal_cost, 2) if crystal_cost else 0,
                    'Total Cost': round(total_cost, 2) if total_cost else 0,
                    'Profit': round(profit, 2) if profit else 0,
                    'ROI %': round(roi, 2),
                    'Velocity/Day': round(md.velocity, 2) if md else 0,
                    'Listings': md.listing_count if md else 0,
                    'Min Listing': round(md.min_listing, 2) if md and md.min_listing else 0,
                    'Server': server,
                }
                
                rows.append(row)
            
            # Create DataFrame and sort by profit
            df = pd.DataFrame(rows)
            if not df.empty:
                df = df.sort_values('Profit', ascending=False)
            
            # Add metadata
            df['Export Time'] = datetime.now().isoformat()
            
            # Save to CSV
            df.to_csv(filename, index=False)
            print(f"[Export] Exported {len(rows)} items to {filename}")
            return True
            
        except Exception as e:
            print(f"[Export] Failed to export to {filename}: {e}")
            return False
    
    def export_shopping_list(self, shopping_list: List, filename: str, 
                           item_name: str, quantity: int) -> bool:
        """
        Export shopping list to CSV
        
        Args:
            shopping_list: List of (item_id, item_name, qty_needed, cost_per_unit)
            filename: Output CSV filename
            item_name: Name of the item being crafted
            quantity: Quantity being crafted
        
        Returns:
            True if export was successful
        """
        try:
            rows = []
            total_cost = 0.0
            
            for item_id, name, qty_needed, cost_per_unit in shopping_list:
                total_item_cost = qty_needed * cost_per_unit
                total_cost += total_item_cost
                
                rows.append({
                    'Item ID': item_id,
                    'Material': name,
                    'Quantity Needed': qty_needed,
                    'Price Per Unit': round(cost_per_unit, 2),
                    'Total Cost': round(total_item_cost, 2)
                })
            
            # Add summary row
            rows.append({
                'Item ID': '',
                'Material': '--- TOTAL ---',
                'Quantity Needed': '',
                'Price Per Unit': '',
                'Total Cost': round(total_cost, 2)
            })
            
            df = pd.DataFrame(rows)
            
            # Add header info
            df.insert(0, 'Crafting', [item_name] + [''] * (len(rows) - 1))
            df.insert(1, 'Quantity', [quantity] + [''] * (len(rows) - 1))
            df['Export Time'] = [datetime.now().isoformat()] + [''] * (len(rows) - 1)
            
            df.to_csv(filename, index=False)
            print(f"[Export] Exported shopping list to {filename}")
            return True
            
        except Exception as e:
            print(f"[Export] Failed to export shopping list to {filename}: {e}")
            return False
