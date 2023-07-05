import logging

from aiogram import Bot, Dispatcher, types
from os import environ
from .last_messages import LastMessages
from .prompt import prompt
from openai import ChatCompletion
from datetime import datetime, timezone
from asyncio import to_thread, gather

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
        await respond(bot, message, last_messages)


@dp.message_handler(lambda msg: msg.chat.id in all_messages)
async def message_edited(message: types.Message):
    all_messages[message.chat.id].edit(message.message_id,
                                       f'{message.from_user.username}: {message.text}')


async def respond(bot: types.User, message: types.Message, last_messages):
    p = prompt(datetime.now(timezone.utc), bot.username, last_messages.get_all())
    placeholder = message.answer("🤖💭", reply=True)
    completion = to_thread(ChatCompletion.create, model="gpt-3.5-turbo", temperature=0, messages=p)
    placeholder, completion = await gather(placeholder, completion)

    response = completion.choices[0].message.content.strip().removeprefix(bot.username + ": ")

    result = await placeholder.edit_text(response)
    last_messages.add(result.message_id, f'{result.from_user.username}: {result.text}')
