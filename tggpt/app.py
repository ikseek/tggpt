import logging

from aiogram import Bot, Dispatcher, types
from os import environ

from aiogram.utils.exceptions import RetryAfter

from .last_messages import LastMessages
from .prompt import prompt
from openai import ChatCompletion
from datetime import datetime, timezone
from asyncio import to_thread, gather, sleep
from re import match, escape, MULTILINE, DOTALL
from textwrap import indent
from .horde import generate_image, list_models
from io import BytesIO
from pathlib import Path
from asyncio import to_thread
from openai import ChatCompletion

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize bot and dispatcher
bot = Bot(token=environ['BOT_TOKEN'])
dp = Dispatcher(bot)

allowed_chats = [int(chat) for chat in environ.get("ALLOWED_CHATS", "").split(",") if chat]
logging.info("Allowed chats: %s", allowed_chats)
all_messages = {chat: LastMessages(2000) for chat in allowed_chats}

@dp.message_handler(commands=types.BotCommand(command="models", description="List all models"))
async def models(message: types.Message):
    res = await list_models()
    await message.reply(", ".join(res))

@dp.message_handler(commands=types.BotCommand(command="draw", description="Draw an image"))
async def draw(message: types.Message):
    prompt = message.get_args()
    if not prompt:
        await message.reply("Please provide image description")
        return
    try:
        prompt.encode('ascii')
    except Exception:

        request = [{"role": "system", "content": "Translate every message user sends to English"},
                   {"role": "user", "content": prompt}]
        completion = await to_thread(ChatCompletion.create, model="gpt-3.5-turbo", temperature=0, messages=request)
        prompt = completion.choices[0].message.content.strip()

    placeholder_text = f"Sending request: {prompt}"
    with Path(__file__).parent.joinpath("line.png").open('rb') as ph_file:
        placeholder = await message.reply_photo(ph_file, placeholder_text)
    try:
        async for status, val in generate_image(prompt):
            if status == "done":
                await sleep(1)
                await placeholder.edit_media(types.InputMediaPhoto(media=BytesIO(val), caption="Here is your image"))
            else:
                progress = f"Waiting in line, ETA {val}"
                if placeholder_text != progress:
                    try:
                        await placeholder.edit_caption(caption=progress)
                        placeholder_text = progress
                    except RetryAfter as e:
                        await sleep(e.timeout)
    except Exception as e:
        await placeholder.edit_caption(f"Error: {e}")


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


@dp.message_handler(lambda msg: msg.chat.id in all_messages)
async def message_edited(message: types.Message):
    all_messages[message.chat.id].edit(message.message_id, message.text)


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
