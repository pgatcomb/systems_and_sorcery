#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FFXIV Housing Opportunity Scanner (standalone)

- Discovers housing/furnishing items via Teamcraft open data.
- Excludes gear using Teamcraft's equip-slot mapping.
- Pulls Universalis aggregated stats (median/min price, daily sale velocity).
- (Optionally) pulls listing counts for scarcity.
- Adds craftability info (min recipe level, craft jobs).
- Exports:
    1) ALL items CSV (aggregated stats) for trend tracking.
    2) Ranked shortlist CSV with a Housing Opportunity Score.

Data sources:
  - Universalis REST API (aggregated & current endpoints):
      https://docs.universalis.app/
  - Teamcraft open data (items, categories, equip-slot, recipes):
      https://github.com/ffxiv-teamcraft/ffxiv-teamcraft/tree/staging/libs/data/src/lib/json

Usage:
  pip install requests pandas
  python housing_scanner.py --dc Zalera --output-all housing_all.csv --output-ranked housing_ranked.csv

Author: single-file edition for Philip's workflow
"""
import argparse
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests

# -------------------- Endpoints & defaults --------------------
TEAMCRAFT_ITEMS_URL = "https://raw.githubusercontent.com/ffxiv-teamcraft/ffxiv-teamcraft/staging/libs/data/src/lib/json/items.json"
TEAMCRAFT_ITEM_CATEGORY_URL = "https://raw.githubusercontent.com/ffxiv-teamcraft/ffxiv-teamcraft/staging/libs/data/src/lib/json/item-category.json"
TEAMCRAFT_EQUIP_SLOT_URL = "https://raw.githubusercontent.com/ffxiv-teamcraft/ffxiv-teamcraft/staging/libs/data/src/lib/json/item-equip-slot-category.json"
TEAMCRAFT_RECIPES_PER_ITEM_URL = "https://raw.githubusercontent.com/ffxiv-teamcraft/ffxiv-teamcraft/staging/libs/data/src/lib/json/recipes-per-item.json"
TEAMCRAFT_RECIPES_URL = "https://raw.githubusercontent.com/ffxiv-teamcraft/ffxiv-teamcraft/staging/libs/data/src/lib/json/recipes.json"

UNIVERSALIS_MARKETABLE_URL = "https://universalis.app/api/v2/marketable"  # list[int]
UNIV_AGG_URL = "https://universalis.app/api/v2/aggregated/{dc}/{item}"  # median/min/velocity
UNIV_CURR_URL = "https://universalis.app/api/v2/{dc}/{item}?listings=40"  # listing depth

REQ_TIMEOUT = 25
DEFAULT_SLEEP = 0.12  # stay far below Universalis limits
DEFAULT_KEYWORDS = [
    "furnishing", "furnishings", "furniture",
    "interior", "exterior",
    "wall", "wall-mounted", "wallpaper",
    "floor", "flooring", "ceiling", "ceiling light",
    "lighting", "lamp", "lantern", "chandelier",
    "rug", "carpet",
    "partition", "window", "door",
    "table", "chair", "sofa", "bench", "bookcase", "cabinet", "bed",
    "garden", "outdoor", "fence", "planter", "flowerpot"
]


# -------------------- HTTP helpers --------------------
def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "HousingScanner/1.0 (Universalis+Teamcraft)"})
    return s


def get_json(session: requests.Session, url: str) -> Optional[dict]:
    try:
        r = session.get(url, timeout=REQ_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[warn] GET failed {url}: {e}")
        return None


# -------------------- Teamcraft loaders --------------------
TEAMCRAFT_RECIPE_LVL_TABLE_URL = "https://raw.githubusercontent.com/ffxiv-teamcraft/ffxiv-teamcraft/staging/libs/data/src/lib/json/recipe-level-table.json"

def load_recipe_level_table(session: requests.Session) -> dict[int, int]:
    """
    Map rlvlId -> actual recipe level (best-effort).
    Teamcraft's recipe-level-table.json stores objects keyed by rlvl id.
    We'll prefer fields commonly present like 'classJobLevel' (sometimes 'level', 'lvl').
    """
    data = get_json(session, TEAMCRAFT_RECIPE_LVL_TABLE_URL) or {}
    out: dict[int, int] = {}
    if isinstance(data, dict):
        for k, v in data.items():
            try:
                rlvl_id = int(k)
            except Exception:
                continue
            lvl = None
            if isinstance(v, dict):
                for cand in ("classJobLevel", "level", "Level", "lvl"):
                    val = v.get(cand)
                    if isinstance(val, (int, float)):
                        lvl = int(val)
                        break
            elif isinstance(v, (int, float)):
                lvl = int(v)
            if lvl is not None:
                out[rlvl_id] = lvl
    return out
def load_teamcraft_items_and_cats(session: requests.Session) -> Tuple[dict, dict]:
    items = get_json(session, TEAMCRAFT_ITEMS_URL) or {}
    cats = get_json(session, TEAMCRAFT_ITEM_CATEGORY_URL) or {}
    return items, cats


def load_marketable_ids(session: requests.Session) -> set:
    data = get_json(session, UNIVERSALIS_MARKETABLE_URL) or []
    return set(data)


def load_equip_slots(session: requests.Session) -> dict:
    data = get_json(session, TEAMCRAFT_EQUIP_SLOT_URL) or {}
    out = {}
    for k, v in data.items():
        try:
            out[int(k)] = int(v)
        except Exception:
            continue
    return out


def load_recipes_per_item(session: requests.Session) -> dict:
    data = get_json(session, TEAMCRAFT_RECIPES_PER_ITEM_URL) or {}
    out = {}
    for k, arr in data.items():
        try:
            iid = int(k)
            if isinstance(arr, list):
                out[iid] = [int(x) for x in arr if isinstance(x, (int, str))]
        except Exception:
            continue
    return out


def load_recipes(session: requests.Session) -> dict[int, dict]:
    """
    Return {recipeId: recipeObj}. Teamcraft's recipes.json is very large and
    can be delivered as a list of recipe objects (with an 'id' field) or as a
    dict keyed by recipeId. This handles both.
    """
    data = get_json(session, TEAMCRAFT_RECIPES_URL) or {}

    # Case A: dict keyed by id -> return as-is, cast keys to int
    if isinstance(data, dict):
        out = {}
        for k, rec in data.items():
            try:
                rid = int(k)
            except Exception:
                continue
            if isinstance(rec, dict):
                out[rid] = rec
        return out

    # Case B: list of recipe objects -> index by obj['id'] (or 'recipeId')
    if isinstance(data, list):
        out = {}
        for rec in data:
            if not isinstance(rec, dict):
                continue
            rid = rec.get("id", rec.get("recipeId"))
            try:
                rid = int(rid)
            except Exception:
                continue
            out[rid] = rec
        return out

    # Fallback: unknown shape
    return {}


# -------------------- Category helpers --------------------
def _cat_text(cat_obj) -> str:
    """Normalize Teamcraft category objects to lowercase text."""
    if isinstance(cat_obj, str):
        return cat_obj.strip().lower()
    if isinstance(cat_obj, dict):
        for key in ("en", "name", "en-US", "english"):
            v = cat_obj.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip().lower()
        vals = [str(v).strip() for v in cat_obj.values() if isinstance(v, str) and v.strip()]
        if vals:
            return " ".join(vals).lower()
    return (str(cat_obj) if cat_obj is not None else "").strip().lower()


def is_housing_category(cat_name: str, keywords: List[str]) -> bool:
    if not cat_name:
        return False
    cn = cat_name.lower()
    return any(kw in cn for kw in keywords)


# -------------------- Discovery (housing items, gear excluded) --------------------
def discover_housing_item_ids(session: requests.Session, keywords: List[str], verbose=False) -> List[Tuple[int, str]]:
    items, cats = load_teamcraft_items_and_cats(session)
    marketable = load_marketable_ids(session)
    equip_slots = load_equip_slots(session)

    results = []
    for sid, payload in items.items():
        try:
            iid = int(sid)
        except Exception:
            continue
        if iid not in marketable:
            continue

        # Exclude anything with an equip slot (gear)
        if equip_slots.get(iid, 0) != 0:
            continue

        cat_id = payload.get("category")
        cat_obj = cats.get(str(cat_id)) if cat_id is not None else None
        cat_name = _cat_text(cat_obj)
        if not cat_name:
            ui_cat = payload.get("uiCategory")
            cat_name = _cat_text(ui_cat)

        name = (payload.get("en") or payload.get("name") or str(iid)).strip()
        name_key_hit = any(k in name.lower() for k in (
            "rug", "partition", "wall", "floor", "lamp", "chandelier", "window", "door",
            "table", "chair", "bench", "sofa", "garden", "outdoor", "planter", "fence"
        ))

        if is_housing_category(cat_name, keywords) or name_key_hit:
            results.append((iid, name))

    if verbose:
        print(f"[info] Discovery: {len(results)} housing items identified.")
    return results


# -------------------- Universalis helpers --------------------
def _pick_stat_from_block(block: dict, keys=("averageSalePrice", "medianListing", "minListing"), field="price"):
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
                return float(pd.Series(vals).median())
        elif isinstance(x, dict):
            v = x.get(field)
            if isinstance(v, (int, float)) and v > 0:
                return float(v)
    return None


def _pick_velocity(block: dict) -> Optional[float]:
    if not isinstance(block, dict):
        return None
    x = block.get("dailySaleVelocity") or {}
    for k in ("dc", "region", "world"):
        if isinstance(x.get(k), dict):
            q = x[k].get("quantity")
            if isinstance(q, (int, float)):
                return float(q)
    return None


def agg_stats(session: requests.Session, dc: str, iid: int) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Return (median_sale_price, min_listing_price, daily_sale_velocity)."""
    data = get_json(session, UNIV_AGG_URL.format(dc=dc, item=iid)) or {}
    results = data.get("results") or []
    if not results:
        return None, None, None
    row = next((r for r in results if r.get("itemId") == iid), results[0])

    choices = []
    for side in ("nq", "hq"):
        blk = row.get(side) or {}
        # For furnishings, prefer sales medians first
        median_sale = _pick_stat_from_block(blk, ("averageSalePrice", "medianListing", "minListing"), "price")
        min_listing = _pick_stat_from_block(blk, ("minListing", "medianListing", "averageSalePrice"), "price")
        vel = _pick_velocity(blk)
        if median_sale is not None:
            choices.append((median_sale, min_listing, vel))

    if not choices:
        return None, None, None
    choices.sort(key=lambda t: ((t[2] or 0.0), t[1] is not None), reverse=True)
    return choices[0]


def listing_count(session: requests.Session, dc: str, iid: int, cap: int = 40) -> int:
    data = get_json(session, UNIV_CURR_URL.format(dc=dc, item=iid)) or {}
    lst = data.get("listings") or []
    return min(len(lst), cap)


# -------------------- Craftability (min recipe level & jobs) --------------------
def compute_min_recipe_info(session: requests.Session, iid_list: list[int]) -> dict[int, dict]:
    """
    For each output item, find its associated recipe ids (recipes-per-item.json),
    pull those recipes, and compute:
      - min_recipe_level (using rlvl -> recipeLevel via recipe-level-table.json)
      - craft_jobs (job codes as strings; we keep numeric codes to avoid extra lookups)
    """
    rpi = load_recipes_per_item(session)
    recipes = load_recipes(session)  # <-- now robust to list/dict
    rlvl_table = load_recipe_level_table(session)  # <-- maps rlvl -> level

    info = {}
    for iid in iid_list:
        rids = rpi.get(iid, [])
        levels: list[int] = []
        jobs = set()
        for rid in rids:
            rec = recipes.get(int(rid), {})
            # Teamcraft recipe objects usually carry 'rlvl' and 'job'
            rlvl_raw = rec.get("rlvl")
            job = rec.get("job")
            # Convert rlvl id to an actual level when possible; otherwise use rlvl as-is if numeric
            level = None
            if isinstance(rlvl_raw, (int, float)):
                level = rlvl_table.get(int(rlvl_raw), int(rlvl_raw))
            elif isinstance(rlvl_raw, str) and rlvl_raw.isdigit():
                level = rlvl_table.get(int(rlvl_raw), int(rlvl_raw))
            if isinstance(level, (int, float)):
                levels.append(int(level))
            if job is not None:
                jobs.add(str(job))

        info[iid] = {
            "min_recipe_level": (min(levels) if levels else None),
            "craft_jobs": ",".join(sorted(jobs)) if jobs else ""
        }
    return info


# -------------------- Scoring --------------------
def cbr(crystals_per_craft: float, crystal_price: float, sale_price: float, qty_out: int = 1) -> float:
    if not sale_price or sale_price <= 0:
        return 1.0
    return (crystals_per_craft * crystal_price) / (sale_price * qty_out)


def compute_score(listings: int, velocity: float, gap: float, cbr_val: float, scarcity_T: int = 12):
    S = max(0.0, (scarcity_T - (listings or 0)) / float(scarcity_T))  # 0..1
    D = min(1.0, (velocity or 0.0) / 5.0)  # cap @ 5/day
    G = min(0.5, max(0.0, gap or 0.0))  # clamp
    P = min(1.0, max(0.0, cbr_val))
    score = 0.4 * S + 0.35 * D + 0.25 * G - 0.3 * P
    return score, S, D, G, P


# -------------------- Progress prints --------------------
def print_progress(prefix: str, i: int, total: int, name: str,
                   median_sale, min_listing, vel):
    ms = "-" if median_sale is None else f"{median_sale:,.0f}"
    ml = "-" if min_listing is None else f"{min_listing:,.0f}"
    vv = 0.0 if vel is None else vel
    print(f"{prefix} [{i:>4}/{total:<4}] {name[:34]:<34} "
          f"median={ms:<8} lowest={ml:<8} vel={vv:>4.2f}")


# -------------------- Main --------------------
def main():
    ap = argparse.ArgumentParser(description="FFXIV Housing Scanner (Universalis + Teamcraft)")
    ap.add_argument("--dc", type=str, default="Zalera", help="World or Data Center (e.g., Zalera, Crystal)")
    ap.add_argument("--output-all", type=str, default="housing_all.csv",
                    help="CSV file for ALL housing items (aggregated stats)")
    ap.add_argument("--output-ranked", type=str, default="housing_ranked.csv",
                    help="CSV file for ranked shortlist (scored)")
    ap.add_argument("--max-candidates", type=int, default=800, help="Max discovered housing IDs to consider")
    ap.add_argument("--shortlist", type=int, default=-1, help="Shortlist size for ranking; use -1 to score ALL")
    ap.add_argument("--include-depth-for-all", action="store_true",
                    help="Also fetch listing counts for ALL items (slower)")
    ap.add_argument("--crystal-price", type=float, default=70.0, help="Average crystal price (gil)")
    ap.add_argument("--crystals-per-craft", type=float, default=5.0, help="Fallback crystals per craft")
    ap.add_argument("--cpc-csv", type=str, default=None,
                    help="CSV with columns: item_id,crystals_per_craft (per-item overrides)")
    ap.add_argument("--min-velocity", type=float, default=0.0, help="Filter: min daily sale velocity for inclusion")
    ap.add_argument("--min-median-price", type=float, default=200.0, help="Filter: min median sale price (gil)")
    ap.add_argument("--max-recipe-lvl", type=int, default=None,
                    help="Flag items craftable at/under this recipe level (e.g., 50, 60)")
    ap.add_argument("--keywords", type=str, default=",".join(DEFAULT_KEYWORDS),
                    help="Comma-separated keywords to detect housing categories")
    ap.add_argument("--sleep", type=float, default=DEFAULT_SLEEP, help="Sleep between API calls (seconds)")
    ap.add_argument("--verbose", action="store_true", help="Print periodic progress lines")
    ap.add_argument("--every", type=int, default=20, help="With --verbose, print a line every N items")
    args = ap.parse_args()

    session = make_session()
    keywords = [k.strip().lower() for k in args.keywords.split(",") if k.strip()]

    # 1) Discover housing items (gear excluded)
    print("[info] Discovering housing items from Teamcraft…")
    discovered = discover_housing_item_ids(session, keywords, verbose=True)
    if not discovered:
        print("[error] No housing items discovered. Check connectivity or keywords.")
        sys.exit(2)

    scan_list = discovered[:max(1, args.max_candidates)]
    total = len(scan_list)
    print(f"[info] Aggregated stats for ALL items: {total}")

    # 2) Aggregated pass over ALL
    rows_all = []
    skipped = 0
    for idx, (iid, name) in enumerate(scan_list, start=1):
        median_sale, min_listing, vel = agg_stats(session, args.dc, iid)
        if median_sale is None:
            skipped += 1
            if args.verbose and (idx % args.every == 0):
                print(f"[all ] [{idx}/{total}] {name[:34]:<34} no data")
            time.sleep(args.sleep)
            continue

        if (median_sale < args.min_median_price) or ((vel or 0) < args.min_velocity):
            # keep it in ALL anyway for trends? -> Yes, we keep it (you asked for ALL)
            pass

        rows_all.append({
            "item_id": iid,
            "name": name,
            "median_sale_gil": median_sale,
            "lowest_listing_gil": min_listing,
            "sale_velocity_per_day": vel or 0.0,
        })
        print(rows_all[-1] if len(rows_all)>=1 else "\n")
        if args.verbose and (idx % args.every == 0):
            print_progress("[all ]", idx, total, name, median_sale, min_listing, vel)
        time.sleep(args.sleep)

    df_all = pd.DataFrame(rows_all)
    if df_all.empty:
        print("[warn] Aggregated phase returned zero rows. Exiting.")
        pd.DataFrame([], columns=[
            "item_id", "name", "median_sale_gil", "lowest_listing_gil", "sale_velocity_per_day",
            "min_recipe_level", "craft_jobs", "craftable_flag", "dc", "timestamp"
        ]).to_csv(args.output_all, index=False)
        sys.exit(0)

    # 3) Craftability enrichment
    print("[info] Enriching craftability (min recipe level & jobs)…")
    minfo = compute_min_recipe_info(session, df_all["item_id"].tolist())
    df_all["min_recipe_level"] = df_all["item_id"].map(lambda x: minfo.get(int(x), {}).get("min_recipe_level"))
    df_all["craft_jobs"] = df_all["item_id"].map(lambda x: minfo.get(int(x), {}).get("craft_jobs"))
    if args.max_recipe_lvl is not None:
        df_all["craftable_flag"] = df_all["min_recipe_level"].apply(
            lambda v: (v is not None) and (v <= args.max_recipe_lvl))
    else:
        df_all["craftable_flag"] = None

    # 4) Listing depth for ALL (optional; slower)
    if args.include_depth_for_all:
        print("[info] Fetching listing counts for ALL items (this may take a while)…")
        counts = []
        total_all = len(df_all)
        for j, iid in enumerate(df_all["item_id"], start=1):
            cnt = listing_count(session, args.dc, int(iid))
            counts.append(cnt)
            if args.verbose and (j % args.every == 0):
                print(f"[depth-all] [{j}/{total_all}] id={iid} listings={cnt}")
            time.sleep(args.sleep)
        df_all["listings_count"] = counts

    # 5) Write ALL CSV
    df_all["dc"] = args.dc
    df_all["timestamp"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    df_all.sort_values(["sale_velocity_per_day", "median_sale_gil"], ascending=[False, False]).to_csv(args.output_all,
                                                                                                      index=False)
    print(f"[info] Wrote ALL housing items to {args.output_all} ({len(df_all)} rows)")

    # 6) Build ranked shortlist (or ALL if --shortlist -1)
    df_rank_src = df_all.copy()
    if args.shortlist is None or args.shortlist < 0:
        df_short = df_rank_src  # score all
    else:
        df_short = df_rank_src.sort_values(["sale_velocity_per_day", "median_sale_gil"],
                                           ascending=[False, False]).head(args.shortlist)

    # Ensure listing counts exist for shortlist
    if "listings_count" not in df_short.columns:
        print(f"[info] Fetching listing counts for ranked shortlist: {len(df_short)}")
        counts = []
        total_short = len(df_short)
        for j, iid in enumerate(df_short["item_id"], start=1):
            cnt = listing_count(session, args.dc, int(iid))
            counts.append(cnt)
            if args.verbose and (j % args.every == 0):
                print(f"[depth-top] [{j}/{total_short}] id={iid} listings={cnt}")
            time.sleep(args.sleep)
        df_short["listings_count"] = counts

    # Optional per-item crystals-per-craft overrides
    cpc_overrides = {}
    if args.cpc_csv and os.path.exists(args.cpc_csv):
        try:
            tmp = pd.read_csv(args.cpc_csv)
            for _, r in tmp.iterrows():
                cpc_overrides[int(r["item_id"])] = float(r["crystals_per_craft"])
        except Exception as e:
            print(f"[warn] Failed to read CPC overrides: {e}")

    def item_cpc(iid: int) -> float:
        return float(cpc_overrides.get(int(iid), args.crystals_per_craft))

    # 7) Compute CBR & Score
    df_short["cbr"] = df_short.apply(lambda r:
                                     cbr(item_cpc(int(r["item_id"])),
                                         args.crystal_price,
                                         r["median_sale_gil"]), axis=1)

    def score_row(r):
        score, S, D, G, P = compute_score(
            listings=int(r["listings_count"]),
            velocity=float(r["sale_velocity_per_day"]),
            gap=float(max(0.0, (r["median_sale_gil"] / (r["lowest_listing_gil"] or r["median_sale_gil"]) - 1.0))) if r[
                "lowest_listing_gil"] else 0.0,
            cbr_val=float(r["cbr"])
        )
        return pd.Series([score, S, D, G, P])

    df_short[["score", "scarcity_S", "demand_D", "gap_G", "penalty_cbr"]] = df_short.apply(score_row, axis=1)

    # 8) Write ranked CSV
    cols = [
        "item_id", "name", "dc", "timestamp",
        "median_sale_gil", "lowest_listing_gil", "sale_velocity_per_day", "listings_count",
        "min_recipe_level", "craft_jobs", "craftable_flag",
        "cbr", "penalty_cbr", "scarcity_S", "demand_D", "gap_G", "score"
    ]
    for c in cols:
        if c not in df_short.columns:
            df_short[c] = None

    df_short[cols].sort_values("score", ascending=False).to_csv(args.output_ranked, index=False)
    print(f"[info] Wrote ranked shortlist to {args.output_ranked} ({len(df_short)} rows)")
    print("[done] Happy house‑flipping!")


if __name__ == "__main__":
    main()