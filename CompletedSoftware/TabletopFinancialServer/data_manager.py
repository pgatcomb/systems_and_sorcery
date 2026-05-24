"""
Data persistence layer for JSON import/export.
"""
import json
import os
from typing import Dict, List
from models import Calendar, Asset, FinancialEvent, Ledger


class DataManager:
    """Manages saving and loading campaign data to/from JSON."""
    
    def __init__(self, filepath: str = "data/campaign_data.json"):
        """Initialize the data manager with a file path."""
        self.filepath = filepath
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Create the data directory if it doesn't exist."""
        directory = os.path.dirname(self.filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
    
    def save_data(self, calendar: Calendar, assets: List[Asset], 
                  events: List[FinancialEvent], ledger: Ledger):
        """Save all game data to JSON file."""
        data = {
            "calendar": calendar.to_dict(),
            "assets": [asset.to_dict() for asset in assets],
            "events": [event.to_dict() for event in events],
            "ledger": ledger.to_dict()
        }
        
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_data(self) -> Dict:
        """Load game data from JSON file."""
        if not os.path.exists(self.filepath):
            # Return default data if file doesn't exist
            return self._get_default_data()
        
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, IOError):
            # Return default data if file is corrupted
            return self._get_default_data()
    
    def _get_default_data(self) -> Dict:
        """Return default data structure for a new campaign."""
        from datetime import datetime
        return {
            "calendar": {
                "current_date": datetime.now().strftime("%Y-%m-%d")
            },
            "assets": [],
            "events": [],
            "ledger": []
        }
    
    def import_from_json(self, json_string: str) -> Dict:
        """Import data from a JSON string."""
        try:
            data = json.loads(json_string)
            # Validate structure
            if not all(key in data for key in ["calendar", "assets", "events", "ledger"]):
                raise ValueError("Invalid JSON structure")
            return data
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid JSON data: {str(e)}")
    
    def export_to_json(self, calendar: Calendar, assets: List[Asset],
                      events: List[FinancialEvent], ledger: Ledger) -> str:
        """Export all game data to a JSON string."""
        data = {
            "calendar": calendar.to_dict(),
            "assets": [asset.to_dict() for asset in assets],
            "events": [event.to_dict() for event in events],
            "ledger": ledger.to_dict()
        }
        return json.dumps(data, indent=2)
    
    def parse_loaded_data(self, data: Dict) -> tuple:
        """Parse loaded data into model objects."""
        calendar = Calendar.from_dict(data["calendar"])
        assets = [Asset.from_dict(a) for a in data.get("assets", [])]
        events = [FinancialEvent.from_dict(e) for e in data.get("events", [])]
        ledger = Ledger.from_dict(data.get("ledger", []))
        return calendar, assets, events, ledger
