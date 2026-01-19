import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# Загрузка переменных
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Меню
MENU = {
    "burgers": {
        "🍔 Классический бургер": 350,
        "🍔 Чизбургер": 400,
        "🍔 Биг Бургер": 500
    },
    "pizza": {
        "🍕 Маргарита": 550,
        "🍕 Пепперони": 600,
        "🍕 Гавайская": 650
    },
    "sushi": {
        "🍣 Филадельфия": 700,
        "🍣 Калифорния": 650,
        "🍣 Ролл с угрем": 800
    }
}

# Хранение корзин в памяти (для простоты)
user_carts = {}

# ========== КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("🍔 Бургеры", callback_data='cat_burgers')],
        [InlineKeyboardButton("🍕 Пицца", callback_data='cat_pizza')],
        [InlineKeyboardButton("🍣 Суши", callback_data='cat_sushi')],
        [InlineKeyboardButton("🛒 Корзина", callback_data='cart')],
        [InlineKeyboardButton("❓ Помощь", callback_data='help')]
    ]
    
    await update.message.reply_text(
        f"🍽️ *Привет, {user.first_name}!*\n\n"
        "Добро пожаловать в *NYC Food Bot*!\n"
        "Выберите категорию:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /menu"""
    await start(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "🤖 *Помощь*\n\n"
        "Команды:\n"
        "/start - Начать заказ\n"
        "/menu - Показать меню\n"
        "/help - Эта справка\n\n"
        "Выбирайте категории, добавляйте в корзину!",
        parse_mode='Markdown'
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /admin (только для админа)"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет доступа!")
        return
    
    users_count = len(user_carts)
    await update.message.reply_text(
        f"👑 *Админ панель*\n\n"
        f"• Пользователей онлайн: {users_count}\n"
        f"• Бот работает: Да\n"
        f"• Режим: 24/7",
        parse_mode='Markdown'
    )

# ========== КНОПКИ ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Создаем корзину если нет
    if user_id not in user_carts:
        user_carts[user_id] = {}
    
    if data == 'cart':
        await show_cart(query, user_id)
    elif data == 'help':
        await show_help(query)
    elif data == 'back':
        await show_main_menu(query)
    elif data.startswith('cat_'):
        category = data[4:]  # 'cat_burgers' → 'burgers'
        await show_category(query, category)
    elif data.startswith('add_'):
        item_name = data[4:]  # 'add_🍔 Классический бургер'
        await add_to_cart(query, user_id, item_name)
    elif data == 'clear_cart':
        user_carts[user_id] = {}
        await query.edit_message_text("🗑️ Корзина очищена!")

async def show_main_menu(query):
    """Показать главное меню"""
    keyboard = [
        [InlineKeyboardButton("🍔 Бургеры", callback_data='cat_burgers')],
        [InlineKeyboardButton("🍕 Пицца", callback_data='cat_pizza')],
        [InlineKeyboardButton("🍣 Суши", callback_data='cat_sushi')],
        [InlineKeyboardButton("🛒 Корзина", callback_data='cart')],
        [InlineKeyboardButton("❓ Помощь", callback_data='help')]
    ]
    
    await query.edit_message_text(
        "🍽️ *NYC Food Bot*\n\nВыберите категорию:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_category(query, category):
    """Показать категорию блюд"""
    category_names = {
        'burgers': '🍔 Бургеры',
        'pizza': '🍕 Пицца',
        'sushi': '🍣 Суши'
    }
    
    items = MENU.get(category, {})
    
    keyboard = []
    for item_name, price in items.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{item_name} - {price}₽",
                callback_data=f"add_{item_name}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("⬅️ Назад", callback_data='back'),
        InlineKeyboardButton("🛒 Корзина", callback_data='cart')
    ])
    
    await query.edit_message_text(
        f"*{category_names.get(category, 'Категория')}:*\n\nВыберите блюдо:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def add_to_cart(query, user_id, item_name):
    """Добавить в корзину"""
    cart = user_carts[user_id]
    
    if item_name in cart:
        cart[item_name] += 1
    else:
        cart[item_name] = 1
    
    # Находим цену
    price = 0
    for category in MENU.values():
        if item_name in category:
            price = category[item_name]
            break
    
    total_items = sum(cart.values())
    
    await query.edit_message_text(
        f"✅ *{item_name} добавлен в корзину!*\n\n"
        f"💰 Цена: {price}₽\n"
        f"🛍️ Товаров в корзине: {total_items}\n\n"
        "Продолжайте выбирать:",
        parse_mode='Markdown'
    )

async def show_cart(query, user_id):
    """Показать корзину"""
    cart = user_carts.get(user_id, {})
    
    if not cart:
        text = "🛒 *Ваша корзина пуста*\n\nДобавьте блюда из меню!"
    else:
        text = "🛒 *Ваша корзина:*\n\n"
        total = 0
        
        for item_name, quantity in cart.items():
            # Находим цену
            price = 0
            for category in MENU.values():
                if item_name in category:
                    price = category[item_name]
                    break
            
            item_total = price * quantity
            total += item_total
            text += f"• {item_name} ×{quantity} = {item_total}₽\n"
        
        text += f"\n💵 *Итого: {total}₽*"
    
    keyboard = [
        [InlineKeyboardButton("✅ Оформить заказ", callback_data='checkout')],
        [InlineKeyboardButton("⬅️ В меню", callback_data='back')],
        [InlineKeyboardButton("🗑️ Очистить корзину", callback_data='clear_cart')]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_help(query):
    """Показать помощь"""
    text = (
        "🤖 *Помощь по боту*\n\n"
        "• Выбирайте категории блюд\n"
        "• Добавляйте в корзину\n"
        "• Оформляйте заказ\n\n"
        "*Команды:*\n"
        "/start - начать заказ\n"
        "/menu - показать меню\n"
        "/help - эта справка\n\n"
        "📞 *Поддержка:* @Muzaffar20081"
    )
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='back')]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# ========== ЗАПУСК ==========
def main():
    """Запуск бота"""
    if not TOKEN:
        logger.error("❌ ОШИБКА: Нет токена бота!")
        logger.error("Создайте файл .env с BOT_TOKEN=ваш_токен")
        return
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin))
    
    # Добавляем обработчик кнопок
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Запускаем бота
    logger.info("✅ Бот запускается...")
    logger.info(f"🤖 Токен: {TOKEN[:10]}...")
    logger.info("📱 Ищите бота в Telegram")
    
    application.run_polling()

if __name__ == "__main__":
    main()
