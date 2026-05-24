
# RPG Inventory Manager (v1)

## Purpose & Scope

**Purpose (one sentence):** Enable tabletop RPG players to easily manage their character inventory, item details, and buying/selling from a curated, game‑relevant item list—making shopping faster, clearer, and more engaging.

**Primary outcome:**
- Simplify item management and currency handling.
- Speed up shopping interactions.
- Reduce abstraction by showing prices, weights, and item details.

**Non‑goals (v1):**
1. No “gamemaster” editing tools inside the app.
2. No external API exposure.
3. Not distributed via app stores.

---

## Users & Context

- **User types:** Players; Game Masters (as ordinary players; no admin features in-app).
- **Environment:** Local area network; clients on phones/desktops/tablets via browser.
- **Access model:** Username‑only login (no passwords). Unique usernames enforced. Sessions persist until server restart.

---

## Core Scenarios

1. **Login & player separation:** Unique username → user sees their inventory view.
2. **View & manage inventory:** See items (name/qty/price/weight); can “use” or “drop” items (quantity change/removal only).
3. **Store browsing & transactions:** View store items from CSV; buy/sell with in‑game currency tracked per player.
4. **Encumbrance warning:** App warns if total carried weight exceeds a configurable limit (no hard block).
5. **Auto‑save on change:** Player inventory is saved immediately to JSON; store items auto‑loaded on startup from CSV.

**Edge cases:** Large inventories/catalogs; insufficient funds; encumbrance exceeded; item not found.

---

## Interfaces & Contracts

- **Primary interface:** Single‑page web app (SPA) served by Flask. Actions trigger full‑page reload rather than AJAX.
- **UI style:** Final Fantasy‑inspired: blue windows, white LCD‑style text, white trim. Mouse‑driven; keyboard only for text/value input.

**Backend endpoints (minimal):**
- `GET /` → login page (if not logged in) or main SPA (inventory+store).
- `POST /login` → start session for `username` (enforce unique).
- `POST /logout` → end session.
- `POST /inventory/use` → use item (decrement qty; remove if 0).
- `POST /inventory/drop` → drop item (remove or decrement).
- `POST /store/buy` → purchase item (currency −= price; inventory qty += 1; warn if encumbrance exceeded).
- `POST /store/sell` → sell item (currency += sell price; inventory qty −= 1; remove if 0).

> Note: Actions post to endpoints and then redirect back to `/` to reload the updated view.

**Session model:** Simple server‑side session keyed by username (Flask session cookie). No passwords; usernames must be unique. Sessions persist until server restart or explicit logout.

---

## Data Schema & Storage

**Store Catalog (CSV columns):**
- `id` (string UUID)
- `name` (string, ≤100)
- `description` (string, optional)
- `price` (integer ≥0; buy price)
- `sell_price` (integer ≥0; default = price unless provided)
- `weight` (float ≥0)
- `category` (string: weapon/armor/consumable/etc.)

**Player Inventory (per‑user JSON file, e.g., `data/inventory_<username>.json`):**
```json
{
  "player": "string",
  "currency": 1234,
  "encumbrance_limit": 100.0,
  "items": [
    { "id": "uuid", "name": "string", "qty": 2, "weight": 0.5, "price": 10, "sell_price": 5, "category": "consumable" }
  ]
}
```

**Derived values:** `total_weight = sum(item.weight * item.qty)`; `encumbrance_exceeded = total_weight > encumbrance_limit`.

**Files:** Store CSV: `data/store_items.csv` (auto‑load on startup). Inventories: `data/inventory_<username>.json` (auto‑save on change). Log: `logs/log.txt` (append‑only).

---

## Error Model & Messages

Simple text banners (no JSON):
- 400: “Insufficient funds.”
- 404: “Item not found.”
- 409: “Username already in use.”
- Warning: “Encumbrance limit exceeded.” (purchase still succeeds)

---

## Quality Attributes

- **Performance:** “Run smoothly” on typical lab hardware; no hard targets in v1.
- **Portability & setup:** No admin rights; single `main.py` file; clients connect via LAN.
- **Reliability:** Immediate auto‑save; atomic writes.
- **Security:** Username‑only; no passwords/roles/PII.

---

## Logging & Observability

Append to `logs/log.txt` with ISO timestamp, username, action, item id/name, qty delta, currency delta, e.g.:
```
2025-12-10T16:20:33Z | philip | BUY | id=abc123 | +1 qty | -10 currency
```

Telemetry: none.

---

## Import/Export & Migration

- **Import:** Store CSV auto‑loads on startup; if missing/malformed, app shows banner and uses empty store.
- **Export (optional):** “Export All” creates `data/inventories_export.csv` snapshot of all player inventories.
- **Migration:** Overwrite old files; best‑effort defaults on schema changes.

---

## Risks & Mitigations

- **Risk:** Players logging in as each other.
- **Mitigation:** Enforce unique usernames; trust‑based usage; no PIN/password.

---

## Success Metrics & Release Plan

- **Success:** Quick, easy, interactive; flexible to modify locally; minimal setup.
- **Release plan (suggested):**
  - **Alpha (Day 1–2):** Login, inventory, store list, buy/sell, auto‑save, FF theme MVP.
  - **Beta (Day 3–4):** Encumbrance warning, use/drop, logging, error banners.
  - **v1 (Day 5):** Export all inventories, styling polish.

---

## Setup & Running

1. **Install dependencies:**
   ```bash
   pip install flask
   ```
2. **Prepare data:** Edit `data/store_items.csv` (sample provided). Optionally create per‑user inventory JSONs (they auto‑create on first login).
3. **Run the server:**
   ```bash
   python main.py
   ```
4. **Connect from clients:** Open `http://<server-ip>:5001/` in a browser; enter a unique username.

**Notes:**
- Inventories auto‑save on each action.
- Logs are written to `logs/log.txt`.
- To reset sessions, restart the server.
