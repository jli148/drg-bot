import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

intents = discord.Intents(messages=True, message_content=True)
bot = commands.Bot(command_prefix='$', intents=intents)
bot.load_extension('cogs.daily_data_cog')

bot.run(os.getenv('TOKEN'))
