import os
import logging
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

# Получение токена из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ ОШИБКА: BOT_TOKEN не найден!")
    logger.error("Добавь BOT_TOKEN в Variables на Railway")
    exit(1)

ADMIN_ID = os.getenv("ADMIN_ID", "0")

# Меню ресторана
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

# Корзины пользователей (в памяти)
user_carts = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("🍔 Бургеры", callback_data='cat_burgers')],
        [InlineKeyboardButton("🍕 Пицца", callback_data='cat_pizza')],
        [InlineKeyboardButton("🍣 Суши", callback_data='cat_sushi')],
        [InlineKeyboardButton("🛒 Корзина", callback_data='cart')],
        [InlineKeyboardButton("❓ Помощь", callback_data='help')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🍽️ *Привет, {user.first_name}!*\n\n"
        "Добро пожаловать в *NYC Food Bot*! 🍔🍕🍣\n"
        "Выберите категорию блюд:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    logger.info(f"Пользователь {user.id} начал работу с ботом")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "🤖 *NYC Food Bot - Помощь*\n\n"
        "📋 *Как пользоваться:*\n"
        "1. Нажмите /start\n"
        "2. Выберите категорию блюд\n"
        "3. Добавляйте блюда в корзину\n"
        "4. Перейдите в корзину для оформления\n\n"
        "⚡ *Команды:*\n"
        "/start - Начать заказ\n"
        "/menu - Показать меню\n"
        "/help - Эта справка\n"
        "/status - Статус бота\n\n"
        "⏰ Бот работает 24/7 на Railway!"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /menu"""
    await start_command(update, context)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status"""
    status_text = (
        "✅ *Статус бота:* Работает нормально\n"
        "🕐 *Время работы:* 24/7\n"
        "🚀 *Хостинг:* Railway\n"
        "👥 *Пользователи онлайн:* 1\n"
        "🍽️ *Доступно блюд:* 9\n\n"
        "Бот готов к заказам! 🍔"
    )
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Инициализируем корзину если нет
    if user_id not in user_carts:
        user_carts[user_id] = {}
    
    if data == 'cart':
        await show_cart(query, user_id)
    elif data == 'help':
        await show_help_menu(query)
    elif data == 'back':
        await show_main_menu(query)
    elif data.startswith('cat_'):
        category = data.replace('cat_', '')
        await show_category_menu(query, category)
    elif data.startswith('add_'):
        item_name = data.replace('add_', '')
        await add_item_to_cart(query, user_id, item_name)
    elif data == 'clear_cart':
        user_carts[user_id] = {}
        await query.edit_message_text("🗑️ *Корзина очищена!*", parse_mode='Markdown')

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
        "🍽️ *NYC Food Bot - Главное меню*\n\n"
        "Выберите категорию блюд:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_category_menu(query, category):
    """Показать меню категории"""
    category_names = {
        'burgers': '🍔 Бургеры',
        'pizza': '🍕 Пицца',
        'sushi': '🍣 Суши'
    }
    
    if category not in MENU:
        await query.edit_message_text("Категория не найдена")
        return
    
    items = MENU[category]
    category_name = category_names.get(category, category)
    
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
        f"*{category_name}*\n\nВыберите блюдо:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def add_item_to_cart(query, user_id, item_name):
    """Добавить товар в корзину"""
    cart = user_carts[user_id]
    
    # Находим цену
    price = None
    for category in MENU.values():
        if item_name in category:
            price = category[item_name]
            break
    
    if price is None:
        await query.edit_message_text("❌ Ошибка: товар не найден")
        return
    
    # Добавляем в корзину
    if item_name in cart:
        cart[item_name] += 1
    else:
        cart[item_name] = 1
    
    total_items = sum(cart.values())
    
    await query.edit_message_text(
        f"✅ *{item_name} добавлен в корзину!*\n\n"
        f"💰 Цена: {price}₽\n"
        f"🛒 Товаров в корзине: {total_items}\n\n"
        "Продолжайте выбирать блюда!",
        parse_mode='Markdown'
    )

async def show_cart(query, user_id):
    """Показать корзину"""
    cart = user_carts.get(user_id, {})
    
    if not cart:
        text = "🛒 *Ваша корзина пуста*\n\nДобавьте блюда из меню!"
        keyboard = [[InlineKeyboardButton("🍽️ В меню", callback_data='back')]]
    else:
        text = "🛒 *Ваша корзина:*\n\n"
        total_price = 0
        
        for item_name, quantity in cart.items():
            # Находим цену
            price = 0
            for category in MENU.values():
                if item_name in category:
                    price = category[item_name]
                    break
            
            item_total = price * quantity
            total_price += item_total
            text += f"• {item_name} ×{quantity} = {item_total}₽\n"
        
        text += f"\n💵 *Итого: {total_price}₽*"
        
        keyboard = [
            [InlineKeyboardButton("✅ Оформить заказ", callback_data='checkout')],
            [InlineKeyboardButton("⬅️ Продолжить покупки", callback_data='back')],
            [InlineKeyboardButton("🗑️ Очистить корзину", callback_data='clear_cart')]
        ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_help_menu(query):
    """Показать меню помощи"""
    help_text = (
        "🤖 *Помощь по боту*\n\n"
        "• Выбирайте категории блюд\n"
        "• Добавляйте в корзину\n"
        "• Оформляйте заказ\n\n"
        "📞 *Поддержка:* @Muzaffar20081\n"
        "🚀 *Хостинг:* Railway 24/7"
    )
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='back')]]
    
    await query.edit_message_text(
        help_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def main():
    """Основная функция запуска бота"""
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК NYC FOOD BOT")
    logger.info(f"🤖 Токен: {BOT_TOKEN[:15]}...")
    logger.info(f"👑 Админ ID: {ADMIN_ID}")
    logger.info("=" * 50)
    
    try:
        # Создаем приложение
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("menu", menu_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("status", status_command))
        
        # Добавляем обработчик кнопок
        application.add_handler(CallbackQueryHandler(button_callback))
        
        # Запускаем бота
        logger.info("✅ Бот успешно запущен!")
        logger.info("📱 Ищите бота в Telegram")
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        logger.error("Бот остановлен")

if __name__ == "__main__":
    main()
