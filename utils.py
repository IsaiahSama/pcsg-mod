from discord.channel import TextChannel
from discord.ext.commands import Bot, Cog
from discord_slash import SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_option
from config import config

class Utils(Cog):
    def __init__(self, bot:Bot):
        self.bot = bot

    @cog_ext.cog_slash(name="portal", description="Creates a link to another channel.", guild_ids=[config['guild_ids']], 
    options=create_option(name="channel", description="Provides a link to the selected channel", option_type=TextChannel, required=True))
    async def portal(self, ctx:SlashContext, channel:TextChannel):
        await ctx.send(channel.mention)

def setup(bot:Bot):
    bot.add_cog(Utils(bot))