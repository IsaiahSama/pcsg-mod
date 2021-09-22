from discord import Intents
from discord.ext.commands import Bot
from yaml import safe_load
from os import listdir

with open("settings.yaml") as file:
    settings = safe_load(file)

bot = Bot(prefix=settings['constants']['prefix'], intents=Intents.all())

# Loads extensions
[bot.load_extension(file) for file in listdir() if file.endswith(".py") and file not in settings['non_cogs']]

# Load cogs
bot.run(settings['constants']['key'])