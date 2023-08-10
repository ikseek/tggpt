import logging

from aiogram import Bot, Dispatcher, types
from os import environ
from .last_messages import LastMessages
from .prompt import prompt
from openai import ChatCompletion
from datetime import datetime, timezone
from asyncio import to_thread, gather
from re import match, escape, MULTILINE, DOTALL
from textwrap import indent
from .horde import generate_image
from io import BytesIO
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize bot and dispatcher
bot = Bot(token=environ['BOT_TOKEN'])
dp = Dispatcher(bot)

allowed_chats = [int(chat) for chat in environ.get("ALLOWED_CHATS", "").split(",") if chat]
logging.info("Allowed chats: %s", allowed_chats)
all_messages = {chat: LastMessages(2000) for chat in allowed_chats}


@dp.message_handler(commands=types.BotCommand(command="draw", description="Draw an image"))
async def draw(message: types.Message):
    placeholder_text = "Sending request"
    with Path(__file__).parent.joinpath("line.png").open('rb') as ph_file:
        placeholder = await message.reply_photo(ph_file, placeholder_text)
    async for status, val in generate_image(message.get_args()):
        if status == "done":
            await placeholder.edit_media(types.InputMediaPhoto(media=BytesIO(val), caption="Here is your image"))
        else:
            progress = f"Waiting in line, ETA {val}"
            if placeholder_text != progress:
                await placeholder.edit_caption(caption=progress)
                placeholder_text = progress

@dp.message_handler(lambda msg: msg.chat.id in all_messages)
async def message_edited(message: types.Message):
    all_messages[message.chat.id].edit(message.message_id, message.text)


@dp.message_handler()
async def message_received(message: types.Message):
    if message.chat.id not in all_messages:
        logging.warning("Ignoring chat %s, message from %s",
                        message.chat.id, message.from_user.username)
        return
    last_messages = all_messages[message.chat.id]
    message_text = message.text
    if message.reply_to_message:
        message_text = indent(message.reply_to_message.text, ">>") + "\n" + message_text
    last_messages.add(message.message_id, datetime.now(timezone.utc), message.from_user.username, message_text)
    mentions = [m.get_text(message.text) for m in message.entities if m.type == "mention"]
    bot = await message.bot.me

    is_reply = message.reply_to_message and message.reply_to_message["from"].username == bot.username

    if "@" + bot.username in mentions or is_reply:
        await respond(bot, message, last_messages)



async def respond(bot: types.User, message: types.Message, last_messages):
    now = datetime.now(timezone.utc)
    p = prompt(now, bot.username, last_messages.get_all())
    placeholder = message.answer("🤖💭", reply=True)
    completion = to_thread(ChatCompletion.create, model="gpt-3.5-turbo", temperature=0, messages=p)
    placeholder, completion = await gather(placeholder, completion)

    response = completion.choices[0].message.content.strip()
    regex = r'### \d+:\d+:\d+ {name}: (.*)'.format(name=escape(bot.username))
    bot_replied_with_header = match(regex, response, MULTILINE | DOTALL)
    if bot_replied_with_header:
        response = bot_replied_with_header.group(1)

    result = await placeholder.edit_text(response)
    last_messages.add(result.message_id, now, bot.username, response)
