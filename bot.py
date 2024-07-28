import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

import drg

load_dotenv()
intents = discord.Intents(messages=True, message_content=True)
bot = commands.Bot(command_prefix='$', intents=intents)

@bot.command()
async def current(ctx, season: str = 's0'):
    global daily_data
    if daily_data.check_if_expired():
        daily_data = drg.DailyData()

    current_missions = (
        daily_data.missions
        .exclude_past_missions()
        .filter_current_missions()
        .filter_season(season)
    )
    
    await ctx.send(str(current_missions))

@bot.command()
async def upcoming(ctx, season: str = 's0'):
    global daily_data
    if daily_data.check_if_expired():
        daily_data = drg.DailyData()

    upcoming_missions = (
        daily_data.missions
        .exclude_past_missions()
        .filter_upcoming_missions()
        .filter_season(season)
    )
    
    await ctx.send(str(upcoming_missions))

@bot.command()
async def goldrush(ctx, season: str = 's0'):
    global daily_data
    if daily_data.check_if_expired():
        daily_data = drg.DailyData()

    gold_rush_missions = (
        daily_data.missions
        .exclude_past_missions()
        .filter_season(season)
        .filter_mutator('Gold Rush')
        .head()
    )
    
    msg = gold_rush_missions.to_markdown(drop_cols=['Season', 'Mission ID', 'Mutator'])
    await ctx.send(msg)

@bot.command()
async def doublexp(ctx, season: str = 's0'):
    global daily_data
    if daily_data.check_if_expired():
        daily_data = drg.DailyData()

    double_xp_missions = (
        daily_data.missions
        .exclude_past_missions()
        .filter_season(season)
        .filter_mutator('Double XP')
        .head()
    )
    
    msg = double_xp_missions.to_markdown(drop_cols=['Season', 'Mission ID', 'Mutator'])
    await ctx.send(msg)

@bot.command()
async def primary(ctx, primary, season: str = 's0'):
    global daily_data
    if daily_data.check_if_expired():
        daily_data = drg.DailyData()

    missions_with_primary = (
        daily_data.missions
        .exclude_past_missions()
        .filter_season(season)
        .filter_primary(primary)
        .head()
    )

    msg = missions_with_primary.to_markdown(drop_cols=['Season', 'Mission ID', 'Primary'])
    await ctx.send(msg)

@bot.command()
async def daily(ctx):
    global daily_data
    if daily_data.check_if_expired():
        daily_data = drg.DailyData()
    
    await ctx.send(str(daily_data.daily_deal))

daily_data = drg.DailyData()
bot.run(os.getenv('TOKEN'))
