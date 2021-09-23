from discord.ext.commands import Cog, command, Bot
from discord.message import Message
from main import settings

class EventHandler(Cog):
    def __init__(self, bot):
        self.bot = bot 

    # Event Handlers
    @Cog.listener()
    async def on_message(self, message:Message):
        if await self.moderate_message(message):
            await message.channel.send(f"{message.author.mention} watch your language!")
            await message.delete()

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

        return True if [word for word in settings['profanity'] if word in content] else False
        

def setup(bot: Bot):
    bot.add_cog(EventHandler(bot))