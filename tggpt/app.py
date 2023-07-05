import logging

from aiogram import Bot, Dispatcher, types
from os import environ
from collections import defaultdict
from .last_messages import LastMessages
from .prompt import prompt
from openai import ChatCompletion

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=environ['BOT_TOKEN'])
dp = Dispatcher(bot)

all_messages = defaultdict(lambda: LastMessages(500))


@dp.message_handler()
async def message_received(message: types.Message):
    last_messages = all_messages[message.chat.id]
    last_messages.add(message.message_id,
                                      f'{message.from_user.username}: {message.text}')
    mentions = [m.get_text(message.text) for m in message.entities if m.type == "mention"]

    if "@toB2222Bot" in mentions:
        p = prompt('toB2222Bot', last_messages.get_all())
        completion = ChatCompletion.create(model="gpt-3.5-turbo", temperature=0, messages=p)
        response = completion.choices[0].message.content.strip()

        result = await message.answer(response)
        last_messages.add(result.message_id, f'{result.from_user.username}: {result.text}')


@dp.edited_message_handler()
async def message_edited(message: types.Message):
    all_messages[message.chat.id].edit(message.message_id,
                                       f'{message.from_user.username}: {message.text}')
