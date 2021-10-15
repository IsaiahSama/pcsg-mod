from discord.channel import TextChannel
from discord import Embed, Member
from discord.ext.commands import Bot, Cog
from discord_slash import SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_choice, create_option
from config import config
from database import db
from random import randint

class Utils(Cog):
    def __init__(self, bot:Bot):
        self.bot = bot

    @cog_ext.cog_slash(name="portal", description="Creates a link to another channel.", guild_ids=config['guild_ids'], 
    options=[create_option(name="channel", description="Provides a link to the selected channel", option_type=TextChannel, required=True)])
    async def portal(self, ctx:SlashContext, channel:TextChannel):
        await ctx.send(channel.mention)

    @cog_ext.cog_slash(name="rank", description="Displays your rank based on level.", guild_ids=config['guild_ids'], options=[
        create_option(
        name="member", description="Optional: The person who's rank you want to check", option_type=Member, required=False)])
    async def rank(self, ctx:SlashContext, member:Member=None):
        target = member or ctx.author
        all_users = await db.query_all_users()
        user = [user for user in all_users if user[0] == target.id]
        if user:
            user = user[0]
            all_users.sort(key=lambda x: x[1], reverse=True)
            embed = Embed(title=f"Showing Activity Level for {target.name}", color=randint(0, 0xffffff))
            embed.add_field(name="Rank", value=f"{all_users.index(user)} of {len(all_users)} members")
            embed.add_field(name="Exp", value=user[1])
            await ctx.send(embed=embed)
        else:
            await ctx.send("Stange... you're not in the database... Try being a bit more active and checking again later.")

    @cog_ext.cog_slash(name="top", description="Displays the 5 most active users.", guild_ids=config['guild_ids'])
    async def top(self, ctx:SlashContext):
        all_users = await db.query_all_users()
        all_users.sort(key=lambda x: x[1], reverse=True)
        embed = Embed(title="SHowing top 5 most active", color=randint(0, 0xffffff))
        for user in all_users[:5]:
            embed.add_field(name="Name:", value=ctx.guild.get_member(user[0]) or "Unknown User")
            embed.add_field(name="Exp:", value=user[1])
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="style", description="Used to view and choose your learning style", guild_ids=config['guild_ids'],
    options=[
        create_option("learn", "Select a learning style that you want to learn more about", str, False, choices=[create_choice(value, name) for value, name in zip(config['styles'].keys(), [name.split("\n")[0] for name in config['styles'].values()])]),
        create_option("choose", "Select your learning style from the provided options", str, False, choices=[create_choice(value, name) for value, name in zip(config['styles'].keys(), [name.split("\n")[0] for name in config['styles'].values()])]),
        create_option("find", "Finds other students that have a similar learning style to you", str, False, choices=[create_choice(value, name) for value, name in zip(config['styles'].keys(), [name.split("\n")[0] for name in config['styles'].values()])])
    ])
    async def style(self, ctx:SlashContext, learn:str='', choose:str='', find:str=''):
        # await ctx.defer()
        if not any((find, learn, choose)): await ctx.send("Nothing was selected", delete_after=5); return False 
        if learn:
            await ctx.send(config['styles'][learn])
        elif choose:
            try:
                role = config['role_styles'][choose]
                await ctx.author.add_roles(role) if role not in ctx.author.roles else ctx.author.remove_roles(role)
                await ctx.send(f"You have successfully {'gained' if role in ctx.author.roles else 'removed'} the {role.name} role")
            except KeyError:
                await ctx.send("Sorry, we're still waiting on the roles to be created before this can work.")
        else:
            try:
                role = config['role_styles'][choose]
            except KeyError:
                await ctx.send("Sorry, we're still waiting on the roles to be created before this can work.")


def setup(bot:Bot):
    bot.add_cog(Utils(bot))