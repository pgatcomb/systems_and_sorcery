"""
Universalis API client for fetching market data
"""
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime
import config
from models.market_data import MarketData

class UniversalisAPI:
    """Client for fetching market data from Universalis"""
    
    def __init__(self):
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with headers"""
        s = requests.Session()
        s.headers.update({"User-Agent": "FFXIV-Market-Analyzer/1.0"})
        return s
    
    def _get_json(self, url: str) -> Optional[dict]:
        """Fetch JSON from URL with error handling"""
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[Universalis] Error fetching {url}: {e}")
            return None
    
    def _pick_stat_from_block(self, block: dict, keys=("averageSalePrice", "medianListing", "minListing"), field="price"):
        """Extract statistical value from Universalis data block"""
        if not isinstance(block, dict):
            return None
        
        for k in keys:
            x = block.get(k)
            if not x:
                continue
            
            x = x.get("dc") or x.get("region") or x
            
            if isinstance(x, list):
                vals = []
                for e in x:
                    if isinstance(e, dict):
                        v = e.get(field)
                        if isinstance(v, (int, float)) and v > 0:
                            vals.append(v)
                if vals:
                    return float(sum(vals) / len(vals))
            elif isinstance(x, dict):
                v = x.get(field)
                if isinstance(v, (int, float)) and v > 0:
                    return float(v)
        return None
    
    def _pick_velocity(self, block: dict) -> Optional[float]:
        """Extract sale velocity from Universalis data block"""
        if not isinstance(block, dict):
            return None
        
        x = block.get("dailySaleVelocity") or {}
        for k in ("dc", "region", "world"):
            if isinstance(x.get(k), dict):
                q = x[k].get("quantity")
                if isinstance(q, (int, float)):
                    return float(q)
        return None
    
    def get_aggregated_stats(self, server: str, item_id: int) -> MarketData:
        """
        Get aggregated market statistics for an item
        Returns MarketData object
        """
        url = config.UNIVERSALIS_AGG_URL.format(dc=server, item=item_id)
        data = self._get_json(url) or {}
        
        results = data.get("results") or []
        if not results:
            return MarketData(item_id, server)
        
        # Find the matching item or use first result
        row = next((r for r in results if r.get("itemId") == item_id), results[0])
        
        # Extract HQ and NQ prices separately
        hq_block = row.get("hq") or {}
        nq_block = row.get("nq") or {}
        
        hq_median = self._pick_stat_from_block(hq_block, ("averageSalePrice", "medianListing", "minListing"), "price")
        nq_median = self._pick_stat_from_block(nq_block, ("averageSalePrice", "medianListing", "minListing"), "price")
        
        # Try both NQ and HQ data, prefer HQ if available
        choices = []
        for side in ("hq", "nq"):
            blk = row.get(side) or {}
            median_sale = self._pick_stat_from_block(blk, ("averageSalePrice", "medianListing", "minListing"), "price")
            min_listing = self._pick_stat_from_block(blk, ("minListing", "medianListing", "averageSalePrice"), "price")
            max_listing = self._pick_stat_from_block(blk, ("maxListing", "medianListing", "averageSalePrice"), "price")
            vel = self._pick_velocity(blk)
            
            if median_sale is not None:
                choices.append((median_sale, min_listing, max_listing, vel))
        
        if not choices:
            return MarketData(item_id, server)
        
        # Sort by velocity and use best option
        choices.sort(key=lambda t: ((t[3] or 0.0), t[1] is not None), reverse=True)
        median_price, min_listing, max_listing, velocity = choices[0]
        
        return MarketData(
            item_id=item_id,
            server=server,
            current_price=median_price,
            median_price=median_price,
            min_listing=min_listing,
            max_listing=max_listing,
            velocity=velocity or 0.0,
            hq_price=hq_median,
            nq_price=nq_median,
            last_updated=datetime.now()
        )
    
    def get_listing_count(self, server: str, item_id: int) -> int:
        """Get current number of listings for an item"""
        url = config.UNIVERSALIS_CURR_URL.format(dc=server, item=item_id)
        data = self._get_json(url) or {}
        
        listings = data.get("listings") or []
        return len(listings)
    
    def get_market_data_batch(self, server: str, item_ids: List[int], 
                             progress_callback=None) -> Dict[int, MarketData]:
        """
        Fetch market data for multiple items
        Returns dict mapping item_id -> MarketData
        """
        market_data = {}
        total = len(item_ids)
        
        for idx, item_id in enumerate(item_ids, 1):
            # Get aggregated stats
            md = self.get_aggregated_stats(server, item_id)
            
            # Get listing count if we have valid price data
            if md.median_price:
                md.listing_count = self.get_listing_count(server, item_id)
            
            market_data[item_id] = md
            
            # Progress callback
            if progress_callback:
                progress_callback(idx, total, item_id)
            
            # Rate limiting
            if idx < total:
                time.sleep(config.API_DELAY)
        
        return market_data
