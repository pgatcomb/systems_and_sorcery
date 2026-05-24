"""
Data models for the Tabletop Campaign Finance application.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid
import re
import random


class Calendar:
    """Manages the game calendar and date tracking."""
    
    def __init__(self, current_date: str = None, cash_on_hand: float = 0):
        """Initialize calendar with a starting date and cash on hand."""
        if current_date:
            self.current_date = datetime.strptime(current_date, "%Y-%m-%d")
        else:
            self.current_date = datetime.now()
        self.cash_on_hand = cash_on_hand
    
    def advance_days(self, days: int):
        """Advance the calendar by a number of days."""
        self.current_date += timedelta(days=days)
    
    def advance_weeks(self, weeks: int):
        """Advance the calendar by a number of weeks."""
        self.advance_days(weeks * 7)
    
    def advance_months(self, months: int):
        """Advance the calendar by a number of months (approximate)."""
        # Approximate month as 30 days for simplicity
        self.advance_days(months * 30)
    
    def set_date(self, date_string: str):
        """Set the calendar to a specific date."""
        self.current_date = datetime.strptime(date_string, "%Y-%m-%d")
    
    def get_date_string(self) -> str:
        """Get the current date as a formatted string."""
        return self.current_date.strftime("%Y-%m-%d")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "current_date": self.get_date_string(),
            "cash_on_hand": self.cash_on_hand
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create Calendar from dictionary."""
        return cls(
            current_date=data.get("current_date"),
            cash_on_hand=data.get("cash_on_hand", 0)
        )


class Asset:
    """Represents an asset or liability in the campaign."""
    
    FREQUENCY_OPTIONS = ["none", "daily", "weekly", "monthly", "quarterly", "yearly"]
    
    def __init__(self, name: str, value: float, income: float = 0, 
                 expense: float = 0, frequency: str = "none", asset_id: str = None):
        """Initialize an asset/liability."""
        self.id = asset_id or str(uuid.uuid4())
        self.name = name
        self.value = value
        self.income = income
        self.expense = expense
        self.frequency = frequency if frequency in self.FREQUENCY_OPTIONS else "none"
    
    def get_net_value(self) -> float:
        """Get the net value of this asset."""
        return self.value
    
    def apply_recurring_income_expense(self) -> float:
        """Calculate net change from income and expenses."""
        return self.income - self.expense
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "income": self.income,
            "expense": self.expense,
            "frequency": self.frequency
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create Asset from dictionary."""
        return cls(
            name=data["name"],
            value=data["value"],
            income=data.get("income", 0),
            expense=data.get("expense", 0),
            frequency=data.get("frequency", "none"),
            asset_id=data.get("id")
        )


class FinancialEvent:
    """Represents a scheduled financial event."""
    
    FREQUENCY_OPTIONS = ["once", "daily", "weekly", "monthly", "quarterly", "yearly"]
    
    def __init__(self, name: str, amount: float, frequency: str = "once",
                 next_date: str = None, dice_formula: str = None, event_id: str = None):
        """Initialize a financial event."""
        self.id = event_id or str(uuid.uuid4())
        self.name = name
        self.amount = amount
        self.frequency = frequency if frequency in self.FREQUENCY_OPTIONS else "once"
        self.next_date = datetime.strptime(next_date, "%Y-%m-%d") if next_date else None
        self.dice_formula = dice_formula  # e.g., "2d6+10" for variable amounts
    
    def calculate_amount(self) -> float:
        """Calculate the event amount, including dice rolls if applicable."""
        if self.dice_formula:
            return self._roll_dice(self.dice_formula)
        return self.amount
    
    def _roll_dice(self, formula: str) -> float:
        """Parse and roll dice formula (e.g., '2d6+10')."""
        try:
            # Match patterns like "2d6", "3d10+5", "1d20-3"
            match = re.match(r'(\d+)d(\d+)([+-]\d+)?', formula.lower())
            if match:
                num_dice = int(match.group(1))
                die_size = int(match.group(2))
                modifier = int(match.group(3)) if match.group(3) else 0
                
                total = sum(random.randint(1, die_size) for _ in range(num_dice))
                return float(total + modifier)
        except Exception:
            pass
        return self.amount
    
    def schedule_next_occurrence(self, current_date: datetime):
        """Schedule the next occurrence based on frequency."""
        if self.frequency == "once":
            self.next_date = None
        elif self.frequency == "daily":
            self.next_date = current_date + timedelta(days=1)
        elif self.frequency == "weekly":
            self.next_date = current_date + timedelta(weeks=1)
        elif self.frequency == "monthly":
            self.next_date = current_date + timedelta(days=30)
        elif self.frequency == "quarterly":
            self.next_date = current_date + timedelta(days=90)
        elif self.frequency == "yearly":
            self.next_date = current_date + timedelta(days=365)
    
    def is_due(self, current_date: datetime) -> bool:
        """Check if the event is due on or before the current date."""
        if self.next_date is None:
            return False
        return self.next_date <= current_date
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "amount": self.amount,
            "frequency": self.frequency,
            "next_date": self.next_date.strftime("%Y-%m-%d") if self.next_date else None,
            "dice_formula": self.dice_formula
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create FinancialEvent from dictionary."""
        return cls(
            name=data["name"],
            amount=data["amount"],
            frequency=data.get("frequency", "once"),
            next_date=data.get("next_date"),
            dice_formula=data.get("dice_formula"),
            event_id=data.get("id")
        )


class LedgerEntry:
    """Represents a single entry in the financial ledger."""
    
    def __init__(self, date: str, net_worth: float):
        """Initialize a ledger entry."""
        self.date = datetime.strptime(date, "%Y-%m-%d")
        self.net_worth = net_worth
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "date": self.date.strftime("%Y-%m-%d"),
            "net_worth": self.net_worth
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create LedgerEntry from dictionary."""
        return cls(date=data["date"], net_worth=data["net_worth"])


class Ledger:
    """Manages the historical financial ledger."""
    
    def __init__(self):
        """Initialize an empty ledger."""
        self.entries: List[LedgerEntry] = []
    
    def add_entry(self, date: str, net_worth: float):
        """Add a new ledger entry."""
        entry = LedgerEntry(date, net_worth)
        self.entries.append(entry)
    
    def get_entries(self) -> List[LedgerEntry]:
        """Get all ledger entries sorted by date."""
        return sorted(self.entries, key=lambda x: x.date)
    
    def to_dict(self) -> List[Dict]:
        """Convert to list of dictionaries for JSON serialization."""
        return [entry.to_dict() for entry in self.entries]
    
    @classmethod
    def from_dict(cls, data: List[Dict]):
        """Create Ledger from list of dictionaries."""
        ledger = cls()
        ledger.entries = [LedgerEntry.from_dict(entry) for entry in data]
        return ledger
