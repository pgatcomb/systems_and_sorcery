"""
Item data model
"""

class Item:
    """Represents a craftable item in FFXIV"""
    
    def __init__(self, item_id, name, item_level=0, can_be_hq=True):
        self.item_id = int(item_id)
        self.name = str(name)
        self.item_level = int(item_level) if item_level else 0
        self.can_be_hq = bool(can_be_hq)
    
    def __repr__(self):
        return f"Item(id={self.item_id}, name='{self.name}', level={self.item_level})"
    
    def to_dict(self):
        """Convert to dictionary for CSV storage"""
        return {
            'item_id': self.item_id,
            'name': self.name,
            'item_level': self.item_level,
            'can_be_hq': self.can_be_hq
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create Item from dictionary (CSV row)"""
        return cls(
            item_id=data.get('item_id'),
            name=data.get('name', ''),
            item_level=data.get('item_level', 0),
            can_be_hq=data.get('can_be_hq', True)
        )
