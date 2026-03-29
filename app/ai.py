import requests
import config

context = {}
def ask_ai(user_id, prompt, system_prompt, history=None):
    url = "https://api.intelligence.io.solutions/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        f"Authorization": f"Bearer {config.AI_KEY}",
    }

    if user_id not in context:
        context[user_id] = []

    context[user_id].append(
            {
                "role": "system",
                "content": system_prompt + '. ТВОЙ ОТВЕТ ДОЛЖЕН СОДЕРЖАТЬ ТОЛЬКО ЗАПРОШЕННУЮ ИНФОРМАЦИЮ БЕЗ ТВОИХ ДОПОЛНИТЕЛЬНЫХ ПОДПИСЕЙ, ТК ОН БУДЕТ ОТПРАВЛЕН ПОЛЬЗОВАТЕЛЮ БЕЗ ИЗМЕНЕНИЙ И НЕ ДОЛЖЕН СОДЕРЖАТЬ НИЧЕГО ЛИШНЕГО.'
            })

    context[user_id].append(
            {
                "role": "user",
                "content": prompt
            })

    data = {
        "model": "deepseek-ai/DeepSeek-R1-0528",
        "messages": context[user_id]
    }

    response = requests.post(url, headers=headers, json=data)
    data = response.json()
    text = data['choices'][0]['message']['content']
    return text.split('</think>\n')[-1]
