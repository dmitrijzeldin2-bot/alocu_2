import asyncio
import logging
import os
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8671402014:AAHOTm69wjosyFxfDzYsN9iC_4iVtlQW-W0'
# ВАЖНО: Укажите здесь URL вашего приложения на Render (с https://)
WEB_APP_URL = 'https://alocu-2.onrender.com'

# --- FLASK И HTML ---
app = Flask(__name__)

html_template = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>ALOCU gift | NFT Wheel</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://telegram.org"></script>
    <style>
        body {{ margin: 0; height: 100vh; display: flex; align-items: center; justify-content: center;
            background: radial-gradient(circle, #463305 0%, #000 100%);
            font-family: 'Segoe UI', sans-serif; overflow: hidden; color: white; }}
        .main-container {{ text-align: center; position: relative; }}
        h1 {{ color: #d4af37; font-size: 2rem; margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: 5px; }}
        .attempts-text {{ margin-bottom: 20px; font-size: 1.1rem; opacity: 0.8; }}
        .arrow {{ position: absolute; top: 115px; left: 50%; transform: translateX(-50%);
            width: 0; height: 0; border-left: 15px solid transparent;
            border-right: 15px solid transparent; border-top: 35px solid #ff4400;
            z-index: 10; filter: drop-shadow(0 0 5px red); }}
        #wheel {{ width: 300px; height: 300px; border-radius: 50%; border: 8px solid #d4af37;
            background: conic-gradient(#d4af37 0deg 45deg, #222 45deg 90deg, #d4af37 90deg 135deg, #222 135deg 180deg, #444 180deg 225deg, #333 225deg 270deg, #444 270deg 315deg, #333 315deg 360deg);
            position: relative; transition: transform 4s cubic-bezier(0.15, 0, 0.15, 1);
            box-shadow: 0 0 50px rgba(212, 175, 55, 0.4); }}
        .label {{ position: absolute; width: 100%; height: 100%; text-align: center; font-weight: bold; font-size: 12px; pointer-events: none; color: #fff; }}
        .spin-btn {{ margin-top: 30px; padding: 15px 40px; font-size: 18px; background: #d4af37; color: black; border: none; cursor: pointer; font-weight: bold; border-radius: 8px; transition: 0.3s; }}
        .spin-btn:disabled {{ opacity: 0.3; }}
    </style>
</head>
<body>
<div class="main-container">
    <h1>ALOCU gift</h1>
    <div class="attempts-text">Попыток: <span id="tries">3</span></div>
    <div class="arrow"></div>
    <div id="wheel">
        <div class="label" style="transform: rotate(22.5deg)">Bear</div>
        <div class="label" style="transform: rotate(67.5deg)">Rocket</div>
        <div class="label" style="transform: rotate(112.5deg)">Heart</div>
        <div class="label" style="transform: rotate(157.5deg)">Rose</div>
        <div class="label" style="transform: rotate(202.5deg)">Ничего</div>
        <div class="label" style="transform: rotate(247.5deg)">Ничего</div>
        <div class="label" style="transform: rotate(292.5deg)">Ничего</div>
        <div class="label" style="transform: rotate(337.5deg)">Ничего</div>
    </div>
    <button class="spin-btn" id="btn" onclick="spin()">Крутить</button>
</div>
<script>
    const wheel = document.getElementById('wheel');
    const btn = document.getElementById('btn');
    const triesDisplay = document.getElementById('tries');
    const prizes = ["Bear", "Rocket", "Heart", "Rose", "Ничего", "Ничего", "Ничего", "Ничего"];
    let attempts = 3;

    function spin() {{
        if (attempts <= 0) return;
        btn.disabled = true;
        attempts--;
        triesDisplay.innerText = attempts;
        const randomIndex = Math.floor(Math.random() * prizes.length);
        const totalRotation = 3600 + (360 - (randomIndex * 45));
        wheel.style.transform = `rotate(${{totalRotation}}deg)`;

        setTimeout(() => {{
            const result = prizes[randomIndex];
            alert(result === "Ничего" ? "Эх, ничего не выпало!" : "ПОЗДРАВЛЯЕМ! Ваш NFT: " + result);
            if (attempts > 0) {{
                btn.disabled = false;
                const currentAngle = totalRotation % 360;
                wheel.style.transition = 'none';
                wheel.style.transform = `rotate(${{currentAngle}}deg)`;
                setTimeout(() => {{ wheel.style.transition = 'transform 4s cubic-bezier(0.15, 0, 0.15, 1)'; }}, 50);
            }} else {{
                alert("Попытки закончились!");
            }}
        }}, 4100);
    }}
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return html_template

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- БОТ AIOGRAM ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer_invoice(
        title="Колесо NFT",
        description="Оплата 2 звезды за доступ к игре (3 попытки)",
        payload="wheel_payment",
        currency="XTR",
        prices=[LabeledPrice(label="2 Звезды", amount=2)],
        provider_token=""
    )

@dp.pre_checkout_query()
async def process_pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def success_payment(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Играть в Mini App", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    await message.answer("Оплата подтверждена! Нажми кнопку ниже:", reply_markup=kb)

async def main():
    # Запуск Flask в потоке для Render
    Thread(target=run_flask, daemon=True).start()
    # Запуск Polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
