"""
Flask application for Tabletop Campaign Finance Manager.
"""
from flask import Flask, render_template, request, jsonify, send_file, Response
import plotly.graph_objs as go
import plotly.io as pio
from io import BytesIO
import json

from models import Calendar, Asset, FinancialEvent, Ledger
from data_manager import DataManager
from finance_logic import FinanceEngine

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tabletop-finance-secret-key'

# Initialize data manager
data_manager = DataManager()

# Load initial data
data = data_manager.load_data()
calendar, assets, events, ledger = data_manager.parse_loaded_data(data)

# Initialize finance engine
finance_engine = FinanceEngine(calendar, assets, events, ledger)


def save_current_state():
    """Save the current game state to JSON."""
    data_manager.save_data(calendar, assets, events, ledger)


@app.route('/')
def index():
    """Render the main dashboard."""
    summary = finance_engine.get_summary()
    return render_template('dashboard.html',
                         calendar=calendar,
                         assets=assets,
                         events=events,
                         summary=summary,
                         asset_frequencies=Asset.FREQUENCY_OPTIONS,
                         event_frequencies=FinancialEvent.FREQUENCY_OPTIONS)


@app.route('/api/advance_time', methods=['POST'])
def advance_time():
    """Advance the calendar by the specified amount."""
    data = request.json
    time_unit = data.get('unit', 'day')
    
    days = 0
    if time_unit == 'day':
        days = 1
    elif time_unit == 'week':
        days = 7
    elif time_unit == 'month':
        days = 30
    
    changes = finance_engine.advance_time(days)
    save_current_state()
    
    summary = finance_engine.get_summary()
    summary['cash_on_hand'] = calendar.cash_on_hand
    
    return jsonify({
        'success': True,
        'changes': changes,
        'summary': summary
    })


@app.route('/api/set_date', methods=['POST'])
def set_date():
    """Set the calendar to a specific date."""
    data = request.json
    new_date = data.get('date')
    
    try:
        calendar.set_date(new_date)
        save_current_state()
        
        summary = finance_engine.get_summary()
        summary['cash_on_hand'] = calendar.cash_on_hand
        return jsonify({
            'success': True,
            'date': calendar.get_date_string(),
            'summary': summary
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/cash_on_hand', methods=['PUT'])
def update_cash_on_hand():
    """Update the cash on hand value."""
    data = request.json
    
    try:
        calendar.cash_on_hand = float(data['amount'])
        save_current_state()
        
        summary = finance_engine.get_summary()
        summary['cash_on_hand'] = calendar.cash_on_hand
        return jsonify({
            'success': True,
            'cash_on_hand': calendar.cash_on_hand,
            'summary': summary
        })
    except (KeyError, ValueError) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/events/<event_id>/process', methods=['POST'])
def process_event(event_id):
    """Process a pending event."""
    result = finance_engine.process_event(event_id)
    
    if result:
        save_current_state()
        summary = finance_engine.get_summary()
        summary['cash_on_hand'] = calendar.cash_on_hand
        
        return jsonify({
            'success': True,
            'event': result,
            'summary': summary
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Event not found'
        }), 404


@app.route('/api/assets', methods=['GET'])
def get_assets():
    """Get all assets."""
    return jsonify({
        'assets': [asset.to_dict() for asset in assets]
    })


@app.route('/api/assets', methods=['POST'])
def add_asset():
    """Add a new asset."""
    data = request.json
    
    try:
        asset = finance_engine.add_asset(
            name=data['name'],
            value=float(data['value']),
            income=float(data.get('income', 0)),
            expense=float(data.get('expense', 0)),
            frequency=data.get('frequency', 'none')
        )
        save_current_state()
        
        return jsonify({
            'success': True,
            'asset': asset.to_dict()
        })
    except (KeyError, ValueError) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/assets/<asset_id>', methods=['PUT'])
def update_asset(asset_id):
    """Update an existing asset."""
    data = request.json
    
    try:
        success = finance_engine.update_asset(
            asset_id=asset_id,
            name=data.get('name'),
            value=float(data['value']) if 'value' in data else None,
            income=float(data['income']) if 'income' in data else None,
            expense=float(data['expense']) if 'expense' in data else None,
            frequency=data.get('frequency')
        )
        
        if success:
            save_current_state()
            return jsonify({'success': True})
        else:
            return jsonify({
                'success': False,
                'error': 'Asset not found'
            }), 404
    except (ValueError, KeyError) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/assets/<asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    """Delete an asset."""
    success = finance_engine.remove_asset(asset_id)
    
    if success:
        save_current_state()
        return jsonify({'success': True})
    else:
        return jsonify({
            'success': False,
            'error': 'Asset not found'
        }), 404


@app.route('/api/events', methods=['GET'])
def get_events():
    """Get all financial events."""
    return jsonify({
        'events': [event.to_dict() for event in events]
    })


@app.route('/api/events', methods=['POST'])
def add_event():
    """Add a new financial event."""
    data = request.json
    
    try:
        event = finance_engine.add_event(
            name=data['name'],
            amount=float(data['amount']),
            frequency=data.get('frequency', 'once'),
            next_date=data.get('next_date'),
            dice_formula=data.get('dice_formula')
        )
        save_current_state()
        
        return jsonify({
            'success': True,
            'event': event.to_dict()
        })
    except (KeyError, ValueError) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    """Update an existing financial event."""
    data = request.json
    
    try:
        success = finance_engine.update_event(
            event_id=event_id,
            name=data.get('name'),
            amount=float(data['amount']) if 'amount' in data else None,
            frequency=data.get('frequency'),
            next_date=data.get('next_date'),
            dice_formula=data.get('dice_formula')
        )
        
        if success:
            save_current_state()
            return jsonify({'success': True})
        else:
            return jsonify({
                'success': False,
                'error': 'Event not found'
            }), 404
    except (ValueError, KeyError) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Delete a financial event."""
    success = finance_engine.remove_event(event_id)
    
    if success:
        save_current_state()
        return jsonify({'success': True})
    else:
        return jsonify({
            'success': False,
            'error': 'Event not found'
        }), 404


@app.route('/api/graph/networth')
def graph_networth():
    """Generate net worth over time graph."""
    entries = ledger.get_entries()
    
    if not entries:
        # Return empty graph if no data
        fig = go.Figure()
        fig.update_layout(
            title="Net Worth Over Time (No Data)",
            xaxis_title="Date",
            yaxis_title="Net Worth",
            template="plotly_white"
        )
    else:
        dates = [entry.date for entry in entries]
        values = [entry.net_worth for entry in entries]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name='Net Worth',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Net Worth Over Time",
            xaxis_title="Date",
            yaxis_title="Net Worth (Gold)",
            template="plotly_white",
            hovermode='x unified',
            height=400
        )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')


@app.route('/api/graph/income_expense')
def graph_income_expense():
    """Generate income vs expense comparison graph."""
    # Calculate total monthly income and expenses
    total_income = sum(a.income for a in assets if a.frequency == "monthly")
    total_expenses = sum(a.expense for a in assets if a.frequency == "monthly")
    
    categories = ['Monthly Income', 'Monthly Expenses', 'Net']
    values = [total_income, total_expenses, total_income - total_expenses]
    colors = ['#06A77D', '#D62828', '#F77F00' if total_income >= total_expenses else '#D62828']
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categories,
        y=values,
        marker_color=colors,
        text=values,
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Monthly Income vs Expenses",
        yaxis_title="Amount (Gold)",
        template="plotly_white",
        height=400,
        showlegend=False
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')


@app.route('/api/export')
def export_data():
    """Export all data as JSON file."""
    json_data = data_manager.export_to_json(calendar, assets, events, ledger)
    
    # Create a file-like object
    buffer = BytesIO()
    buffer.write(json_data.encode('utf-8'))
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name='campaign_data.json',
        mimetype='application/json'
    )


@app.route('/api/import', methods=['POST'])
def import_data():
    """Import data from uploaded JSON file."""
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file uploaded'
        }), 400
    
    file = request.files['file']
    
    try:
        json_string = file.read().decode('utf-8')
        imported_data = data_manager.import_from_json(json_string)
        
        # Parse and update global state
        global calendar, assets, events, ledger, finance_engine
        calendar, assets, events, ledger = data_manager.parse_loaded_data(imported_data)
        finance_engine = FinanceEngine(calendar, assets, events, ledger)
        
        # Save the imported data
        save_current_state()
        
        summary = finance_engine.get_summary()
        return jsonify({
            'success': True,
            'summary': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


if __name__ == '__main__':
    # Run on all network interfaces to allow LAN access
    app.run(host='0.0.0.0', port=5000, debug=True)
