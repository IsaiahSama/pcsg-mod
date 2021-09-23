from discord.ext.commands import Cog, Bot
from discord import Embed
from discord.message import Message
from config import config
from random import randint

class EventHandler(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot 

    # Event Handlers
    @Cog.listener()
    async def on_message(self, message:Message):
        if await self.moderate_message(message):
            await message.channel.send(f"{message.author.mention} watch your language!")
            await message.delete()

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