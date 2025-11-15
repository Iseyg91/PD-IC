import discord
from discord.ext import commands
from keep_alive import keep_alive
from collections import defaultdict, deque
import pymongo
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from discord import ui
import os
import time

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
rappels = db["rappels"]  # collection

def load_guild_settings(guild_id):
    rappels_data = rappels.find_one({"guild_id": guild_id}) or {}
    
    # Débogage : Afficher les données de setup
    print(f"Setup data for guild {guild_id}: {setup_data}")

    combined_data = {
        "rappels": rappels_data
    }

    return combined_data

@bot.event
async def on_ready():
    print(f"{bot.user} est connecté.")
    bot.loop.create_task(start_background_tasks())
    bot.uptime = time.time()
# Supprime toutes les commandes globales
    bot.tree.clear_commands(guild=None)
    await bot.tree.sync()
    print("Toutes les slash commands globales ont été supprimées.")


# === ID du rôle autorisé à utiliser la commande ===
ROLE_AUTORISE_1 = 1439237432552722614  
ROLE_AUTORISE_2 = 1439237555764858900

# === COMMANDE HYBRIDE ===
@bot.hybrid_command(name="ope", description="Choisir 1 ou 2 et recevoir un rappel dans 24h.")
async def choix(ctx, nombre: int):
    # --- Vérification des rôles ---
    allowed1 = discord.utils.get(ctx.author.roles, id=ROLE_AUTORISE_1)
    allowed2 = discord.utils.get(ctx.author.roles, id=ROLE_AUTORISE_2)
    if not (allowed1 or allowed2):
        return await ctx.reply("❌ Vous devez avoir un des rôles autorisés pour utiliser cette commande.", ephemeral=True)

    # On veut uniquement 1 ou 2
    if nombre not in [1, 2]:
        return await ctx.reply("Précise **1** ou **2**.")

    # Création du premier embed
    embed1 = discord.Embed(
        title="Cooldown Ope de {ctx.author.mention}",
        description=f"Tu as utilisé **{nombre}** heal.\nDans 24h tu seras ping",
        color=discord.Color.blurple()
    )
    embed1.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    
        # Ajout d'une image principale
    embed1.set_image(url="https://i.imgur.com/ExempleImage.png")  # change l'URL
    # Ajout d'un thumbnail (petite image)
    embed1.set_thumbnail(url=ctx.author.display_avatar.url)

    # Envoi du premier embed
    await ctx.reply(embed=embed1)

    # === Enregistrement dans MongoDB ===
    rappel_doc = {
        "user_id": ctx.author.id,
        "channel_id": ctx.channel.id,
        "choix": nombre,
        "date_creation": datetime.datetime.utcnow(),
        "rappel_envoye": False
    }

    rappels.insert_one(rappel_doc)

    print(f"[MongoDB] Rappel enregistré pour {ctx.author} (choix {nombre})")

    # === Attente 24h ===
    await asyncio.sleep(86400)  # 24 * 3600

    # === Envoi du second embed ===
    embed2 = discord.Embed(
        title="Tu n'es plus en cooldown",
        description=f"{ctx.author.mention}, voici ton rappel !\n"
                    f"Tu as récupéré tes heals",
        color=discord.Color.green()
    )
    embed2.set_image(url="https://static.wikia.nocookie.net/onepiece/images/0/03/Kroom_Anime.png/revision/latest?cb=20230411080710&path-prefix=fr")  # change l'URL
    embed2.set_thumbnail(url=ctx.author.display_avatar.url)

    await ctx.send(ctx.author.mention, embed=embed2)

    # === Mise à jour MongoDB ===
    rappels.update_one(
        {"user_id": ctx.author.id, "choix": nombre},
        {"$set": {"rappel_envoye": True}}
    )

    print(f"[MongoDB] Rappel marqué comme envoyé pour {ctx.author}")

@bot.hybrid_command(
    name="cooldownope",
    description="Voir les membres avec les rôles autorisés et leur choix + cooldown."
)
async def statut_choix(ctx):
    guild = ctx.guild
    if not guild:
        return await ctx.reply("Cette commande doit être utilisée dans un serveur.")

    # Récupère les membres avec au moins un des deux rôles
    membres = [
        m for m in guild.members
        if any(role.id in [ROLE_AUTORISE_1, ROLE_AUTORISE_2] for role in m.roles)
    ]

    if not membres:
        return await ctx.reply("Aucun membre avec les rôles requis.")

    embed = discord.Embed(
        title="Statut des membres +choix",
        color=discord.Color.orange(),
        timestamp=datetime.datetime.utcnow()
    )

    for member in membres:
        # Cherche le dernier choix de l'utilisateur dans MongoDB
        doc = rappels.find_one(
            {"user_id": member.id},
            sort=[("date_creation", -1)]
        )

        if doc:
            choix = doc.get("choix")
            dernier_rappel = doc.get("date_creation")
            rappel_envoye = doc.get("rappel_envoye", False)
            maintenant = datetime.datetime.utcnow()

            cooldown = (maintenant - dernier_rappel).total_seconds() < 86400 and not rappel_envoye
            cooldown_str = "Oui" if cooldown else "Non"

            # Affiche date du dernier choix
            date_str = dernier_rappel.strftime("%d/%m/%Y %H:%M:%S UTC")

            embed.add_field(
                name=member.display_name,
                value=f"Nombre de heal utilisé : {choix} | Cooldown actif : {cooldown_str} | Date de la dernière utilisation : {date_str}",
                inline=False
            )
        else:
            embed.add_field(
                name=member.display_name,
                value="Aucun choix enregistré",
                inline=False
            )

    await ctx.reply(embed=embed)

# Token pour démarrer le bot (à partir des secrets)
# Lancer le bot avec ton token depuis l'environnement  
keep_alive()
bot.run(token)
