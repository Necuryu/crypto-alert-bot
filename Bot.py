import telebot
import requests
import threading
import time
import matplotlib.pyplot as plt
import io

# Bot token from BotFather
TOKEN = "YOUR_BOT_TOKEN_HERE"
bot = telebot.TeleBot(TOKEN)

# Store alerts, portfolios and user language preferences
alerts = {}
portfolios = {}
user_lang = {}

# All bot messages in two languages
TEXTS = {
    "ru": {
        "choose_lang": "👋 Привет! Выбери язык:",
        "welcome": "👋 Привет! Я крипто бот.\nВыбери действие:",
        "price_btn": "💰 Цена",
        "top_btn": "📊 Топ 10",
        "chart_btn": "📈 График",
        "portfolio_btn": "💼 Портфолио",
        "alert_btn": "🚨 Алерт",
        "stop_btn": "🛑 Стоп алерты",
        "lang_btn": "🌐 Язык",
        "choose_coin": "Выбери монету:",
        "chart_prompt": "Напиши монету. Пример:\n/chart bitcoin",
        "alert_prompt": "Пример:\n/alert bitcoin 50000",
        "no_alerts": "У тебя нет активных алертов.",
        "alerts_stopped": "🛑 Все алерты остановлены.",
        "coin_not_found": "Монета не найдена. Попробуй: bitcoin, ethereum, solana",
        "alert_set": "✅ Алерт установлен!\n{coin} сейчас: ${current}\nЦель: ${target}",
        "alert_fired": "🚨 Алерт сработал!\n{coin} достиг ${price}!",
        "invalid_price": "Неверная цена.",
        "portfolio_empty": "Портфолио пусто.\nДобавь монету: /portfolio add bitcoin 0.5",
        "portfolio_title": "💼 Твоё портфолио:\n\n",
        "portfolio_total": "\n💰 Итого: ${total}",
        "portfolio_added": "✅ Добавлено: {coin} x{amount}",
        "portfolio_removed": "🗑 {coin} удалён из портфолио.",
        "portfolio_no_coin": "Монета не найдена в портфолио.",
        "top_title": "📊 Топ 10 монет:\n\n",
        "api_error": "Ошибка получения данных.",
        "lang_changed": "✅ Язык изменён на Русский 🇷🇺",
        "price_label": "💰 {coin}: ${price}",
        "prev": "⬅️ Назад",
        "next": "Вперёд ➡️",
    },
    "en": {
        "choose_lang": "👋 Hello! Choose your language:",
        "welcome": "👋 Hello! I'm a crypto bot.\nChoose an action:",
        "price_btn": "💰 Price",
        "top_btn": "📊 Top 10",
        "chart_btn": "📈 Chart",
        "portfolio_btn": "💼 Portfolio",
        "alert_btn": "🚨 Alert",
        "stop_btn": "🛑 Stop alerts",
        "lang_btn": "🌐 Language",
        "choose_coin": "Choose a coin:",
        "chart_prompt": "Enter a coin. Example:\n/chart bitcoin",
        "alert_prompt": "Example:\n/alert bitcoin 50000",
        "no_alerts": "You have no active alerts.",
        "alerts_stopped": "🛑 All alerts stopped.",
        "coin_not_found": "Coin not found. Try: bitcoin, ethereum, solana",
        "alert_set": "✅ Alert set!\n{coin} now: ${current}\nTarget: ${target}",
        "alert_fired": "🚨 Alert triggered!\n{coin} reached ${price}!",
        "invalid_price": "Invalid price.",
        "portfolio_empty": "Portfolio is empty.\nAdd a coin: /portfolio add bitcoin 0.5",
        "portfolio_title": "💼 Your portfolio:\n\n",
        "portfolio_total": "\n💰 Total: ${total}",
        "portfolio_added": "✅ Added: {coin} x{amount}",
        "portfolio_removed": "🗑 {coin} removed from portfolio.",
        "portfolio_no_coin": "Coin not found in portfolio.",
        "top_title": "📊 Top 10 coins:\n\n",
        "api_error": "Error fetching data.",
        "lang_changed": "✅ Language changed to English 🇬🇧",
        "price_label": "💰 {coin}: ${price}",
        "prev": "⬅️ Back",
        "next": "Next ➡️",
    }
}

def t(chat_id, key):
    # Get text in user's language, default to Russian
    lang = user_lang.get(chat_id, "ru")
    return TEXTS[lang][key]

def get_price(coin):
    # Fetch current USD price from CoinGecko API
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        return data[coin]["usd"]
    except:
        return None

# List of supported coins
COINS = [
    ("Bitcoin", "bitcoin"), ("Ethereum", "ethereum"), ("Solana", "solana"),
    ("BNB", "binancecoin"), ("XRP", "ripple"), ("Dogecoin", "dogecoin"),
    ("Cardano", "cardano"), ("Avalanche", "avalanche-2"), ("Polkadot", "polkadot"),
    ("Chainlink", "chainlink"), ("Litecoin", "litecoin"), ("Shiba Inu", "shiba-inu"),
    ("Tron", "tron"), ("Polygon", "matic-network"), ("Uniswap", "uniswap"),
    ("Stellar", "stellar"), ("Monero", "monero"), ("Cosmos", "cosmos"),
    ("Filecoin", "filecoin"), ("Aptos", "aptos"), ("Arbitrum", "arbitrum"),
    ("Near", "near"), ("VeChain", "vechain"), ("Algorand", "algorand")
]

def coins_markup(chat_id, page=0):
    # Build paginated inline keyboard, 8 coins per page
    markup = telebot.types.InlineKeyboardMarkup()
    per_page = 8
    start = page * per_page
    end = start + per_page
    chunk = COINS[start:end]

    for i in range(0, len(chunk), 2):
        row = []
        row.append(telebot.types.InlineKeyboardButton(chunk[i][0], callback_data=f"price_{chunk[i][1]}_{page}"))
        if i + 1 < len(chunk):
            row.append(telebot.types.InlineKeyboardButton(chunk[i+1][0], callback_data=f"price_{chunk[i+1][1]}_{page}"))
        markup.row(*row)

    nav = []
    if page > 0:
        nav.append(telebot.types.InlineKeyboardButton(t(chat_id, "prev"), callback_data=f"page_{page-1}"))
    if end < len(COINS):
        nav.append(telebot.types.InlineKeyboardButton(t(chat_id, "next"), callback_data=f"page_{page+1}"))
    if nav:
        markup.row(*nav)

    return markup

def main_menu(chat_id):
    # Build main reply keyboard in user's language
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(t(chat_id, "price_btn"), t(chat_id, "top_btn"))
    markup.row(t(chat_id, "chart_btn"), t(chat_id, "portfolio_btn"))
    markup.row(t(chat_id, "alert_btn"), t(chat_id, "stop_btn"))
    markup.row(t(chat_id, "lang_btn"))
    return markup

def lang_markup():
    # Language selection inline keyboard
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        telebot.types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    # Show language selection on first launch
    bot.send_message(message.chat.id,
        "👋 Привет! / Hello!\nВыбери язык / Choose language:",
        reply_markup=lang_markup()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def callback_lang(call):
    # Save language choice and show main menu
    lang = call.data.replace("lang_", "")
    user_lang[call.message.chat.id] = lang
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
        t(call.message.chat.id, "welcome"),
        reply_markup=main_menu(call.message.chat.id)
    )

@bot.message_handler(func=lambda m: m.text in [
    "💰 Цена", "📊 Топ 10", "📈 График", "💼 Портфолио", "🚨 Алерт", "🛑 Стоп алерты", "🌐 Язык",
    "💰 Price", "📊 Top 10", "📈 Chart", "💼 Portfolio", "🚨 Alert", "🛑 Stop alerts", "🌐 Language"
])
def handle_buttons(message):
    chat_id = message.chat.id
    text = message.text

    # Language button
    if text in ["🌐 Язык", "🌐 Language"]:
        bot.send_message(chat_id, "🇷🇺 / 🇬🇧", reply_markup=lang_markup())

    # Price button
    elif text in ["💰 Цена", "💰 Price"]:
        bot.send_message(chat_id, t(chat_id, "choose_coin"), reply_markup=coins_markup(chat_id, 0))

    # Top 10 button
    elif text in ["📊 Топ 10", "📊 Top 10"]:
        top(message)

    # Chart button
    elif text in ["📈 График", "📈 Chart"]:
        bot.send_message(chat_id, t(chat_id, "chart_prompt"))

    # Portfolio button
    elif text in ["💼 Портфолио", "💼 Portfolio"]:
        portfolio(message)

    # Alert button
    elif text in ["🚨 Алерт", "🚨 Alert"]:
        bot.send_message(chat_id, t(chat_id, "alert_prompt"))

    # Stop alerts button
    elif text in ["🛑 Стоп алерты", "🛑 Stop alerts"]:
        stop(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("page_"))
def callback_page(call):
    # Navigate between coin pages
    page = int(call.data.replace("page_", ""))
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=coins_markup(call.message.chat.id, page))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("price_"))
def callback_price(call):
    # Handle coin selection from inline keyboard
    parts = call.data.split("_")
    coin = parts[1]
    p = get_price(coin)
    if p:
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id,
            t(call.message.chat.id, "price_label").format(coin=coin.upper(), price=f"{p:,.2f}")
        )
    else:
        bot.answer_callback_query(call.id, t(call.message.chat.id, "coin_not_found"))

@bot.message_handler(commands=["price"])
def price(message):
    # Get current price for a specific coin
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, t(message.chat.id, "coin_not_found"))
        return
    coin = args[1].lower()
    p = get_price(coin)
    if p:
        bot.send_message(message.chat.id,
            t(message.chat.id, "price_label").format(coin=coin.upper(), price=f"{p:,.2f}")
        )
    else:
        bot.send_message(message.chat.id, t(message.chat.id, "coin_not_found"))

@bot.message_handler(commands=["alert"])
def set_alert(message):
    # Set a price alert for a coin
    args = message.text.split()
    if len(args) < 3:
        bot.send_message(message.chat.id, t(message.chat.id, "alert_prompt"))
        return
    coin = args[1].lower()
    try:
        target = float(args[2])
    except:
        bot.send_message(message.chat.id, t(message.chat.id, "invalid_price"))
        return
    current = get_price(coin)
    if not current:
        bot.send_message(message.chat.id, t(message.chat.id, "coin_not_found"))
        return
    if message.chat.id not in alerts:
        alerts[message.chat.id] = []
    alerts[message.chat.id].append({"coin": coin, "target": target, "current": current})
    bot.send_message(message.chat.id,
        t(message.chat.id, "alert_set").format(
            coin=coin.upper(),
            current=f"{current:,.2f}",
            target=f"{target:,.2f}"
        )
    )

@bot.message_handler(commands=["stop"])
def stop(message):
    # Cancel all active alerts for this user
    if message.chat.id in alerts:
        del alerts[message.chat.id]
        bot.send_message(message.chat.id, t(message.chat.id, "alerts_stopped"))
    else:
        bot.send_message(message.chat.id, t(message.chat.id, "no_alerts"))

@bot.message_handler(commands=["top"])
def top(message):
    # Fetch and display top 10 coins by market cap
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1"
        response = requests.get(url)
        data = response.json()
        text = t(message.chat.id, "top_title")
        for i, coin in enumerate(data, 1):
            change = coin['price_change_percentage_24h']
            emoji = "🟢" if change > 0 else "🔴"
            text += f"{i}. {coin['symbol'].upper()} — ${coin['current_price']:,.2f} {emoji} {change:.1f}%\n"
        bot.send_message(message.chat.id, text)
    except:
        bot.send_message(message.chat.id, t(message.chat.id, "api_error"))

@bot.message_handler(commands=["chart"])
def chart(message):
    # Generate a 7-day price chart and send it as an image
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, t(message.chat.id, "chart_prompt"))
        return
    coin = args[1].lower()
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart?vs_currency=usd&days=7"
        response = requests.get(url)
        data = response.json()
        prices = data["prices"]
        times = [p[0] for p in prices]
        values = [p[1] for p in prices]

        import datetime
        dates = [datetime.datetime.fromtimestamp(t/1000) for t in times]

        plt.figure(figsize=(6, 3))
        plt.plot(dates, values, color='#00ff88', linewidth=2)
        plt.fill_between(dates, values, alpha=0.1, color='#00ff88')
        plt.title(f"{coin.upper()} — 7 days", fontsize=14)
        plt.xlabel("Date")
        plt.ylabel("Price (USD)")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # Save chart to memory buffer and send
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        plt.close()

        bot.send_photo(message.chat.id, buf)
    except:
        bot.send_message(message.chat.id, t(message.chat.id, "coin_not_found"))

@bot.message_handler(commands=["portfolio"])
def portfolio(message):
    # Manage user portfolio — view, add, or remove coins
    args = message.text.split()
    chat_id = message.chat.id

    if len(args) == 1:
        # Show current portfolio with live prices
        if chat_id not in portfolios or not portfolios[chat_id]:
            bot.send_message(chat_id, t(chat_id, "portfolio_empty"))
            return
        text = t(chat_id, "portfolio_title")
        total = 0
        for coin, amount in portfolios[chat_id].items():
            p = get_price(coin)
            if p:
                value = p * amount
                total += value
                text += f"• {coin.upper()}: {amount} — ${value:,.2f}\n"
        text += t(chat_id, "portfolio_total").format(total=f"{total:,.2f}")
        bot.send_message(chat_id, text)

    elif len(args) >= 3 and args[1] == "add":
        coin = args[2].lower()
        try:
            amount = float(args[3]) if len(args) > 3 else 1.0
        except:
            amount = 1.0
        p = get_price(coin)
        if not p:
            bot.send_message(chat_id, t(chat_id, "coin_not_found"))
            return
        if chat_id not in portfolios:
            portfolios[chat_id] = {}
        portfolios[chat_id][coin] = amount
        bot.send_message(chat_id, t(chat_id, "portfolio_added").format(coin=coin.upper(), amount=amount))

    elif len(args) >= 3 and args[1] == "remove":
        coin = args[2].lower()
        if chat_id in portfolios and coin in portfolios[chat_id]:
            del portfolios[chat_id][coin]
            bot.send_message(chat_id, t(chat_id, "portfolio_removed").format(coin=coin.upper()))
        else:
            bot.send_message(chat_id, t(chat_id, "portfolio_no_coin"))

def check_alerts():
    # Background thread — checks prices every 30 seconds and fires alerts
    while True:
        for chat_id, alert_list in list(alerts.items()):
            for alert in alert_list[:]:
                p = get_price(alert["coin"])
                if p:
                    if (alert["current"] < alert["target"] <= p) or (alert["current"] > alert["target"] >= p):
                        bot.send_message(chat_id,
                            t(chat_id, "alert_fired").format(
                                coin=alert['coin'].upper(),
                                price=f"{p:,.2f}"
                            )
                        )
                        alert_list.remove(alert)
                    else:
                        alert["current"] = p
        time.sleep(30)


# Start alert checker in background
threading.Thread(target=check_alerts, daemon=True).start()
print("Bot started!")
bot.polling()
