from discord.ext.commands import Cog, Bot, command, has_guild_permissions
import discord
from discord.ext.commands.context import Context
from discord import Permissions
from discord.permissions import PermissionOverwrite

class Admin(Cog):
    def __init__(self, bot: Bot):
        """Class where all ADMIN commands will be located"""
        self.bot = bot
        

    @command(name="Kick", brief="Kicks a user", help="Used to kick a user from the server", usage="@member reason")
    @has_guild_permissions(kick_members=True)
    async def kick(self, ctx: Context, member:discord.Member, reason:str):
        try:
            await member.send(f"You have been kicked from {ctx.guild.name} by {ctx.author}. Reason: {reason}")
        except:
            pass 
        await member.kick(reason=reason)
        await ctx.send(f"{member} has been kicked from the server by {ctx.author}. Reason: {reason}")

    @command(name="Ban", brief="Bans a user from the server", help="Used to ban a user from the server", usage="@user|user_id reason")
    @has_guild_permissions(ban_members=True)
    async def ban(self, ctx:Context, user:discord.User, reason:str):
        try:
            await user.send(f"You have been banned from PCSG. Reason: {reason}")
        except:
            pass 
        await ctx.guild.ban(user)
        await ctx.send(f"{user} has been banned by {ctx.author}. Reason: {reason}")

    @command(name="Mute", brief="Mutes a user from the server for a given time", help="Prevents a user from speaking in the server for a given duration.", usage="@member time_in_minutes reason")
    @has_guild_permissions(manage_messages=True)
    async def mute(self, ctx:Context, member:discord.Member, timeout:int, reason:str):
        muted_role = discord.utils.get(ctx.guild.roles, name="E-Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="E-Muted")
            [await channel.edit(overwrites=channel.overwrites.update({muted_role: PermissionOverwrite(send_messages=False)})) for channel in ctx.guild.text_channels]
        
        await member.edit()
        

def setup(bot: Bot):
    bot.add_cog(Admin(bot))
    