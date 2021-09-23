from discord.ext.commands import Cog, Bot
from discord import Embed
from discord.member import Member
from discord.message import Message
from config import config
from random import randint
from time import ctime
from database import db

class EventHandler(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot 

    # Event Handlers
    @Cog.listener()
    async def on_message(self, message:Message):
        if await self.moderate_message(message):
            await message.channel.send(f"{message.author.mention} watch your language!")
            await message.delete()
        
        if await db.is_monitored(message.author.id):
            monitor = config['channels']['monitor-logs']
            if monitor:
                await monitor.send(f"{message.author} in {message.channel.mention}: {message.content}")

    @Cog.listener()
    async def on_message_delete(self, message:Message):
        channel = message.guild.get_channel(config['channels']['message-logs']) or message.guild.get_member(config['constants']['owner_id'])
        embed = Embed(title="Message Deleted", description=message.content[:2500], color=randint(0, 0xffffff))
        embed.add_field(name="Sender", value=message.author)
        embed.add_field(name="Channel", value=message.channel.mention)
        if channel:
            await channel.send(embed=embed)
    
    @Cog.listener()
    async def on_bulk_message_delete(self, messages:list):
        channel = messages[0].guild.get_channel(config['channels']['message-logs'])
        embed = Embed(title="Bulk deleted", description=f"Channel {messages[0].channel.name}", color=randint(0, 0xffffff))
        [embed.add_field(name=f"{message.author}:", value=message.content[:300]) for message in messages]
        if channel:
            await channel.send(embed=embed)


    @Cog.listener()
    async def on_message_edit(self, before:Message, after:Message):
        channel = before.guild.get_channel(config['channels']['message-logs']) or before.guild.get_member(config['constants']['owner_id'])
        embed = Embed(title="Message Edited", description=f"Before: {before.content[:1000]}\nAfter: {after.content[:1000]}")
        embed.add_field(name="Editor:", value=before.author)
        embed.add_field(name="Channel:", value=before.channel)
        embed.add_field(name="Jump URL", value=after.jump_url)
        if channel:
            await channel.send(embed=embed)

    @Cog.listener()
    async def on_member_join(self, member:Member):
        welcome = member.guild.get_channel(config['channels']['welcome'])
        join = member.guild.get_channel(config['channels']['join-logs'])

        embed = Embed(title="!!!", description=f"{member.mention} has just joined the server", color=randint(0, 0xffffff))
        embed.add_field(name="Account Creation Date", value=member.created_at.strftime("%d/%m/%y"))
        embed.add_field(name="Joined at", value=ctime())

        family_role = member.guild.get_role(config['roles']['family'])

        if family_role:
            await member.add_roles(family_role)
        else:
            print("No family role was found")

        if join:
            await join.send(embed=embed)
        if welcome:
            await welcome.send(config['welcome_message'].format(member.mention, sum(not user.bot for user in member.guild.members)))
            await welcome.send("https://cdn.discordapp.com/attachments/813888001775370320/831305455237988402/WELCOME_TO_STUDY_GOALS_E-SCHOOL_4.gif")

    @Cog.listener()
    async def on_member_remove(self, member:Member):
        join = member.guild.get_channel(config['channels']['join-logs'])

        embed = Embed(title="'-'", description=f"{member} has just left the server", color=randint(0, 0xffffff))
        if join:
            await join.send(embed=embed)

    @Cog.listener()
    async def on_member_ban(self, member:Member):
        join = member.guild.get_channel(config['channels']['join-logs'])

        embed = Embed(title="BANNED!!!", description=f"{member} with id {member.id} has been banned.")
        if join:
            await join.send(embed=embed)
        
    @Cog.listener()
    async def on_member_update(self, before:Member, after:Member):
        channel = config['channels']['member-logs']
        embed = self.handle_changed(before, after)
        if channel:
            await channel.send(embed=embed)
    
    async def handle_changed(self, before:Member, after:Member) -> Embed:
        """Checks to see what part of the Member was updated, and formats an Embed to suit
        
        Args:
            before (Member): The member before the change
            after (Member): The member after the change
            
        Returns:
            discord.Embed()"""
        
        embed = Embed(title='Member Update', color=randint(0, 0xffffff))
        if before.status != after.status:
            changed = "status"
        elif before.activity != after.activity:
            changed = "activity"
        elif before.nickname != after.nickname:
            changed = "nickname"
        elif before.roles != after.roles:
            changed = "roles"
        elif before.pending != after.pending:
            changed = "pending"

        embed.description = f"{before.name}'s {changed} has been changed"
        embed.add_field(name="Before:", value=getattr(before, changed))
        embed.add_field(name="After:", value=getattr(after, changed))
        return embed

    # Functions
    async def moderate_message(self, message:Message) -> bool:
        """Checks to see if a message contains any profanity
        
        Args:
            message (Message): The message object
        
        Returns: 
            bool
        """

        content = message.content
        if "fuck" in content:
            return True

        return True if [word for word in config['profanity'] if word in content] else False
        

def setup(bot: Bot):
    bot.add_cog(EventHandler(bot))