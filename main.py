from discord import Intents
from discord.ext.commands import Bot
from discord_slash import SlashCommand
from config import config
from os import listdir

bot = Bot(command_prefix=config['constants']['prefix'], intents=Intents.all(), case_insensitive=True)
slash = SlashCommand(bot, sync_commands=False, sync_on_cog_reload=True)

# Loads extensions
[bot.load_extension(file.strip(".py")) for file in listdir() if file.endswith(".py") and file not in config['non_cogs']]

# Load cogs
bot.run(config['constants']['key'])