from discord.ext import tasks, commands
from drg import missions

class MissionDataCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_data = None
        self.refresh_daily_data.start()
    
    def cog_unload(self):
        self.refresh_daily_data.cancel()
    
    @tasks.loop(hours=24)
    async def refresh_daily_data(self):
        self.daily_data = missions.MissionData()
    
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
        )
        
        await ctx.send(str(gold_rush_missions))

    @commands.command()
    async def doublexp(self, ctx, season: str = 's0'):
        double_xp_missions = (
            self.daily_data.missions
            .exclude_past_missions()
            .filter_season(season)
            .filter_mutator('Double XP')
        )
        
        await ctx.send(str(double_xp_missions))

    @commands.command()
    async def primary(self, ctx, primary, season: str = 's0'):
        missions_with_primary = (
            self.daily_data.missions
            .exclude_past_missions()
            .filter_season(season)
            .filter_primary(primary)
        )

        await ctx.send(str(missions_with_primary))

    @commands.command()
    async def daily(self, ctx):
        await ctx.send(str(self.daily_data.daily_deal))

async def setup(bot):
    await bot.add_cog(MissionDataCog(bot))