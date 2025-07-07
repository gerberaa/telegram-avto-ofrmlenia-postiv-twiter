import logging
import os
import random
import requests
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- Налаштування ---
TELEGRAM_TOKEN = '8178078578:AAFxzfWH98Lo1w55wHlQlX16BkRitHJZsPY'  # <-- Встав сюди свій токен
GEMINI_API_KEY = 'AIzaSyDnvjGm9g3XAIBfZcaXLhNXMmlqQtjDOBQ'
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=' + GEMINI_API_KEY

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# --- Сетапи для оформлення ---
STYLES = [
    {
        'name': 'Емодзі + жирний',
        'prompt': 'Додай до тексту релевантні емодзі, зроби важливі слова жирними (bold unicode), оформи як креативний твіт.'
    },
    {
        'name': 'Креативний шрифт',
        'prompt': 'Оформи текст з використанням креативних unicode-шрифтів, додай емодзі, зроби пост унікальним для Twitter.'
    },
    {
        'name': 'Мінімалізм',
        'prompt': 'Оформи текст стильно, мінімалістично, додай 1-2 емодзі, зроби читабельним для Twitter.'
    },
    # Додай ще стилі за бажанням
]

def generate_prompt(user_text: str, style: dict) -> str:
    # Додаємо інструкцію не використовувати емодзі ракети
    return f"{style['prompt']} Не використовуй емодзі ракети (🚀) у жодному варіанті. Ось текст: {user_text}"

# --- Функція для запиту до Gemini ---
def ask_gemini(user_text: str, style: dict) -> str:
    prompt = generate_prompt(user_text, style)
    data = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(GEMINI_API_URL, json=data, headers=headers)
    if response.status_code == 200:
        try:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            return f"[Помилка парсингу відповіді Gemini: {e}]"
    else:
        return f"[Помилка Gemini API: {response.status_code}]"

# --- Хендлер для старту ---
@dp.message_handler(commands=['start'])
async def start_handler(message: Message):
    await message.reply("Привіт! Надішли мені текст, і я оформлю його для Twitter за допомогою AI ✨\n\nМожеш також написати /style для вибору стилю.")

# --- Хендлер для вибору стилю ---
@dp.message_handler(commands=['style'])
async def style_handler(message: Message):
    text = "Оберіть стиль оформлення (відправте номер):\n"
    for i, style in enumerate(STYLES, 1):
        text += f"{i}. {style['name']}\n"
    await message.reply(text)

# --- Зберігаємо стиль для кожного користувача ---
user_styles = {}

@dp.message_handler(lambda m: m.text and m.text.isdigit() and 1 <= int(m.text) <= len(STYLES))
async def set_style_handler(message: Message):
    idx = int(message.text) - 1
    user_styles[message.from_user.id] = idx
    await message.reply(f"Стиль '{STYLES[idx]['name']}' обрано! Надішліть текст для оформлення.")

# --- Основний хендлер для тексту ---
@dp.message_handler(lambda m: m.text and not m.text.startswith('/'))
async def main_handler(message: Message):
    user_text = message.text
    progress_msg = await message.reply("Генерую варіанти оформлення... ⏳")
    responses = []
    for idx, style in enumerate(STYLES):
        await progress_msg.edit_text(f"Генерую варіант {idx+1} з {len(STYLES)}... ⏳")
        result = ask_gemini(user_text, style)
        responses.append((idx, style['name'], result))
    await progress_msg.edit_text("Готово! Ось ваші варіанти:")
    for idx, name, result in responses:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton('Перекласти на англійську', callback_data=f'translate_{idx}'))
        text = f"<b>Стиль {idx+1}: {name}</b>\n<code>\n{result}\n</code>"
        await message.reply(text, parse_mode='HTML', reply_markup=kb)

# --- Обробник для перекладу ---
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('translate_'))
async def translate_handler(callback_query: CallbackQuery):
    idx = int(callback_query.data.split('_')[1])
    last_message = callback_query.message.text
    # Витягуємо текст для перекладу (після першого \n)
    text_to_translate = last_message.split('\n', 1)[-1]
    prompt = f"Переклади цей текст на англійську максимально природньо для Twitter:\n{text_to_translate}"
    data = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(GEMINI_API_URL, json=data, headers=headers)
    if response.status_code == 200:
        try:
            result = response.json()
            translated = result['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            translated = f"[Помилка парсингу відповіді Gemini: {e}]"
    else:
        translated = f"[Помилка Gemini API: {response.status_code}]"
    await callback_query.answer()  # Прибрати "годинник"
    await callback_query.message.reply(f"<b>Переклад на англійську:</b>\n{translated}", parse_mode='HTML')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True) 