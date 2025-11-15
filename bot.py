import discord
from discord.ext import commands
from keep_alive import keep_alive
from collections import defaultdict, deque
import pymongo
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from discord import ui
import os

token = os.environ['ETHERYA']
intents = discord.Intents.all()
start_time = time.time()
bot = commands.Bot(command_prefix="+", intents=intents, help_command=None)

# Connexion MongoDB
mongo_uri = os.getenv("MONGO_DB")  # URI de connexion à MongoDB
print("Mongo URI :", mongo_uri)  # Cela affichera l'URI de connexion (assure-toi de ne pas laisser cela en prod)
client = MongoClient(mongo_uri)
db = client['Cass-Eco2']

# Collections
collection62 = db['ether_ticket'] 

def load_guild_settings(guild_id):
    ether_ticket_data = collection62.find_one({"guild_id": guild_id}) or {}
    
    # Débogage : Afficher les données de setup
    print(f"Setup data for guild {guild_id}: {setup_data}")

    combined_data = {
        "ether_ticket": ether_ticket_data
    }

    return combined_data

@bot.event
async def on_ready():
    print(f"{bot.user} est connecté.")
    bot.loop.create_task(start_background_tasks())
    bot.uptime = time.time()

    try:
        synced = await bot.tree.sync()
        print(f"Commandes slash synchronisées : {[cmd.name for cmd in synced]}")
    except Exception as e:
        print(f"Erreur de synchronisation : {e}")


@bot.event
async def on_error(event, *args, **kwargs):
    print(f"Erreur : {event}")

@bot.hybrid_command(name="embed", description="Envoie un embed d'exemple.")
async def embed_cmd(ctx):
    embed = discord.Embed(
        title="✨ Exemple d'Embed",
        description="Ceci est un embed envoyé par une **commande hybride**.",
        color=discord.Color.blurple()
    )

    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
    embed.add_field(name="Fonctionne en :", value="Slash + Préfixe", inline=False)
    embed.set_footer(text="Exemple d'embed")

    await ctx.reply(embed=embed)

# Token pour démarrer le bot (à partir des secrets)
# Lancer le bot avec ton token depuis l'environnement  
keep_alive()
bot.run(token)
