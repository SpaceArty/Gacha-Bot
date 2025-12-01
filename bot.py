import discord; from discord.ext import commands
import os; import traceback
from utils import config

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

async def load_cogs():
    plugins_dir = "plugins"
    if not os.path.exists(plugins_dir):
        print(f"Le répertoire {plugins_dir} n'existe pas!")
        return

    for filename in os.listdir(plugins_dir):
        if filename.endswith(".py") and filename not in {""}: # Exclut rien pour l'instant
            extension = f"plugins.{filename[:-3]}" # Retire le .py du nom du fichier
            try:
                await bot.load_extension(extension)
                print(f"Cog {filename} chargé avec succès !") # Affiche un message de succès
            except Exception as e:
                print(f"Erreur lors du chargement du cog {filename}: {e}")
                traceback.print_exc() # Affiche le traceback pour mieux comprendre l'erreur

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    await load_cogs() # Charger les cogs après que le bot soit connecté

bot.run(config.BOT_TOKEN)