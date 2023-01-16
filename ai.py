import asyncio
import openai

from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import defer_call, info as session_info, run_async, run_js

chat_msgs = []
online_users = set()
count_users_online = []

MAX_MESSAGES_COUNT = 1000

openai.api_key = "" # YOUR API KEY OPENAI   https://beta.openai.com/signup/

def generate_response(prompt):
  completions = openai.Completion.create(
    engine="text-davinci-002",
    prompt=prompt,
    max_tokens=2048,
    n=1,
    stop=None,
    temperature=0.5,
  )

  message = completions.choices[0].text
  return message.strip()

async def main():
    global chat_msgs

    put_markdown("## Добро пожаловать в чат с искусственным интеллектом !\nНапишите знак '!' перед сообщением чтобы получить ответ от ИИ\nИскусственный интеллект на базе - GPT3")

    msg_box = output()
    put_scrollable(msg_box, height=300, keep_bottom=True)


    nickname = await input("Войти в чат", required=True, placeholder="Ваше имя", validate=lambda n: "Такой ник уже используется!" if n in online_users or n == '📢' or n == 'AI' else None)
    online_users.add(nickname)
    count_users_online.append(nickname)

    chat_msgs.append(('📢', f'`{nickname}` присоединился к чату!'))
    msg_box.append(put_markdown(f'📢 `{nickname}` присоединился к чату'))

    refresh_task = run_async(refresh_msg(nickname, msg_box, online_users))

    while True:
        data = await input_group("💭 Новое сообщение", [
            input(placeholder="Текст сообщения ...", name="msg"),
            actions(name="cmd", buttons=["Отправить", {'label': "Выйти из чата", 'type': 'cancel'}])
        ], validate = lambda m: ('msg', "Введите текст сообщения!") if m["cmd"] == "Отправить" and not m['msg'] else None)

        if data is None:
            break

        msg_box.append(put_markdown(f"`{nickname}`: {data['msg']}"))
        chat_msgs.append((nickname, data['msg']))

        print(online_users)

        if data['msg'].startswith('!'):
        	text_for_ai = data['msg'].split('!')[1]
	        response = generate_response(prompt=text_for_ai)
	        chat_msgs.append(("`AI`", f"`{nickname}`, `{response}`"))


        if data['msg'] == '/online_count':
            chat_msgs.append(("`ONLINE`", f"Онлайн: {len(online_users)}\n{', '.join(count_users_online)}"))

    refresh_task.close()


    online_users.remove(nickname)
    count_users_online.remove(nickname)
    toast("Вы вышли из чата!")
    msg_box.append(put_markdown(f'📢 Пользователь `{nickname}` покинул чат!'))
    chat_msgs.append(('📢', f'Пользователь `{nickname}` покинул чат!'))

    put_buttons(['Перезайти'], onclick=lambda btn:run_js('window.location.reload()'))

async def refresh_msg(nickname, msg_box, online_users):
    global chat_msgs
    global users
    users = online_users
    last_idx = len(chat_msgs)
    while True:
        await asyncio.sleep(1)
        #users = online_users
        #online_box.append(put_markdown(f"Online: {users}"))
        for m in chat_msgs[last_idx:]:
            if m[0] != nickname: # if not a message from current user
                msg_box.append(put_markdown(f"`{m[0]}`: {m[1]}"))
        # remove expired
        if len(chat_msgs) > MAX_MESSAGES_COUNT:
            chat_msgs = chat_msgs[len(chat_msgs) // 2:]
        
        last_idx = len(chat_msgs)
		
if __name__ == "__main__":
    start_server(main, debug=True, port=8080, cdn=False)