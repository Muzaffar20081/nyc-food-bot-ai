import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

async def ai_response(user_message):
    """Ответ от AI"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты помощник в ресторане NYC Food Bot. Помогай с заказами, меню и отвечай на вопросы."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Извините, произошла ошибка: {str(e)}"