"""Telegram accountability bot. Single user, single file.

Run with: python -m tracker.bot
"""

import logging
from datetime import date, datetime, time as dtime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from tracker import config, db

log = logging.getLogger(__name__)
FOCUS, BODY, PEOPLE = range(3)

SCORE_REPLIES = {
    0: "0/3. It happens. Never miss twice — tomorrow you come back.",
    1: "1/3 — you came back with something. Take it.",
    2: "2/3. Solid.",
    3: "3/3 — a won day. Whatever else burned, you won it.",
}


def today() -> date:
    return datetime.now(config.TZ).date()


def score_keyboard(day: date) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(str(i), callback_data=f"score:{day.isoformat()}:{i}")
            for i in range(4)
        ]]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Drill sergeant online.\n\n"
        "/drill — set today's Daily 3 (2 minutes)\n"
        "/score 0-3 — score the day\n"
        "/weight 91.2 [waist_cm] — log weight\n"
        "/today — today's plan\n"
        "/stats — the numbers"
    )


async def drill_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "1/3 FOCUS — the ONE task that makes today a win. "
        "Which task, done by when? Vague answers rejected."
    )
    return FOCUS


async def drill_focus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["focus"] = update.message.text.strip()
    await update.message.reply_text(
        "2/3 BODY — one physical thing. Floor counts: walk, 10 push-ups, "
        "keep the fasting window."
    )
    return BODY


async def drill_body(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["body"] = update.message.text.strip()
    await update.message.reply_text(
        "3/3 PEOPLE — one deliberate moment with wife or daughter. "
        "When exactly? Phone in another room."
    )
    return PEOPLE


async def drill_people(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["people"] = update.message.text.strip()
    with db.connect() as conn:
        db.set_daily3(
            conn,
            today(),
            context.user_data["focus"],
            context.user_data["body"],
            context.user_data["people"],
        )
    await update.message.reply_text(
        "Locked in. 3/3 tonight = a won day, whatever else burns. "
        "I'll ask for the score at 21:30."
    )
    return ConversationHandler.END


async def drill_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Drill aborted. Never miss twice.")
    return ConversationHandler.END


async def on_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != config.OWNER_ID:
        await q.answer()
        return
    _, day_iso, val = q.data.split(":")
    with db.connect() as conn:
        db.set_score(conn, date.fromisoformat(day_iso), int(val))
    await q.answer()
    await q.edit_message_text(f"{day_iso}: {SCORE_REPLIES[int(val)]}")


async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        try:
            val = int(context.args[0])
            if not 0 <= val <= 3:
                raise ValueError
        except ValueError:
            await update.message.reply_text("Usage: /score 0-3")
            return
        with db.connect() as conn:
            db.set_score(conn, today(), val)
        await update.message.reply_text(SCORE_REPLIES[val])
    else:
        await update.message.reply_text(
            "How many of the Daily 3 landed?", reply_markup=score_keyboard(today())
        )


async def weight_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        kg = float(context.args[0].replace(",", "."))
        waist = float(context.args[1].replace(",", ".")) if len(context.args) > 1 else None
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /weight 91.2 [waist_cm]")
        return
    with db.connect() as conn:
        db.add_weight(conn, today(), kg, waist)
    to_go = round(kg - config.MISSION_TARGET_KG, 1)
    await update.message.reply_text(
        f"Logged {kg} kg. {to_go} kg to the 12-week target ({config.MISSION_TARGET_KG} kg). "
        "Judge the 3-week trend, not today."
    )


async def today_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with db.connect() as conn:
        row = db.get_day(conn, today())
    if row is None or not row["focus"]:
        await update.message.reply_text("No Daily 3 yet. /drill — two minutes, go.")
        return
    score = "not scored yet" if row["score"] is None else f"{row['score']}/3"
    await update.message.reply_text(
        f"FOCUS: {row['focus']}\nBODY: {row['body']}\nPEOPLE: {row['people']}\n"
        f"Score: {score}"
    )


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with db.connect() as conn:
        s = db.stats(conn, today())
    scores = " ".join("·" if v is None else str(v) for v in s["scores7"])
    lines = [f"Last 7 days: {scores}"]
    if s["avg7"] is not None:
        lines.append(f"Average: {s['avg7']}/3")
    if s["miss_gap"] is not None and s["miss_gap"] >= 2:
        lines.append(
            f"⚠️ {s['miss_gap']} days without a scored win. "
            "Missed twice is a decision. Come back today."
        )
    if s["weight"] is not None:
        trend = f" ({s['delta21']:+} kg over 3 weeks)" if s["delta21"] is not None else ""
        lines.append(f"Weight: {s['weight']} kg{trend}")
    else:
        lines.append("No weights logged. /weight 91.2")
    await update.message.reply_text("\n".join(lines))


async def morning_job(context: ContextTypes.DEFAULT_TYPE):
    yesterday = today() - timedelta(days=1)
    with db.connect() as conn:
        row = db.get_day(conn, yesterday)
    if row is None or row["score"] is None:
        await context.bot.send_message(
            config.OWNER_ID,
            f"Score yesterday ({yesterday}) first:",
            reply_markup=score_keyboard(yesterday),
        )
    await context.bot.send_message(
        config.OWNER_ID, "Morning drill: /drill — pick today's 3. Two minutes, go."
    )


async def evening_job(context: ContextTypes.DEFAULT_TYPE):
    with db.connect() as conn:
        row = db.get_day(conn, today())
    if row is not None and row["score"] is not None:
        return
    await context.bot.send_message(
        config.OWNER_ID,
        "Score the day — how many of the Daily 3 landed?",
        reply_markup=score_keyboard(today()),
    )


async def weekly_job(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        config.OWNER_ID,
        "Weekly review — 15 minutes, now:\n"
        "1. /stats — anything missed twice?\n"
        "2. Parking lot: one swap-in allowed, now or never.\n"
        "3. Book next week's hard session (paid / with a human) "
        "and pick the Demo Friday target.",
    )


def main():
    logging.basicConfig(level=logging.INFO)
    if not config.BOT_TOKEN or not config.OWNER_ID:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_USER_ID (see .env.example)")

    app = Application.builder().token(config.BOT_TOKEN).build()
    owner = filters.User(config.OWNER_ID)
    answer = filters.TEXT & ~filters.COMMAND & owner

    app.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("drill", drill_start, filters=owner)],
            states={
                FOCUS: [MessageHandler(answer, drill_focus)],
                BODY: [MessageHandler(answer, drill_body)],
                PEOPLE: [MessageHandler(answer, drill_people)],
            },
            fallbacks=[CommandHandler("cancel", drill_cancel, filters=owner)],
        )
    )
    app.add_handler(CommandHandler("start", start, filters=owner))
    app.add_handler(CommandHandler("score", score_cmd, filters=owner))
    app.add_handler(CommandHandler("weight", weight_cmd, filters=owner))
    app.add_handler(CommandHandler("today", today_cmd, filters=owner))
    app.add_handler(CommandHandler("stats", stats_cmd, filters=owner))
    app.add_handler(CallbackQueryHandler(on_score, pattern=r"^score:"))

    jq = app.job_queue
    jq.run_daily(morning_job, time=dtime(8, 0, tzinfo=config.TZ))
    jq.run_daily(evening_job, time=dtime(21, 30, tzinfo=config.TZ))
    jq.run_daily(weekly_job, time=dtime(18, 0, tzinfo=config.TZ), days=(0,))  # PTB: 0 = Sunday

    log.info("Bot starting (owner=%s, tz=%s)", config.OWNER_ID, config.TZ)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
