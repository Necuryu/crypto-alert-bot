import telebot
import requests
import threading
import time
import matplotlib.pyplot as plt
import io

TOKEN = "YOUR_BOT_TOKEN_HERE"
bot = telebot.TeleBot(TOKEN)

alerts = {}
portfolios = {}

def get_price(coin):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        return data[coin]["usd"]
    except:
        return None

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, 
        "👋 Привет! Я крипто бот.\n\n"
        "📋 Команды:\n"
        "/price bitcoin — текущая цена\n"
        "/alert bitcoin 50000 — алерт на цену\n"
        "/stop — остановить алерты\n"
        "/top — топ 10 монет\n"
        "/chart bitcoin — график за 7 дней\n"
        "/portfolio — моё портфолио\n"
        "/portfolio add bitcoin 0.5 — добавить монету\n"
        "/portfolio remove bitcoin — удалить монету"
    )

@bot.message_handler(commands=["price"])
def price(message):
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "Укажи монету. Пример: /price bitcoin")
        return
    coin = args[1].lower()
    p = get_price(coin)
    if p:
        bot.send_message(message.chat.id, f"💰 {coin.upper()}: ${p:,.2f}")
    else:
        bot.send_message(message.chat.id, "Монета не найдена. Попробуй: bitcoin, ethereum, solana")

@bot.message_handler(commands=["alert"])
def set_alert(message):
    args = message.text.split()
    if len(args) < 3:
        bot.send_message(message.chat.id, "Пример: /alert bitcoin 50000")
        return
    coin = args[1].lower()
    try:
        target = float(args[2])
    except:
        bot.send_message(message.chat.id, "Неверная цена.")
        return
    current = get_price(coin)
    if not current:
        bot.send_message(message.chat.id, "Монета не найдена.")
        return
    if message.chat.id not in alerts:
        alerts[message.chat.id] = []
    alerts[message.chat.id].append({"coin": coin, "target": target, "current": current})
    bot.send_message(message.chat.id, f"✅ Алерт установлен!\n{coin.upper()} сейчас: ${current:,.2f}\nЦель: ${target:,.2f}")

@bot.message_handler(commands=["stop"])
def stop(message):
    if message.chat.id in alerts:
        del alerts[message.chat.id]
        bot.send_message(message.chat.id, "🛑 Все алерты остановлены.")
    else:
        bot.send_message(message.chat.id, "У тебя нет активных алертов.")

@bot.message_handler(commands=["top"])
def top(message):
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1"
        response = requests.get(url)
        data = response.json()
        text = "📊 Топ 10 монет:\n\n"
        for i, coin in enumerate(data, 1):
            change = coin['price_change_percentage_24h']
            emoji = "🟢" if change > 0 else "🔴"
            text += f"{i}. {coin['symbol'].upper()} — ${coin['current_price']:,.2f} {emoji} {change:.1f}%\n"
        bot.send_message(message.chat.id, text)
    except:
        bot.send_message(message.chat.id, "Ошибка получения данных.")

@bot.message_handler(commands=["chart"])
def chart(message):
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "Пример: /chart bitcoin")
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
        plt.title(f"{coin.upper()} — цена за 7 дней", fontsize=14)
        plt.xlabel("Дата")
        plt.ylabel("Цена (USD)")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        plt.close()

        bot.send_photo(message.chat.id, buf)
    except:
        bot.send_message(message.chat.id, "Монета не найдена. Попробуй: bitcoin, ethereum, solana")

@bot.message_handler(commands=["portfolio"])
def portfolio(message):
    args = message.text.split()
    chat_id = message.chat.id

    if len(args) == 1:
        if chat_id not in portfolios or not portfolios[chat_id]:
            bot.send_message(chat_id, "Портфолио пусто.\nДобавь монету: /portfolio add bitcoin 0.5")
            return
        text = "💼 Твоё портфолио:\n\n"
        total = 0
        for coin, amount in portfolios[chat_id].items():
            p = get_price(coin)
            if p:
                value = p * amount
                total += value
                text += f"• {coin.upper()}: {amount} шт = ${value:,.2f}\n"
        text += f"\n💰 Итого: ${total:,.2f}"
        bot.send_message(chat_id, text)

    elif len(args) >= 3 and args[1] == "add":
        coin = args[2].lower()
        try:
            amount = float(args[3]) if len(args) > 3 else 1.0
        except:
            amount = 1.0
        p = get_price(coin)
        if not p:
            bot.send_message(chat_id, "Монета не найдена.")
            return
        if chat_id not in portfolios:
            portfolios[chat_id] = {}
        portfolios[chat_id][coin] = amount
        bot.send_message(chat_id, f"✅ Добавлено: {coin.upper()} x{amount}")

    elif len(args) >= 3 and args[1] == "remove":
        coin = args[2].lower()
        if chat_id in portfolios and coin in portfolios[chat_id]:
            del portfolios[chat_id][coin]
            bot.send_message(chat_id, f"🗑 {coin.upper()} удалён из портфолио.")
        else:
            bot.send_message(chat_id, "Монета не найдена в портфолио.")

def check_alerts():
    while True:
        for chat_id, alert_list in list(alerts.items()):
            for alert in alert_list[:]:
                p = get_price(alert["coin"])
                if p:
                    if (alert["current"] < alert["target"] <= p) or (alert["current"] > alert["target"] >= p):
                        bot.send_message(chat_id, f"🚨 Алерт сработал!\n{alert['coin'].upper()} достиг ${p:,.2f}!")
                        alert_list.remove(alert)
                    else:
                        alert["current"] = p
        time.sleep(30)

threading.Thread(target=check_alerts, daemon=True).start()
print("Бот запущен!")
bot.polling()