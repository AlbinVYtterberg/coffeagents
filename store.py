"""Inventory (lager.md), supplier quotes, our prices, and the sales ledger (sales.md)."""
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
INVENTORY_FILE = ROOT / "lager.md"
SALES_FILE = ROOT / "sales.md"
STATE_FILE = DATA / "state.json"

# How much below the cheapest competitor we price, per unit.
UNDERCUT = 0.01

INVENTORY_LINE = re.compile(
    r"^(?P<qty>\d+(?:\.\d+)?)\s+(?:(?P<qty_unit>kg|liter|l)\s+)?(?P<name>.+?),"
    r"\s*\$(?P<cost>\d+(?:\.\d+)?)/(?P<unit>\w+)\s*$"
)
SALES_HEADER = (
    "# Sales\n\n"
    "| Date | Café | Email | Item | Quantity | Unit | Unit price | Total | Unit cost | Profit |\n"
    "|---|---|---|---|---:|---|---:|---:|---:|---:|\n"
)


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_table(filename: str) -> list[list[str]]:
    """Data rows of the first markdown table in a file (header and separator skipped)."""
    rows = []
    for line in (ROOT / filename).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(cells)
    return rows[1:] if len(rows) > 1 and "@" not in "".join(rows[0]) else rows


def contacts(filename: str) -> dict[str, str]:
    """email -> name, from suppliers.md or cafe.md."""
    return {row[1].lower(): row[0] for row in read_table(filename)}


# ---------- state (quotes, inquiries, processed mail) ----------

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"quotes": {}, "inquiries": {}, "seen_mail": [], "pending": []}


def save_state(state: dict) -> None:
    DATA.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------- inventory ----------

def _fmt(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else f"{x:.3f}".rstrip("0")


def read_inventory() -> dict[str, dict]:
    items = {}
    for line in INVENTORY_FILE.read_text(encoding="utf-8").splitlines():
        m = INVENTORY_LINE.match(line.strip())
        if m:
            items[m["name"]] = {
                "qty": float(m["qty"]),
                "qty_unit": m["qty_unit"] or "",
                "cost": float(m["cost"]),
                "cost_text": m["cost"],
                "unit": m["unit"],
            }
    return items


def find_item(name: str) -> str | None:
    """Match an item name case-insensitively against lager.md."""
    wanted = name.strip().lower()
    for item in read_inventory():
        if item.lower() == wanted:
            return item
    return None


def _set_quantity(item: str, qty: float) -> None:
    lines = INVENTORY_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, line in enumerate(lines):
        m = INVENTORY_LINE.match(line.strip())
        if m and m["name"] == item:
            qty_unit = f"{m['qty_unit']} " if m["qty_unit"] else ""
            ending = "\n" if line.endswith("\n") else ""
            lines[i] = f"{_fmt(qty)} {qty_unit}{item}, ${m['cost']}/{m['unit']}{ending}"
    INVENTORY_FILE.write_text("".join(lines), encoding="utf-8")


# ---------- prices ----------

def our_price(state: dict, item: str) -> tuple[float | None, str]:
    """(price, explanation). Undercut the cheapest quote, but never sell below cost."""
    quotes = state["quotes"].get(item, {})
    if not quotes:
        return None, "no supplier quote yet"
    cheapest_supplier, cheapest = min(quotes.items(), key=lambda kv: kv[1]["price"])
    cost = read_inventory()[item]["cost"]
    price = round(cheapest["price"] - UNDERCUT, 2)
    if price < cost:
        return cost, f"at cost floor (cheapest competitor {cheapest['price']} from {cheapest_supplier})"
    return price, f"{UNDERCUT} below {cheapest_supplier} ({cheapest['price']})"


# ---------- sales ----------

def record_sale(state: dict, cafe_name: str, cafe_email: str, item: str, quantity: float) -> dict:
    inventory = read_inventory()
    stock = inventory[item]
    if quantity <= 0:
        raise ValueError("Quantity must be positive.")
    if stock["unit"] == "ps" and not float(quantity).is_integer():
        raise ValueError(f"{item} is sold per piece; quantity must be a whole number.")
    if quantity > stock["qty"]:
        raise ValueError(f"Only {_fmt(stock['qty'])} {stock['unit']} of {item} in stock.")
    price, _ = our_price(state, item)
    if price is None:
        raise ValueError(f"No price for {item} yet (waiting for supplier quotes).")

    total = round(price * quantity, 2)
    profit = round((price - stock["cost"]) * quantity, 2)
    if not SALES_FILE.exists():
        SALES_FILE.write_text(SALES_HEADER, encoding="utf-8")
    with SALES_FILE.open("a", encoding="utf-8") as f:
        f.write(
            f"| {now()} | {cafe_name} | {cafe_email} | {item} | {_fmt(quantity)} | {stock['unit']} "
            f"| {price:.2f} | {total:.2f} | {stock['cost']:.2f} | {profit:.2f} |\n"
        )
    _set_quantity(item, stock["qty"] - quantity)
    return {"item": item, "quantity": quantity, "unit": stock["unit"],
            "unit_price": price, "total": total, "left_in_stock": stock["qty"] - quantity}


def earnings_report() -> str:
    if not SALES_FILE.exists():
        return "No sales yet."
    rows = [r for r in read_table("sales.md") if len(r) == 10]
    if not rows:
        return "No sales yet."
    revenue = sum(float(r[7]) for r in rows)
    profit = sum(float(r[9]) for r in rows)
    by_item: dict[str, list[float]] = {}
    by_cafe: dict[str, float] = {}
    for r in rows:
        totals = by_item.setdefault(r[3], [0.0, 0.0])
        totals[0] += float(r[7])
        totals[1] += float(r[9])
        by_cafe[r[1]] = by_cafe.get(r[1], 0.0) + float(r[7])
    lines = [
        f"Sales: {len(rows)}",
        f"Revenue: ${revenue:.2f}",
        f"Cost of goods sold: ${revenue - profit:.2f}",
        f"Earnings (profit): ${profit:.2f}",
        "",
        "Per item (revenue / profit):",
        *[f"  {item}: ${rev:.2f} / ${prof:.2f}" for item, (rev, prof) in by_item.items()],
        "",
        "Per café (revenue):",
        *[f"  {cafe}: ${rev:.2f}" for cafe, rev in by_cafe.items()],
    ]
    return "\n".join(lines)
