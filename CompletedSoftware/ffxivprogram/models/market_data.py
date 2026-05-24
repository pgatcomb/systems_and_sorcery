"""
Market data model
"""
from datetime import datetime

class MarketData:
    """Represents market statistics for an item"""
    
    def __init__(self, item_id, server, current_price=None, median_price=None, 
                 min_listing=None, max_listing=None, velocity=None, listing_count=None, 
                 hq_price=None, nq_price=None, last_updated=None):
        self.item_id = int(item_id)
        self.server = str(server)
        self.current_price = float(current_price) if current_price else None
        self.median_price = float(median_price) if median_price else None
        self.min_listing = float(min_listing) if min_listing else None
        self.max_listing = float(max_listing) if max_listing else None
        self.velocity = float(velocity) if velocity else 0.0
        self.listing_count = int(listing_count) if listing_count else 0
        self.hq_price = float(hq_price) if hq_price else None
        self.nq_price = float(nq_price) if nq_price else None
        self.last_updated = last_updated if isinstance(last_updated, datetime) else datetime.now()
    
    def __repr__(self):
        return f"MarketData(item={self.item_id}, server='{self.server}', median={self.median_price}, velocity={self.velocity})"
    
    def is_stale(self, max_age_seconds):
        """Check if market data is older than max_age_seconds"""
        age = (datetime.now() - self.last_updated).total_seconds()
        return age > max_age_seconds
    
    def to_dict(self):
        """Convert to dictionary for CSV storage"""
        return {
            'item_id': self.item_id,
            'server': self.server,
            'current_price': self.current_price,
            'median_price': self.median_price,
            'min_listing': self.min_listing,
            'max_listing': self.max_listing,
            'velocity': self.velocity,
            'listing_count': self.listing_count,
            'hq_price': self.hq_price,
            'nq_price': self.nq_price,
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create MarketData from dictionary (CSV row)"""
        last_updated = data.get('last_updated')
        if isinstance(last_updated, str):
            try:
                last_updated = datetime.fromisoformat(last_updated)
            except (ValueError, TypeError):
                last_updated = datetime.now()
        
        return cls(
            item_id=data.get('item_id'),
            server=data.get('server', ''),
            current_price=data.get('current_price'),
            median_price=data.get('median_price'),
            min_listing=data.get('min_listing'),
            max_listing=data.get('max_listing'),
            velocity=data.get('velocity', 0.0),
            listing_count=data.get('listing_count', 0),
            hq_price=data.get('hq_price'),
            nq_price=data.get('nq_price'),
            last_updated=last_updated
        )
