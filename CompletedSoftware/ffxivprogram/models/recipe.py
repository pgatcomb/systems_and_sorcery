"""
Recipe data model
"""
import json

class Recipe:
    """Represents a crafting recipe in FFXIV"""
    
    def __init__(self, recipe_id, result_item_id, level, job, materials=None, crystals=None, result_amount=1):
        self.recipe_id = int(recipe_id)
        self.result_item_id = int(result_item_id)
        self.level = int(level) if level else 0
        self.job = int(job) if job else 0
        self.materials = materials if materials else []  # List of (item_id, quantity) tuples
        self.crystals = crystals if crystals else []  # List of (crystal_id, quantity) tuples
        self.result_amount = int(result_amount) if result_amount else 1
    
    def __repr__(self):
        return f"Recipe(id={self.recipe_id}, item={self.result_item_id}, level={self.level}, job={self.job})"
    
    def to_dict(self):
        """Convert to dictionary for CSV storage"""
        return {
            'recipe_id': self.recipe_id,
            'result_item_id': self.result_item_id,
            'level': self.level,
            'job': self.job,
            'materials': json.dumps(self.materials),
            'crystals': json.dumps(self.crystals),
            'result_amount': self.result_amount
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create Recipe from dictionary (CSV row)"""
        materials = []
        crystals = []
        
        try:
            if data.get('materials'):
                materials = json.loads(data['materials'])
        except (json.JSONDecodeError, TypeError):
            pass
        
        try:
            if data.get('crystals'):
                crystals = json.loads(data['crystals'])
        except (json.JSONDecodeError, TypeError):
            pass
        
        return cls(
            recipe_id=data.get('recipe_id'),
            result_item_id=data.get('result_item_id'),
            level=data.get('level', 0),
            job=data.get('job', 0),
            materials=materials,
            crystals=crystals,
            result_amount=data.get('result_amount', 1)
        )
