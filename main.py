from discord import Intents
from discord.ext.commands import Bot
from config import config
from os import listdir

bot = Bot(command_prefix=config['constants']['prefix'], intents=Intents.all())

# Loads extensions
[bot.load_extension(file.strip(".py")) for file in listdir() if file.endswith(".py") and file not in config['non_cogs']]

# Load cogs
bot.run(config['constants']['key'])