"""
Preset manager for saving and loading filter configurations
"""
import os
import json
from typing import Dict, List, Optional
import config

class PresetManager:
    """Manages saving and loading filter presets as JSON files"""
    
    def __init__(self):
        self._ensure_presets_dir()
    
    def _ensure_presets_dir(self):
        """Create presets directory if it doesn't exist"""
        os.makedirs(config.PRESETS_DIR, exist_ok=True)
    
    def save_preset(self, name: str, filter_config: Dict) -> bool:
        """
        Save a filter preset to JSON file
        
        Args:
            name: Name of the preset
            filter_config: Dictionary containing filter settings
        
        Returns:
            True if save was successful
        """
        try:
            filename = os.path.join(config.PRESETS_DIR, f"{name}.json")
            with open(filename, 'w') as f:
                json.dump(filter_config, f, indent=2)
            print(f"[Presets] Saved preset: {name}")
            return True
        except Exception as e:
            print(f"[Presets] Failed to save preset {name}: {e}")
            return False
    
    def load_preset(self, name: str) -> Optional[Dict]:
        """
        Load a filter preset from JSON file
        
        Args:
            name: Name of the preset
        
        Returns:
            Filter configuration dict or None if failed
        """
        try:
            filename = os.path.join(config.PRESETS_DIR, f"{name}.json")
            if not os.path.exists(filename):
                print(f"[Presets] Preset not found: {name}")
                return None
            
            with open(filename, 'r') as f:
                data = json.load(f)
            print(f"[Presets] Loaded preset: {name}")
            return data
        except Exception as e:
            print(f"[Presets] Failed to load preset {name}: {e}")
            return None
    
    def list_presets(self) -> List[str]:
        """
        Get list of available preset names
        
        Returns:
            List of preset names (without .json extension)
        """
        try:
            if not os.path.exists(config.PRESETS_DIR):
                return []
            
            files = os.listdir(config.PRESETS_DIR)
            presets = [f[:-5] for f in files if f.endswith('.json')]
            return sorted(presets)
        except Exception as e:
            print(f"[Presets] Failed to list presets: {e}")
            return []
    
    def delete_preset(self, name: str) -> bool:
        """
        Delete a preset
        
        Args:
            name: Name of the preset to delete
        
        Returns:
            True if deletion was successful
        """
        try:
            filename = os.path.join(config.PRESETS_DIR, f"{name}.json")
            if os.path.exists(filename):
                os.remove(filename)
                print(f"[Presets] Deleted preset: {name}")
                return True
            return False
        except Exception as e:
            print(f"[Presets] Failed to delete preset {name}: {e}")
            return False
    
    def create_filter_config(self, enabled_jobs: set, min_level: int, max_level: int, 
                           min_profit: float, min_velocity: float) -> Dict:
        """
        Create a filter configuration dictionary
        
        Args:
            enabled_jobs: Set of enabled job IDs
            min_level: Minimum recipe level
            max_level: Maximum recipe level
            min_profit: Minimum profit threshold
            min_velocity: Minimum sale velocity
        
        Returns:
            Configuration dictionary
        """
        return {
            'enabled_jobs': list(enabled_jobs),
            'min_level': min_level,
            'max_level': max_level,
            'min_profit': min_profit,
            'min_velocity': min_velocity
        }
    
    def create_default_presets(self):
        """Create some default preset examples"""
        # High Profit - All Crafters
        self.save_preset("High Profit All", self.create_filter_config(
            enabled_jobs=set(config.CRAFTER_JOBS.keys()),
            min_level=80,
            max_level=100,
            min_profit=5000,
            min_velocity=1.0
        ))
        
        # Quick Turnover
        self.save_preset("Quick Turnover", self.create_filter_config(
            enabled_jobs=set(config.CRAFTER_JOBS.keys()),
            min_level=1,
            max_level=100,
            min_profit=500,
            min_velocity=5.0
        ))
        
        # Carpenter Only
        self.save_preset("Carpenter 90+", self.create_filter_config(
            enabled_jobs={8},  # CRP
            min_level=90,
            max_level=100,
            min_profit=2000,
            min_velocity=0.5
        ))
        
        # Goldsmith Only
        self.save_preset("Goldsmith 90+", self.create_filter_config(
            enabled_jobs={11},  # GSM
            min_level=90,
            max_level=100,
            min_profit=2000,
            min_velocity=0.5
        ))
        
        print("[Presets] Created default presets")
