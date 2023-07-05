import logging

from aiogram import Bot, Dispatcher, types
from os import environ
from .last_messages import LastMessages
from .prompt import prompt
from openai import ChatCompletion

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize bot and dispatcher
bot = Bot(token=environ['BOT_TOKEN'])
dp = Dispatcher(bot)

allowed_chats = [int(chat) for chat in environ.get("ALLOWED_CHATS", "").split(",") if chat]
logging.info("Allowed chats: %s", allowed_chats)
all_messages = {chat: LastMessages(500) for chat in allowed_chats}


@dp.message_handler()
async def message_received(message: types.Message):
    if message.chat.id not in all_messages:
        logging.warning("Ignoring chat %s, message from %s",
                        message.chat.id, message.from_user.username)
        return
    last_messages = all_messages[message.chat.id]
    last_messages.add(message.message_id,
                      f'{message.from_user.username}: {message.text}')
    mentions = [m.get_text(message.text) for m in message.entities if m.type == "mention"]
    bot = await message.bot.me

    if "@" + bot.username in mentions:
        p = prompt(bot.username, last_messages.get_all())
        completion = ChatCompletion.create(model="gpt-3.5-turbo", temperature=0, messages=p)
        response = completion.choices[0].message.content.strip().removeprefix(bot.username + ": ")

        result = await message.answer(response)
        last_messages.add(result.message_id, f'{result.from_user.username}: {result.text}')


@dp.message_handler(lambda msg: msg.chat.id in all_messages)
async def message_edited(message: types.Message):
    all_messages[message.chat.id].edit(message.message_id,
                                       f'{message.from_user.username}: {message.text}')
