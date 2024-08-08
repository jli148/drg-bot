from datetime import datetime, time, timezone
from discord.ext import tasks, commands
from drg import deep_dive

DELAY_AFTER_REFRESH_SECONDS = 5
loop_time = time(
    hour=deep_dive.DEEP_DIVE_REFRESH_HOUR,
    minute=0,
    second=DELAY_AFTER_REFRESH_SECONDS,
    tzinfo=timezone.utc
)

class DeepDiveDataCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = deep_dive.DeepDiveData()
        self.refresh_data.start()
    
    def cog_unload(self):
        self.refresh_data.cancel()
    
    @tasks.loop(time=loop_time)
    async def refresh_data(self):
        if datetime.today().weekday() == deep_dive.DEEP_DIVE_REFRESH_DAY:
            self.data = deep_dive.DeepDiveData()
    
    @commands.command()
    async def deepdive(self, ctx):
        await ctx.send(str(self.data.deep_dive))

    @commands.command()
    async def elitedeepdive(self, ctx):
        await ctx.send(str(self.data.elite_deep_dive))

async def setup(bot):
    await bot.add_cog(DeepDiveDataCog(bot))
