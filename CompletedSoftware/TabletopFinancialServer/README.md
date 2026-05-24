# Tabletop Campaign Finance Manager

A web-based application for managing finances and scheduling in tabletop RPG campaigns. Run locally and share with your gaming group over LAN.

## Features

- **Calendar Management**: Track in-game dates and advance time by days, weeks, or months
- **Cash on Hand**: Dedicated tracking for liquid currency separate from asset values
- **Asset & Liability Tracking**: Manage ships, properties, stocks, and debts
- **Recurring Income/Expenses**: Automatic cash flow from assets (affects cash on hand, not asset value)
- **Financial Events**: Schedule one-time or recurring events with optional dice roll formulas (e.g., "2d6+10")
- **Event Pause System**: Time advancement pauses at scheduled events for manual processing
- **Financial Graphs**: Visualize net worth over time and income vs expenses
- **Data Persistence**: Save and load campaign data as human-readable JSON files
- **Multi-User Support**: Access from any device on your local network

## Installation

### Requirements

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Install Dependencies**

```bash
pip install -r requirements.txt
```

2. **Run the Application**

```bash
python app.py
```

3. **Access the Dashboard**

Open your web browser and navigate to:
- Local access: `http://localhost:5000`
- LAN access: `http://<your-ip-address>:5000`

To find your IP address:
- Windows: Run `ipconfig` and look for IPv4 Address
- Mac/Linux: Run `ifconfig` or `ip addr`

## Usage Guide

### Time Management

- **Advance Time**: Click "+1 Day", "+1 Week", or "+1 Month" buttons
- **Set Date**: Click "📅 Set Date" to jump to a specific date
- **Event Pausing**: When advancing time, the system pauses at the next scheduled event
  - A modal appears showing pending events
  - Process events manually to apply them to cash on hand
  - Events can involve dice rolls for variable amounts
- Advancing time automatically applies recurring income/expenses to cash on hand

### Cash on Hand

- Click on the "Cash on Hand" value in the summary bar to edit it
- This represents liquid currency available for spending
- Recurring income/expenses from assets affect cash on hand
- Events affect cash on hand when processed
- Net worth = Total asset values + Cash on hand

### Managing Assets

1. Click "+ Add Asset" in the Assets & Liabilities panel
2. Fill in the form:
   - **Name**: Asset name (e.g., "House", "Merchant Ship")
   - **Value**: Current value in gold (e.g., 150000 for a house)
   - **Income**: Recurring income amount (e.g., rent collected)
   - **Expense**: Recurring expense amount (e.g., 300 for monthly electric bill)
   - **Frequency**: How often income/expenses apply (none, daily, weekly, monthly, quarterly, yearly)
3. Click "Save"

**Important**: Income and expense on assets affect **cash on hand**, not the asset value itself. For example:
- A house worth 150,000 with a 300 monthly electric bill will keep its 150,000 value
- The 300 expense is deducted from cash on hand each month
- This represents operational costs or depreciation, not changes to asset value

**Editing**: Click the ✏️ icon next to any asset
**Deleting**: Click the 🗑️ icon next to any asset

### Managing Events

1. Click "+ Add Event" in the Scheduled Events panel
2. Fill in the form:
   - **Name**: Event name (e.g., "Quarterly Tax Payment")
   - **Amount**: Positive for income, negative for expenses
   - **Frequency**: once, daily, weekly, monthly, quarterly, yearly
   - **Next Date**: When the event should first occur
   - **Dice Formula** (optional): Variable amounts using dice notation
3. Click "Save"

**Dice Formula Examples**:
- `2d6+10` - Roll 2 six-sided dice and add 10
- `3d10-5` - Roll 3 ten-sided dice and subtract 5
- `1d20` - Roll 1 twenty-sided die

### Import/Export Data

1. Click "📁 Import/Export" in the header
2. **Export**: Download current campaign data as JSON
3. **Import**: Upload a previously saved JSON file

The JSON file is human-readable and can be edited manually if needed.

## Data Structure

Campaign data is stored in `data/campaign_data.json`:

```json
{
  "calendar": {
    "current_date": "2024-01-15",
    "cash_on_hand": 5000.00
  },
  "assets": [
    {
      "id": "uuid",
      "name": "Merchant Ship",
      "value": 50000,
      "income": 500,
      "expense": 200,
      "frequency": "monthly"
    }
  ],
  "events": [
    {
      "id": "uuid",
      "name": "Quarterly Tax",
      "amount": -1000,
      "frequency": "quarterly",
      "next_date": "2024-04-01",
      "dice_formula": null
    }
  ],
  "ledger": [
    {
      "date": "2024-01-01",
      "net_worth": 48000
    }
  ]
}
```

## Network Access

To allow other players on your LAN to connect:

1. Make sure the Flask server is running (`python app.py`)
2. Find your computer's local IP address
3. Share the URL: `http://<your-ip>:5000` with your players
4. Ensure your firewall allows connections on port 5000

**Note**: The server runs with `host='0.0.0.0'` which allows LAN access. This is safe for local networks but should not be exposed to the internet.

## Tips

- Set up recurring income/expenses on assets for passive revenue streams
- Use financial events for one-time transactions or irregular income
- Advance time incrementally to see how income/expenses accumulate
- Export your data regularly as a backup
- The net worth graph shows historical financial trends
- Dice formulas add variability to events (perfect for trading income, random events, etc.)

## Troubleshooting

**Port already in use**: If port 5000 is already in use, modify `app.py` line:
```python
app.run(host='0.0.0.0', port=5000, debug=True)
```
Change `5000` to another port like `5001` or `8000`.

**Cannot connect from other devices**: 
- Check firewall settings
- Ensure devices are on the same network
- Verify the IP address is correct

**Data not saving**: Check that the `data/` directory exists and is writable.

## License

This project is open source and available for personal use.
