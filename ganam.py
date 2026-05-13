import asyncio
import json
import os
import re
import time
import requests
from datetime import datetime
from typing import Dict, Optional, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8501053348:AAHpkfCxLvX_bKjhdC1ReDUDvce_AElpYtU"  # သင့် Bot Token ထည့်ပါ
OWNER_ID = 7887025848  # သင့် Telegram User ID ထည့်ပါ

# ==================== JSONBin.io DATABASE ====================
class JSONBinDB:
    def __init__(self):
        self.api_key = os.environ.get("$2a$10$yfXmXpNq1yjY1gQ4dHt1iu9Tz76gqne9v7Bx5CnGSsRcSLdugs0ZG")
        self.bin_id = os.environ.get("6a03dbffadc21f119a90a97d")
        self.users = {}
        self.groups = {}
        self.start_time = time.time()
        
        if self.api_key:
            print("✅ JSONBin.io connected")
            self.load_data()
        else:
            print("⚠️ No JSONBin API key, using local file")
            self.load_local()
    
    def load_data(self):
        """Load data from JSONBin"""
        if not self.bin_id:
            self.create_bin()
            return
        
        url = f"https://api.jsonbin.io/v3/b/{self.bin_id}/latest"
        headers = {"X-Master-Key": self.api_key}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.users = data.get("record", {}).get("users", {})
                self.groups = data.get("record", {}).get("groups", {})
                print(f"✅ Loaded: {len(self.users)} users, {len(self.groups)} groups")
            else:
                self.create_bin()
        except Exception as e:
            print(f"⚠️ Load error: {e}")
            self.create_bin()
    
    def create_bin(self):
        """Create new bin on JSONBin"""
        url = "https://api.jsonbin.io/v3/b"
        headers = {
            "X-Master-Key": self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "users": {},
            "groups": {},
            "created_at": datetime.now().isoformat()
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                self.bin_id = response.json()["metadata"]["id"]
                print(f"✅ New bin created: {self.bin_id}")
                print(f"📝 Save this BIN_ID: {self.bin_id}")
                print("⚠️ Add this to Railway Env Variables: JSONBIN_BIN_ID")
            else:
                print("❌ Failed to create bin")
        except Exception as e:
            print(f"⚠️ Create bin error: {e}")
    
    def save_data(self):
        """Save data to JSONBin"""
        if not self.api_key or not self.bin_id:
            self.save_local()
            return
        
        url = f"https://api.jsonbin.io/v3/b/{self.bin_id}"
        headers = {
            "X-Master-Key": self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "users": self.users,
            "groups": self.groups,
            "last_save": datetime.now().isoformat()
        }
        
        try:
            requests.put(url, json=data, headers=headers)
            print(f"💾 Saved to JSONBin")
        except Exception as e:
            print(f"⚠️ Save error: {e}")
            self.save_local()
    
    def add_user(self, user_id: int, first_name: str = "", last_name: str = "", username: str = ""):
        user_id_str = str(user_id)
        if user_id_str not in self.users:
            self.users[user_id_str] = {
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "joined_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat()
            }
            self.save_data()
        else:
            self.users[user_id_str]["last_active"] = datetime.now().isoformat()
            self.save_data()
    
    def add_group(self, group_id: int, title: str = ""):
        group_id_str = str(group_id)
        if group_id_str not in self.groups:
            self.groups[group_id_str] = {
                "title": title,
                "joined_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat()
            }
            self.save_data()
        else:
            self.groups[group_id_str]["last_active"] = datetime.now().isoformat()
            self.save_data()
    
    def get_user_count(self) -> int:
        return len(self.users)
    
    def get_group_count(self) -> int:
        return len(self.groups)
    
    def get_all_users(self) -> list:
        return list(self.users.keys())
    
    def get_all_groups(self) -> list:
        return list(self.groups.keys())
    
    def get_uptime(self) -> str:
        uptime_seconds = int(time.time() - self.start_time)
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        return f"{days}d {hours}h {minutes}m {seconds}s"
    
    def load_local(self):
        """Fallback to local JSON file"""
        try:
            with open("local_data.json", "r") as f:
                data = json.load(f)
                self.users = data.get("users", {})
                self.groups = data.get("groups", {})
                print(f"📁 Loaded from local: {len(self.users)} users")
        except:
            pass
    
    def save_local(self):
        """Fallback save to local file"""
        with open("local_data.json", "w") as f:
            json.dump({"users": self.users, "groups": self.groups}, f)
        print("💾 Saved to local file")

# Initialize database
db = JSONBinDB()
# ==================== CALCULATOR FUNCTION ====================
def calculate(expression: str) -> Tuple[Optional[float], Optional[str]]:
    expression = expression.replace(" ", "")
    
    if not re.match(r'^[\d+\-*/%().]+$', expression):
        return None, "ခွင့်မပြုပါ။ + - * / % ( ) . သာ သုံးပါ"
    
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        
        if isinstance(result, (int, float)):
            if isinstance(result, float):
                result = round(result, 10)
                if result.is_integer():
                    result = int(result)
            return result, None
        return None, "တွက်လို့မရပါ"
    except ZeroDivisionError:
        return None, "သုညနဲ့ မစားရပါ"
    except Exception as e:
        return None, f"အမှား: {str(e)}"

# ==================== CALCULATOR KEYBOARD ====================
def get_keyboard():
    buttons = [
        ["7", "8", "9", "/", "DEL"],
        ["4", "5", "6", "*", "AC"],
        ["1", "2", "3", "-", "("],
        ["0", ".", "C", "+", ")"],
        ["%", "=", "🧹", "←"]
    ]
    
    keyboard = []
    for row in buttons:
        keyboard_row = []
        for btn in row:
            keyboard_row.append(InlineKeyboardButton(btn, callback_data=f"btn_{btn}"))
        keyboard.append(keyboard_row)
    
    return InlineKeyboardMarkup(keyboard)

# ==================== COMMAND HANDLERS ====================
EMOJI_IDS = {
    "⚡": "5368324170671202286",
    "👑": "6124902893452529683",
    "🛡️": "5368324170671202288",
}

def build_premium_entities(text: str):
    entities = []

    for emoji, emoji_id in EMOJI_IDS.items():
        start = text.find(emoji)
        while start != -1:
            entities.append(
                MessageEntity(
                    type="custom_emoji",
                    offset=start,
                    length=len(emoji),
                    custom_emoji_id=emoji_id
                )
            )
            start = text.find(emoji, start + len(emoji))

    return entities
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type in ["group", "supergroup"]:
        db.add_group(chat.id, chat.title)
    else:
        db.add_user(user.id, user.first_name, user.last_name, user.username)
    
    text = f"""👑မင်္ဂလာပါ {user.first_name}!

🤖 *OrinX Calculator Bot*

အောက်ပါနည်းလမ်းတွေနဲ့ သုံးနိုင်ပါတယ်:

• `/calculator` - ခလုတ်တွေနဲ့ တွက်ချက်မယ်
• `/calc` `12*(3+4)` - command နဲ့တွက်မယ်
• တိုက်ရိုက်ရိုက်ထည့်မယ် - `12*5` (DM မှာသုံးလို့ရ)

✨ *သင်္ချာအမှတ်အသားများ:* + - * / % ( )

🎮 *ခလုတ်များ အကြောင်း:*
• `DEL` - နောက်ဆုံးစာလုံးကိုဖျက်မယ်
• `AC` - အားလုံးဖျက်မယ် (All Clear)
• `C` - လက်ရှိဖျက်မယ်
• `🧹` - Calculator ကိုရှင်းမယ်
• `←` - နောက်သို့ပြန်မယ်

🔧 *Owner Commands:*
• `/admin` - စာရင်းကြည့်မယ်
• `/broadcast message` - အားလုံးကို ပို့မယ်
• `/broadcast users message` - User များကိုသာ ပို့မယ်
• `/broadcast groups message`- Group များကိုသာ ပို့မယ်

💡 *နမူနာ:* 12*(3+4) = 84
"""
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def calculator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.first_name, user.last_name, user.username)
    
    context.user_data["calc_expr"] = ""
    context.user_data["calc_result"] = ""
    
    text = "🧮 *OrinX Calculator*\n\n"
    text += "*Expr:* (empty)\n"
    text += "*Result:* (click = to calculate)\n\n"
    text += "💡 _ခလုတ်များကိုနှိပ်၍ တွက်ချက်ပါ_"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_keyboard())

async def calc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.first_name, user.last_name, user.username)
    
    if not context.args:
        await update.message.reply_text("❌ ဥပမာ: `/calc 12*(3+4)`", parse_mode=ParseMode.MARKDOWN)
        return
    
    expr = "".join(context.args)
    result, error = calculate(expr)
    
    if error:
        await update.message.reply_text(f"❌ {error}")
    else:
        await update.message.reply_text(f"🧮 `{expr}` = `{result}`", parse_mode=ParseMode.MARKDOWN)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner မှသာ သုံးနိုင်ပါတယ်")
        return
    
    text = f"📊 *OrinX Calculator Stats*\n\n"
    text += f"👤 *Users:* {db.get_user_count()}\n"
    text += f"👥 *Groups:* {db.get_group_count()}\n"
    text += f"⏱️ *Uptime:* {db.get_uptime()}\n"
    text += f"💾 *Database:* JSONBin.io"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast command - users, groups, or all"""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner မှသာ သုံးနိုင်ပါတယ်")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ အသုံးပြုပုံ:\n"
            "• `/broadcast မင်္ဂလာပါ` - အားလုံးကိုပို့မယ်\n"
            "• `/broadcast users မင်္ဂလာပါ` - User များကိုသာပို့မယ်\n"
            "• `/broadcast groups မင်္ဂလာပါ` - Group များကိုသာပို့မယ်",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    first_word = context.args[0].lower()
    message_start = 1
    
    if first_word == "users":
        target = "users"
        broadcast_message = " ".join(context.args[message_start:])
    elif first_word == "groups":
        target = "groups"
        broadcast_message = " ".join(context.args[message_start:])
    else:
        target = "all"
        broadcast_message = " ".join(context.args)
    
    if not broadcast_message:
        await update.message.reply_text("❌ မက်ဆေ့ချ် ထည့်ပါ!")
        return
    
    status_msg = await update.message.reply_text(f"📢 {target} သို့ ပို့နေပါပြီ...")
    
    sent = 0
    failed = 0
    
    broadcast_text = f"{broadcast_message}"
    
    if target in ["all", "users"]:
        for uid in db.get_all_users():
            try:
                await context.bot.send_message(int(uid), broadcast_text, parse_mode=ParseMode.MARKDOWN)
                sent += 1
                await asyncio.sleep(0.05)
            except:
                failed += 1
    
    if target in ["all", "groups"]:
        for gid in db.get_all_groups():
            try:
                await context.bot.send_message(int(gid), broadcast_text, parse_mode=ParseMode.MARKDOWN)
                sent += 1
                await asyncio.sleep(0.05)
            except:
                failed += 1
    
    await status_msg.edit_text(
        f"✅ ပို့ပြီးပါပြီ!\n"
        f"📨 ရောက်ရှိသူ: {sent}\n"
        f"❌ မရောက်သူ: {failed}\n"
        f"🎯 ပစ်မှတ်: {target}"
    )

# ==================== BUTTON CALLBACK ====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    db.add_user(user.id, user.first_name, user.last_name, user.username)
    
    data = query.data
    if not data.startswith("btn_"):
        return
    
    button = data.replace("btn_", "")
    
    expr = context.user_data.get("calc_expr", "")
    result_text = context.user_data.get("calc_result", "")
    
    if button in ["DEL", "←"]:
        expr = expr[:-1]
        result_text = ""
        context.user_data["calc_result"] = ""
    elif button in ["AC", "C", "🧹"]:
        expr = ""
        result_text = ""
        context.user_data["calc_result"] = ""
    elif button == "=":
        if expr:
            result, error = calculate(expr)
            if error:
                result_text = f"Error: {error}"
            else:
                result_text = str(result)
                context.user_data["calc_result"] = result_text
        else:
            result_text = "No expression"
    else:
        expr += button
        result_text = ""
        context.user_data["calc_result"] = ""
    
    context.user_data["calc_expr"] = expr
    
    text = "🧮 *OrinX Calculator*\n\n"
    text += f"*Expr:* `{expr if expr else '(empty)'}`\n"
    
    if result_text:
        if len(result_text) > 50:
            result_text = result_text[:47] + "..."
        text += f"*Result:* `{result_text}`\n"
    else:
        text += "*Result:* (click = to calculate)\n"
    
    text += "\n💡 _ခလုတ်များ: DEL=နောက်ဆုံးဖျက်, AC=အကုန်ဖျက်_"
    
    try:
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_keyboard())
    except:
        await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_keyboard())

# ==================== MESSAGE HANDLER ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    text = update.message.text.strip()
    
    if chat.type in ["group", "supergroup"]:
        db.add_group(chat.id, chat.title)
    else:
        db.add_user(user.id, user.first_name, user.last_name, user.username)
    
    if re.match(r'^[\d\(\)].*[+\-*/%]', text) and not text.startswith('/'):
        result, error = calculate(text)
        
        if error:
            if chat.type == "private":
                await update.message.reply_text(f"❌ {error}")
        else:
            await update.message.reply_text(f"🧮 `{text}` = `{result}`", parse_mode=ParseMode.MARKDOWN)

# ==================== MAIN ====================
async def post_init(app: Application):
    commands = [
        BotCommand("start", "စတင်ရန်"),
        BotCommand("calculator", "ခလုတ်တွေနဲ့ calculator ဖွင့်ရန်"),
        BotCommand("calc", "တိုက်ရိုက်တွက်ရန်"),
        BotCommand("admin", "စာရင်းကြည့်ရန် (owner သာ)"),
    ]
    await app.bot.set_my_commands(commands)
    print("✅ Bot commands set")

def main():
    print("🤖 OrinX Calculator Bot စတင်နေပါပြီ...")
    print("=" * 40)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("calculator", calculator))
    app.add_handler(CommandHandler("calc", calc_command))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^btn_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.post_init = post_init
    
    print("✅ Bot အသင့်ဖြစ်ပါပြီ!")
    app.run_polling()

if __name__ == "__main__":
    main()