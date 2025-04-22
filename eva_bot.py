import requests
import time

# Токены
BOT_TOKEN = '7283353383:AAHfhUL2YIzxAOhNxvjO7TQalYDakQ6Wlbs'
GROQ_API_KEY = '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'

URL = f'https://api.telegram.org/bot{BOT_TOKEN}/'
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

user_dialogs = {}
last_update_id = 0

def set_bot_commands():
    commands = [
        {"command": "start", "description": "Начать диалог"},
        {"command": "save", "description": "Сохранить диалог"},
        {"command": "draw", "description": "Сгенерировать изображение"}
    ]
    requests.post(URL + 'setMyCommands', json={"commands": commands})

def get_updates(offset):
    try:
        response = requests.get(URL + 'getUpdates', params={'timeout': 30, 'offset': offset})
        return response.json()
    except Exception as e:
        print("Ошибка получения обновлений:", e)
        return {"ok": False, "result": []}

def send_message(chat_id, text):
    try:
        requests.post(URL + 'sendMessage', data={'chat_id': chat_id, 'text': text})
    except Exception as e:
        print("Ошибка отправки:", e)

def send_typing(chat_id):
    try:
        requests.post(URL + 'sendChatAction', data={'chat_id': chat_id, 'action': 'typing'})
    except:
        pass

def get_groq_answer(user_id, text):
    history = user_dialogs.get(user_id, [])
    history.append({"role": "user", "content": text})

    try:
        response = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "system", "content": "Ты милая девушка по имени Ева, всегда отвечаешь в женском роде, с добрым и дружелюбным тоном."}] + history,
                "temperature": 0.7
            }
        )
        data = response.json()
        result = data['choices'][0]['message']['content']
    except Exception as e:
        print("Ошибка Groq:", e)
        result = "Извини, я пока не могу ответить. Попробуй позже."

    history.append({"role": "assistant", "content": result})
    user_dialogs[user_id] = history[-10:]
    return result

def handle_draw(text, chat_id):
    prompt = text.replace("/draw", "").strip()
    if not prompt:
        send_message(chat_id, "Напиши запрос после /draw, например: /draw девушка в киберпанке")
        return
    send_typing(chat_id)
    time.sleep(1)
    try:
        image_url = f"https://image.pollinations.ai/prompt/{prompt}"
        requests.post(URL + 'sendPhoto', data={'chat_id': chat_id, 'photo': image_url})
    except Exception as e:
        print("Ошибка генерации изображения:", e)
        send_message(chat_id, "Не удалось создать изображение. Попробуй снова.")

def handle_command(command, chat_id):
    if chat_id not in user_dialogs:
        user_dialogs[chat_id] = []
        print(f"Новый пользователь: {chat_id}")

    if command.startswith('/draw'):
        handle_draw(command, chat_id)
    elif command == '/start':
        send_message(chat_id, "Привет, я Ева — AI помощник. Спроси что-нибудь.")
    elif command == '/save':
        history = user_dialogs.get(chat_id, [])
        if not history:
            send_message(chat_id, "Диалог пуст.")
            return
        result = "\n".join([f"{h['role']}: {h['content']}" for h in history])
        send_message(chat_id, f"Вот твой диалог:\n{result}")

def handle_text(text, chat_id):
    print(f"Пользователь {chat_id} написал: {text}")
    if chat_id not in user_dialogs:
        user_dialogs[chat_id] = []
    send_typing(chat_id)
    time.sleep(1)
    reply = get_groq_answer(chat_id, text)
    send_message(chat_id, reply)

def main():
    global last_update_id
    set_bot_commands()
    print("Бот 'Ева' запущен!")

    while True:
        try:
            updates = get_updates(last_update_id + 1)
            if updates.get("ok"):
                for update in updates["result"]:
                    last_update_id = update["update_id"]
                    message = update.get("message")
                    if not message:
                        continue
                    chat_id = message["chat"]["id"]
                    text = message.get("text", "")
                    if text.startswith('/'):
                        handle_command(text, chat_id)
                    else:
                        handle_text(text, chat_id)
            time.sleep(0.1)
        except Exception as e:
            print("Ошибка в главном цикле:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()
