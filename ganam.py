    
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
