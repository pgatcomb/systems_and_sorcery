from flask import Flask, request, redirect, url_for, session, render_template
import json
import csv
import os
from datetime import datetime, timezone
from uuid import uuid4

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Change in production

store_items = []
active_users = set()

def load_store():
    global store_items
    try:
        with open('data/store_items.csv', 'r') as f:
            reader = csv.DictReader(f)
            store_items = list(reader)
            for item in store_items:
                item['price'] = int(item['price'])
                item['sell_price'] = int(item.get('sell_price', item['price']))
                item['weight'] = float(item['weight'])
    except FileNotFoundError:
        store_items = []
    except Exception as e:
        print(f"Error loading store: {e}")
        store_items = []

def save_inventory(username, inventory):
    os.makedirs('data', exist_ok=True)
    with open(f'data/inventory_{username}.json', 'w') as f:
        json.dump(inventory, f, indent=2)

def load_inventory(username):
    try:
        with open(f'data/inventory_{username}.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "player": username,
            "currency": 1000,
            "encumbrance_limit": 100.0,
            "items": []
        }

def log_action(username, action, item_id=None, item_name=None, qty_delta=0, currency_delta=0):
    timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    entry = f"{timestamp} | {username} | {action}"
    if item_id or item_name:
        entry += f" | id={item_id}"
        if item_name:
            entry += f" name={item_name}"
    if qty_delta != 0:
        entry += f" | {qty_delta:+d} qty"
    if currency_delta != 0:
        entry += f" | {currency_delta:+d} currency"
    with open('logs/log.txt', 'a') as f:
        f.write(entry + '\n')

def calculate_total_weight(inventory):
    return sum(item['weight'] * item['qty'] for item in inventory['items'])

@app.route('/', methods=['GET'])
def index():
    banner = None
    if 'banner' in request.args:
        banner = request.args.get('banner')
    sort_by = request.args.get('sort_by')
    order = request.args.get('order', 'asc')
    sorted_store_items = store_items
    if sort_by and sort_by in ['name', 'price', 'description', 'category']:
        reverse = order == 'desc'
        sorted_store_items = sorted(store_items, key=lambda i: i.get(sort_by, ''), reverse=reverse)
    if 'user' not in session:
        return render_template('index.html', logged_in=False, banner=banner, store_items=sorted_store_items, sort_by=sort_by, order=order)
    username = session['user']
    inventory = load_inventory(username)
    inventory['total_weight'] = calculate_total_weight(inventory)
    inventory_exceeded = inventory['total_weight'] > inventory['encumbrance_limit']
    return render_template('index.html', logged_in=True, inventory=inventory, store_items=sorted_store_items, exceeded=inventory_exceeded, banner=banner, sort_by=sort_by, order=order)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    if not username:
        return redirect(url_for('index', banner='400:%20Invalid%20username.'))
    if username in active_users:
        return redirect(url_for('index', banner='409:%20Username%20already%20in%20use.'))
    active_users.add(username)
    session['user'] = username
    load_inventory(username)  # Ensure created
    log_action(username, 'LOGIN')
    return redirect(url_for('index', **request.args))

@app.route('/logout', methods=['POST'])
def logout():
    if 'user' in session:
        username = session.pop('user')
        active_users.discard(username)
        log_action(username, 'LOGOUT')
    return redirect(url_for('index', **request.args))

@app.route('/inventory/use', methods=['POST'])
def use_item():
    if 'user' not in session:
        return redirect(url_for('index', **request.args))
    username = session['user']
    item_id = request.form.get('id')
    inventory = load_inventory(username)
    item = next((i for i in inventory['items'] if i['id'] == item_id), None)
    if not item:
        return redirect(url_for('index', banner='404:%20Item%20not%20found.', **request.args))
    item['qty'] -= 1
    qty_delta = -1
    if item['qty'] <= 0:
        inventory['items'].remove(item)
        qty_delta = -item['qty'] if item['qty'] < 0 else 1  # But since -=1, if was 1, remove
    save_inventory(username, inventory)
    log_action(username, 'USE', item_id, item['name'], qty_delta)
    return redirect(url_for('index', **request.args))

@app.route('/inventory/drop', methods=['POST'])
def drop_item():
    if 'user' not in session:
        return redirect(url_for('index', **request.args))
    username = session['user']
    item_id = request.form.get('id')
    inventory = load_inventory(username)
    item = next((i for i in inventory['items'] if i['id'] == item_id), None)
    if not item:
        return redirect(url_for('index', banner='404:%20Item%20not%20found.', **request.args))
    if item['qty'] > 1:
        qty_delta = -1
        item['qty'] -= 1
    else:
        qty_delta = -1
        inventory['items'].remove(item)
    save_inventory(username, inventory)
    log_action(username, 'DROP', item_id, item['name'], qty_delta)
    return redirect(url_for('index', **request.args))

@app.route('/store/buy', methods=['POST'])
def buy_item():
    if 'user' not in session:
        return redirect(url_for('index', **request.args))
    username = session['user']
    item_id = request.form.get('id')
    store_item = next((i for i in store_items if i['id'] == item_id), None)
    if not store_item:
        return redirect(url_for('index', banner='404:%20Item%20not%20found.', **request.args))
    inventory = load_inventory(username)
    if inventory['currency'] < store_item['price']:
        return redirect(url_for('index', banner='400:%20Insufficient%20funds.', **request.args))
    inventory['currency'] -= store_item['price']
    currency_delta = -store_item['price']
    # Add to inventory
    inv_item = next((i for i in inventory['items'] if i['id'] == item_id), None)
    if inv_item:
        inv_item['qty'] += 1
        qty_delta = 1
    else:
        new_item = {
            'id': store_item['id'],
            'name': store_item['name'],
            'qty': 1,
            'weight': store_item['weight'],
            'price': store_item['price'],
            'sell_price': store_item['sell_price'],
            'category': store_item['category']
        }
        inventory['items'].append(new_item)
        qty_delta = 1
    total_weight = sum(item['weight'] * item['qty'] for item in inventory['items'])
    banner = None
    if total_weight > inventory['encumbrance_limit']:
        banner = 'Warning:%20Encumbrance%20limit%20exceeded.'
    save_inventory(username, inventory)
    log_action(username, 'BUY', item_id, store_item['name'], qty_delta, currency_delta)
    if banner:
        return redirect(url_for('index', banner=banner, **request.args))
    else:
        return redirect(url_for('index', **request.args))

@app.route('/store/sell', methods=['POST'])
def sell_item():
    if 'user' not in session:
        return redirect(url_for('index', **request.args))
    username = session['user']
    item_id = request.form.get('id')
    inventory = load_inventory(username)
    item = next((i for i in inventory['items'] if i['id'] == item_id), None)
    if not item:
        return redirect(url_for('index', banner='404:%20Item%20not%20found.', **request.args))
    sell_price = item['sell_price']
    inventory['currency'] += sell_price
    currency_delta = sell_price
    if item['qty'] > 1:
        qty_delta = -1
        item['qty'] -= 1
    else:
        qty_delta = -1
        inventory['items'].remove(item)
    save_inventory(username, inventory)
    log_action(username, 'SELL', item_id, item['name'], qty_delta, currency_delta)
    return redirect(url_for('index', **request.args))

@app.route('/store/add', methods=['POST'])
def add_item():
    if 'user' not in session:
        return redirect(url_for('index', **request.args))
    username = session['user']
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    price_str = request.form.get('price', '').strip()
    sell_price_str = request.form.get('sell_price', '').strip()
    weight_str = request.form.get('weight', '').strip()
    category = request.form.get('category', '').strip()
    if not name:
        return redirect(url_for('index', banner='400:%20Name%20is%20required.', **request.args))
    try:
        price = int(price_str)
        if price < 0:
            raise ValueError
    except ValueError:
        return redirect(url_for('index', banner='400:%20Invalid%20price.', **request.args))
    try:
        weight = float(weight_str)
        if weight < 0:
            raise ValueError
    except ValueError:
        return redirect(url_for('index', banner='400:%20Invalid%20weight.', **request.args))
    sell_price = price
    if sell_price_str:
        try:
            sell_price = int(sell_price_str)
            if sell_price < 0:
                raise ValueError
        except ValueError:
            return redirect(url_for('index', banner='400:%20Invalid%20sell_price.', **request.args))
    item_id = str(uuid4())
    new_item = {
        'id': item_id,
        'name': name,
        'description': description,
        'price': price,
        'sell_price': sell_price,
        'weight': weight,
        'category': category
    }
    global store_items
    store_items.append(new_item)
    os.makedirs('data', exist_ok=True)
    with open('data/store_items.csv', 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'name', 'description', 'price', 'sell_price', 'weight', 'category'])
        writer.writerow(new_item)
    log_action(username, 'ADD_ITEM', item_id, name)
    return redirect(url_for('index', banner='Item%20added%20successfully.', **request.args))

if __name__ == '__main__':
    load_store()
    app.run(debug=False, host='0.0.0.0', port=5001)
