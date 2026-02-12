#!/usr/bin/env python3
import json
import logging
import os
import sys
from datetime import datetime
from typing import Optional

import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

CONFIG_PATH = "/etc/zivpn-udp/config.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("zivpn-bot")


def load_config() -> dict:
  if not os.path.isfile(CONFIG_PATH):
    logger.error("Config tidak ditemukan: %s", CONFIG_PATH)
    sys.exit(1)
  with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    return json.load(f)


def call_api(base_url: str, token: Optional[str], path: str) -> str:
  url = f"{base_url.rstrip('/')}/{path}"
  headers = {"Authorization": f"Bearer {token}"} if token else None
  try:
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text
  except Exception as exc:  # noqa: BLE001
    logger.exception("Gagal memanggil API: %s", exc)
    return f"Terjadi kesalahan memanggil API: {exc}"


def ensure_admin(config: dict, chat_id: int) -> bool:
  admin_id = str(config.get("telegram_admin_id") or "").strip()
  return not admin_id or admin_id == str(chat_id)


def require_config(config: dict):
  if not config.get("api_url"):
    logger.error("api_url belum diisi di config.json")
    sys.exit(1)
  if not config.get("telegram_bot_token"):
    logger.error("telegram_bot_token belum diisi di config.json")
    sys.exit(1)


def format_users(raw: str) -> str:
  if len(raw) > 3000:
    return raw[:3000] + "\n... (dipotong)"
  return raw


async def handle_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
  config = context.bot_data["config"]
  result = call_api(config["api_url"], config.get("api_token"), "ping")
  await update.message.reply_text(result)


async def handle_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
  config = context.bot_data["config"]
  result = call_api(config["api_url"], config.get("api_token"), "users")
  await update.message.reply_text(format_users(result))


async def handle_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
  config = context.bot_data["config"]
  result = call_api(config["api_url"], config.get("api_token"), "info")
  await update.message.reply_text(result)


async def handle_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
  config = context.bot_data["config"]
  try:
    user, password, days = context.args[0], context.args[1], context.args[2]
  except Exception:  # noqa: BLE001
    await update.message.reply_text("Format: /add user pass days")
    return
  result = call_api(config["api_url"], config.get("api_token"), f"add?user={user}&pass={password}&days={days}")
  await update.message.reply_text(result)


async def handle_trial(update: Update, context: ContextTypes.DEFAULT_TYPE):
  config = context.bot_data["config"]
  if not context.args:
    await update.message.reply_text("Format: /trial minutes")
    return
  minutes = context.args[0]
  result = call_api(config["api_url"], config.get("api_token"), f"trial?minutes={minutes}")
  await update.message.reply_text(result)


async def handle_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
  config = context.bot_data["config"]
  if not context.args:
    await update.message.reply_text("Format: /delete user")
    return
  user = context.args[0]
  result = call_api(config["api_url"], config.get("api_token"), f"delete?user={user}")
  await update.message.reply_text(result)


async def handle_renew(update: Update, context: ContextTypes.DEFAULT_TYPE):
  config = context.bot_data["config"]
  if len(context.args) < 2:
    await update.message.reply_text("Format: /renew user days")
    return
  user, days = context.args[0], context.args[1]
  result = call_api(config["api_url"], config.get("api_token"), f"renew?user={user}&days={days}")
  await update.message.reply_text(result)


async def handle_changepass(update: Update, context: ContextTypes.DEFAULT_TYPE):
  config = context.bot_data["config"]
  if len(context.args) < 2:
    await update.message.reply_text("Format: /changepass user pass")
    return
  user, password = context.args[0], context.args[1]
  result = call_api(config["api_url"], config.get("api_token"), f"changepass?user={user}&pass={password}")
  await update.message.reply_text(result)


async def handle_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
  config = context.bot_data["config"]
  result = call_api(config["api_url"], config.get("api_token"), "backup")
  await update.message.reply_text(result)


async def handle_restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
  config = context.bot_data["config"]
  if not context.args:
    await update.message.reply_text("Format: /restore id")
    return
  backup_id = context.args[0]
  result = call_api(config["api_url"], config.get("api_token"), f"restore?id={backup_id}")
  await update.message.reply_text(result)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  config = context.bot_data["config"]
  ping = call_api(config["api_url"], config.get("api_token"), "ping")
  info = call_api(config["api_url"], config.get("api_token"), "info")
  message = (
    "Selamat datang di ZIVPN Telegram Bot!\n"
    "Gunakan perintah: /ping /users /add /trial /delete /renew /changepass /backup /restore.\n\n"
    f"Ping: {ping}\nInfo: {info}"
  )
  await update.message.reply_text(message)


async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
  config = context.bot_data["config"]
  chat_id = update.effective_chat.id if update.effective_chat else None
  if chat_id is None:
    return False
  if ensure_admin(config, chat_id):
    return True
  await update.message.reply_text("Anda tidak memiliki izin mengakses bot ini.")
  return False


async def admin_wrapper(handler, update: Update, context: ContextTypes.DEFAULT_TYPE):
  if await check_admin(update, context):
    await handler(update, context)


def main():
  config = load_config()
  require_config(config)
  token = config.get("telegram_bot_token")
  admin_id = config.get("telegram_admin_id")
  logger.info("Memulai bot pada %s, admin: %s", datetime.now().isoformat(), admin_id or "(semua diizinkan)")

  application = ApplicationBuilder().token(token).build()
  application.bot_data["config"] = config

  # Command handlers
  application.add_handler(CommandHandler("start", lambda u, c: admin_wrapper(handle_start, u, c)))
  application.add_handler(CommandHandler("ping", lambda u, c: admin_wrapper(handle_ping, u, c)))
  application.add_handler(CommandHandler("users", lambda u, c: admin_wrapper(handle_users, u, c)))
  application.add_handler(CommandHandler("info", lambda u, c: admin_wrapper(handle_info, u, c)))
  application.add_handler(CommandHandler("add", lambda u, c: admin_wrapper(handle_add, u, c)))
  application.add_handler(CommandHandler("trial", lambda u, c: admin_wrapper(handle_trial, u, c)))
  application.add_handler(CommandHandler("delete", lambda u, c: admin_wrapper(handle_delete, u, c)))
  application.add_handler(CommandHandler("renew", lambda u, c: admin_wrapper(handle_renew, u, c)))
  application.add_handler(CommandHandler("changepass", lambda u, c: admin_wrapper(handle_changepass, u, c)))
  application.add_handler(CommandHandler("backup", lambda u, c: admin_wrapper(handle_backup, u, c)))
  application.add_handler(CommandHandler("restore", lambda u, c: admin_wrapper(handle_restore, u, c)))

  application.run_polling()


if __name__ == "__main__":
  main()
