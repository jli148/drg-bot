from discord.ext import tasks, commands
from drg import daily_data

class DailyDataCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_data = None
        self.refresh_daily_data.start()
    
    def cog_unload(self):
        self.refresh_daily_data.cancel()
    
    @tasks.loop(hours=24)
    async def refresh_daily_data(self):
        self.daily_data = daily_data.DailyData()
    
    @commands.command()
    async def current(self, ctx, season: str = 's0'):
        current_missions = (
            self.daily_data.missions
            .exclude_past_missions()
            .filter_current_missions()
            .filter_season(season)
        )
        
        await ctx.send(str(current_missions))

    @commands.command()
    async def upcoming(self, ctx, season: str = 's0'):
        upcoming_missions = (
            self.daily_data.missions
            .exclude_past_missions()
            .filter_upcoming_missions()
            .filter_season(season)
        )
        
        await ctx.send(str(upcoming_missions))

    @commands.command()
    async def goldrush(self, ctx, season: str = 's0'):
        gold_rush_missions = (
            self.daily_data.missions
            .exclude_past_missions()
            .filter_season(season)
            .filter_mutator('Gold Rush')
            .head()
        )
        
        msg = gold_rush_missions.to_markdown(drop_cols=['Season', 'Mission ID', 'Mutator'])
        await ctx.send(msg)

    @commands.command()
    async def doublexp(self, ctx, season: str = 's0'):
        double_xp_missions = (
            self.daily_data.missions
            .exclude_past_missions()
            .filter_season(season)
            .filter_mutator('Double XP')
            .head()
        )
        
        msg = double_xp_missions.to_markdown(drop_cols=['Season', 'Mission ID', 'Mutator'])
        await ctx.send(msg)

    @commands.command()
    async def primary(self, ctx, primary, season: str = 's0'):
        missions_with_primary = (
            self.daily_data.missions
            .exclude_past_missions()
            .filter_season(season)
            .filter_primary(primary)
            .head()
        )

        msg = missions_with_primary.to_markdown(drop_cols=['Season', 'Mission ID', 'Primary'])
        await ctx.send(msg)

    @commands.command()
    async def daily(self, ctx):
        await ctx.send(str(self.daily_data.daily_deal))

async def setup(bot):
    await bot.add_cog(DailyDataCog(bot))