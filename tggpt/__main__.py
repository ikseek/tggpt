from aiogram import executor
from .app import dp

executor.start_polling(dp, skip_updates=True)