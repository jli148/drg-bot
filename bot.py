import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

intents = discord.Intents(messages=True, message_content=True)
bot = commands.Bot(command_prefix='$', intents=intents)

async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            # cut off the .py from the file name
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.getenv('TOKEN'))

asyncio.run(main())
