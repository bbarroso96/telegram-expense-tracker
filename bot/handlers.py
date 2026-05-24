import re
from datetime import date

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from config import config
from bot.sheets import (
    append_expense, load_defaults, load_categories,
    load_budget, load_month_expenses,
)
from bot.budget import compute_balance


CHOOSING_TYPE = 1


def _is_allowed(update: Update) -> bool:
    return update.effective_user.id in config.allowed_user_ids


def _parse_message(text: str):
    """Parses 'Costco 95' or 'Coffee 4.50' → (item, amount) or None."""
    text = text.strip()
    match = re.search(r'([+-]?\$?[\d,]+\.?\d*)\s*$', text)
    if not match:
        return None
    raw = match.group(1).replace("$", "").replace(",", "")
    try:
        amount = float(raw)
    except ValueError:
        return None
    item = text[:match.start()].strip().title()
    return (item, amount) if item else None


def _build_type_keyboard() -> InlineKeyboardMarkup:
    """Builds a 2-column inline keyboard from the Categories sheet."""
    categories = load_categories()
    buttons = [InlineKeyboardButton(cat, callback_data=cat) for cat in categories]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(rows)


def _format_cost(amount: float, type_: str) -> str:
    is_income = type_.lower() == "income"
    sign = "+" if is_income else "-"
    return f"{sign}${abs(amount):.2f}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_allowed(update):
        return
    await update.message.reply_text(
        "👋 Hi! Send me an expense like:\n\n"
        "  `Costco 95`\n"
        "  `Coffee 4.50`\n"
        "  `Salary 3500`\n\n"
        "I'll ask you what type it is and log it to your sheet.",
        parse_mode="Markdown",
    )


async def handle_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: receives 'Costco 95', checks defaults, or asks for type."""
    if not _is_allowed(update):
        return

    parsed = _parse_message(update.message.text)
    if not parsed:
        await update.message.reply_text(
            "❓ Couldn't parse that. Try: `Item amount`\nExample: `Costco 95`",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    item, amount = parsed
    default_type = load_defaults().get(item.lower())

    if default_type:
        try:
            week = append_expense(item, default_type, amount)
            await update.message.reply_text(
                f"✅ Logged!\n  *{item}* — {default_type}\n  Week {week} | {_format_cost(amount, default_type)}",
                parse_mode="Markdown",
            )
        except Exception as e:
            await update.message.reply_text("❌ Couldn't write to sheet. Check logs.")
        return ConversationHandler.END

    context.user_data["pending_item"] = item
    context.user_data["pending_amount"] = amount

    await update.message.reply_text(
        f"Got *{item}* for *${amount:.2f}* — what type is it?",
        parse_mode="Markdown",
        reply_markup=_build_type_keyboard(),
    )
    return CHOOSING_TYPE


async def handle_type_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: receives button tap, logs the expense."""
    query = update.callback_query
    await query.answer()

    type_ = query.data
    item = context.user_data.get("pending_item")
    amount = context.user_data.get("pending_amount")

    if not item or amount is None:
        await query.edit_message_text("❌ Something went wrong. Please try again.")
        return ConversationHandler.END

    try:
        week = append_expense(item, type_, amount)
        await query.edit_message_text(
            f"✅ Logged!\n  *{item}* — {type_}\n  Week {week} | {_format_cost(amount, type_)}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await query.edit_message_text("❌ Couldn't write to sheet. Check logs.")

    context.user_data.clear()
    return ConversationHandler.END


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a budget vs actual spending report for the current month."""
    if not _is_allowed(update):
        return

    await update.message.reply_text("⏳ Calculating balance...")

    budget = load_budget()
    if not budget:
        await update.message.reply_text("❌ Couldn't load budget. Check your Budget sheet.")
        return

    result = compute_balance(budget, load_month_expenses())
    month = date.today().strftime("%B %Y")

    lines = [f"📊 *{month} Balance*\n"]
    total_budget = total_spent = 0

    for cat, data in result.items():
        b, s, r = data["budget"], data["spent"], data["remaining"]
        total_budget += b
        total_spent += s
        bar = "🟢" if r >= 0 else "🔴"
        lines.append(
            f"{bar} *{cat}*\n"
            f"  Budget:    ${b:,.2f}\n"
            f"  Spent:     ${s:,.2f}\n"
            f"  Remaining: ${r:+,.2f}\n"
        )

    total_remaining = total_budget - total_spent
    total_bar = "🟢" if total_remaining >= 0 else "🔴"
    lines.append(
        f"─────────────────\n"
        f"{total_bar} *Total*\n"
        f"  Budget:    ${total_budget:,.2f}\n"
        f"  Spent:     ${total_spent:,.2f}\n"
        f"  Remaining: ${total_remaining:+,.2f}"
    )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END
