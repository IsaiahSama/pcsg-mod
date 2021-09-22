from discord import Intents
from discord.ext.commands import Bot
from yaml import safe_load

with open("settings.yaml") as file:
    settings = safe_load(file)

bot = Bot(prefix=settings['constants']['prefix'], intents=Intents.all())

# Load cogs
bot.run(settings['constants']['key'])