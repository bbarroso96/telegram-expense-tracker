from datetime import date, timedelta

import gspread
from google.oauth2.service_account import Credentials

from config import config


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

FIXED_EXPENSES_STARTER = [
    ["Internet and Phone",              "Bill - Internet and Phone", -75.00],
    ["Rivergate Rent",                  "Bill - Rivergate",          -1565.00],
    ["Rivergate Car Garage",            "Bill - Parking",            -125.00],
    ["Thami Health Insurance",          "Bill - Health Insurance",   -320.00],
    ["Bruno Health Insurance",          "Bill - Health Insurance",   -403.00],
    ["Xfinity Streaming Bundle",        "Bill - Streaming",          -20.00],
    ["Rua General Severiano 319",       "Income",                    700.00],
    ["Diogenes Thami Health Insurance", "Income",                    300.00],
    ["Bruno Income Tax",                "Tax",                       -500.00],
    ["Bruno Income",                    "Income",                    3500.00],
]

CATEGORIES_STARTER = [
    ["Food"], ["Groceries"], ["Leasure"],
    ["Bill - Internet and Phone"], ["Bill - Rivergate"], ["Bill - Parking"],
    ["Bill - Health Insurance"], ["Bill - Streaming"], ["Bill - Gas"],
    ["Tax"], ["Income"], ["Other"],
]

DEFAULTS_STARTER = [
    ["Costco", "Groceries"], ["Tj Maxx", "Groceries"], ["Target", "Groceries"],
    ["Amazon", "Other"], ["Gas", "Bill - Gas"], ["Uber", "Other"],
    ["Parking", "Bill - Parking"],
]

BUDGET_STARTER = [
    ["Bill", 2600.00],
    ["Groceries", 800.00],
    ["The Rest", 600.00],
]


def _get_spreadsheet():
    creds = Credentials.from_service_account_info(config.google_creds, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open(config.spreadsheet_name)


def get_or_create_sheet(name: str, headers: list, starter_rows: list = None, cols: int = None) -> gspread.Worksheet:
    """Generic helper — returns a worksheet by name, creating it with headers and optional starter rows if missing."""
    spreadsheet = _get_spreadsheet()
    existing = [ws.title for ws in spreadsheet.worksheets()]

    if name in existing:
        return spreadsheet.worksheet(name)

    num_cols = cols or len(headers)
    worksheet = spreadsheet.add_worksheet(title=name, rows=500, cols=num_cols)
    header_range = f"A1:{chr(64 + num_cols)}1"
    worksheet.append_row(headers)
    worksheet.format(header_range, {"textFormat": {"bold": True}})

    if starter_rows:
        worksheet.append_rows(starter_rows)
    return worksheet


def current_week() -> int:
    """Returns the week number within the current month (Mon–Sun weeks)."""
    today = date.today()
    first_day = today.replace(day=1)
    first_monday = first_day - timedelta(days=first_day.weekday())
    return (today - first_monday).days // 7 + 1


def get_or_create_month_sheet() -> gspread.Worksheet:
    """Returns the worksheet for the current month, pre-populated with fixed expenses on creation."""
    tab_name = date.today().strftime("%B %Y")
    spreadsheet = _get_spreadsheet()
    existing = [ws.title for ws in spreadsheet.worksheets()]

    if tab_name in existing:
        return spreadsheet.worksheet(tab_name)

    worksheet = spreadsheet.add_worksheet(title=tab_name, rows=500, cols=4)
    worksheet.append_row(["Item", "Week", "Type", "Cost"])
    worksheet.format("A1:D1", {"textFormat": {"bold": True}})

    fixed = load_fixed_expenses()
    if fixed:
        rows = [
            [item, 0, type_, f"${abs(cost):.2f}" if cost >= 0 else f"-${abs(cost):.2f}"]
            for item, type_, cost in fixed
        ]
        worksheet.append_rows(rows)

    return worksheet


def append_expense(item: str, type_: str, cost: float) -> int:
    """Appends a single expense row to the current month sheet. Returns the week number."""
    sheet = get_or_create_month_sheet()
    week = current_week()
    cost_str = f"${abs(cost):.2f}" if type_.lower() == "income" else f"-${abs(cost):.2f}"
    sheet.append_row([item, week, type_, cost_str])
    return week


def load_defaults() -> dict:
    """Returns {item_lowercase: type} from the Defaults sheet."""
    try:
        sheet = get_or_create_sheet("Defaults", ["Item", "Type"], DEFAULTS_STARTER)
        return {r["Item"].strip().lower(): r["Type"].strip() for r in sheet.get_all_records() if r["Item"]}
    except Exception as e:
        return {}


def load_fixed_expenses() -> list:
    """Returns [(item, type, cost)] from the Fixed sheet."""
    try:
        sheet = get_or_create_sheet("Fixed", ["Item", "Type", "Cost"], FIXED_EXPENSES_STARTER, cols=3)
        result = []
        for r in sheet.get_all_records():
            if r["Item"]:
                result.append((
                    str(r["Item"]).strip(),
                    str(r["Type"]).strip(),
                    float(str(r["Cost"]).replace("$", "").replace(",", "")),
                ))
        return result
    except Exception as e:
        return []


def load_categories() -> list:
    """Returns a list of category type strings from the Categories sheet."""
    try:
        sheet = get_or_create_sheet("Categories", ["Type"], CATEGORIES_STARTER, cols=1)
        return [r["Type"].strip() for r in sheet.get_all_records() if r["Type"]]
    except Exception as e:
        return ["Food", "Groceries", "Leasure", "Bill - Gas", "Tax", "Income", "Other"]


def load_budget() -> dict:
    """Returns {category: budget_amount} from the Budget sheet."""
    try:
        sheet = get_or_create_sheet("Budget", ["Category", "Budget"], BUDGET_STARTER)
        return {
            r["Category"].strip(): float(str(r["Budget"]).replace("$", "").replace(",", ""))
            for r in sheet.get_all_records() if r["Category"]
        }
    except Exception as e:
        return {}


def load_month_expenses() -> list:
    """Returns [(item, week, type, cost)] for all rows in the current month sheet."""
    try:
        sheet = get_or_create_month_sheet()
        result = []
        for r in sheet.get_all_records():
            try:
                cost = float(str(r["Cost"]).replace("$", "").replace(",", ""))
                result.append((r["Item"], r["Week"], r["Type"], cost))
            except Exception:
                continue
        return result
    except Exception as e:
        return []
