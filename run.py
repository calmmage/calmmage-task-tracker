import asyncio
from dotenv import load_dotenv

load_dotenv()
from project_name.bot import bot, dp


if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
