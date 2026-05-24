"""
Finance logic for time advancement and event processing.
"""
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from models import Calendar, Asset, FinancialEvent, Ledger


class FinanceEngine:
    """Handles financial calculations and time advancement logic."""
    
    def __init__(self, calendar: Calendar, assets: List[Asset], 
                 events: List[FinancialEvent], ledger: Ledger):
        """Initialize the finance engine with game state."""
        self.calendar = calendar
        self.assets = assets
        self.events = events
        self.ledger = ledger
    
    def advance_time(self, days: int) -> dict:
        """
        Advance time and apply all scheduled events.
        Returns a summary of changes.
        If an event is encountered, time advancement pauses at that event.
        """
        old_date = self.calendar.current_date
        target_date = old_date + timedelta(days=days)
        
        # Check if there's an event between now and target date
        next_event_date = self._find_next_event_date(old_date, target_date)
        
        if next_event_date:
            # Pause at the event date
            actual_target = next_event_date
            paused_at_event = True
        else:
            actual_target = target_date
            paused_at_event = False
        
        # Advance to the actual target (either event date or requested date)
        days_advanced = (actual_target - old_date).days
        self.calendar.advance_days(days_advanced)
        new_date = self.calendar.current_date
        
        # Track all changes
        changes = {
            "date_changed": True,
            "old_date": old_date.strftime("%Y-%m-%d"),
            "new_date": new_date.strftime("%Y-%m-%d"),
            "paused_at_event": paused_at_event,
            "events_pending": [],
            "recurring_applied": [],
            "net_change": 0
        }
        
        # If paused at event, identify pending events but don't apply them yet
        if paused_at_event:
            pending_events = self._get_pending_events(new_date)
            changes["events_pending"] = pending_events
        
        # Apply recurring income/expenses from assets (affects cash on hand)
        recurring_changes = self._apply_recurring_income_expenses(old_date, new_date)
        changes["recurring_applied"] = recurring_changes["items"]
        changes["net_change"] += recurring_changes["total"]
        
        # Update cash on hand from recurring changes
        self.calendar.cash_on_hand += recurring_changes["total"]
        
        # Update net worth in ledger
        net_worth = self.calculate_net_worth()
        self.ledger.add_entry(new_date.strftime("%Y-%m-%d"), net_worth)
        changes["new_net_worth"] = net_worth
        changes["cash_on_hand"] = self.calendar.cash_on_hand
        
        return changes
    
    def _find_next_event_date(self, start_date: datetime, end_date: datetime) -> Optional[datetime]:
        """Find the next event date between start and end date."""
        next_event_date = None
        
        for event in self.events:
            if event.next_date and start_date < event.next_date <= end_date:
                if next_event_date is None or event.next_date < next_event_date:
                    next_event_date = event.next_date
        
        return next_event_date
    
    def _get_pending_events(self, current_date: datetime) -> List[dict]:
        """Get all events that are due on the current date."""
        pending = []
        
        for event in self.events:
            if event.is_due(current_date):
                pending.append({
                    "id": event.id,
                    "name": event.name,
                    "amount": event.amount,
                    "dice_formula": event.dice_formula,
                    "frequency": event.frequency
                })
        
        return pending
    
    def process_event(self, event_id: str) -> dict:
        """
        Process a specific event manually.
        Returns details about the processed event.
        """
        for event in self.events:
            if event.id == event_id:
                # Calculate the amount (handles dice rolls)
                amount = event.calculate_amount()
                
                # Apply to cash on hand
                self.calendar.cash_on_hand += amount
                
                result = {
                    "name": event.name,
                    "amount": amount,
                    "date": event.next_date.strftime("%Y-%m-%d") if event.next_date else "N/A",
                    "cash_on_hand": self.calendar.cash_on_hand
                }
                
                # Schedule next occurrence or remove if one-time
                if event.frequency == "once":
                    self.events.remove(event)
                else:
                    event.schedule_next_occurrence(self.calendar.current_date)
                
                return result
        
        return None
    
    def _apply_recurring_income_expenses(self, old_date: datetime, 
                                         new_date: datetime) -> dict:
        """Apply recurring income/expenses from assets based on frequency to cash on hand."""
        applied_items = []
        total_change = 0
        
        days_passed = (new_date - old_date).days
        
        for asset in self.assets:
            if asset.frequency == "none":
                continue
            
            # Calculate how many times to apply based on frequency
            occurrences = self._calculate_occurrences(asset.frequency, days_passed)
            
            if occurrences > 0:
                net_change = asset.apply_recurring_income_expense() * occurrences
                total_change += net_change
                
                # Note: We do NOT update asset.value anymore
                # The net_change will be applied to cash_on_hand instead
                
                applied_items.append({
                    "name": asset.name,
                    "frequency": asset.frequency,
                    "occurrences": occurrences,
                    "per_occurrence": asset.apply_recurring_income_expense(),
                    "total_change": net_change
                })
        
        return {
            "items": applied_items,
            "total": total_change
        }
    
    def _calculate_occurrences(self, frequency: str, days_passed: int) -> int:
        """Calculate how many times an event should occur based on frequency."""
        if frequency == "daily":
            return days_passed
        elif frequency == "weekly":
            return days_passed // 7
        elif frequency == "monthly":
            return days_passed // 30
        elif frequency == "quarterly":
            return days_passed // 90
        elif frequency == "yearly":
            return days_passed // 365
        return 0
    
    def calculate_net_worth(self) -> float:
        """Calculate total net worth from all assets plus cash on hand."""
        return sum(asset.get_net_value() for asset in self.assets) + self.calendar.cash_on_hand
    
    def add_asset(self, name: str, value: float, income: float = 0,
                  expense: float = 0, frequency: str = "none") -> Asset:
        """Add a new asset to the portfolio."""
        asset = Asset(name, value, income, expense, frequency)
        self.assets.append(asset)
        return asset
    
    def update_asset(self, asset_id: str, name: str = None, value: float = None,
                    income: float = None, expense: float = None, 
                    frequency: str = None) -> bool:
        """Update an existing asset."""
        for asset in self.assets:
            if asset.id == asset_id:
                if name is not None:
                    asset.name = name
                if value is not None:
                    asset.value = value
                if income is not None:
                    asset.income = income
                if expense is not None:
                    asset.expense = expense
                if frequency is not None:
                    asset.frequency = frequency
                return True
        return False
    
    def remove_asset(self, asset_id: str) -> bool:
        """Remove an asset from the portfolio."""
        for i, asset in enumerate(self.assets):
            if asset.id == asset_id:
                self.assets.pop(i)
                return True
        return False
    
    def add_event(self, name: str, amount: float, frequency: str = "once",
                  next_date: str = None, dice_formula: str = None) -> FinancialEvent:
        """Add a new financial event."""
        event = FinancialEvent(name, amount, frequency, next_date, dice_formula)
        self.events.append(event)
        return event
    
    def update_event(self, event_id: str, name: str = None, amount: float = None,
                    frequency: str = None, next_date: str = None,
                    dice_formula: str = None) -> bool:
        """Update an existing financial event."""
        for event in self.events:
            if event.id == event_id:
                if name is not None:
                    event.name = name
                if amount is not None:
                    event.amount = amount
                if frequency is not None:
                    event.frequency = frequency
                if next_date is not None:
                    event.next_date = datetime.strptime(next_date, "%Y-%m-%d")
                if dice_formula is not None:
                    event.dice_formula = dice_formula
                return True
        return False
    
    def remove_event(self, event_id: str) -> bool:
        """Remove a financial event."""
        for i, event in enumerate(self.events):
            if event.id == event_id:
                self.events.pop(i)
                return True
        return False
    
    def get_summary(self) -> dict:
        """Get a summary of the current financial state."""
        net_worth = self.calculate_net_worth()
        total_income = sum(a.income for a in self.assets if a.frequency != "none")
        total_expenses = sum(a.expense for a in self.assets if a.frequency != "none")
        
        return {
            "current_date": self.calendar.get_date_string(),
            "net_worth": net_worth,
            "total_assets": len(self.assets),
            "total_events": len(self.events),
            "monthly_income": total_income,
            "monthly_expenses": total_expenses,
            "monthly_net": total_income - total_expenses
        }
