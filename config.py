import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота из .env файла
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Админ ID
ADMIN_IDS = [123456789]  # Замени на свой ID

# Настройки AI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Настройки базы данных
DB_PATH = "data/bot_database.db"

# Меню ресторана
MENU = {
    "burgers": {
        "Чизбургер": 350,
        "Гамбургер": 300,
        "Биг Бургер": 500
    },
    "italian": {
        "Маргарита": 550,
        "Пепперони": 600,
        "Карбонара": 450
    },
    "sushi": {
        "Филадельфия": 750,
        "Калифорния": 700,
        "Ролл с угрем": 850
    }
}