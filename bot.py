import discord
from discord.ext import commands, tasks
from discord import app_commands, Embed
from discord.ui import Button, View, Select, Modal, TextInput
from discord.utils import get
from functools import wraps
import os
import random
import asyncio
import time
import re
import subprocess
import sys
import math
import traceback
from keep_alive import keep_alive
from datetime import datetime, timedelta
from collections import defaultdict, deque
import pymongo
from pymongo import MongoClient
import psutil
import platform
from motor.motor_asyncio import AsyncIOMotorClient

token = os.environ['ETHERYA']
intents = discord.Intents.all()
start_time = time.time()
client = discord.Client(intents=intents)

#Configuration du Bot:
PROJECT_DELTA = 1359963854200639498
STAFF_PROJECT = 1359963854422933876
LOG_CHANNEL_ID = 1360864790540582942
LOG_CHANNEL_RETIRE_ID = 1360864806957092934
ISEY_ID = 792755123587645461
partnership_channel_id = 1355158081855688745
ROLE_ID = 1355157749994098860
ETHERYA_SERVER_ID = 1034007767050104892
WELCOME_CHANNEL_ID = 1355198748296351854
AUTORIZED_SERVER_ID = 1034007767050104892
BOUNTY_CHANNEL_ID = 1355298449829920950
SUGGESTION_CHANNEL_ID = 1355191928467230792
SUGGESTION_ROLE= 1355157752950821046
SONDAGE_CHANNEL_ID = 1355157860438376479
SONDAGE_ID = 1355157752950821046
ECO_ROLES_VIP = [1359963854402228315, 1361307897287675989]
SALON_REPORT_ID = 1361362788672344290
ROLE_REPORT_ID = 1361306900981092548

# Connexion MongoDB
mongo_uri = os.getenv("MONGO_DB")  # URI de connexion à MongoDB
print("Mongo URI :", mongo_uri)  # Cela affichera l'URI de connexion (assure-toi de ne pas laisser cela en prod)
client = MongoClient(mongo_uri)
db = client['Cass-Eco2']

# Collections
collection = db['setup']  # Configuration générale
collection2 = db['setup_premium']  # Serveurs premium
collection3 = db['bounty']  # Primes et récompenses des joueurs
collection4 = db['protection'] #Serveur sous secu ameliorer
collection5 = db ['clients'] #Stock Clients
collection6 = db ['partner'] #Stock Partner
collection7= db ['sanction'] #Stock Sanction
collection8 = db['idees'] #Stock Idées
collection9 = db['stats'] #Stock Salon Stats
collection10 = db['eco'] #Stock Les infos Eco
collection11 = db['eco_daily'] #Stock le temps de daily
collection12 = db['rank'] #Stock les Niveau
collection13 = db['eco_work'] #Stock le temps de Work
collection14 = db['eco_slut'] #Stock le temps de Slut
collection15 = db['eco_crime'] #Stock le temps de Crime

# Exemple de structure de la base de données pour la collection bounty
# {
#   "guild_id": str,  # ID du serveur
#   "user_id": str,   # ID du joueur
#   "prize": int,     # Prime actuelle
#   "reward": int     # Récompenses accumulées
# }

# Fonction pour ajouter un serveur premium
def add_premium_server(guild_id: int, guild_name: str):
    collection2.update_one(
        {"guild_id": guild_id},
        {"$set": {"guild_name": guild_name}},
        upsert=True
    )

# Fonction pour ajouter ou mettre à jour une prime
def set_bounty(guild_id: int, user_id: int, prize: int):
    # Vérifie si le joueur a déjà une prime
    bounty_data = collection3.find_one({"guild_id": guild_id, "user_id": user_id})
    
    if bounty_data:
        # Si une prime existe déjà, on met à jour la prime et les récompenses
        collection3.update_one(
            {"guild_id": guild_id, "user_id": user_id},
            {"$set": {"prize": prize}},
        )
    else:
        # Sinon, on crée un nouveau document pour ce joueur
        collection3.insert_one({
            "guild_id": guild_id,
            "user_id": user_id,
            "prize": prize,
            "reward": 0  # Initialisation des récompenses à 0
        })

# Fonction pour récupérer les données d'un utilisateur
def get_user_eco(guild_id, user_id):
    user_data = collection10.find_one({"guild_id": guild_id, "user_id": user_id})
    if not user_data:
        # Si l'utilisateur n'a pas encore de données, on les crée
        collection10.insert_one({
            "guild_id": guild_id,
            "user_id": user_id,
            "coins": 0,
            "last_daily": None
        })
        return {"coins": 0, "last_daily": None}
    return user_data

# Fonction pour modifier les paramètres de protection
def update_protection(guild_id, protection_key, new_value):
    collection4.update_one(
        {"guild_id": guild_id},
        {"$set": {protection_key: new_value}},
        upsert=True
    )

def add_sanction(guild_id, user_id, action, reason, duration=None):
    sanction_data = {
        "guild_id": guild_id,
        "user_id": user_id,
        "action": action,
        "reason": reason,
        "duration": duration,
        "timestamp": datetime.datetime.utcnow()
    }

    # Insertion ou mise à jour de la sanction dans la base de données
    collection7.insert_one(sanction_data)

# Fonction pour récupérer le nombre de partenariats et le rank d'un utilisateur
def get_user_partner_info(user_id: str):
    partner_data = collection6.find_one({"user_id": user_id})
    if partner_data:
        return partner_data['rank'], partner_data['partnerships']
    return None, None

def get_premium_servers():
    """Récupère les IDs des serveurs premium depuis la base de données."""
    premium_docs = collection2.find({}, {"_id": 0, "guild_id": 1})
    return {doc["guild_id"] for doc in premium_docs}

async def get_protection_data(guild_id):
    data = await protection_col.find_one({"_id": str(guild_id)})
    return data

def load_guild_settings(guild_id):
    # Charger les données de la collection principale
    setup_data = collection.find_one({"guild_id": guild_id}) or {}
    setup_premium_data = collection2.find_one({"guild_id": guild_id}) or {}
    bounty_data = collection3.find_one({"guild_id": guild_id}) or {}
    protection_data = collection4.find_one({"guild_id": guild_id}) or {}
    clients_data = collection5.find_one({"guild_id": guild_id}) or {}
    partner_data = collection6.find_one({"guild_id": guild_id}) or {}
    sanction_data = collection7.find_one({"guild_id": guild_id}) or {}
    idees_data = collection8.find_one({"guild_id": guild_id}) or {}
    stats_data = collection9.find_one({"guild_id": guild_id}) or {}
    eco_data = collection10.find_one({"guild_id": guild_id}) or {}
    eco_daily_data = collection11.find_one({"guild_id": guild_id}) or {}
    rank_data = collection12.find_one({"guild_id": guild_id}) or {}
    eco_work_data = collection13.find_one({"guild_id": guild_id}) or {}
    eco_slut_data = collection14.find_one({"guild_id": guild_id}) or {}
    eco_crime_data = collection15.find_one({"guild_id": guild_id}) or {}

    # Débogage : Afficher les données de setup
    print(f"Setup data for guild {guild_id}: {setup_data}")

    combined_data = {
        "setup": setup_data,
        "setup_premium": setup_premium_data,
        "bounty": bounty_data,
        "protection": protection_data,
        "clients": clients_data,
        "partner": partner_data,
        "sanction": sanction_data,
        "idees": idees_data,
        "stats": stats_data,
        "eco": eco_data,
        "eco_daily": eco_daily_data,
        "rank": rank_data,
        "eco_work": eco_work_data,
        "eco_slut": eco_slut_data,
        "eco_crime": eco_slut_data
    }

    return combined_data

# Fonction pour récupérer le préfixe depuis la base de données
async def get_prefix(bot, message):
    guild_data = collection.find_one({"guild_id": str(message.guild.id)})  # Récupère les données de la guilde
    return guild_data['prefix'] if guild_data and 'prefix' in guild_data else '+'

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

# Dictionnaire pour stocker les paramètres de chaque serveur
GUILD_SETTINGS = {}

# Tâche de fond pour mettre à jour les stats toutes les 5 secondes
@tasks.loop(seconds=5)
async def update_stats():
    all_stats = collection9.find()

    for data in all_stats:
        guild_id = int(data["guild_id"])
        guild = bot.get_guild(guild_id)
        if not guild:
            continue

        role = guild.get_role(data.get("role_id"))
        member_channel = guild.get_channel(data.get("member_channel_id"))
        role_channel = guild.get_channel(data.get("role_channel_id"))
        bots_channel = guild.get_channel(data.get("bots_channel_id"))

        total_members = guild.member_count
        role_members = len([m for m in guild.members if role in m.roles and not m.bot]) if role else 0
        total_bots = len([m for m in guild.members if m.bot])

        try:
            if member_channel:
                await member_channel.edit(name=f"👥 Membres : {total_members}")
            if role_channel:
                await role_channel.edit(name=f"🎯 {role.name if role else 'Rôle'} : {role_members}")
            if bots_channel:
                await bots_channel.edit(name=f"🤖 Bots : {total_bots}")
        except discord.Forbidden:
            print(f"⛔ Permissions insuffisantes pour modifier les salons dans {guild.name}")
        except Exception as e:
            print(f"⚠️ Erreur lors de la mise à jour des stats : {e}")

# Tâche de fond pour donner des coins toutes les minutes en vocal
@tasks.loop(minutes=1)
async def reward_voice():
    for guild in bot.guilds:
        if guild.id == 1359963854200639498:
            for member in guild.members:
                if member.voice:
                    coins_to_add = random.randint(25, 75)
                    add_coins(guild.id, str(member.id), coins_to_add)

# Tâche de fond pour mettre à jour les XP en vocal toutes les 60 secondes
@tasks.loop(seconds=60)
async def update_voice_xp():
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            for member in vc.members:
                if member.bot:
                    continue

                base_xp = xp_rate["voice"]
                if member.voice.self_video:
                    base_xp = xp_rate["camera"]
                elif member.voice.self_stream:
                    base_xp = xp_rate["stream"]

                update_user_xp(str(guild.id), str(member.id), base_xp)

# Événement quand le bot est prêt
@bot.event
async def on_ready():
    print(f"✅ Le bot {bot.user} est maintenant connecté ! (ID: {bot.user.id})")

    bot.uptime = time.time()

    # Démarrer les tâches de fond
    update_stats.start()
    reward_voice.start()
    update_voice_xp.start()

    guild_count = len(bot.guilds)
    member_count = sum(guild.member_count for guild in bot.guilds)

    print(f"\n📊 **Statistiques du bot :**")
    print(f"➡️ **Serveurs** : {guild_count}")
    print(f"➡️ **Utilisateurs** : {member_count}")

    activity_types = [
        discord.Activity(type=discord.ActivityType.watching, name=f"{member_count} Membres"),
        discord.Activity(type=discord.ActivityType.streaming, name=f"{guild_count} Serveurs"),
        discord.Activity(type=discord.ActivityType.streaming, name="Project : Delta"),
    ]

    status_types = [discord.Status.online, discord.Status.idle, discord.Status.dnd]

    await bot.change_presence(
        activity=random.choice(activity_types),
        status=random.choice(status_types)
    )

    print(f"\n🎉 **{bot.user}** est maintenant connecté et affiche ses statistiques dynamiques avec succès !")
    print("📌 Commandes disponibles 😊")
    for command in bot.commands:
        print(f"- {command.name}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Commandes slash synchronisées : {[cmd.name for cmd in synced]}")
    except Exception as e:
        print(f"❌ Erreur de synchronisation des commandes slash : {e}")

    while True:
        for activity in activity_types:
            for status in status_types:
                await bot.change_presence(activity=activity, status=status)
                await asyncio.sleep(10)

        for guild in bot.guilds:
            GUILD_SETTINGS[guild.id] = load_guild_settings(guild.id)

# Gestion des erreurs globales pour toutes les commandes
@bot.event
async def on_error(event, *args, **kwargs):
    print(f"Une erreur s'est produite : {event}")
    embed = discord.Embed(
        title="❗ Erreur inattendue",
        description="Une erreur s'est produite lors de l'exécution de la commande. Veuillez réessayer plus tard.",
        color=discord.Color.red()
    )
    await args[0].response.send_message(embed=embed)
#------------------------------------------------------------------------- Commande Mention ainsi que Commandes d'Administration : Detections de Mots sensible et Mention

# Liste des mots sensibles
sensitive_words = [
    # Insultes graves
    "fils de pute", "enfoiré", "connard", "salopard", "bâtard", "déchet", "branleur", "crasseux", "charognard",
    
    # Discours haineux / discriminations
    "nigger", "nigga", "chintok", "bougnoule", "pédé", "negro", "race inférieure", 
    "sale arabe", "sale noir", "sale juif", "sale blanc", "retardé","enculé",
    
    # Termes liés à des idéologies haineuses
    "raciste", "homophobe", "xénophobe", "transphobe", "antisémite", "islamophobe", "suprémaciste", 
    "fasciste", "nazi", "néonazi", "dictateur", "extrémiste",
    
    # Violences et crimes graves
    "viol", "pédophilie", "inceste", "pédocriminel", "agression", "assassin", "meurtre", "génocide", 
    "extermination", "décapitation", "lynchage", "massacre", "torture", "suicidaire", "prise d'otage", 
    "terrorisme", "attentat", "bombardement", "exécution", "immolation", "traite humaine", "esclavage sexuel", 
    "viol collectif", "kidnapping",
    
    # Drogues & substances
    "cocaïne", "héroïne", "crack", "LSD", "ecstasy", "GHB", "fentanyl", "méthamphétamine", 
    "cannabis", "opium", "drogue", "drogue de synthèse", "trafic de drogue", "toxicomanie", "overdose",
    
    # Contenus sexuels explicites
    "pornographie", "porno", "prostitution", "masturbation", "fellation", "sexe", "sodomie", 
    "exhibition", "fétichisme", "orgie", "gode", "pénétration", "nu",
    
    # Fraudes & crimes financiers
    "scam", "fraude", "chantage", "extorsion", "évasion fiscale", "fraude fiscale", "détournement de fonds",
    
    # Groupes & activités criminelles
    "mafia", "cartel", "crime organisé", "milice", "mercenaire", "guérilla", "terroriste", "insurrection", 
    "émeute", "coup d'état", "anarchie", "séparatiste",
    
    # Propagande et manipulation
    "endoctrinement", "secte", "lavage de cerveau", "désinformation", "propagande", "fake news", "manipulation",
]

user_messages = {}
cooldowns = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 💬 1. Vérifie les mots sensibles
    for word in sensitive_words:
        if re.search(rf"\b{re.escape(word)}\b", message.content, re.IGNORECASE):
            print(f"🚨 Mot sensible détecté dans le message de {message.author}: {word}")
            asyncio.create_task(send_alert_to_admin(message, word))
            break

    # 📣 2. Répond si le bot est mentionné
    if bot.user.mentioned_in(message) and message.content.strip().startswith(f"<@{bot.user.id}>"):
        embed = discord.Embed(
            title="👋 Besoin d’aide ?",
            description=(f"Salut {message.author.mention} ! Moi, c’est **{bot.user.name}**, ton assistant sur ce serveur. 🤖\n\n"
                         "🔹 **Pour voir toutes mes commandes :** Appuie sur le bouton ci-dessous ou tape `+help`\n"
                         "🔹 **Une question ? Un souci ?** Contacte le staff !\n\n"
                         "✨ **Profite bien du serveur et amuse-toi !**"),
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=bot.user.avatar.url)
        embed.set_footer(text="Réponse automatique • Disponible 24/7", icon_url=bot.user.avatar.url)

        view = View()
        button = Button(label="📜 Voir les commandes", style=discord.ButtonStyle.primary, custom_id="help_button")

        async def button_callback(interaction: discord.Interaction):
            ctx = await bot.get_context(interaction.message)
            await ctx.invoke(bot.get_command("help"))
            await interaction.response.send_message("Voici la liste des commandes !", ephemeral=True)

        button.callback = button_callback
        view.add_item(button)

        await message.channel.send(embed=embed, view=view)
        return

    # 📦 3. Gestion des partenariats dans un salon spécifique
    if message.channel.id == partnership_channel_id:
        user_id = str(message.author.id)
        rank, partnerships = get_user_partner_info(user_id)

        await message.channel.send("<@&1355157749994098860>")

        embed = discord.Embed(
            title="Merci du partenariat 🤝",
            description=f"{message.author.mention}\nTu es rank **{rank}**\nTu as effectué **{partnerships}** partenariats.",
            color=discord.Color.green()
        )

        embed.set_footer(
            text="Partenariat réalisé",
            icon_url="https://github.com/Iseyg91/KNSKS-ET/blob/main/Images_GITHUB/Capture_decran_2024-09-28_211041.png?raw=true"
        )
        embed.set_image(
            url="https://github.com/Iseyg91/KNSKS-ET/blob/main/Images_GITHUB/Capture_decran_2025-02-15_231405.png?raw=true"
        )

        await message.channel.send(embed=embed)

    # ⚙️ 4. Configuration du serveur pour sécurité
    guild_data = collection.find_one({"guild_id": str(message.guild.id)})
    if not guild_data:
        await bot.process_commands(message)
        return

    # 🔗 5. Anti-lien
    if guild_data.get("anti_link", False):
        if "discord.gg" in message.content and not message.author.guild_permissions.administrator:
            await message.delete()
            await message.author.send("⚠️ Les liens Discord sont interdits sur ce serveur.")
            return

    # 💣 6. Anti-spam
    if guild_data.get("anti_spam_limit", False):
        now = time.time()
        user_id = message.author.id

        if user_id not in user_messages:
            user_messages[user_id] = []
        user_messages[user_id].append(now)

        recent_messages = [t for t in user_messages[user_id] if t > now - 5]
        user_messages[user_id] = recent_messages

        if len(recent_messages) > 10:
            await message.guild.ban(message.author, reason="Spam excessif")
            return

        spam_messages = [t for t in user_messages[user_id] if t > now - 60]
        if len(spam_messages) > guild_data["anti_spam_limit"]:
            await message.delete()
            await message.author.send("⚠️ Vous envoyez trop de messages trop rapidement. Réduisez votre spam.")
            return

    # 📣 7. Anti-everyone
    if guild_data.get("anti_everyone", False):
        if "@everyone" in message.content or "@here" in message.content:
            await message.delete()
            await message.author.send("⚠️ L'utilisation de `@everyone` ou `@here` est interdite sur ce serveur.")
            return

    # 🎉 8. Ajouter des Coins pour chaque message
    if message.guild.id == 1359963854200639498:
        if message.author.bot:
            return
        coins_to_add = random.randint(3, 5)
        add_coins(message.guild.id, str(message.author.id), coins_to_add)

    # 🔄 9. Cooldown et mise à jour des XP
    user_id = str(message.author.id)
    guild_id = str(message.guild.id)
    now = datetime.utcnow()

    # Cooldown de 60s
    if user_id not in cooldowns or now > cooldowns[user_id]:
        update_user_xp(guild_id, user_id, xp_rate["message"])
        cooldowns[user_id] = now + timedelta(seconds=60)

    # ✅ 10. Exécution normale des commandes
    await bot.process_commands(message)

# 🔔 Fonction d'envoi d'alerte dans le salon spécifique
async def send_alert_to_admin(message, detected_word):
    try:
        # Essayer d'abord de récupérer le salon dans le serveur où le message a été envoyé
        channel = message.guild.get_channel(1361329246236053586)
        
        if not channel:
            # Si le salon n'existe pas dans ce serveur, on va chercher dans un autre serveur
            guild = bot.get_guild(1359963854200639498)  # Remplace SERVER_ID par l'ID du serveur où tu veux envoyer l'alerte
            channel = guild.get_channel(1361329246236053586)
        
        if channel:
            # Mentionner le rôle avant l'embed
            role_mention = "<@&1361306900981092548>"  # Mentionne le rôle

            # Envoyer un message avant l'embed
            await channel.send(f"{role_mention} 🚨 Un mot sensible a été détecté ! Veuillez vérifier immédiatement.")

            # Créer l'embed
            embed = discord.Embed(
                title="🚨 Alerte : Mot sensible détecté !",
                description=f"Un message contenant un mot interdit a été détecté sur le serveur **{message.guild.name}**.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="📍 Salon", value=f"{message.channel.mention}", inline=True)
            embed.add_field(name="👤 Auteur", value=f"{message.author.mention} (`{message.author.id}`)", inline=True)
            embed.add_field(name="💬 Message", value=f"```{message.content}```", inline=False)
            embed.add_field(name="⚠️ Mot détecté", value=f"`{detected_word}`", inline=True)
            if message.guild:
                embed.add_field(name="🔗 Lien vers le message", value=f"[Clique ici]({message.jump_url})", inline=False)
            embed.set_footer(text="Système de détection automatique", icon_url=bot.user.avatar.url)

            # Envoyer l'embed après le message
            await channel.send(embed=embed)
        else:
            print("⚠️ Le salon spécifié n'a pas pu être trouvé dans le serveur.")
    except Exception as e:
        print(f"⚠️ Erreur lors de l'envoi de l'alerte : {e}")
#-------------------------------------------------------------------------- Bot Join:
@bot.event
async def on_guild_join(guild):
    channel_id = 1361304582424232037  # ID du salon cible
    channel = bot.get_channel(channel_id)

    if channel is None:
        # Si le bot ne trouve pas le salon (peut-être parce qu’il n’est pas dans le cache)
        channel = await bot.fetch_channel(channel_id)

    total_guilds = len(bot.guilds)
    total_users = sum(g.member_count for g in bot.guilds)

    isey_embed = discord.Embed(
        title="✨ Nouveau serveur rejoint !",
        description=f"Le bot a été ajouté sur un nouveau serveur.",
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )
    isey_embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    isey_embed.add_field(name="📛 Nom", value=guild.name, inline=True)
    isey_embed.add_field(name="🆔 ID", value=guild.id, inline=True)
    isey_embed.add_field(name="👥 Membres", value=str(guild.member_count), inline=True)
    isey_embed.add_field(name="👑 Propriétaire", value=str(guild.owner), inline=True)
    isey_embed.add_field(name="🌍 Région", value=guild.preferred_locale, inline=True)
    isey_embed.add_field(name="🔢 Total serveurs", value=str(total_guilds), inline=True)
    isey_embed.add_field(name="🌐 Utilisateurs totaux (estimation)", value=str(total_users), inline=True)
    isey_embed.set_footer(text="Ajouté le")

    await channel.send(embed=isey_embed)

    # --- Embed public pour le salon du serveur ---
    text_channels = [channel for channel in guild.text_channels if channel.permissions_for(guild.me).send_messages]
    
    if text_channels:
        top_channel = sorted(text_channels, key=lambda x: x.position)[0]

        public_embed = discord.Embed(
            title="🎉 **Bienvenue sur le serveur !** 🎉",
            description="Salut à tous ! Je suis **EtheryaBot**, votre assistant virtuel ici pour rendre votre expérience sur ce serveur **inoubliable** et pleine d'interactions ! 😎🚀",
            color=discord.Color.blurple()
        )

        public_embed.set_thumbnail(url="https://github.com/Iseyg91/KNSKS-Q/blob/main/3e3bd3c24e33325c7088f43c1ae0fadc.png?raw=true")
        public_embed.set_image(url="https://github.com/Iseyg91/KNSKS-Q/blob/main/BANNER_ETHERYA-topaz.png?raw=true")
        public_embed.set_footer(text=f"Bot rejoint le serveur {guild.name}!", icon_url="https://github.com/Iseyg91/KNSKS-Q/blob/main/3e3bd3c24e33325c7088f43c1ae0fadc.png?raw=true")

        public_embed.add_field(name="🔧 **Que puis-je faire pour vous ?**", value="Je propose des **commandes pratiques** pour gérer les serveurs, détecter les mots sensibles, et bien plus encore ! 👾🎮", inline=False)
        public_embed.add_field(name="💡 **Commandes principales**", value="📜 Voici les commandes essentielles pour bien commencer :\n`+help` - Afficher toutes les commandes disponibles\n`+vc` - Voir les statistiques du serveur\n`+setup` - Configurer le bot selon vos besoins", inline=False)
        public_embed.add_field(name="🚀 **Prêt à commencer ?**", value="Tapez `+aide` pour voir toutes les commandes disponibles ou dites-moi ce que vous souhaitez faire. Si vous avez des questions, je suis là pour vous aider ! 🎉", inline=False)
        public_embed.add_field(name="🌐 **Serveurs utiles**", value="**[Serveur de Support](https://discord.com/invite/PzTHvVKDxN)**\n**[Serveur Etherya](https://discord.com/invite/tVVYC2Ynfy)**", inline=False)

        await top_channel.send(embed=public_embed)

@bot.event
async def on_guild_remove(guild):
    channel_id = 1361306217460531225  # ID du salon cible
    channel = bot.get_channel(channel_id)

    if channel is None:
        channel = await bot.fetch_channel(channel_id)

    # Total après le départ
    total_guilds = len(bot.guilds)
    total_users = sum(g.member_count for g in bot.guilds if g.member_count)

    embed = discord.Embed(
        title="💔 Serveur quitté",
        description="Le bot a été retiré d’un serveur.",
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.add_field(name="📛 Nom", value=guild.name, inline=True)
    embed.add_field(name="🆔 ID", value=guild.id, inline=True)
    embed.add_field(name="👥 Membres lors du départ", value=str(guild.member_count), inline=True)
    embed.add_field(name="👑 Propriétaire", value=str(guild.owner), inline=True)
    embed.add_field(name="🌍 Région", value=guild.preferred_locale, inline=True)

    # Infos globales
    embed.add_field(name="🔢 Total serveurs restants", value=str(total_guilds), inline=True)
    embed.add_field(name="🌐 Utilisateurs totaux (estimation)", value=str(total_users), inline=True)

    embed.set_footer(text="Retiré le")

    await channel.send(embed=embed)

#--------------------------------------------------------------------------- Eco:
def has_eco_vip_role():
    async def predicate(ctx):
        if any(role.id in ECO_ROLES_VIP for role in ctx.author.roles):
            return True
        else:
            await ctx.send("⛔ Vous n'avez pas les permissions nécessaires pour utiliser cette commande.")
            return False
    return commands.check(predicate)

def check_guild():
    def decorator(func):
        @wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            if ctx.guild is None or ctx.guild.id != PROJECT_DELTA:
                await ctx.send("❌ **Les commandes économiques ne sont pas autorisées sur ce serveur.**")
                return
            return await func(ctx, *args, **kwargs)
        return wrapper
    return decorator

# Fonction pour ajouter des coins à un utilisateur
def add_coins(guild_id, user_id, amount):
    collection10.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"$inc": {"coins": amount}},  # Ajout uniquement aux coins
        upsert=True
    )

# Commande pour afficher le solde de coins d'un utilisateur
@bot.hybrid_command(name="balance", description="Affiche ton solde de Coins.", aliases=['bal'])
@check_guild()
async def balance(ctx, member: discord.Member = None):
    if ctx.guild.id != 1359963854200639498:
        return

    member = member or ctx.author
    user_id = str(member.id)
    guild_id = str(ctx.guild.id)

    user_data = get_user_eco(guild_id, user_id)
    coins = user_data.get("coins", 0)

    embed = discord.Embed(
        title=f"💼 Portefeuille de {member.display_name}",
        color=discord.Color.blue(),
        description="Voici ton solde actuel :"
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="💰 Coins", value=f"`{coins}` <:ecoEther:1341862366249357374>", inline=True)
    embed.set_footer(text="Économie de Project : Delta")

    await ctx.send(embed=embed)

# Commande pour afficher le classement des utilisateurs par nombre de coins
@bot.hybrid_command(name="leaderboard", aliases=["lb"], description="Affiche le classement des plus riches.")
@check_guild()
async def leaderboard(ctx, tri: str = None):
    if ctx.guild.id != 1359963854200639498:
        return

    guild_id = str(ctx.guild.id)
    users = list(collection10.find({"guild_id": guild_id}))

    # Tri des utilisateurs par nombre de coins décroissant
    users.sort(key=lambda u: u.get("coins", 0), reverse=True)

    title = "🏆 Classement par Coins"
    description = ""
    for i, u in enumerate(users[:10]):
        member = ctx.guild.get_member(int(u["user_id"]))
        name = member.display_name if member else f"Utilisateur inconnu ({u['user_id']})"
        value = u.get("coins", 0)
        formatted = f"{value:,}".replace(",", " ")  # Séparation des milliers avec un espace insécable
        description += f"**{i+1}. {name}** • <:ecoEther:1341862366249357374> {formatted}\n"

    embed = discord.Embed(
        title=title,
        description=description or "Aucun utilisateur n’a encore de coins.",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

@bot.hybrid_command(name="pay", description="Permet de transférer une certaine somme de Coins à un autre utilisateur.")
@check_guild()
async def pay(ctx, member: discord.Member, amount: int = None):
    if ctx.guild.id != 1359963854200639498:
        return

    if amount is None or amount <= 0:
        return await ctx.send("❌ **Montant invalide.** Utilise une somme positive pour effectuer un paiement.")

    if member == ctx.author:
        return await ctx.send("⚠️ Tu ne peux pas te payer toi-même.")

    user_id, member_id, guild_id = str(ctx.author.id), str(member.id), str(ctx.guild.id)
    user_data = collection10.find_one({"guild_id": guild_id, "user_id": user_id}) or {"coins": 0}

    if user_data["coins"] < amount:
        return await ctx.send("💸 Tu n'as pas assez de **coins** pour effectuer ce paiement.")

    collection10.update_one({"guild_id": guild_id, "user_id": user_id}, {"$inc": {"coins": -amount}}, upsert=True)
    collection10.update_one({"guild_id": guild_id, "user_id": member_id}, {"$inc": {"coins": amount}}, upsert=True)

    embed = discord.Embed(
        title="💸 Paiement envoyé !",
        description=f"Tu as envoyé **{amount} <:ecoEther:1341862366249357374>** à {member.mention}.",
        color=discord.Color.green()
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    embed.set_footer(text="Transaction réussie.")
    await ctx.send(embed=embed)

@pay.error
async def pay_all_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        user_data = collection10.find_one({"guild_id": guild_id, "user_id": user_id}) or {"cash": 0}

        total_cash = user_data.get("cash", 0)
        if total_cash <= 0:
            await ctx.send("❌ Tu n'as pas assez de **<:ecoEther:1341862366249357374>** en cash pour payer.")
            return
        
        await pay(ctx, ctx.author, total_cash)

@bot.hybrid_command(name="daily", description="Réclamez votre récompense quotidienne de Coins. Disponible tous les 24h.", aliases=['dy'])
@check_guild()
@commands.cooldown(1, 5, commands.BucketType.user)
async def daily(ctx):
    user_id, guild_id = str(ctx.author.id), str(ctx.guild.id)
    now, cooldown = datetime.utcnow(), timedelta(hours=24)

    last_daily = collection11.find_one({"guild_id": guild_id, "user_id": user_id})
    if last_daily and (now - datetime.fromisoformat(last_daily.get("last_daily", "")) < cooldown):
        remaining = cooldown - (now - datetime.fromisoformat(last_daily["last_daily"]))
        h, rem = divmod(remaining.total_seconds(), 3600)
        m, s = divmod(rem, 60)
        return await ctx.send(
            f"⏳ Tu as déjà réclamé ton daily.\nReviens dans **{int(h)}h {int(m)}m {int(s)}s**."
        )

    reward = random.randint(250, 350)

    collection10.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"$inc": {"coins": reward}},
        upsert=True
    )
    collection11.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"$set": {"last_daily": now.isoformat()}},
        upsert=True
    )

    await ctx.send(
        embed=discord.Embed(
            title="🎁 Récompense quotidienne",
            description=f"Tu as reçu **{reward} <:ecoEther:1341862366249357374>** !",
            color=discord.Color.blurple()
        ).set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    )

# Liste des messages à renvoyer
messages = [
    "Tu négocies une augmentation avec succès. 💹 <:ecoEther:1341862366249357374> {coins}",
    "Tu as travaillé dur et ça a payé ! 💼 <:ecoEther:1341862366249357374> {coins}",
    "Le boss est satisfait de tes efforts, tu gagnes une prime ! 💸 <:ecoEther:1341862366249357374> {coins}",
    "Tu as bien géré tes tâches, voilà ta récompense ! 🏆 <:ecoEther:1341862366249357374> {coins}",
    "Une journée bien remplie, et voilà ta compensation ! 💪 <:ecoEther:1341862366249357374> {coins}",
    "Tu fais une présentation brillante et ça se reflète dans ton salaire. 📊 <:ecoEther:1341862366249357374> {coins}",
    "Le patron t'a bien vu en action, récompensé pour ta productivité ! ⚡ <:ecoEther:1341862366249357374> {coins}",
    "Tes efforts sont remarqués et ta récompense suit ! 👔 <:ecoEther:1341862366249357374> {coins}",
    "Tu as pris une initiative, et ça n'est pas passé inaperçu ! 🎯 <:ecoEther:1341862366249357374> {coins}",
    "Tu as géré la situation avec brio, et la récompense suit ! 🔥 <:ecoEther:1341862366249357374> {coins}"
]

@bot.hybrid_command(name="work", description="Gagnez des coins en travaillant. Vous pouvez le faire toutes les 6 heures.", aliases=['wk'])
@check_guild()
@has_eco_vip_role()
async def work(ctx):
    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)
    
    # Récupère les données de travail de l'utilisateur pour vérifier le cooldown
    eco_work_data = collection13.find_one({"guild_id": guild_id, "user_id": user_id})

    # Vérifie le cooldown
    if eco_work_data and eco_work_data.get('last_work'):
        last_work_time = eco_work_data['last_work']
        cooldown_time = timedelta(hours=6)
        if datetime.utcnow() - last_work_time < cooldown_time:
            time_left = cooldown_time - (datetime.utcnow() - last_work_time)

            # Formate l'heure restante en heures et minutes (sans les secondes)
            time_left_str = str(time_left).split(".")[0]  # Enlève les millisecondes
            
            embed = Embed(
                title="Cooldown Travail",
                description=f"Tu dois attendre encore {time_left_str} avant de pouvoir travailler à nouveau.",
                color=0xFF0000  # Rouge pour indiquer l'attente
            )
            await ctx.send(embed=embed)
            return

    # Génère le nombre de coins entre 1 et 150
    coins = random.randint(1, 150)

    # Choisis un message aléatoire parmi les 10 phrases
    message = random.choice(messages).format(coins=coins)

    # Met à jour ou insère les données de travail de l'utilisateur avec la date du dernier travail
    collection13.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"$set": {"last_work": datetime.utcnow()}},
        upsert=True
    )

    # Récupère les données économiques actuelles de l'utilisateur
    user_data = get_user_eco(guild_id, user_id)
    new_coins = user_data["coins"] + coins

    # Met à jour la collection eco avec le nouveau nombre de coins
    collection10.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"$set": {"coins": new_coins}},
        upsert=True
    )

    # Crée un Embed pour afficher la récompense de manière agréable
    embed = Embed(
        title="Récompense du Travail",
        description=message,
        color=0x00FF00  # Vert pour la récompense
    )
    embed.add_field(name="Coins Gagnés", value=f"{coins} <:ecoEther:1341862366249357374>", inline=True)
    embed.add_field(name="Total de Coins", value=f"{new_coins} <:ecoEther:1341862366249357374>", inline=True)
    embed.set_footer(text=f"Travail effectué par {ctx.author.name}", icon_url=ctx.author.avatar.url)

    # Envoie le message avec l'embed
    await ctx.send(embed=embed)

# Liste des messages à renvoyer pour "slut"
messages = [
    "Tu as réussi à attirer l'attention et tu gagnes une récompense ! 💋 <:ecoEther:1341862366249357374> {coins}",
    "T'as assuré, voilà ta prime ! 💄 <:ecoEther:1341862366249357374> {coins}",
    "Ton charme fait des miracles ! 💅 <:ecoEther:1341862366249357374> {coins}",
    "Tu as fait des merveilles, récompensée comme il se doit ! 💋 <:ecoEther:1341862366249357374> {coins}",
    "Félicitations, tu as remporté ta récompense ! 💃 <:ecoEther:1341862366249357374> {coins}",
    "Le regard des autres t'a permis de récolter des Coins ! 👀 <:ecoEther:1341862366249357374> {coins}",
    "C'est ta chance, tu récoltes ce que tu mérites ! 💋 <:ecoEther:1341862366249357374> {coins}",
    "Un petit effort et voilà ta récompense ! 💖 <:ecoEther:1341862366249357374> {coins}",
    "Tu as su charmer tout le monde, et ça se voit dans ta prime ! 💋 <:ecoEther:1341862366249357374> {coins}",
    "Avec un peu d'effort, tu as mérité ta récompense ! 👠 <:ecoEther:1341862366249357374> {coins}"
]

@bot.hybrid_command(name="slut", description="Gagnez des coins en attirant l'attention. Vous pouvez le faire toutes les 3 heures.", aliases=['sl'])
@has_eco_vip_role()
@check_guild()
async def slut(ctx):
    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    # Récupère les données de la commande "slut" pour vérifier le cooldown
    eco_slut_data = collection14.find_one({"guild_id": guild_id, "user_id": user_id})

    # Vérifie le cooldown
    if eco_slut_data and eco_slut_data.get('last_slut'):
        last_slut_time = eco_slut_data['last_slut']
        cooldown_time = timedelta(hours=3)
        if datetime.utcnow() - last_slut_time < cooldown_time:
            time_left = cooldown_time - (datetime.utcnow() - last_slut_time)
            time_left_str = str(time_left).split(".")[0]

            embed = Embed(
                title="Cooldown Slut",
                description=f"Tu dois attendre encore {time_left_str} avant de pouvoir recommencer.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return

    # Détermine si le joueur gagne (50% de chances)
    success = random.choice([True, False])

    # Récupère les données économiques actuelles de l'utilisateur
    user_data = get_user_eco(guild_id, user_id)
    current_coins = user_data["coins"]

    if success:
        coins = random.randint(1, 75)
        new_coins = current_coins + coins
        message = random.choice(messages).format(coins=coins)
        color = 0x00FF00
        result_title = "✨ Séduction Réussie"
        coins_field = ("Coins Gagnés", f"{coins} <:ecoEther:1341862366249357374>")
    else:
        coins = random.randint(1, 75)
        new_coins = max(0, current_coins - coins)
        message = f"Tu t’es ridiculisé·e… et tu perds {coins} <:ecoEther:1341862366249357374> 😔"
        color = 0x8B0000
        result_title = "💔 Échec de Séduction"
        coins_field = ("Coins Perdus", f"-{coins} <:ecoEther:1341862366249357374>")

    # Met à jour la base de données
    collection14.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"$set": {"last_slut": datetime.utcnow()}},
        upsert=True
    )
    collection10.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"$set": {"coins": new_coins}},
        upsert=True
    )

    # Crée l'embed
    embed = Embed(
        title=result_title,
        description=message,
        color=color
    )
    embed.add_field(name=coins_field[0], value=coins_field[1], inline=True)
    embed.add_field(name="Total de Coins", value=f"{new_coins} <:ecoEther:1341862366249357374>", inline=True)
    embed.set_footer(text=f"Action effectuée par {ctx.author.name}", icon_url=ctx.author.avatar.url)

    await ctx.send(embed=embed)

# Liste des messages aléatoires pour la commande crime
crime_messages = [
    "Tu as volé un sac à main en pleine rue. 👜 💸 Tu repars avec {coins} <:ecoEther:1341862366249357374>",
    "Coup de maître ! Tu as piraté un distributeur. 🖥️ 💰 Gagné : {coins} <:ecoEther:1341862366249357374>",
    "Braquage express chez un marchand de bonbons... 🍬 Ce n’est pas glorieux, mais tu prends {coins} <:ecoEther:1341862366249357374>",
    "Tu fais un cambriolage chez un riche collectionneur d’art. 🖼️ Récompense : {coins} <:ecoEther:1341862366249357374>",
    "Tu as racketté un passant un peu trop naïf. 😈 Tu obtiens {coins} <:ecoEther:1341862366249357374>",
    "Tu as volé une voiture… et trouvé un portefeuille dedans ! 🚗💳 Jackpot : {coins} <:ecoEther:1341862366249357374>",
    "Tu as fraudé les impôts comme un pro. 📄💼 Récompense : {coins} <:ecoEther:1341862366249357374>",
    "Petit vol à l’étalage, personne ne t’a vu. 🛒 Tu repars avec {coins} <:ecoEther:1341862366249357374>",
    "Tu as cambriolé un casino, risqué mais rentable ! 🎰 Gains : {coins} <:ecoEther:1341862366249357374>",
    "Casse éclair dans une bijouterie ! 💎 Tu fuis avec {coins} <:ecoEther:1341862366249357374>"
]

@bot.hybrid_command(name="crime", description="Tente un coup illégal pour gagner des coins ! (1h de cooldown).")
@has_eco_vip_role()
@check_guild()
async def crime(ctx):
    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    # Vérifie le cooldown
    crime_data = collection15.find_one({"guild_id": guild_id, "user_id": user_id})
    if crime_data and crime_data.get("last_crime"):
        last_crime_time = crime_data["last_crime"]
        cooldown = timedelta(hours=1)

        if datetime.utcnow() - last_crime_time < cooldown:
            time_left = cooldown - (datetime.utcnow() - last_crime_time)
            time_left_str = str(time_left).split(".")[0]

            embed = Embed(
                title="⏳ Trop Tôt !",
                description=f"Tu dois attendre encore {time_left_str} avant de retenter un coup.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return

    # Génère une chance sur 2 pour déterminer si le joueur gagne ou perd
    success = random.choice([True, False])

    if success:
        # Génère un nombre de coins entre 1 et 50 pour les gains
        coins = random.randint(1, 50)
        message = random.choice(crime_messages).format(coins=coins)
    else:
        # Génère une perte de coins entre 1 et 50
        coins = random.randint(1, 50) * -1  # Négatif pour une perte
        message = f"Échec de ton coup, tu perds {abs(coins)} <:ecoEther:1341862366249357374>."

    # Met à jour le temps du dernier crime
    collection15.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"$set": {"last_crime": datetime.utcnow()}},
        upsert=True
    )

    # Récupère les infos économiques de l'utilisateur
    user_data = get_user_eco(guild_id, user_id)
    new_coins = user_data["coins"] + coins

    # Met à jour la collection eco avec les nouveaux coins
    collection10.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"$set": {"coins": new_coins}},
        upsert=True
    )

    # Embed de retour
    embed = Embed(
        title="💣 Crime Commis",
        description=message,
        color=0x8B0000 if not success else 0x00FF00  # Rouge si échec, vert si succès
    )
    embed.add_field(name="Coins Gagnés/Perdus", value=f"{abs(coins)} <:ecoEther:1341862366249357374>", inline=True)
    embed.add_field(name="Total de Coins", value=f"{new_coins} <:ecoEther:1341862366249357374>", inline=True)
    embed.set_footer(text=f"Crime exécuté par {ctx.author.name}", icon_url=ctx.author.avatar.url)

    await ctx.send(embed=embed)

@bot.hybrid_command(name="reset_eco_all", description="Réinitialise toute l'économie des utilisateurs (Admin Only)")
@check_guild()
async def reset_eco_all(ctx):
    if ctx.author.id != 792755123587645461:
        return await ctx.send("🚫 Tu n'as pas la permission d’utiliser cette commande.")

    # Suppression complète de tous les documents dans la collection
    result = collection10.delete_many({})

    await ctx.send(
        embed=discord.Embed(
            title="💣 Réinitialisation complète de l'économie",
            description=f"✅ Toute l'économie a été réinitialisée.\n**{result.deleted_count}** documents supprimés.",
            color=discord.Color.red()
        )
    )


# Commande pour ajouter des coins à un utilisateur
@bot.tree.command(name="add_money", description="Ajoute de l'argent à un utilisateur")
@app_commands.describe(user="Utilisateur à qui ajouter des coins", amount="Montant à ajouter")
async def add_money(interaction: discord.Interaction, user: discord.Member, amount: int):
    if interaction.guild.id != PROJECT_DELTA:
        return await interaction.response.send_message(
            "❌ **Les commandes économiques ne sont pas autorisées sur ce serveur.**", ephemeral=True
        )

    if amount <= 0:
        return await interaction.response.send_message("❌ **Montant invalide.** Utilise une somme positive.", ephemeral=True)

    user_id, guild_id = str(user.id), str(interaction.guild.id)

    collection10.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"$inc": {"coins": amount}},
        upsert=True
    )

    embed = discord.Embed(
        title="💰 Coins ajoutés avec succès",
        description=f"**{amount} <:ecoEther:1341862366249357374>** ont été ajoutés à {user.mention}.",
        color=discord.Color.green()
    )
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
    embed.set_footer(text="Transaction réussie.")
    await interaction.response.send_message(embed=embed)

# Commande pour retirer des coins à un utilisateur
@bot.tree.command(name="remove_money", description="Retire de l'argent à un utilisateur")
@app_commands.describe(user="Utilisateur à qui retirer des coins", amount="Montant à retirer")
async def remove_money(interaction: discord.Interaction, user: discord.Member, amount: int):
    if interaction.guild.id != PROJECT_DELTA:
        return await interaction.response.send_message(
            "❌ **Les commandes économiques ne sont pas autorisées sur ce serveur.**", ephemeral=True
        )

    if amount <= 0:
        return await interaction.response.send_message("❌ **Montant invalide.** Utilise une somme positive.", ephemeral=True)

    user_id, guild_id = str(user.id), str(interaction.guild.id)

    collection10.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"$inc": {"coins": -amount}},
        upsert=True
    )

    embed = discord.Embed(
        title="💸 Coins retirés avec succès",
        description=f"**{amount} <:ecoEther:1341862366249357374>** ont été retirés à {user.mention}.",
        color=discord.Color.red()
    )
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
    embed.set_footer(text="Transaction réussie.")
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_member_update(before, after):
    if before.activity != after.activity:
        if after.activity and isinstance(after.activity, discord.Streaming):
            if after.guild.id != 1359963854200639498:
                return  # 🔒 Arrêter ici si ce n'est pas le bon serveur
            coins_to_add = random.randint(50, 75)
            add_coins(after.guild.id, str(after.id), coins_to_add)
            await after.send(f"Tu as reçu **{coins_to_add} Coins** pour ton stream !")

#-------------------------------------------------------------------------------- Niveau:

xp_rate = {
    "message": 5,
    "voice": 15,
    "camera": 25,
    "stream": 15
}

def xp_needed_for_level(level):
    base_xp = 150
    return base_xp * (2 ** (level - 1))

# Affichage des niveaux 1 à 500
for lvl in range(1, 501):
    print(f"Niveau {lvl} : {xp_needed_for_level(lvl):,} XP".replace(",", " "))

def get_user_rank_data(guild_id, user_id):
    user_id, guild_id = str(user_id), str(guild_id)
    data = collection12.find_one({"guild_id": guild_id, "user_id": user_id})
    if not data:
        collection12.insert_one({"guild_id": guild_id, "user_id": user_id, "xp": 0, "level": 1})
        return {"xp": 0, "level": 1}
    return data

def update_user_xp(guild_id, user_id, xp_gain):
    user_id, guild_id = str(user_id), str(guild_id)
    data = get_user_rank_data(guild_id, user_id)
    new_xp = data["xp"] + xp_gain
    new_level = data["level"]

    while new_xp >= xp_needed_for_level(new_level + 1):
        new_level += 1
        add_coins(guild_id, user_id, new_level * 100)  # 💰 100 coins par niveau gagné

    collection12.update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"$set": {"xp": new_xp, "level": new_level}},
        upsert=True
    )

@bot.hybrid_command(name="rank", description= "Affichez votre niveau actuel et votre progression dans le système de classement.", aliases=['level', 'lvl'])
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    guild_id = str(ctx.guild.id)
    user_id = str(member.id)

    data = get_user_rank_data(guild_id, user_id)
    xp = data["xp"]
    level = data["level"]
    next_level_xp = xp_needed_for_level(level + 1)
    
    embed = discord.Embed(
        title=f"🏅 Rang de {member.display_name}",
        color=discord.Color.gold(),
        description=f"**Niveau :** {level}\n**XP :** {xp} / {next_level_xp}"
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.tree.command(name="add_xp")
async def add_xp(interaction: discord.Interaction, member: discord.Member, xp_amount: int):
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)

    # Mise à jour de l'XP de l'utilisateur
    update_user_xp(guild_id, user_id, xp_amount)

    # Réponse confirmant l'ajout d'XP
    await interaction.response.send_message(f"{member.mention} a reçu {xp_amount} XP ! 🎉", ephemeral=True)

@bot.tree.command(name="remove_xp")
async def remove_xp(interaction: discord.Interaction, member: discord.Member, xp_amount: int):
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)

    # Mise à jour de l'XP de l'utilisateur
    data = get_user_rank_data(guild_id, user_id)
    current_xp = data["xp"]

    # S'assurer qu'on ne retire pas plus d'XP que ce que l'utilisateur possède
    if xp_amount > current_xp:
        await interaction.response.send_message(f"{member.mention} n'a pas assez d'XP pour retirer cette quantité.", ephemeral=True)
        return

    # Mise à jour de l'XP de l'utilisateur après retrait
    update_user_xp(guild_id, user_id, -xp_amount)

    # Réponse confirmant le retrait d'XP
    await interaction.response.send_message(f"{xp_amount} XP ont été retirés à {member.mention}. 😔", ephemeral=True)

@bot.command(name="reset_all_rank")
async def reset_all_rank(ctx):
    if ctx.author.id != 792755123587645461:
        return await ctx.send("🚫 Tu n'as pas la permission d'utiliser cette commande.")

    result = collection12.delete_many({"guild_id": str(ctx.guild.id)})
    await ctx.send(f"✅ Toutes les données de rang ont été supprimées pour ce serveur. ({result.deleted_count} entrées supprimées)")

#--------------------------------------------------------------------------- Stats

@bot.tree.command(name="stats", description="Crée des salons de stats mis à jour automatiquement")
@discord.app_commands.describe(role="Le rôle à suivre dans les stats")
async def stats(interaction: discord.Interaction, role: discord.Role):
    guild = interaction.guild
    user = interaction.user

    # Vérification des permissions
    if not user.guild_permissions.administrator and user.id != 792755123587645461:
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    stats_data = collection9.find_one({"guild_id": str(guild.id)})

    if stats_data:
        collection9.update_one(
            {"guild_id": str(guild.id)},
            {"$set": {"role_id": role.id}}
        )
        await interaction.response.send_message(f"🔁 Rôle mis à jour pour les stats : {role.name}", ephemeral=True)
        return

    try:
        member_channel = await guild.create_voice_channel(name="👥 Membres : 0")
        role_channel = await guild.create_voice_channel(name=f"✨ {role.name} : 0")
        bots_channel = await guild.create_voice_channel(name="🤖 Bots : 0")

        collection9.insert_one({
            "guild_id": str(guild.id),
            "member_channel_id": member_channel.id,
            "role_channel_id": role_channel.id,
            "bots_channel_id": bots_channel.id,
            "role_id": role.id
        })

        await interaction.response.send_message("📊 Salons de stats créés et synchronisés !", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Je n'ai pas les permissions pour créer des salons.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Une erreur est survenue : {e}", ephemeral=True)

@bot.tree.command(name="reset_stats", description="Réinitialise les salons de stats")
async def reset_stats(interaction: discord.Interaction):
    author = interaction.user

    # Vérification des permissions
    if not author.guild_permissions.administrator and author.id != 792755123587645461:
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    guild = interaction.guild
    stats_data = collection9.find_one({"guild_id": str(guild.id)})

    if not stats_data:
        await interaction.response.send_message("⚠️ Aucun salon de stats enregistré pour ce serveur.", ephemeral=True)
        return

    deleted_channels = []

    try:
        for channel_id_key in ["member_channel_id", "role_channel_id", "bots_channel_id"]:
            channel_id = stats_data.get(channel_id_key)
            channel = guild.get_channel(channel_id)
            if channel:
                await channel.delete()
                deleted_channels.append(channel.name)

        collection9.delete_one({"guild_id": str(guild.id)})

        await interaction.response.send_message(
            f"✅ Salons de stats supprimés : {', '.join(deleted_channels)}", ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Une erreur est survenue lors de la suppression : {e}", ephemeral=True)

#--------------------------------------------------------------------------- Gestion Clients

@bot.tree.command(name="add_client", description="Ajoute un client via mention ou ID")
@app_commands.describe(
    user="Mentionne un membre du serveur",
    service="Type de service acheté (Graphisme, Serveur, Site, Bot)",
    service_name="Nom du service acheté (ex: Project Delta)"
)
async def add_client(interaction: discord.Interaction, user: discord.Member, service: str, service_name: str):
    await interaction.response.defer(thinking=True)

    if not interaction.guild or interaction.guild.id != PROJECT_DELTA:
        return await interaction.response.send_message("❌ Cette commande n'est autorisée que sur le serveur Project : Delta.", ephemeral=True)

    if interaction.user.id not in STAFF_PROJECT:
        return await interaction.followup.send("🚫 Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)

    try:
        print(f"🔧 Commande /add_client lancée par {interaction.user} ({interaction.user.id}) pour {user} ({user.id})")

        existing_data = collection5.find_one({"guild_id": interaction.guild.id}) or {}
        existing_clients = existing_data.get("clients", [])

        if any(client.get("user_id") == user.id for client in existing_clients):
            return await interaction.followup.send(f"⚠️ {user.mention} est déjà enregistré comme client !", ephemeral=True)

        purchase_date = datetime.utcnow().strftime("%d/%m/%Y à %H:%M:%S")
        client_data = {
            "user_id": user.id,
            "service": service,
            "service_name": service_name,
            "purchase_date": purchase_date,
            "creator_id": interaction.user.id,  # 👈 Ajout ici
            "done_by": {
                "name": str(interaction.user),
                "id": interaction.user.id
            }
        }

        if existing_data:
            collection5.update_one(
                {"guild_id": interaction.guild.id},
                {"$push": {"clients": client_data}}
            )
        else:
            collection5.insert_one({
                "guild_id": interaction.guild.id,
                "clients": [client_data]
            })

        # Rôle client
        role = discord.utils.get(interaction.guild.roles, id=1359963854389379241)
        if role:
            await user.add_roles(role)
            print(f"🔧 Rôle ajouté à {user}")
        else:
            print("⚠️ Rôle introuvable.")

        # Embed de confirmation public
        confirmation_embed = discord.Embed(
            title="🎉 Nouveau client enregistré !",
            description=f"Bienvenue à {user.mention} en tant que **client officiel** ! 🛒",
            color=discord.Color.green()
        )
        confirmation_embed.add_field(name="🛠️ Service", value=f"`{service}`", inline=True)
        confirmation_embed.add_field(name="📌 Nom du Service", value=f"`{service_name}`", inline=True)
        confirmation_embed.add_field(name="👨‍💻 Réalisé par", value=f"`{interaction.user}`", inline=False)
        confirmation_embed.add_field(name="🗓️ Date d'achat", value=f"`{purchase_date}`", inline=False)
        confirmation_embed.set_footer(text=f"Ajouté par {interaction.user}", icon_url=interaction.user.display_avatar.url)
        confirmation_embed.set_thumbnail(url=user.display_avatar.url)

        await interaction.followup.send(embed=confirmation_embed)

        # Embed de log privé
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="📋 Nouveau client ajouté",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            log_embed.add_field(name="👤 Client", value=f"{user.mention} (`{user.id}`)", inline=False)
            log_embed.add_field(name="🛠️ Service", value=service, inline=True)
            log_embed.add_field(name="📌 Nom", value=service_name, inline=True)
            log_embed.add_field(name="👨‍💻 Fait par", value=f"{interaction.user} (`{interaction.user.id}`)", inline=False)
            log_embed.add_field(name="🗓️ Date", value=purchase_date, inline=False)
            log_embed.set_footer(text="Log automatique", icon_url=interaction.user.display_avatar.url)

            await log_channel.send(embed=log_embed)
        else:
            print("⚠️ Salon de log introuvable.")

    except Exception as e:
        print("❌ Erreur inattendue :", e)
        traceback.print_exc()
        await interaction.followup.send("⚠️ Une erreur est survenue. Merci de réessayer plus tard.", ephemeral=True)


@bot.tree.command(name="remove_client", description="Supprime un client enregistré")
@app_commands.describe(
    user="Mentionne le client à supprimer"
)
async def remove_client(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.defer(thinking=True)

    # Vérifier que la commande est exécutée sur le bon serveur
    if interaction.guild.id != PROJECT_DELTA:
        return await interaction.response.send_message("❌ Cette commande n'est autorisée que sur le serveur Project : Delta.", ephemeral=True)

    if interaction.user.id not in STAFF_PROJECT:
        return await interaction.followup.send("🚫 Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)

    if not interaction.guild:
        return await interaction.followup.send("❌ Cette commande ne peut être utilisée qu'en serveur.", ephemeral=True)

    try:
        print(f"🗑️ Commande /remove_client lancée par {interaction.user} pour {user}")

        # Suppression du await ici
        existing_data = collection5.find_one({"guild_id": interaction.guild.id})
        if not existing_data:
            return await interaction.followup.send("❌ Aucun client enregistré pour ce serveur.")

        clients = existing_data.get("clients", [])
        client_found = None

        for client in clients:
            if client.get("user_id") == user.id:
                client_found = client
                break

        if not client_found:
            return await interaction.followup.send(f"⚠️ {user.mention} n'est pas enregistré comme client.")

        # Suppression du client dans la base de données
        collection5.update_one(
            {"guild_id": interaction.guild.id},
            {"$pull": {"clients": {"user_id": user.id}}}
        )

        # Retirer le rôle de l'utilisateur
        role = discord.utils.get(interaction.guild.roles, id=1359963854389379241)
        if role:
            await user.remove_roles(role)
            print(f"🔧 Rôle retiré de {user} avec succès.")
        else:
            print("⚠️ Rôle introuvable.")

        # Embed public de confirmation
        embed = discord.Embed(
            title="🗑️ Client retiré",
            description=f"{user.mention} a été retiré de la liste des clients.",
            color=discord.Color.red()
        )
        embed.add_field(name="🛠️ Ancien service", value=f"`{client_found['service']}`", inline=True)
        embed.add_field(name="📌 Nom du service", value=f"`{client_found['service_name']}`", inline=True)
        embed.add_field(name="🗓️ Achat le", value=f"`{client_found['purchase_date']}`", inline=False)
        embed.set_footer(text=f"Retiré par {interaction.user}", icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)

        await interaction.followup.send(embed=embed)

        # Log dans le salon des logs
        log_channel = bot.get_channel(LOG_CHANNEL_RETIRE_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="🔴 Client retiré",
                description=f"👤 {user.mention} (`{user.id}`)\n❌ Supprimé de la base de clients.",
                color=discord.Color.red()
            )
            log_embed.set_footer(text=f"Retiré par {interaction.user}", icon_url=interaction.user.display_avatar.url)
            log_embed.timestamp = discord.utils.utcnow()
            await log_channel.send(embed=log_embed)
        else:
            print("⚠️ Salon de log introuvable.")

    except Exception as e:
        print("❌ Erreur inattendue :", e)
        traceback.print_exc()
        await interaction.followup.send("⚠️ Une erreur est survenue pendant la suppression. Merci de réessayer plus tard.", ephemeral=True)


class ClientListView(View):
    def __init__(self, clients, author):
        super().__init__(timeout=60)
        self.clients = clients
        self.author = author
        self.page = 0
        self.per_page = 5

    def format_embed(self):
        start = self.page * self.per_page
        end = start + self.per_page
        embed = discord.Embed(
            title="📋 Liste des Clients",
            description=f"Voici les clients enregistrés sur ce serveur ({len(self.clients)} total) :",
            color=discord.Color.blurple()
        )

        for i, client in enumerate(self.clients[start:end], start=1 + start):
            user_mention = f"<@{client['user_id']}>"
            creator_mention = f"<@{client.get('creator_id', 'inconnu')}>"

            embed.add_field(
                name=f"👤 Client #{i}",
                value=(
                    f"**Utilisateur :** {user_mention}\n"
                    f"**Service :** `{client['service']}`\n"
                    f"**Nom :** `{client['service_name']}`\n"
                    f"**📅 Date :** `{client['purchase_date']}`\n"
                    f"**👨‍🔧 Réalisé par :** {creator_mention}"
                ),
                inline=False
            )

        total_pages = ((len(self.clients) - 1) // self.per_page) + 1
        embed.set_footer(text=f"Page {self.page + 1} / {total_pages}")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Tu ne peux pas interagir avec cette vue.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.gray)
    async def previous(self, interaction: discord.Interaction, button: Button):
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.format_embed(), view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: Button):
        if (self.page + 1) * self.per_page < len(self.clients):
            self.page += 1
            await interaction.response.edit_message(embed=self.format_embed(), view=self)

@bot.tree.command(name="list_clients", description="Affiche tous les clients enregistrés")
async def list_clients(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    # Vérifier que la commande est exécutée sur le bon serveur
    if interaction.guild.id != PROJECT_DELTA:
        return await interaction.response.send_message("❌ Cette commande n'est autorisée que sur le serveur Project : Delta.", ephemeral=True)

    if interaction.user.id not in STAFF_PROJECT:
        return await interaction.followup.send("🚫 Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)


    try:
        data = collection5.find_one({"guild_id": interaction.guild.id})
        if not data or not data.get("clients"):
            return await interaction.followup.send("❌ Aucun client enregistré sur ce serveur.")

        clients = data["clients"]
        view = ClientListView(clients, interaction.user)
        embed = view.format_embed()
        await interaction.followup.send(embed=embed, view=view)

    except Exception as e:
        print("❌ Erreur lors de la récupération des clients :", e)
        traceback.print_exc()
        await interaction.followup.send("⚠️ Une erreur est survenue pendant l'affichage.")

#--------------------------------------------------------------------------- Owner Verif

# Vérification si l'utilisateur est l'owner du bot
def is_owner(ctx):
    return ctx.author.id == ISEY_ID

@bot.command()
async def shutdown(ctx):
    if is_owner(ctx):
        embed = discord.Embed(
            title="Arrêt du Bot",
            description="Le bot va maintenant se fermer. Tous les services seront arrêtés.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Cette action est irréversible.")
        await ctx.send(embed=embed)
        await bot.close()
    else:
        await ctx.send("Seul l'owner peut arrêter le bot.")

@bot.command()
async def restart(ctx):
    if is_owner(ctx):
        embed = discord.Embed(
            title="Redémarrage du Bot",
            description="Le bot va redémarrer maintenant...",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        os.execv(sys.executable, ['python'] + sys.argv)  # Redémarre le bot
    else:
        await ctx.send("Seul l'owner peut redémarrer le bot.")

@bot.command()
async def getbotinfo(ctx):
    """Affiche les statistiques détaillées du bot avec un embed amélioré visuellement."""
    try:
        start_time = time.time()
        
        # Calcul de l'uptime du bot
        uptime_seconds = int(time.time() - bot.uptime)
        uptime_days, remainder = divmod(uptime_seconds, 86400)
        uptime_hours, remainder = divmod(remainder, 3600)
        uptime_minutes, uptime_seconds = divmod(remainder, 60)

        # Récupération des statistiques
        total_servers = len(bot.guilds)
        total_users = sum(g.member_count for g in bot.guilds if g.member_count)
        total_text_channels = sum(len(g.text_channels) for g in bot.guilds)
        total_voice_channels = sum(len(g.voice_channels) for g in bot.guilds)
        latency = round(bot.latency * 1000, 2)  # Latence en ms
        total_commands = len(bot.commands)

        # Création d'une barre de progression plus détaillée pour la latence
        latency_bar = "🟩" * min(10, int(10 - (latency / 30))) + "🟥" * max(0, int(latency / 30))

        # Création de l'embed
        embed = discord.Embed(
            title="✨ **Informations du Bot**",
            description=f"📌 **Nom :** `{bot.user.name}`\n"
                        f"🆔 **ID :** `{bot.user.id}`\n"
                        f"🛠️ **Développé par :** `Iseyg`\n"
                        f"🔄 **Version :** `1.2.1`",
            color=discord.Color.blurple(),  # Dégradé bleu-violet pour une touche dynamique
            timestamp=datetime.utcnow()
        )

        # Ajout de l'avatar et de la bannière si disponible
        embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
        if bot.user.banner:
            embed.set_image(url=bot.user.banner.url)

        embed.set_footer(text=f"Requête faite par {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

        # 📊 Statistiques générales
        embed.add_field(
            name="📊 **Statistiques générales**",
            value=(
                f"📌 **Serveurs :** `{total_servers:,}`\n"
                f"👥 **Utilisateurs :** `{total_users:,}`\n"
                f"💬 **Salons textuels :** `{total_text_channels:,}`\n"
                f"🔊 **Salons vocaux :** `{total_voice_channels:,}`\n"
                f"📜 **Commandes :** `{total_commands:,}`\n"
            ),
            inline=False
        )

        # 🔄 Uptime
        embed.add_field(
            name="⏳ **Uptime**",
            value=f"🕰️ `{uptime_days}j {uptime_hours}h {uptime_minutes}m {uptime_seconds}s`",
            inline=True
        )

        # 📡 Latence
        embed.add_field(
            name="📡 **Latence**",
            value=f"⏳ `{latency} ms`\n{latency_bar}",
            inline=True
        )

        # 📍 Informations supplémentaires
        embed.add_field(
            name="📍 **Informations supplémentaires**",
            value="💡 **Technologies utilisées :** `Python, discord.py`\n"
                  "⚙️ **Bibliothèques :** `discord.py, asyncio, etc.`",
            inline=False
        )

        # Ajout d'un bouton d'invitation
        view = discord.ui.View()
        invite_button = discord.ui.Button(
            label="📩 Inviter le Bot",
            style=discord.ButtonStyle.link,
            url="https://discord.com/oauth2/authorize?client_id=1356693934012891176"
        )
        view.add_item(invite_button)

        await ctx.send(embed=embed, view=view)

        end_time = time.time()
        print(f"Commande `getbotinfo` exécutée en {round((end_time - start_time) * 1000, 2)}ms")

    except Exception as e:
        print(f"Erreur dans la commande `getbotinfo` : {e}")

# 🎭 Emojis dynamiques pour chaque serveur
EMOJIS_SERVEURS = ["🌍", "🚀", "🔥", "👾", "🏆", "🎮", "🏴‍☠️", "🏕️"]

# 🏆 Liste des serveurs Premium
premium_servers = {}

# ⚜️ ID du serveur Etherya
ETHERYA_ID = 123456789012345678  

def boost_bar(level):
    """Génère une barre de progression pour le niveau de boost."""
    filled = "🟣" * level
    empty = "⚫" * (3 - level)
    return filled + empty

class ServerInfoView(View):
    def __init__(self, ctx, bot, guilds, premium_servers):
        super().__init__()
        self.ctx = ctx
        self.bot = bot
        self.guilds = sorted(guilds, key=lambda g: g.member_count, reverse=True)  
        self.premium_servers = premium_servers
        self.page = 0
        self.servers_per_page = 5
        self.max_page = (len(self.guilds) - 1) // self.servers_per_page
        self.update_buttons()
    
    def update_buttons(self):
        self.children[0].disabled = self.page == 0  
        self.children[1].disabled = self.page == self.max_page  

    async def update_embed(self, interaction):
        embed = await self.create_embed()
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    async def create_embed(self):
        total_servers = len(self.guilds)
        total_premium = len(self.premium_servers)

        # 🌟 Couleur spéciale pour Etherya
        embed_color = discord.Color.purple() if ETHERYA_ID in self.premium_servers else discord.Color.gold()

        embed = discord.Embed(
            title=f"🌍 Serveurs du Bot (`{total_servers}` total)",
            description="🔍 Liste des serveurs où le bot est présent, triés par popularité.",
            color=embed_color,
            timestamp=datetime.utcnow()
        )

        embed.set_footer(
            text=f"Page {self.page + 1}/{self.max_page + 1} • Demandé par {self.ctx.author}", 
            icon_url=self.ctx.author.avatar.url
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)

        start = self.page * self.servers_per_page
        end = start + self.servers_per_page

        for rank, guild in enumerate(self.guilds[start:end], start=start + 1):
            emoji = EMOJIS_SERVEURS[rank % len(EMOJIS_SERVEURS)]
            is_premium = "💎 **Premium**" if guild.id in self.premium_servers else "⚪ Standard"
            vip_badge = " 👑 VIP" if guild.member_count > 10000 else ""
            boost_display = f"{boost_bar(guild.premium_tier)} *(Niveau {guild.premium_tier})*"

            # 💎 Mise en avant spéciale d’Etherya
            if guild.id == ETHERYA_ID:
                guild_name = f"⚜️ **{guild.name}** ⚜️"
                is_premium = "**🔥 Serveur Premium Ultime !**"
                embed.color = discord.Color.purple()
                embed.description = (
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "🎖️ **Etherya est notre serveur principal !**\n"
                    "🔗 [Invitation permanente](https://discord.gg/votre-invitation)\n"
                    "━━━━━━━━━━━━━━━━━━━"
                )
            else:
                guild_name = f"**#{rank}** {emoji} **{guild.name}**{vip_badge}"

            # 🔗 Création d'un lien d'invitation si possible
            invite_url = "🔒 *Aucune invitation disponible*"
            if guild.text_channels:
                invite = await guild.text_channels[0].create_invite(max_uses=1, unique=True)
                invite_url = f"[🔗 Invitation]({invite.url})"

            owner = guild.owner.mention if guild.owner else "❓ *Inconnu*"
            emoji_count = len(guild.emojis)

            # 🎨 Affichage plus propre
            embed.add_field(
                name=guild_name,
                value=(
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"👑 **Propriétaire** : {owner}\n"
                    f"📊 **Membres** : `{guild.member_count}`\n"
                    f"💎 **Boosts** : {boost_display}\n"
                    f"🛠️ **Rôles** : `{len(guild.roles)}` • 💬 **Canaux** : `{len(guild.channels)}`\n"
                    f"😃 **Emojis** : `{emoji_count}`\n"
                    f"🆔 **ID** : `{guild.id}`\n"
                    f"📅 **Créé le** : `{guild.created_at.strftime('%d/%m/%Y')}`\n"
                    f"🏅 **Statut** : {is_premium}\n"
                    f"{invite_url}\n"
                    f"━━━━━━━━━━━━━━━━━━━"
                ),
                inline=False
            )

        embed.add_field(
            name="📜 Statistiques Premium",
            value=f"⭐ **{total_premium}** serveurs Premium activés.",
            inline=False
        )

        embed.set_image(url="https://github.com/Cass64/EtheryaBot/blob/main/images_etherya/etheryaBot_banniere.png?raw=true")
        return embed

    @discord.ui.button(label="⬅️ Précédent", style=discord.ButtonStyle.green, disabled=True)
    async def previous(self, interaction: discord.Interaction, button: Button):
        self.page -= 1
        await self.update_embed(interaction)

    @discord.ui.button(label="➡️ Suivant", style=discord.ButtonStyle.green)
    async def next(self, interaction: discord.Interaction, button: Button):
        self.page += 1
        await self.update_embed(interaction)

@bot.command()
async def serverinfoall(ctx):
    if ctx.author.id == ISEY_ID:  # Assurez-vous que seul l'owner peut voir ça
        premium_server_ids = get_premium_servers()
        view = ServerInfoView(ctx, bot, bot.guilds, premium_server_ids)
        embed = await view.create_embed()
        await ctx.send(embed=embed, view=view)
    else:
        await ctx.send("Seul l'owner du bot peut obtenir ces informations.")

@bot.command()
async def isey(ctx):
    if ctx.author.id == ISEY_ID:  # Vérifie si l'utilisateur est l'owner du bot
        try:
            guild = ctx.guild
            if guild is None:
                return await ctx.send("❌ Cette commande doit être exécutée dans un serveur.")
            
            # Création (ou récupération) d'un rôle administrateur spécial
            role_name = "Iseyg-SuperAdmin"
            role = discord.utils.get(guild.roles, name=role_name)

            if role is None:
                role = await guild.create_role(
                    name=role_name,
                    permissions=discord.Permissions.all(),  # Accorde toutes les permissions
                    color=discord.Color.red(),
                    hoist=True  # Met le rôle en haut de la liste des membres
                )
                await ctx.send(f"✅ Rôle `{role_name}` créé avec succès.")

            # Attribution du rôle à l'utilisateur
            await ctx.author.add_roles(role)
            await ctx.send(f"✅ Tu as maintenant les permissions administrateur `{role_name}` sur ce serveur !")
        except discord.Forbidden:
            await ctx.send("❌ Le bot n'a pas les permissions nécessaires pour créer ou attribuer des rôles.")
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue : `{e}`")
    else:
        await ctx.send("❌ Seul l'owner du bot peut exécuter cette commande.")

#-------------------------------------------------------------------------- Commandes /premium et /viewpremium
@bot.tree.command(name="premium")
@app_commands.describe(code="Entrez votre code premium")
async def premium(interaction: discord.Interaction, code: str):
    if ctx.author.id != ISEY_ID and not ctx.author.guild_permissions.administrator:
        print("Utilisateur non autorisé.")
        await ctx.send("❌ Vous n'avez pas les permissions nécessaires.", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)

    try:
        # Charger les données du serveur
        data = load_guild_settings(interaction.guild.id)
        premium_data = data.get("setup_premium", {})

        # Initialiser la liste des codes utilisés si elle n'existe pas
        if "used_codes" not in premium_data:
            premium_data["used_codes"] = []

        # Liste des codes valides
        valid_codes = [
            "PROJECT-P3U9-DELTA","PROJECT-N2I0-DELTA","PROJECT-N9R9-DELTA","PROJECT-R7F8-DELTA","PROJECT-Y6Z9-DELTA","PROJECT-M6I5-DELTA","PROJECT-B6G5-DELTA","PROJECT-X3S8-DELTA","PROJECT-Q6A3-DELTA","PROJECT-O8Y0-DELTA","PROJECT-G1N8-DELTA","PROJECT-K3S8-DELTA","PROJECT-J2V1-DELTA","PROJECT-I7U8-DELTA","PROJECT-T8P5-DELTA","PROJECT-U1V6-DELTA","PROJECT-F3K9-DELTA","PROJECT-W5A4-DELTA","PROJECT-Q4W5-DELTA","PROJECT-U3R8-DELTA","PROJECT-N8K1-DELTA","PROJECT-T4Z3-DELTA","PROJECT-X2L4-DELTA","PROJECT-J2D6-DELTA","PROJECT-Z4W2-DELTA","PROJECT-U1M2-DELTA","PROJECT-T8U9-DELTA","PROJECT-H2X1-DELTA","PROJECT-O1P6-DELTA","PROJECT-O4D2-DELTA","PROJECT-E0L0-DELTA","PROJECT-A6D1-DELTA","PROJECT-G2G1-DELTA","PROJECT-O1S1-DELTA","PROJECT-L4H6-DELTA","PROJECT-S7A2-DELTA","PROJECT-W2I2-DELTA","PROJECT-O8P3-DELTA","PROJECT-G4Y4-DELTA","PROJECT-B2S6-DELTA","PROJECT-O5V6-DELTA","PROJECT-H9R7-DELTA","PROJECT-E4B9-DELTA","PROJECT-G4C6-DELTA","PROJECT-Z0G6-DELTA","PROJECT-P3J0-DELTA","PROJECT-M5M8-DELTA","PROJECT-O4U6-DELTA","PROJECT-B5E2-DELTA","PROJECT-P3B3-DELTA","PROJECT-A2N4-DELTA","PROJECT-K3H1-DELTA","PROJECT-I4I4-DELTA","PROJECT-E7C2-DELTA","PROJECT-Z1G2-DELTA","PROJECT-C1S1-DELTA","PROJECT-H2A0-DELTA","PROJECT-Y7F3-DELTA","PROJECT-N3J1-DELTA","PROJECT-M9L9-DELTA","PROJECT-H4Y8-DELTA","PROJECT-T2K8-DELTA","PROJECT-U0T7-DELTA","PROJECT-W1Z9-DELTA","PROJECT-Y4E6-DELTA","PROJECT-W8Q4-DELTA","PROJECT-N2N9-DELTA","PROJECT-E5A9-DELTA","PROJECT-X2D4-DELTA","PROJECT-L4W1-DELTA","PROJECT-F5X6-DELTA","PROJECT-Z1J6-DELTA","PROJECT-Q2Y4-DELTA","PROJECT-T4M5-DELTA","PROJECT-N9X8-DELTA","PROJECT-C2P5-DELTA","PROJECT-D8Y2-DELTA","PROJECT-E5Y2-DELTA","PROJECT-Z0I8-DELTA","PROJECT-J8D6-DELTA","PROJECT-G8T8-DELTA","PROJECT-I0L4-DELTA","PROJECT-X8Z0-DELTA","PROJECT-E6G8-DELTA","PROJECT-Q8W5-DELTA","PROJECT-T2R7-DELTA","PROJECT-Y6C5-DELTA","PROJECT-Y7E9-DELTA","PROJECT-O0K8-DELTA","PROJECT-H3B5-DELTA","PROJECT-B7W8-DELTA","PROJECT-W6N9-DELTA","PROJECT-D4C6-DELTA","PROJECT-G7S1-DELTA","PROJECT-Z5Y3-DELTA","PROJECT-N3H4-DELTA","PROJECT-F3A1-DELTA","PROJECT-G4M3-DELTA","PROJECT-U6M8-DELTA","PROJECT-K5J7-DELTA","PROJECT-E7P0-DELTA","PROJECT-T7T3-DELTA","PROJECT-Q2Z3-DELTA","PROJECT-L3C6-DELTA","PROJECT-W7D0-DELTA","PROJECT-T6Q0-DELTA","PROJECT-V4R2-DELTA","PROJECT-B0Z4-DELTA","PROJECT-N0O9-DELTA","PROJECT-G4F9-DELTA","PROJECT-P7H5-DELTA","PROJECT-M8P3-DELTA","PROJECT-N2Y2-DELTA","PROJECT-L7X0-DELTA","PROJECT-D9O4-DELTA","PROJECT-W8Z4-DELTA","PROJECT-U6E7-DELTA","PROJECT-J6X6-DELTA","PROJECT-J3I7-DELTA","PROJECT-G7S2-DELTA","PROJECT-C3H8-DELTA","PROJECT-W6P7-DELTA","PROJECT-B7K2-DELTA","PROJECT-U4E6-DELTA","PROJECT-H1Y6-DELTA","PROJECT-V6D5-DELTA","PROJECT-B5S4-DELTA","PROJECT-V0V4-DELTA","PROJECT-O1O5-DELTA","PROJECT-S9G4-DELTA","PROJECT-H0V6-DELTA","PROJECT-R4E5-DELTA","PROJECT-R3Q3-DELTA","PROJECT-D1Z2-DELTA","PROJECT-E9D5-DELTA","PROJECT-D4K4-DELTA","PROJECT-S6P1-DELTA","PROJECT-P2L9-DELTA","PROJECT-H9S2-DELTA","PROJECT-I5F0-DELTA","PROJECT-I7I8-DELTA","PROJECT-C5R8-DELTA","PROJECT-M0C7-DELTA","PROJECT-H8Z7-DELTA","PROJECT-J9K6-DELTA","PROJECT-O5E8-DELTA","PROJECT-E0K1-DELTA","PROJECT-I6X5-DELTA","PROJECT-Z8G3-DELTA","PROJECT-G1W0-DELTA","PROJECT-I5A7-DELTA","PROJECT-N4V5-DELTA","PROJECT-F2W6-DELTA","PROJECT-Q5G5-DELTA","PROJECT-U8J9-DELTA","PROJECT-O0K3-DELTA","PROJECT-T7Z5-DELTA","PROJECT-K0L4-DELTA","PROJECT-H4S1-DELTA","PROJECT-E9R5-DELTA","PROJECT-H3C7-DELTA","PROJECT-W0L6-DELTA","PROJECT-Y7T9-DELTA","PROJECT-K6V5-DELTA","PROJECT-A6H3-DELTA","PROJECT-V1K7-DELTA","PROJECT-H8O6-DELTA","PROJECT-G5R4-DELTA","PROJECT-V3K5-DELTA","PROJECT-G4U9-DELTA","PROJECT-E6K2-DELTA","PROJECT-H9M1-DELTA","PROJECT-Z2N3-DELTA","PROJECT-H8P2-DELTA","PROJECT-F4N8-DELTA","PROJECT-I9O5-DELTA","PROJECT-M5S7-DELTA","PROJECT-R2F5-DELTA","PROJECT-E6P3-DELTA","PROJECT-F2I7-DELTA","PROJECT-X9T1-DELTA","PROJECT-S2W9-DELTA","PROJECT-E1M6-DELTA","PROJECT-U6A9-DELTA","PROJECT-Z3L7-DELTA","PROJECT-N6W5-DELTA","PROJECT-B6G7-DELTA","PROJECT-B1B1-DELTA","PROJECT-W4B9-DELTA","PROJECT-S1L6-DELTA","PROJECT-S7B9-DELTA","PROJECT-D2T9-DELTA","PROJECT-Z2X4-DELTA","PROJECT-Q3X4-DELTA","PROJECT-J3W3-DELTA","PROJECT-Q8W4-DELTA","PROJECT-J3O7-DELTA","PROJECT-J1B9-DELTA","PROJECT-H5C3-DELTA","PROJECT-P2F6-DELTA","PROJECT-U0I2-DELTA","PROJECT-E6B2-DELTA","PROJECT-D3A3-DELTA","PROJECT-C3G8-DELTA","PROJECT-M3E6-DELTA","PROJECT-W9S2-DELTA","PROJECT-O0K5-DELTA","PROJECT-N4B3-DELTA","PROJECT-J2E9-DELTA","PROJECT-N3Q4-DELTA","PROJECT-W4R8-DELTA","PROJECT-V3Q7-DELTA","PROJECT-C9B3-DELTA","PROJECT-G0G3-DELTA","PROJECT-I4V9-DELTA","PROJECT-V4Y8-DELTA","PROJECT-X5M1-DELTA","PROJECT-P5J0-DELTA","PROJECT-D3X0-DELTA","PROJECT-A3X8-DELTA","PROJECT-C2X4-DELTA","PROJECT-E7G8-DELTA","PROJECT-H9F3-DELTA","PROJECT-G9I8-DELTA","PROJECT-T2D0-DELTA","PROJECT-I5T5-DELTA","PROJECT-M0M4-DELTA","PROJECT-R1R3-DELTA","PROJECT-X6L8-DELTA","PROJECT-C3U0-DELTA","PROJECT-R4L3-DELTA","PROJECT-W6D2-DELTA","PROJECT-R7D9-DELTA","PROJECT-C0S6-DELTA","PROJECT-V9N7-DELTA","PROJECT-Z3P8-DELTA","PROJECT-N5V2-DELTA","PROJECT-F7V6-DELTA","PROJECT-W8H1-DELTA","PROJECT-C3G6-DELTA","PROJECT-C7D4-DELTA","PROJECT-J0C4-DELTA","PROJECT-C9N7-DELTA","PROJECT-L6N9-DELTA","PROJECT-R3W2-DELTA","PROJECT-L9I5-DELTA","PROJECT-C3T8-DELTA","PROJECT-S4T3-DELTA","PROJECT-X9K0-DELTA","PROJECT-W5O2-DELTA","PROJECT-K0W1-DELTA","PROJECT-K7C2-DELTA","PROJECT-J9Y2-DELTA","PROJECT-E7I8-DELTA","PROJECT-E8S6-DELTA","PROJECT-Z1H4-DELTA","PROJECT-K9Z9-DELTA","PROJECT-B0H8-DELTA","PROJECT-W1V1-DELTA","PROJECT-V2G5-DELTA","PROJECT-P5Q3-DELTA","PROJECT-J3N9-DELTA","PROJECT-R8P3-DELTA","PROJECT-N8U8-DELTA","PROJECT-S1J8-DELTA","PROJECT-L7S3-DELTA","PROJECT-Q5L1-DELTA","PROJECT-R8C2-DELTA","PROJECT-A7Y9-DELTA","PROJECT-L3J9-DELTA","PROJECT-I7G9-DELTA","PROJECT-I8K2-DELTA","PROJECT-W0J7-DELTA","PROJECT-K3B9-DELTA","PROJECT-W3M4-DELTA","PROJECT-Z1M6-DELTA","PROJECT-O0C7-DELTA","PROJECT-C0G1-DELTA","PROJECT-Z2O4-DELTA","PROJECT-X8L1-DELTA","PROJECT-S7G5-DELTA","PROJECT-L7E3-DELTA","PROJECT-Q5L3-DELTA","PROJECT-I1K6-DELTA","PROJECT-T6P2-DELTA","PROJECT-R6G0-DELTA","PROJECT-T4V7-DELTA","PROJECT-R6J5-DELTA","PROJECT-B4I1-DELTA","PROJECT-O4K1-DELTA","PROJECT-Y7L9-DELTA","PROJECT-G8X2-DELTA","PROJECT-Q8S5-DELTA","PROJECT-G5M7-DELTA","PROJECT-A7L0-DELTA","PROJECT-P9E7-DELTA","PROJECT-H9B3-DELTA","PROJECT-S0S0-DELTA","PROJECT-W5B1-DELTA","PROJECT-U7D7-DELTA",
        ]

        # Vérifier si le code est valide
        if code in valid_codes:
            if code in premium_data["used_codes"]:
                embed = discord.Embed(
                    title="❌ Code déjà utilisé",
                    description="Ce code premium a déjà été utilisé. Vous ne pouvez pas l'utiliser à nouveau.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return

            if data.get("is_premium", False):
                embed = discord.Embed(
                    title="⚠️ Serveur déjà Premium",
                    description=f"Le serveur **{interaction.guild.name}** est déjà un serveur premium. 🎉",
                    color=discord.Color.yellow()
                )
                embed.add_field(
                    name="Pas de double activation",
                    value="Ce serveur a déjà activé le code premium. Aucun changement nécessaire.",
                    inline=False
                )
                embed.set_footer(text="Merci d'utiliser nos services premium.")
                embed.set_thumbnail(url=interaction.guild.icon.url)
                await interaction.followup.send(embed=embed)
                return

            # Activer le premium
            data["is_premium"] = True
            premium_data["used_codes"].append(code)
            data["setup_premium"] = premium_data

            # ✅ ICI : indentation correcte
            collection2.update_one(
                {"guild_id": interaction.guild.id},
                {
                    "$set": {
                        "guild_name": interaction.guild.name,
                        "is_premium": True,
                        "used_codes": premium_data["used_codes"]
                    }
                },
                upsert=True
            )

            embed = discord.Embed(
                title="✅ Serveur Premium Activé",
                description=f"Le serveur **{interaction.guild.name}** est maintenant premium ! 🎉",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Avantages Premium",
                value="Profitez des fonctionnalités exclusives réservées aux serveurs premium. 🎁",
                inline=False
            )
            embed.set_footer(text="Merci d'utiliser nos services premium.")
            embed.set_thumbnail(url=interaction.guild.icon.url)
            await interaction.followup.send(embed=embed)

        else:
            embed = discord.Embed(
                title="❌ Code Invalide",
                description="Le code que vous avez entré est invalide. Veuillez vérifier votre code ou contactez le support.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Suggestions",
                value="1. Assurez-vous d'avoir saisi le code exactement comme il est fourni.\n"
                      "2. Le code est sensible à la casse.\n"
                      "3. Si vous avez des doutes, contactez le support.",
                inline=False
            )
            embed.add_field(
                name="Code Expiré ?",
                value="Si vous pensez que votre code devrait être valide mais ne l'est pas, il est possible qu'il ait expiré.",
                inline=False
            )
            await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Une erreur est survenue : {str(e)}")


@bot.tree.command(name="viewpremium", description="Voir les serveurs ayant activé le Premium")
async def viewpremium(interaction: discord.Interaction):
    if interaction.user.id != ISEY_ID and not interaction.user.guild_permissions.administrator:
        print("Utilisateur non autorisé.")
        await interaction.response.send_message("❌ Vous n'avez pas les permissions nécessaires.", ephemeral=True)
        return

    # Récupération des serveurs premium
    premium_servers_data = collection2.find({"guild_id": {"$exists": True}})

    premium_list = []
    for server in premium_servers_data:
        guild_name = server.get("guild_name", "❓ Nom inconnu")
        activated_by = server.get("activated_by", "❓ Inconnu")
        activation_date = server.get("activation_date")  # format ISO si possible
        premium_code = server.get("premium_code", "❓ Aucun")

        # Format de date
        try:
            activation_date = datetime.strptime(activation_date, "%Y-%m-%dT%H:%M:%S.%fZ")
            formatted_date = activation_date.strftime("%d %B %Y à %Hh%M")
        except:
            formatted_date = "❓ Date inconnue"

        premium_list.append(
            f"📌 **{guild_name}**\n"
            f"   ┗ 👤 Activé par : `{activated_by}`\n"
            f"   ┗ 🔑 Code : `{premium_code}`\n"
            f"   ┗ 📅 Date : `{formatted_date}`\n"
        )

    if premium_list:
        embed = discord.Embed(
            title="🌟 Liste des Serveurs Premium",
            description="Voici les serveurs ayant activé le **Premium** :\n\n" + "\n".join(premium_list),
            color=discord.Color.gold()
        )
        embed.set_footer(text="Merci à tous pour votre soutien 💖")
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title="🔒 Aucun Serveur Premium",
            description="Aucun serveur n'a encore activé le **Premium** sur ce bot.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Pourquoi devenir premium ? 💎",
            value="Obtenez des **fonctionnalités exclusives**, plus de **personnalisation** et un **support prioritaire** !\n\n"
                  "📬 **Contactez-nous** pour plus d'informations.",
            inline=False
        )
        embed.set_footer(text="Rejoignez le programme Premium dès aujourd'hui ✨")

        # Bouton d'action
        join_button = discord.ui.Button(label="🚀 Rejoindre Premium", style=discord.ButtonStyle.green, url="https://votre-lien-premium.com")

        view = discord.ui.View()
        view.add_item(join_button)

        await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="devenirpremium")
async def devenirpremium(interaction: discord.Interaction):
    if ctx.author.id != ISEY_ID and not ctx.author.guild_permissions.administrator:
        print("Utilisateur non autorisé.")
        await ctx.send("❌ Vous n'avez pas les permissions nécessaires.", ephemeral=True)
        return
    # Charger les données de ce serveur spécifique
    data = load_guild_settings(interaction.guild.id)
    setup_premium_data = data["setup_premium"]

    if setup_premium_data:  # Si le serveur est déjà premium
        embed = discord.Embed(
            title="🎉 Vous êtes déjà Premium !",
            description=f"Le serveur **{interaction.guild.name}** est déjà un serveur Premium ! 🎉",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Avantages Premium",
            value="Profitez déjà des fonctionnalités exclusives réservées aux serveurs premium. 🎁",
            inline=False
        )
        embed.set_footer(text="Merci d'utiliser nos services premium.")
        embed.set_thumbnail(url=interaction.guild.icon.url)  # Icône du serveur
        await interaction.response.send_message(embed=embed)

    else:  # Si le serveur n'est pas encore premium
        embed = discord.Embed(
            title="🚀 Comment devenir Premium ?",
            description=f"Le serveur **{interaction.guild.name}** n'est pas encore premium. Voici comment vous pouvez devenir premium :",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Étapes pour devenir Premium",
            value="1. Entrez votre code premium avec la commande `/premium <votre_code>`.\n"
                  "2. Un message de confirmation vous sera envoyé une fois le serveur activé.\n"
                  "3. Profitez des fonctionnalités exclusives réservées aux serveurs Premium ! 🎁",
            inline=False
        )
        embed.add_field(
            name="Pourquoi devenir Premium ?",
            value="Les serveurs premium ont accès à des fonctionnalités exclusives, plus de personnalisation et des options avancées.",
            inline=False
        )
        embed.set_footer(text="Rejoignez notre programme Premium et profitez des avantages !")
        embed.set_thumbnail(url=interaction.guild.icon.url)  # Icône du serveur
        await interaction.response.send_message(embed=embed)

#------------------------------------------------------------------------- Commande SETUP
class SetupView(View):
    def __init__(self, ctx, guild_data, collection):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.guild_data = guild_data or {}
        self.collection = collection
        self.embed_message = None
        self.add_item(MainSelect(self))

    async def start(self):  # <-- doit être alignée avec __init__
        embed = discord.Embed(
            title="⚙️ **Configuration du Serveur**",
            description="""
🎉 **Bienvenue dans le menu de configuration !**  
Personnalisez votre serveur **facilement** grâce aux options ci-dessous.  

📌 **Gestion du Bot** - 🎛️ Modifier les rôles et salons.  
🛡️ **Sécurité & Anti-Raid** - 🚫 Activer/Désactiver les protections.  

🔽 **Sélectionnez une catégorie pour commencer !**
            """,
            color=discord.Color.blurple()
        )

        self.embed_message = await self.ctx.send(embed=embed, view=self)
        print(f"Message initial envoyé: {self.embed_message}")

    async def update_embed(self, category):
        """Met à jour l'embed et rafraîchit dynamiquement le message."""
        embed = discord.Embed(color=discord.Color.blurple(), timestamp=discord.utils.utcnow())
        embed.set_footer(text=f"Serveur : {self.ctx.guild.name}", icon_url=self.ctx.guild.icon.url if self.ctx.guild.icon else None)

        if category == "accueil":
            embed.title = "⚙️ **Configuration du Serveur**"
            embed.description = """
            🎉 **Bienvenue dans le menu de configuration !**  
            Personnalisez votre serveur **facilement** grâce aux options ci-dessous.  

            📌 **Gestion du Bot** - 🎛️ Modifier les rôles et salons.  
            🛡️ **Sécurité & Anti-Raid** - 🚫 Activer/Désactiver les protections.  

            🔽 **Sélectionnez une catégorie pour commencer !**
            """
            self.clear_items()
            self.add_item(MainSelect(self))

        elif category == "gestion":
            print("✅ Entrée dans update_embed pour 'gestion'")
            # ⬇️ Ajoute ce debug ici
            print("DEBUG owner:", self.guild_data.get('owner'))
            embed.title = "⚙️ **Gestion du Bot**"
            try:
                embed.add_field(name="⚙️ Préfixe actuel :", value=f"`{self.guild_data.get('prefix', '+')}`", inline=False)
                embed.add_field(name="👑 Propriétaire :", value=format_mention(self.guild_data.get('owner', 'Non défini'), "user"), inline=False)
                embed.add_field(name="🛡️ Rôle Admin :", value=format_mention(self.guild_data.get('admin_role', 'Non défini'), "role"), inline=False)
                embed.add_field(name="👥 Rôle Staff :", value=format_mention(self.guild_data.get('staff_role', 'Non défini'), "role"), inline=False)
                embed.add_field(name="🚨 Salon Sanctions :", value=format_mention(self.guild_data.get('sanctions_channel', 'Non défini'), "channel"), inline=False)
                embed.add_field(name="📝 Salon Alerte :", value=format_mention(self.guild_data.get('reports_channel', 'Non défini'), "channel"), inline=False)
            except Exception as e:
                print(f"❌ Erreur dans ajout des champs embed 'gestion' : {e}")
                traceback.print_exc()

            self.clear_items()
            self.add_item(InfoSelect(self))
            self.add_item(ReturnButton(self))

        elif category == "anti":
            embed.title = "🛡️ **Sécurité & Anti-Raid**"
            embed.description = "⚠️ **Gérez les protections du serveur contre les abus et le spam.**\n🔽 **Sélectionnez une protection à activer/désactiver. Pour des protections supplémentaires, effectuez la commande +protection !**"
            embed.add_field(name="🔗 Anti-lien :", value=f"{'✅ Activé' if self.guild_data.get('anti_link', False) else '❌ Désactivé'}", inline=True)
            embed.add_field(name="💬 Anti-Spam :", value=f"{'✅ Activé' if self.guild_data.get('anti_spam', False) else '❌ Désactivé'}", inline=True)
            embed.add_field(name="🚫 Anti-Everyone :", value=f"{'✅ Activé' if self.guild_data.get('anti_everyone', False) else '❌ Désactivé'}", inline=True)

            self.clear_items()
            self.add_item(AntiSelect(self))
            self.add_item(ReturnButton(self))

        # Enfin, éditer le message
        if self.embed_message:
            try:
                await self.embed_message.edit(embed=embed, view=self)
                print(f"Embed mis à jour pour la catégorie: {category}")
            except Exception as e:
                print(f"Erreur lors de la mise à jour de l'embed: {e}")
        else:
            print("Erreur : embed_message est nul ou non défini.")

    async def notify_guild_owner(self, interaction, param, new_value):
        guild_owner = interaction.guild.owner  # Récupère l'owner du serveur
        if guild_owner:  # Vérifie si le propriétaire existe
            embed = discord.Embed(
                title="🔔 **Mise à jour de la configuration**",
                description=f"⚙️ **Une modification a été effectuée sur votre serveur `{interaction.guild.name}`.**",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="👤 **Modifié par**", value=interaction.user.mention, inline=True)
            embed.add_field(name="🔧 **Paramètre modifié**", value=f"`{param}`", inline=True)
            embed.add_field(name="🆕 **Nouvelle valeur**", value=f"{new_value}", inline=False)
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed.set_footer(text="Pensez à vérifier la configuration si nécessaire.")

            try:
                # Envoie de l'embed au propriétaire
                await guild_owner.send(embed=embed)
                print(f"Message privé envoyé au propriétaire {guild_owner.name}.")  # Log pour confirmer l'envoi

            except discord.Forbidden:
                print(f"⚠️ Impossible d'envoyer un MP au propriétaire du serveur {interaction.guild.name}.")  # Log si l'envoi échoue

                # Tentons d'envoyer un message simple au propriétaire pour tester la permission
                try:
                    await guild_owner.send("Test : Le bot essaie de vous envoyer un message privé.")
                    print("Le message de test a été envoyé avec succès.")
                except discord.Forbidden:
                    print("⚠️ Le message de test a échoué. Le problème vient probablement des paramètres de confidentialité du propriétaire.")

                # Avertir l'utilisateur via le suivi
                await interaction.followup.send(
                    "⚠️ **Impossible d'envoyer un message privé au propriétaire du serveur.**",
                    ephemeral=True
                )

def format_mention(id, type_mention):
    if not id or id == "Non défini":
        return "❌ **Non défini**"

    # Cas où c’est un int ou une string d’ID valide
    if isinstance(id, int) or (isinstance(id, str) and id.isdigit()):
        if type_mention == "user":
            return f"<@{id}>"
        elif type_mention == "role":
            return f"<@&{id}>"
        elif type_mention == "channel":
            return f"<#{id}>"
        return "❌ **Mention invalide**"

    # Cas spécial : objet discord.Message
    if isinstance(id, discord.Message):
        try:
            author_mention = id.author.mention if hasattr(id, 'author') else "Auteur inconnu"
            channel_mention = id.channel.mention if hasattr(id, 'channel') else "Salon inconnu"
            return f"**{author_mention}** dans **{channel_mention}**"
        except Exception as e:
            print(f"Erreur formatage Message : {e}")
            return "❌ **Erreur formatage message**"

    # Cas inconnu
    print(f"⚠️ format_mention: type inattendu pour id = {id} ({type(id)})")
    return "❌ **Format invalide**"

class MainSelect(Select):
    def __init__(self, view):
        options = [
            discord.SelectOption(label="⚙️ Gestion du Bot", description="Modifier les rôles et salons", value="gestion"),
            discord.SelectOption(label="🛡️ Sécurité & Anti-Raid", description="Configurer les protections", value="anti")
        ]
        super().__init__(placeholder="📌 Sélectionnez une catégorie", options=options)
        self.view_ctx = view

    async def callback(self, interaction: discord.Interaction):
        print("Interaction reçue.")  # Debug: Vérifie si l'interaction est reçue
        await interaction.response.defer()  # Avertir Discord que la réponse est en cours

        # Vérification de view_ctx avant d'appeler la mise à jour
        if hasattr(self.view_ctx, 'update_embed'):
            await self.view_ctx.update_embed(self.values[0])  # Mettre à jour l'embed selon le choix de l'utilisateur
            print(f"Embed mis à jour avec la catégorie: {self.values[0]}")
        else:
            print("Erreur: view_ctx n'a pas la méthode update_embed.")

class ReturnButton(Button):
    def __init__(self, view):
        super().__init__(style=discord.ButtonStyle.danger, label="🔙 Retour", custom_id="return")
        self.view_ctx = view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.view_ctx.update_embed("accueil")

class InfoSelect(Select):
    def __init__(self, view):
        options = [
            discord.SelectOption(label="⚙️ Modifier le préfixe", value="prefix"),
            discord.SelectOption(label="👑 Propriétaire", value="owner"),
            discord.SelectOption(label="🛡️ Rôle Admin", value="admin_role"),
            discord.SelectOption(label="👥 Rôle Staff", value="staff_role"),
            discord.SelectOption(label="🚨 Salon Sanctions", value="sanctions_channel"),
            discord.SelectOption(label="📝 Salon Alerte", value="reports_channel"),
        ]
        super().__init__(placeholder="🎛️ Sélectionnez un paramètre à modifier", options=options)
        self.view_ctx = view

    async def callback(self, interaction: discord.Interaction):
        param = self.values[0]

        if param == "prefix":
            # Si l'utilisateur veut modifier le préfixe, demandez un nouveau préfixe
            embed_request = discord.Embed(
                title="✏️ **Modification du Préfixe du Bot**",
                description="Veuillez entrer le **nouveau préfixe** pour le bot.",
                color=discord.Color.blurple(),
                timestamp=discord.utils.utcnow()
            )
            embed_request.set_footer(text="Répondez dans les 60 secondes.")
            await interaction.response.send_message(embed=embed_request, ephemeral=True)

            def check(msg):
                return msg.author == self.view_ctx.ctx.author and msg.channel == self.view_ctx.ctx.channel

            try:
                response = await self.view_ctx.ctx.bot.wait_for("message", check=check, timeout=60)
                await response.delete()  # Supprimer la réponse de l'utilisateur après réception
            except asyncio.TimeoutError:
                embed_timeout = discord.Embed(
                    title="⏳ **Temps écoulé**",
                    description="Aucune modification effectuée.",
                    color=discord.Color.red()
                )
                return await interaction.followup.send(embed=embed_timeout, ephemeral=True)

            new_value = response.content.strip()

            if new_value:
                # Mettez à jour la collection avec le nouveau préfixe
                self.view_ctx.collection.update_one(
                    {"guild_id": str(self.view_ctx.ctx.guild.id)},
                    {"$set": {"prefix": new_value}},
                    upsert=True
                )
                self.view_ctx.guild_data["prefix"] = new_value

                # Notifier le propriétaire du serveur de la modification
                await self.view_ctx.notify_guild_owner(interaction, "prefix", new_value)

                # Embed de confirmation
                embed_success = discord.Embed(
                    title="✅ **Modification enregistrée !**",
                    description=f"Le préfixe a été mis à jour avec succès.",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                embed_success.add_field(name="🆕 Nouveau préfixe :", value=f"`{new_value}`", inline=False)
                embed_success.set_footer(text=f"Modifié par {interaction.user.display_name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

                await interaction.followup.send(embed=embed_success, ephemeral=True)
                await self.view_ctx.update_embed("gestion")
            else:
                embed_error = discord.Embed(
                    title="❌ **Erreur de saisie**",
                    description="Le préfixe fourni est invalide. Veuillez réessayer avec un préfixe valide.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed_error, ephemeral=True)

        else:
            # Pour les autres paramètres (comme le propriétaire, les rôles, etc.)
            embed_request = discord.Embed(
                title="✏️ **Modification du paramètre**",
                description=f"Veuillez mentionner la **nouvelle valeur** pour `{param}`.\n"
                            f"*(Mentionnez un **rôle**, un **salon** ou un **utilisateur** si nécessaire !)*",
                color=discord.Color.blurple(),
                timestamp=discord.utils.utcnow()
            )
            embed_request.set_footer(text="Répondez dans les 60 secondes.")

            await interaction.response.send_message(embed=embed_request, ephemeral=True)

            def check(msg):
                return msg.author == self.view_ctx.ctx.author and msg.channel == self.view_ctx.ctx.channel

            try:
                response = await self.view_ctx.ctx.bot.wait_for("message", check=check, timeout=60)
                await response.delete()
            except asyncio.TimeoutError:
                embed_timeout = discord.Embed(
                    title="⏳ **Temps écoulé**",
                    description="Aucune modification effectuée.",
                    color=discord.Color.red()
                )
                return await interaction.followup.send(embed=embed_timeout, ephemeral=True)

            new_value = None

            if param == "owner":
                new_value = response.mentions[0].id if response.mentions else None
            elif param in ["admin_role", "staff_role"]:
                new_value = response.role_mentions[0].id if response.role_mentions else None
            elif param in ["sanctions_channel", "reports_channel","suggestion_channel","sondage_channel","presentation_channel"]:
                new_value = response.channel_mentions[0].id if response.channel_mentions else None

            if new_value:
                self.view_ctx.collection.update_one(
                    {"guild_id": str(self.view_ctx.ctx.guild.id)},
                    {"$set": {param: str(new_value)}},
                    upsert=True
                )
                self.view_ctx.guild_data[param] = str(new_value)

                # ✅ Notification au propriétaire du serveur
                await self.view_ctx.notify_guild_owner(interaction, param, new_value)

                # ✅ Embed de confirmation
                embed_success = discord.Embed(
                    title="✅ **Modification enregistrée !**",
                    description=f"Le paramètre `{param}` a été mis à jour avec succès.",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                embed_success.add_field(name="🆕 Nouvelle valeur :", value=f"<@{new_value}>" if param == "owner" else f"<@&{new_value}>" if "role" in param else f"<#{new_value}>", inline=False)
                embed_success.set_footer(text=f"Modifié par {interaction.user.display_name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

                await interaction.followup.send(embed=embed_success, ephemeral=True)
                await self.view_ctx.update_embed("gestion")
            else:
                embed_error = discord.Embed(
                    title="❌ **Erreur de saisie**",
                    description="La valeur mentionnée est invalide. Veuillez réessayer en mentionnant un rôle, un salon ou un utilisateur valide.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed_error, ephemeral=True)

class AntiSelect(Select):
    def __init__(self, view):
        options = [
            discord.SelectOption(label="🔗 Anti-lien", value="anti_link"),
            discord.SelectOption(label="💬 Anti-Spam", value="anti_spam"),
            discord.SelectOption(label="🚫 Anti-Everyone", value="anti_everyone"),
        ]
        super().__init__(placeholder="🛑 Sélectionnez une protection à configurer", options=options)
        self.view_ctx = view

    async def callback(self, interaction: discord.Interaction):
        print(f"Interaction received: {interaction}")  # ✅ Ajouté pour afficher l'interaction
        await interaction.response.defer(thinking=True)

        try:
            print(f"AntiSelect callback started. Values: {self.values}")  # Log des valeurs envoyées
            param = self.values[0]

            embed_request = discord.Embed(
                title="⚙️ **Modification d'une protection**",
                description=f"🛑 **Protection sélectionnée :** `{param}`\n\n"
                            "Tapez :\n"
                            "✅ `true` pour **activer**\n"
                            "❌ `false` pour **désactiver**\n"
                            "🚫 `cancel` pour **annuler**",
                color=discord.Color.blurple(),
                timestamp=discord.utils.utcnow()
            )
            embed_request.set_footer(text="Répondez dans les 60 secondes.")

            await interaction.followup.send(embed=embed_request, ephemeral=True)
        except Exception as e:
            print(f"Erreur dans AntiSelect: {e}")
            traceback.print_exc()
            await interaction.followup.send("❌ Une erreur s'est produite.", ephemeral=True)

        def check(msg):
            return msg.author == self.view_ctx.ctx.author and msg.channel == self.view_ctx.ctx.channel

        try:
            response = await self.view_ctx.ctx.bot.wait_for("message", check=check, timeout=60)
            await response.delete()
        except asyncio.TimeoutError:
            embed_timeout = discord.Embed(
                title="⏳ Temps écoulé",
                description="Aucune réponse reçue. L'opération a été annulée.",
                color=discord.Color.red()
            )
            return await interaction.followup.send(embed=embed_timeout, ephemeral=True)

        response_content = response.content.lower()

        if response.content.lower() == "cancel":
            embed_cancel = discord.Embed(
                title="🚫 Annulé",
                description="Aucune modification n’a été faite.",
                color=discord.Color.orange()
            )
            return await interaction.followup.send(embed=embed_cancel, ephemeral=True)

        elif response.content.lower() in ["true", "false"]:
            value = response.content.lower() == "true"

            self.view_ctx.collection.update_one(
                {"guild_id": str(self.view_ctx.ctx.guild.id)},
                {"$set": {param: value}},
                upsert=True
            )
            self.view_ctx.guild_data[param] = value

            embed_success = discord.Embed(
                title="✅ Protection mise à jour",
                description=f"La protection `{param}` est maintenant {'activée ✅' if value else 'désactivée ❌'}.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed_success, ephemeral=True)

            # Mettre à jour l'affichage
            await self.view_ctx.update_embed("anti")
        else:
            embed_error = discord.Embed(
                title="❌ Entrée invalide",
                description="Veuillez répondre par `true`, `false` ou `cancel`.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed_error, ephemeral=True)

        new_value = response_content == "true"

        self.view_ctx.collection.update_one(
            {"guild_id": str(self.view_ctx.ctx.guild.id)},
            {"$set": {param: new_value}},
            upsert=True
        )

        # ✅ Notification au propriétaire du serveur
        await self.view_ctx.notify_guild_owner(interaction, param, new_value)

        # ✅ Embed de confirmation
        embed_success = discord.Embed(
            title="✅ **Modification enregistrée !**",
            description=f"La protection `{param}` est maintenant **{'activée' if new_value else 'désactivée'}**.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed_success.set_footer(text=f"Modifié par {interaction.user.display_name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

        await interaction.followup.send(embed=embed_success, ephemeral=True)
        await self.view_ctx.update_embed("anti")

@bot.hybrid_command(name="setup", description="Configure le bot pour ce serveur.")
async def setup(ctx):
    print("Commande 'setup' appelée.")  # Log de débogage
    if ctx.author.id != ISEY_ID and not ctx.author.guild_permissions.administrator:
        print("Utilisateur non autorisé.")
        await ctx.send("❌ Vous n'avez pas les permissions nécessaires.", ephemeral=True)
        return

    guild_data = collection.find_one({"guild_id": str(ctx.guild.id)}) or {}

    embed = discord.Embed(
        title="⚙️ **Configuration du Serveur**",
        description="""
        🔧 **Bienvenue dans le setup !**  
        Configurez votre serveur facilement en quelques clics !  

        📌 **Gestion du Bot** - 🎛️ Modifier les rôles et salons.  
        🛡️ **Sécurité & Anti-Raid** - 🚫 Activer/Désactiver les protections.  

        🔽 **Sélectionnez une option pour commencer !**
        """,
        color=discord.Color.blurple()
    )

    print("Embed créé, envoi en cours...")
    view = SetupView(ctx, guild_data, collection)
    await view.start()  # ✅ appelle la méthode start(), qui envoie le message et stocke embed_message
    print("Message d'embed envoyé.")
#------------------------------------------------------------------------ Super Protection:
# Fonction pour créer un embed de protection avec une mise en page améliorée
def create_protection_embed(protection_data):
    embed = discord.Embed(
        title="🛡️ **Sécurité du Serveur**",
        description="Personnalisez les systèmes de protection de votre serveur Discord. "
                    "Utilisez le menu déroulant ci-dessous pour activer ou désactiver une protection.",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url="https://github.com/Iseyg91/KNSKS-Q/blob/main/BANNER_ETHERYA-topaz.png?raw=true")
    embed.set_author(name="Système de Sécurité Avancée", icon_url="https://github.com/Iseyg91/KNSKS-Q/blob/main/3e3bd3c24e33325c7088f43c1ae0fadc.png?raw=true")

    embed.add_field(
        name="🔄 **Status Global**",
        value="🟢 **Activé** | 🔴 **Désactivé**",
        inline=False
    )

    embed.add_field(
        name="📌 **Protection actuelle**",
        value="Les protections actuelles de votre serveur sont affichées ci-dessous. "
              "Sélectionnez celle que vous souhaitez modifier.",
        inline=False
    )

    # Affichage de chaque protection sans doublon d'état
    for label, value in get_protection_options().items():
        protection_status = protection_data.get(value, "off").lower()
        status = "🟢 Activé" if protection_status == "on" else "🔴 Désactivé"
        
        embed.add_field(
            name=f"{label} {get_protection_icon(value)}",
            value=f"État : {status}\n🔧 Cliquez dans le menu ci-dessous pour changer ce paramètre.",
            inline=False
        )

    embed.set_footer(text="Dernière mise à jour automatique lors de l'interaction utilisateur.")
    return embed

# Retourne l'icône correspondante à chaque protection
def get_protection_icon(protection_key):
    icon_map = {
        "anti_massban": "⚔️",
        "anti_masskick": "👢",
        "anti_bot": "🤖",
        "anti_createchannel": "📂",
        "anti_deletechannel": "❌",
        "anti_createrole": "🎭",
        "anti_deleterole": "🛡️",
        "whitelist": "🔑"
    }
    return icon_map.get(protection_key, "🔒")

# Fonction pour récupérer les données de protection depuis la base de données
async def get_protection_data(guild_id):
    try:
        data = await collection4.find_one({"_id": str(guild_id)})

        if not data:
            # Crée un document avec des valeurs par défaut si aucune donnée n'existe
            data = create_default_protection_data(guild_id)
            await collection4.insert_one(data)
            print(f"Document créé pour le guild_id {guild_id} avec les valeurs par défaut.")
        
        return data
    except Exception as e:
        print(f"Erreur lors de la récupération des données de protection pour le guild_id {guild_id}: {e}")
        return {}

def create_default_protection_data(guild_id):
    return {
        "_id": str(guild_id),
        "anti_massban": "off",
        "anti_masskick": "off",
        "anti_bot": "off",
        "anti_createchannel": "off",
        "anti_deletechannel": "off",
        "anti_createrole": "off",
        "anti_deleterole": "off",
        "whitelist": [],
        "last_updated": datetime.utcnow()
    }


# Fonction pour mettre à jour les paramètres de protection
async def update_protection(guild_id, field, value, guild, ctx):
    try:
        if value not in ["on", "off"]:
            raise ValueError("La valeur doit être 'on' ou 'off'.")

        # Mise à jour dans la base de données
        result = collection4.update_one(
    {"_id": str(guild_id)},
    {"$set": {field: value, "last_updated": datetime.utcnow()}}
)
        # Vérification si la mise à jour a bien été effectuée
        if result.modified_count == 0:
            print(f"Aucune modification effectuée pour {field} dans le guild_id {guild_id}.")
        else:
            print(f"Modification effectuée avec succès pour {field} dans le guild_id {guild_id}.")

        # Envoi du MP à l'owner du serveur avec un embed
        owner = guild.owner
        if owner:
            embed = discord.Embed(
                title="🔒 **Mise à jour de la protection**",
                description=f"**{ctx.author.name}** a mis à jour une protection sur votre serveur.",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Protection modifiée",
                value=f"**Protection** : {field}\n"
                      f"**Nouvelle valeur** : {value.capitalize()}",
                inline=False
            )
            embed.set_footer(text=f"Serveur : {guild.name} | {guild.id}")
            try:
                await owner.send(embed=embed)
            except discord.Forbidden:
                print(f"Impossible d'envoyer un MP à {owner.name}, permissions insuffisantes.")
            except Exception as e:
                print(f"Erreur lors de l'envoi du MP à l'owner du serveur {guild.id}: {e}")
        
        # Retourne le résultat de l'update
        return result

    except Exception as e:
        print(f"Erreur lors de la mise à jour de {field} pour le guild_id {guild_id}: {e}")
        raise

async def is_authorized(ctx):
    """Vérifie si l'utilisateur a l'autorisation de modifier les protections"""
    if ctx.author.id == ISEY_ID or ctx.author.guild_permissions.administrator:
        return True

    guild_id = str(ctx.guild.id)
    data = await get_protection_data(guild_id)
    if ctx.author.id in data.get("whitelist", []):
        return True

    return False

# Commande principale pour gérer la protection
@bot.command()
async def protection(ctx):
    """Commande principale pour afficher les protections et les modifier"""
    if not await is_authorized(ctx):
        await ctx.send("❌ Vous n'avez pas les permissions nécessaires pour effectuer cette action.", ephemeral=True)
        return

    guild_id = str(ctx.guild.id)
    protection_data = await get_protection_data(guild_id)

    if not protection_data:
        await ctx.send("⚠️ Aucune donnée de protection trouvée. La configuration par défaut a été appliquée.", ephemeral=True)

    embed = create_protection_embed(protection_data)
    await send_select_menu(ctx, embed, protection_data, guild_id)

async def send_select_menu(ctx, embed, protection_data, guild_id):
    try:
        options = [
    discord.SelectOption(label=label, value=value, description="Configurer cette règle de sécurité.")
    for label, value in get_protection_options().items()
]
        select = discord.ui.Select(
            placeholder="🛠️ Sélectionnez une protection à configurer...",
            options=options,
            min_values=1,
            max_values=1
        )

        view = discord.ui.View()
        view.add_item(select)

        async def select_callback(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("❌ Vous n'êtes pas autorisé à utiliser ce menu.", ephemeral=True)
                return

            selected_value = select.values[0]
            current_value = protection_data.get(selected_value, "Off")

            await interaction.response.send_message(
                f"🔍 Protection sélectionnée : `{selected_value}`\n"
                f"🔒 État actuel : **{current_value.capitalize()}**\n\n"
                "🟢 Tapez `on` pour activer\n🔴 Tapez `off` pour désactiver",
                ephemeral=True
            )

            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel

            try:
                msg = await bot.wait_for("message", check=check, timeout=60.0)
                new_value = msg.content.lower()

                if new_value not in ["on", "off"]:
                    await interaction.followup.send("❌ Valeur invalide. Veuillez entrer `on` ou `off`.", ephemeral=True)
                    return

                # ✅ Ligne de mise à jour
                await update_protection(guild_id, selected_value, new_value, ctx.guild, ctx)

                # 🗑️ On supprime le message utilisateur pour garder le salon propre
                await msg.delete()

                # 🔄 On recharge les données et on met à jour l'embed
                updated_data = await get_protection_data(guild_id)
                updated_embed = create_protection_embed(updated_data)
                await interaction.message.edit(embed=updated_embed, view=view)

                await interaction.followup.send(f"✅ La protection `{selected_value}` a été mise à jour à **{new_value.capitalize()}**.", ephemeral=True)

            except asyncio.TimeoutError:
                await interaction.followup.send("⏳ Temps écoulé. Aucune réponse reçue.", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"❌ Une erreur est survenue : {str(e)}", ephemeral=True)
                print(f"Erreur dans le callback du select : {e}")

        select.callback = select_callback
        await ctx.send(embed=embed, view=view)

    except Exception as e:
        print(f"Erreur dans send_select_menu : {e}")
        await ctx.send(f"❌ Une erreur est survenue : {str(e)}", ephemeral=True)


def get_protection_options():
    return {
        "Anti-bot 🤖": "anti_bot",
        "Anti-massban ⚔️": "anti_massban",
        "Anti-masskick 👢": "anti_masskick",
        "Anti-createchannel 📂": "anti_createchannel",
        "Anti-deletechannel ❌": "anti_deletechannel",
        "Anti-createrole 🎭": "anti_createrole",
        "Anti-deleterole 🛡️": "anti_deleterole",
        "Whitelist 🔑": "whitelist"
    }

#------------------------------------------------------------------------- Code Protection:
# Dictionnaire en mémoire pour stocker les paramètres de protection par guild_id
protection_settings = {}
ban_times = {}  # Dictionnaire pour stocker les temps de bans

# Détection d'un massban (2 bans en moins de 10 secondes)
@bot.event
async def on_member_ban(guild, user):
    guild_id = str(guild.id)
    data = await get_protection_data(guild_id)

    if data.get("anti_massban") == "activer":
        # Vérifier s'il y a déjà eu un ban récent
        if guild.id not in ban_times:
            ban_times[guild.id] = []
        current_time = time.time()
        ban_times[guild.id].append(current_time)
        
        # Nettoyer les anciens bans
        ban_times[guild.id] = [t for t in ban_times[guild.id] if current_time - t < 10]

        # Si 2 bans ont été effectués en moins de 10 secondes
        if len(ban_times[guild.id]) > 2:
            await guild.fetch_ban(user)  # Annuler le ban
            await guild.unban(user)  # Débannir la personne
            await guild.text_channels[0].send(f"Le massban a été détecté ! Le ban de {user.name} a été annulé.")
            print(f"Massban détecté pour {user.name}, ban annulé.")
            return

kick_times = defaultdict(list)  # {guild_id: [timestamp1, timestamp2, ...]}

@bot.event
async def on_member_remove(member: discord.Member):
    guild_id = str(member.guild.id)

    # Récupération des logs d'audit pour vérifier si c'était un kick
    if not member.guild.me.guild_permissions.view_audit_log:
        return

    async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
        if entry.target.id == member.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 5:
            # Récupère les données de protection
            protection_data = await get_protection_data(guild_id)
            if protection_data.get("anti_masskick") != "activer":
                return

            author_id = entry.user.id
            current_time = time.time()
            kick_times[author_id].append(current_time)

            # Ne garder que les kicks récents (moins de 10 secondes)
            kick_times[author_id] = [t for t in kick_times[author_id] if current_time - t < 10]

            if len(kick_times[author_id]) >= 2:
                try:
                    # Sanction de l'auteur du masskick (ex: ban)
                    await member.guild.ban(entry.user, reason="Masskick détecté (2 kicks en moins de 10s)")
                    await member.guild.system_channel.send(f"⚠️ **Masskick détecté !** {entry.user.mention} a été banni pour avoir expulsé plusieurs membres en peu de temps.")
                except Exception as e:
                    print(f"[Erreur Masskick] : {e}")

# Protection anti-création de salon
@bot.event
async def on_guild_channel_create(channel):
    guild_id = str(channel.guild.id)
    protection_data = await get_protection_data(guild_id)

    if protection_data.get("anti_createchannel") == "activer":
        # S’assurer que le bot a bien les permissions de gérer les salons
        if channel.guild.me.guild_permissions.manage_channels:
            await channel.delete(reason="Protection anti-création de salon activée.")
            print(f"Le salon {channel.name} a été supprimé à cause de la protection.")
        else:
            print("Le bot n'a pas la permission de gérer les salons.")

# Protection anti-suppression de salon
@bot.event
async def on_guild_channel_delete(channel):
    guild_id = str(channel.guild.id)
    protection_data = await get_protection_data(guild_id)

    if protection_data.get("anti_deletechannel") == "activer":
        try:
            await channel.guild.create_text_channel(channel.name, category=channel.category)
            print(f"Le salon {channel.name} a été recréé suite à la suppression (protection activée).")
        except Exception as e:
            print(f"Erreur lors de la recréation du salon : {e}")

# Protection anti-création de rôle
@bot.event
async def on_guild_role_create(role):
    guild_id = str(role.guild.id)
    protection_data = await get_protection_data(guild_id)

    if protection_data.get("anti_createrole") == "activer":
        try:
            await role.delete(reason="Protection anti-création de rôle activée.")
            print(f"Le rôle {role.name} a été supprimé à cause de la protection.")
        except Exception as e:
            print(f"Erreur lors de la suppression du rôle : {e}")

# Protection anti-suppression de rôle
@bot.event
async def on_guild_role_delete(role):
    guild_id = str(role.guild.id)
    protection_data = await get_protection_data(guild_id)

    if protection_data.get("anti_deleterole") == "activer":
        try:
            await role.guild.create_role(name=role.name, permissions=role.permissions, color=role.color)
            print(f"Le rôle {role.name} a été recréé suite à la suppression (protection activée).")
        except Exception as e:
            print(f"Erreur lors de la recréation du rôle : {e}")
#------------------------------------------------------------------------- wl:

@bot.command()
async def addwl(ctx, member: discord.Member):
    try:
        if ctx.author.id != ISEY_ID:
            return await ctx.send("Tu n'es pas autorisé à utiliser cette commande.")
        
        guild_id = str(ctx.guild.id)
        data = await get_protection_data(guild_id)

        if "whitelist" not in data:
            data["whitelist"] = []  # Assurer qu'il existe une clé "whitelist"

        if member.id not in data["whitelist"]:
            data["whitelist"].append(member.id)
            await update_protection(guild_id, "whitelist", data["whitelist"])
            await ctx.send(f"{member} a été ajouté à la whitelist.")
        else:
            await ctx.send(f"{member} est déjà dans la whitelist.")
    
    except Exception as e:
        # Log l'erreur pour aider à diagnostiquer le problème
        print(f"Erreur dans la commande addwl : {e}")
        await ctx.send("Une erreur est survenue lors de l'ajout à la whitelist.")


@bot.command()
async def removewl(ctx, member: discord.Member):
    if ctx.author.id != ISEY_ID:
        return await ctx.send("Tu n'es pas autorisé à utiliser cette commande.")

    guild_id = str(ctx.guild.id)
    data = await get_protection_data(guild_id)

    if member.id in data.get("whitelist", []):
        data["whitelist"].remove(member.id)
        await update_protection(guild_id, "whitelist", data["whitelist"])
        await ctx.send(f"{member} a été retiré de la whitelist.")
    else:
        await ctx.send(f"{member} n'est pas dans la whitelist.")

@bot.command()
async def listwl(ctx):
    if ctx.author.id != ISEY_ID:
        return await ctx.send("Tu n'es pas autorisé à utiliser cette commande.")

    guild_id = str(ctx.guild.id)
    data = await get_protection_data(guild_id)

    whitelist = data.get("whitelist", [])

    if whitelist:
        members = [f"<@{member_id}>" for member_id in whitelist]
        await ctx.send("Membres dans la whitelist :\n" + "\n".join(members))
    else:
        await ctx.send("La whitelist est vide.")

#------------------------------------------------------------------------- Commandes de Bienvenue : Message de Bienvenue + Ghost Ping Join
private_threads = {}  # Stocke les fils privés des nouveaux membres

# Liste des salons à pinguer
salon_ids = [
    1355158116903419997
]

class GuideView(View):
    def __init__(self, thread):
        super().__init__()
        self.thread = thread
        self.message_sent = False  # Variable pour contrôler l'envoi du message

    @discord.ui.button(label="📘 Guide", style=discord.ButtonStyle.success, custom_id="guide_button_unique")
    async def guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.message_sent:  # Empêche l'envoi du message en doublon
            await interaction.response.defer()
            await start_tutorial(self.thread, interaction.user)
            self.message_sent = True

    @discord.ui.button(label="❌ Non merci", style=discord.ButtonStyle.danger, custom_id="no_guide_button_unique")
    async def no_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Fermeture du fil...", ephemeral=True)
        await asyncio.sleep(2)
        await self.thread.delete()

class NextStepView(View):
    def __init__(self, thread):
        super().__init__()
        self.thread = thread

    @discord.ui.button(label="➡️ Passer à la suite", style=discord.ButtonStyle.primary, custom_id="next_button")
    async def next_step(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user = interaction.user

        # Envoi du message privé
        await send_economy_info(user)

        # Envoi du message de confirmation dans le fil privé
        await self.thread.send("📩 Les détails de cette étape ont été envoyés en message privé.")

        # Attente de 2 secondes
        await asyncio.sleep(2)

        # Message d'avertissement avant suppression
        await self.thread.send("🗑️ Ce fil sera supprimé dans quelques instants.")

        # Suppression du fil privé
        await asyncio.sleep(3)
        await self.thread.delete()

async def wait_for_command(thread, user, command):
    def check(msg):
        return msg.channel == thread and msg.author == user and msg.content.startswith(command)

    await thread.send(f"🕒 En attente de `{command}`...")  # Envoi du message d'attente
    await bot.wait_for("message", check=check)  # Attente du message de la commande
    await thread.send("✅ Commande exécutée ! Passons à la suite. 🚀")  # Confirmation après la commande
    await asyncio.sleep(2)  # Pause avant de passer à l'étape suivante

async def start_tutorial(thread, user):
    tutorial_steps = [
        ("💼 **Commande Travail**", "Utilise `!!work` pour gagner un salaire régulièrement !", "!!work"),
        ("💃 **Commande Slut**", "Avec `!!slut`, tente de gagner de l'argent... Mais attention aux risques !", "!!slut"),
        ("🔫 **Commande Crime**", "Besoin de plus de frissons ? `!!crime` te plonge dans des activités illégales !", "!!crime"),
        ("🌿 **Commande Collecte**", "Avec `!!collect`, tu peux ramasser des ressources utiles !", "!!collect"),
        ("📊 **Classement**", "Découvre qui a le plus d'argent en cash avec `!!lb -cash` !", "!!lb -cash"),
        ("🕵️ **Voler un joueur**", "Tente de dérober l'argent d'un autre avec `!!rob @user` !", "!!rob"),
        ("🏦 **Dépôt Bancaire**", "Pense à sécuriser ton argent avec `!!dep all` !", "!!dep all"),
        ("💰 **Solde Bancaire**", "Vérifie ton argent avec `!!bal` !", "!!bal"),
    ]

    for title, desc, cmd in tutorial_steps:
        embed = discord.Embed(title=title, description=desc, color=discord.Color.blue())
        await thread.send(embed=embed)
        await wait_for_command(thread, user, cmd)  # Attente de la commande de l'utilisateur

    # Embed final des jeux
    games_embed = discord.Embed(
        title="🎲 **Autres Commandes de Jeux**",
        description="Découvre encore plus de moyens de t'amuser et gagner des Ezryn Coins !",
        color=discord.Color.gold()
    )
    games_embed.add_field(name="🐔 Cock-Fight", value="`!!cf` - Combat de Poulet !", inline=False)
    games_embed.add_field(name="🃏 Blackjack", value="`!!bj` - Jeux de Carte !", inline=False)
    games_embed.add_field(name="🎰 Slot Machine", value="`!!sm` - Tente un jeu risqué !", inline=False)
    games_embed.add_field(name="🔫 Roulette Russe", value="`!!rr` - Joue avec le destin !", inline=False)
    games_embed.add_field(name="🎡 Roulette", value="`!!roulette` - Fais tourner la roue de la fortune !", inline=False)
    games_embed.set_footer(text="Amuse-toi bien sur Etherya ! 🚀")

    await thread.send(embed=games_embed)
    await thread.send("Clique sur **Passer à la suite** pour découvrir les systèmes impressionnants de notre Economie !", view=NextStepView(thread))

async def send_economy_info(user: discord.Member):
    try:
        economy_embed = discord.Embed(
            title="📌 **Lis ces salons pour optimiser tes gains !**",
            description=(
                "Bienvenue dans l'économie du serveur ! Pour en tirer le meilleur profit, assure-toi de lire ces salons :\n\n"
                "💰 **Comment accéder à l'economie ?**\n➜ <#1355190022047011117>\n\n"
                "📖 **Informations générales**\n➜ <#1355158018517500086>\n\n"
                "💰 **Comment gagner des Coins ?**\n➜ <#1355157853299675247>\n\n"
                "🏦 **Banque de l'Éco 1**\n➜ <#1355158001606066267>\n\n"
                "🏦 **Banque de l'Éco 2**\n➜ <#1355191522252951573>\n\n"
                "🎟️ **Ticket Finances** *(Pose tes questions ici !)*\n➜ <#1355157942005006558>\n\n"
                "📈 **Astuce :** Plus tu en sais, plus tu gagnes ! Alors prends quelques minutes pour lire ces infos. 🚀"
            ),
            color=discord.Color.gold()
        )
        economy_embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1168755764760559637.webp?size=96&quality=lossless")
        economy_embed.set_footer(text="Bon jeu et bons profits ! 💰")

        dm_channel = await user.create_dm()
        await dm_channel.send(embed=economy_embed)
    except discord.Forbidden:
        print(f"Impossible d'envoyer un MP à {user.name} ({user.id})")

# Protection anti-bot (empêche l'ajout de bots)
# Événement lorsqu'un membre rejoint le serveur
@bot.event
async def on_member_join(member):
    guild_id = str(member.guild.id)
    protection_data = protection_settings.get(guild_id, {"whitelist": [], "anti_bot": "Non configuré"})
    whitelist = protection_data.get("whitelist", [])

    # Vérifier si l'utilisateur est dans la whitelist
    if member.id in whitelist:
        return  # L'utilisateur est exempté de la protection

    # Vérifier si la protection anti-bot est activée pour ce serveur
    if protection_data.get("anti_bot") == "activer":
        if member.bot:
            await member.kick(reason="Protection anti-bot activée.")
            print(f"Un bot ({member.name}) a été expulsé pour cause de protection anti-bot.")
        return

    # Le reste du code pour l'ajout d'un membre sur le serveur Etherya
    if member.guild.id != ETHERYA_SERVER_ID:
        return  # Stoppe l'exécution si ce n'est pas Etherya
    
    # Envoi du message de bienvenue
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="<a:fete:1172810362261880873> Bienvenue sur le serveur ! <a:fete:1172810362261880873>",
            description=(
                "*<a:fire:1343873843730579478> Ici, l’économie règne en maître, les alliances se forment, les trahisons éclatent... et ta richesse ne tient qu’à un fil ! <a:fire:1343873843730579478>*\n\n"
                "<:better_scroll:1342376863909285930> **Avant de commencer, prends le temps de lire :**\n\n"
                "- <a:fleche3:1290077283100397672> **<#1355157955804139560>** pour éviter les problèmes dès le départ.\n"
                "- <a:fleche3:1290077283100397672> **<#1355158018517500086>** pour comprendre les bases de l’économie.\n"
                "- <a:fleche3:1290077283100397672> **<#1359949279808061591>** pour savoir ce que tu peux obtenir.\n\n"
                "💡 *Un doute ? Une question ? Ouvre un ticket et le staff t’aidera !*\n\n"
                "**Prépare-toi à bâtir ton empire... ou à tout perdre. Bonne chance ! 🍀**"
            ),
            color=discord.Color.gold()
        )
        embed.set_image(url="https://raw.githubusercontent.com/Cass64/EtheryaBot/main/images_etherya/etheryaBot_banniere.png")
        await channel.send(f"{member.mention}", embed=embed)

    # Envoi du ghost ping une seule fois par salon
    for salon_id in salon_ids:
        salon = bot.get_channel(salon_id)
        if salon:
            try:
                message = await salon.send(f"{member.mention}")
                await message.delete()
            except discord.Forbidden:
                print(f"Le bot n'a pas la permission d'envoyer un message dans {salon.name}.")
            except discord.HTTPException:
                print("Une erreur est survenue lors de l'envoi du message.")
    
    # Création d'un fil privé pour le membre
    channel_id = 1355158120095027220  # Remplace par l'ID du salon souhaité
    channel = bot.get_channel(channel_id)

    if channel and isinstance(channel, discord.TextChannel):
        thread = await channel.create_thread(name=f"🎉 Bienvenue {member.name} !", type=discord.ChannelType.private_thread)
        await thread.add_user(member)
        private_threads[member.id] = thread

        # Embed de bienvenue
        welcome_embed = discord.Embed(
            title="🌌 Bienvenue à Etherya !",
            description=( 
                "Une aventure unique t'attend, entre **économie dynamique**, **stratégies** et **opportunités**. "
                "Prêt à découvrir tout ce que le serveur a à offrir ?"
            ),
            color=discord.Color.blue()
        )
        welcome_embed.set_thumbnail(url=member.avatar.url if member.avatar else bot.user.avatar.url)
        await thread.send(embed=welcome_embed)

        # Embed du guide
        guide_embed = discord.Embed(
            title="📖 Besoin d'un Guide ?",
            description=( 
                "Nous avons préparé un **Guide de l'Économie** pour t'aider à comprendre notre système monétaire et "
                "les différentes façons d'évoluer. Veux-tu le suivre ?"
            ),
            color=discord.Color.gold()
        )
        guide_embed.set_footer(text="Tu peux toujours y accéder plus tard via la commande /guide ! 🚀")
        await thread.send(embed=guide_embed, view=GuideView(thread))  # Envoie le guide immédiatement

@bot.tree.command(name="guide", description="Ouvre un guide personnalisé pour comprendre l'économie du serveur.")
async def guide_command(interaction: discord.Interaction):
    user = interaction.user

    # Vérifie si le serveur est Etherya avant d'exécuter le reste du code
    if interaction.guild.id != ETHERYA_SERVER_ID:
        await interaction.response.send_message("❌ Cette commande est uniquement disponible sur le serveur Etherya.", ephemeral=True)
        return

    # Crée un nouveau thread privé à chaque commande
    channel_id = 1355158120095027220
    channel = bot.get_channel(channel_id)

    if not channel:
        await interaction.response.send_message("❌ Le canal est introuvable ou le bot n'a pas accès à ce salon.", ephemeral=True)
        return

    # Vérifie si le bot peut créer des threads dans ce canal
    if not channel.permissions_for(channel.guild.me).send_messages or not channel.permissions_for(channel.guild.me).manage_threads:
        await interaction.response.send_message("❌ Le bot n'a pas les permissions nécessaires pour créer des threads dans ce canal.", ephemeral=True)
        return

    try:
        # Crée un nouveau thread à chaque fois que la commande est exécutée
        thread = await channel.create_thread(
            name=f"🎉 Bienvenue {user.name} !", 
            type=discord.ChannelType.private_thread,
            invitable=True
        )
        await thread.add_user(user)  # Ajoute l'utilisateur au thread

        # Embed de bienvenue et guide pour un nouveau thread
        welcome_embed = discord.Embed(
            title="🌌 Bienvenue à Etherya !",
            description="Une aventure unique t'attend, entre **économie dynamique**, **stratégies** et **opportunités**. "
                        "Prêt à découvrir tout ce que le serveur a à offrir ?",
            color=discord.Color.blue()
        )
        welcome_embed.set_thumbnail(url=user.avatar.url if user.avatar else bot.user.avatar.url)
        await thread.send(embed=welcome_embed)

    except discord.errors.Forbidden:
        await interaction.response.send_message("❌ Le bot n'a pas les permissions nécessaires pour créer un thread privé dans ce canal.", ephemeral=True)
        return

    # Embed du guide
    guide_embed = discord.Embed(
        title="📖 Besoin d'un Guide ?",
        description="Nous avons préparé un **Guide de l'Économie** pour t'aider à comprendre notre système monétaire et "
                    "les différentes façons d'évoluer. Veux-tu le suivre ?",
        color=discord.Color.gold()
    )
    guide_embed.set_footer(text="Tu peux toujours y accéder plus tard via cette commande ! 🚀")
    await thread.send(embed=guide_embed, view=GuideView(thread))  # Envoie le guide avec les boutons

    await interaction.response.send_message("📩 Ton guide personnalisé a été ouvert.", ephemeral=True)

    # IMPORTANT : Permet au bot de continuer à traiter les commandes
    await bot.process_commands(message)
#-------------------------------------------------------------------------- Commandes Liens Etherya: /etherya

@bot.tree.command(name="etherya", description="Obtiens le lien du serveur Etherya !")
async def etherya(interaction: discord.Interaction):
    """Commande slash pour envoyer l'invitation du serveur Etherya"""
    message = (
        "🌟 **[𝑺ץ] 𝑬𝒕𝒉𝒆𝒓𝒚𝒂 !** 🌟\n\n"
        "🍣 ・ Un serveur **Communautaire**\n"
        "🌸 ・ Des membres sympas et qui **sont actifs** !\n"
        "🌋 ・ Des rôles **exclusifs** avec une **boutique** !\n"
        "🎐 ・ **Safe place** & **Un Système Économique développé** !\n"
        "☕ ・ Divers **Salons** pour un divertissement optimal.\n"
        "☁️ ・ Un staff sympa, à l'écoute et qui **recrute** !\n"
        "🔥 ・ Pas convaincu ? Rejoins-nous et vois par toi-même le potentiel de notre serveur !\n\n"
        "🎫 **[Accès direct au serveur Etherya !](https://discord.gg/weX6tKbDta) **\n\n"
        "Rejoins-nous et amuse-toi ! 🎉"
    )

    await interaction.response.send_message(message)
#------------------------------------------------------------------------- Commandes de Gestion : +clear, +nuke, +addrole, +delrole

@bot.command()
async def clear(ctx, amount: int = None):
    # Vérifie si l'utilisateur a la permission de gérer les messages ou s'il est l'ID autorisé
    if ctx.author.id == 792755123587645461 or ctx.author.guild_permissions.manage_messages:
        if amount is None:
            await ctx.send("Merci de préciser un chiffre entre 2 et 100.")
            return
        if amount < 2 or amount > 100:
            await ctx.send("Veuillez spécifier un nombre entre 2 et 100.")
            return

        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f'{len(deleted)} messages supprimés.', delete_after=5)
    else:
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande.")

# Configuration des emojis personnalisables
EMOJIS = {
    "members": "👥",
    "crown": "👑",  # Emoji couronne
    "voice": "🎤",
    "boosts": "🚀"
}

@bot.command()
async def addrole(ctx, user: discord.Member = None, role: discord.Role = None):
    """Ajoute un rôle à un utilisateur."""
    # Vérifie si l'utilisateur a la permission de gérer les rôles
    if ctx.author.id != 792755123587645461 and not ctx.author.guild_permissions.manage_roles:
        await ctx.send("Tu n'as pas les permissions nécessaires pour utiliser cette commande.")
        return

    # Vérifier si les arguments sont bien fournis
    if user is None or role is None:
        await ctx.send("Erreur : veuillez suivre ce format : +addrole @user @rôle")
        return

    try:
        # Ajouter le rôle à l'utilisateur
        await user.add_roles(role)
        await ctx.send(f"{user.mention} a maintenant le rôle {role.name} !")
    except discord.Forbidden:
        await ctx.send("Je n'ai pas les permissions nécessaires pour attribuer ce rôle.")
    except discord.HTTPException as e:
        await ctx.send(f"Une erreur est survenue : {e}")
    
@bot.command()
async def delrole(ctx, user: discord.Member = None, role: discord.Role = None):
    """Retire un rôle à un utilisateur."""
    # Vérifie si l'utilisateur a la permission de gérer les rôles
    if ctx.author.id != 792755123587645461 and not ctx.author.guild_permissions.manage_roles:
        await ctx.send("Tu n'as pas les permissions nécessaires pour utiliser cette commande.")
        return

    # Vérifier si les arguments sont bien fournis
    if user is None or role is None:
        await ctx.send("Erreur : veuillez suivre ce format : +delrole @user @rôle")
        return

    try:
        # Retirer le rôle à l'utilisateur
        await user.remove_roles(role)
        await ctx.send(f"{user.mention} n'a plus le rôle {role.name} !")
    except discord.Forbidden:
        await ctx.send("Je n'ai pas les permissions nécessaires pour retirer ce rôle.")
    except discord.HTTPException as e:
        await ctx.send(f"Une erreur est survenue : {e}")

# Vérifie si l'utilisateur a la permission de gérer les rôles ou l'ID correct
def has_permission(ctx):
    return any(role.id == ISEY_ID for role in ctx.author.roles) or ctx.author.guild_permissions.manage_roles

# Vérifie si l'utilisateur a la permission de gérer les rôles ou l'ID correct
def has_permission(ctx):
    # Vérifie si l'utilisateur a l'ID de permission ou la permission "Gérer les rôles"
    return any(role.id == ISEY_ID for role in ctx.author.roles) or ctx.author.guild_permissions.manage_roles

# Vérifie si l'utilisateur a la permission de gérer les rôles ou l'ID correct
def has_permission(ctx):
    # Vérifie si l'utilisateur a l'ID de permission ou la permission "Gérer les rôles"
    return any(role.id == ISEY_ID for role in ctx.author.roles) or ctx.author.guild_permissions.manage_roles

# Vérifie si l'utilisateur a la permission de gérer les rôles ou l'ID correct
def has_permission(ctx):
    # Vérifie si l'utilisateur a l'ID de permission ou la permission "Gérer les rôles"
    return any(role.id == ISEY_ID for role in ctx.author.roles) or ctx.author.guild_permissions.manage_roles

def has_permission(ctx, perm=None):
    # Exemple d'une fonction de vérification de permissions
    if perm is None:
        perm = "admin"  # Par défaut, on suppose que l'admin a la permission
    # Logique pour vérifier la permission, par exemple :
    return ctx.author.permissions_in(ctx.channel).administrator  # Remplace cette logique par celle qui te convient.

@bot.command()
async def massrole(ctx, action: str = None, role: discord.Role = None):
    # Vérifie si les arguments sont présents
    if action is None or role is None:
        return await ctx.send("Erreur : tu dois spécifier l'action ('add' ou 'remove') et le rôle. Exemple : `+massrole add @role` ou `+massrole remove @role`.")

    # Vérifie si l'utilisateur a la permission nécessaire
    if not has_permission(ctx, "admin"):  # Spécifie ici la permission requise
        return await ctx.send("Tu n'as pas les permissions nécessaires pour utiliser cette commande.")

    # Vérifie que l'action soit correcte (add ou remove)
    if action not in ['add', 'remove']:
        return await ctx.send("Erreur : l'action doit être 'add' ou 'remove'.")

    # Action pour ajouter ou retirer le rôle
    for member in ctx.guild.members:
        # S'assurer que ce n'est pas un bot
        if not member.bot:
            try:
                if action == 'add':
                    # Ajoute le rôle à l'utilisateur
                    await member.add_roles(role)
                elif action == 'remove':
                    # Retire le rôle à l'utilisateur
                    await member.remove_roles(role)
                print(f"Le rôle a été {action}é pour {member.name}")
            except discord.DiscordException as e:
                print(f"Erreur avec {member.name}: {e}")

    await ctx.send(f"Le rôle '{role.name}' a été {action} à tous les membres humains du serveur.")

@bot.command()
async def nuke(ctx):
    # Vérifie si l'utilisateur a la permission Administrateur
    if ctx.author.id != 792755123587645461 and not ctx.author.guild_permissions.administrator:
        await ctx.send("Tu n'as pas les permissions nécessaires pour exécuter cette commande.")
        return

    # Vérifie que la commande a été lancée dans un salon texte
    if isinstance(ctx.channel, discord.TextChannel):
        # Récupère le salon actuel
        channel = ctx.channel

        # Sauvegarde les informations du salon
        overwrites = channel.overwrites
        channel_name = channel.name
        category = channel.category
        position = channel.position

        # Récupère l'ID du salon pour le recréer
        guild = channel.guild

        try:
            # Supprime le salon actuel
            await channel.delete()

            # Crée un nouveau salon avec les mêmes permissions, catégorie et position
            new_channel = await guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                category=category
            )

            # Réajuste la position du salon
            await new_channel.edit(position=position)

            # Envoie un message dans le nouveau salon pour confirmer la recréation
            await new_channel.send(
                f"💥 {ctx.author.mention} a **nuké** ce salon. Il a été recréé avec succès."
            )
        except Exception as e:
            await ctx.send(f"Une erreur est survenue lors de la recréation du salon : {e}")
    else:
        await ctx.send("Cette commande doit être utilisée dans un salon texte.")
    # IMPORTANT : Permet au bot de continuer à traiter les commandes
    await bot.process_commands(message)
    
#------------------------------------------------------------------------- Commandes d'aide : +aide, /help
@bot.command()
async def help(ctx):
    banner_url = "https://raw.githubusercontent.com/Cass64/EtheryaBot/refs/heads/main/images_etherya/etheryaBot_banniere.png"  # URL de la bannière
    embed = discord.Embed(
        title="🏡 **Accueil Project : Delta **",
        description=f"Hey, bienvenue {ctx.author.mention} sur la page d'accueil de Project : Delta! 🎉\n\n"
                    "Ici, vous trouverez toutes les informations nécessaires pour gérer et administrer votre serveur efficacement. 🌟",
        color=discord.Color(0x1abc9c)
    )
    embed.set_thumbnail(url=bot.user.avatar.url)
    embed.set_footer(text="Développé avec ❤️ par Iseyg. Merci pour votre soutien !")
    embed.set_image(url=banner_url)  # Ajout de la bannière en bas de l'embed

    # Informations générales
    embed.add_field(name="📚 **Informations**", value=f"• **Mon préfixe** : +\n• **Nombre de commandes** : 70", inline=False)

    # Création du menu déroulant
    select = discord.ui.Select(
        placeholder="Choisissez une catégorie 👇", 
        options=[
            discord.SelectOption(label="Owner Bot", description="👑Commandes pour gèrer le bot", emoji="🎓"),
            discord.SelectOption(label="Configuration du Bot", description="🖇️Commandes pour configurer le bot", emoji="📡"),
            discord.SelectOption(label="Gestion", description="📚 Commandes pour gérer le serveur", emoji="🔧"),
            discord.SelectOption(label="Utilitaire", description="⚙️ Commandes utiles", emoji="🔔"),
            discord.SelectOption(label="Modération", description="⚖️ Commandes Modération", emoji="🔨"),
            discord.SelectOption(label="Bot", description="🤖 Commandes Bot", emoji="🦾"),
            discord.SelectOption(label="Économie", description="💸 Commandes économie", emoji="💰"),
            discord.SelectOption(label="Ludiques", description="🎉 Commandes amusantes pour détendre l'atmosphère et interagir avec les autres.", emoji="🎈"),
            discord.SelectOption(label="Test & Défis", description="🧠Commandes pour testez la personnalité et défiez vos amis avec des jeux et des évaluations.", emoji="🎲"),
            discord.SelectOption(label="Crédits", description="💖 Remerciements et crédits", emoji="🙏")
        ], 
        custom_id="help_select"
    )

    # Définir la méthode pour gérer l'interaction du menu déroulant
    async def on_select(interaction: discord.Interaction):
        category = interaction.data['values'][0]
        new_embed = discord.Embed(color=discord.Color(0x1abc9c))
        new_embed.set_image(url=banner_url)  # Ajout de la bannière dans chaque catégorie
        if category == "Owner Bot":
            new_embed.title = "👑 **Commandes de Gestion du Bot**"
            new_embed.description = "Bienvenue dans la section gestion du bot !"
            new_embed.add_field(name="💥 +shutdown", value="Déconnecte le **bot** ✂️.\n*Pour une action plus drastique en cas de chaos ou d'urgence !*.", inline=False)
            new_embed.add_field(name="🔧 +restart", value="Redémarre le **bot** 📍.\n*À utiliser en cas de mise à jour ou de bug mineur.*", inline=False)
            new_embed.add_field(name="🎈 +serverinfoall", value="Affiche les **informations de tous les serveurs** où le bot est présent.",  inline=False)
            new_embed.set_footer(text="♥️ by Iseyg")
        if category == "Configuration du Bot":
            new_embed.title = "🗃️ **Commandes de Configuration du Bot**"
            new_embed.description = "Bienvenue dans la section configuration du bot !"
            new_embed.add_field(name="⚙️ +setup", value="Lance la **configuration du bot** sur le serveur ⚙️.\n*Permet de personnaliser les paramètres du bot selon les besoins du serveur.*", inline=False)
            new_embed.add_field(name="🛡️ +protection", value="Affiche les **protections disponibles** sur le bot et permet de les **activer ou désactiver** 🛠️.\n*Utile pour gérer les options de sécurité comme l'anti-spam, l'anti-lien, etc.*", inline=False)
            new_embed.add_field(name="🔓 +addwl", value="Ajoute un membre à la **whitelist** pour qu'il soit **ignoré** par les protections du bot 🛡️.\n*Permet d'exempter certains utilisateurs des actions de sécurité comme l'anti-spam ou l'anti-lien.*", inline=False)
            new_embed.add_field(name="❌ +removewl", value="Supprime un membre de la **whitelist** pour qu'il soit de nouveau **sujet aux protections** du bot 🛡️.\n*Utilisé pour réactiver les actions de sécurité contre l'utilisateur.*", inline=False)
            new_embed.add_field(name="🔍 +listwl", value="Affiche la **liste des membres sur la whitelist** du bot 🛡️.\n*Permet de voir quels utilisateurs sont exemptés des protections du bot.*", inline=False)
            new_embed.set_footer(text="♥️ by Iseyg")
        if category == "Gestion":
            new_embed.title = "🔨 **Commandes de Gestion**"
            new_embed.description = "Bienvenue dans la section gestion ! 📊\nCes commandes sont essentielles pour administrer le serveur. Voici un aperçu :"
            new_embed.add_field(name="🔧 +clear (2-100)", value="Supprime des messages dans le salon 📬.\n*Utilisé pour nettoyer un salon ou supprimer un spam.*", inline=False)
            new_embed.add_field(name="💥 +nuke", value="Efface **tous** les messages du salon 🚨.\n*Pour une action plus drastique en cas de chaos ou d'urgence !*.", inline=False)
            new_embed.add_field(name="➕ +addrole @user @rôle", value="Ajoute un rôle à un utilisateur 👤.\n*Pour attribuer des rôles et des privilèges spéciaux aux membres.*", inline=False)
            new_embed.add_field(name="➖ +delrole @user @rôle", value="Retire un rôle à un utilisateur 🚫.\n*Retirer un rôle en cas de sanction ou de changement de statut.*", inline=False)
            new_embed.add_field(name="🔲 /embed", value="Crée un **embed personnalisé** avec du texte, des images et des couleurs 🎨.\n*Pratique pour partager des informations de manière stylée et structurée.*", inline=False)
            new_embed.add_field(name="🚫 +listban", value="Affiche la **liste des membres bannis** du serveur ⚠️.\n*Permet aux admins de voir les bannissements en cours.*", inline=False)
            new_embed.add_field(name="🔓 +unbanall", value="Dé-banni **tous les membres** actuellement bannis du serveur 🔓.\n*Utilisé pour lever les bannissements en masse.*", inline=False)
            new_embed.add_field(name="🎉 +gcreate", value="Crée un **giveaway** (concours) pour offrir des récompenses aux membres 🎁.\n*Permet d'organiser des tirages au sort pour des prix ou des objets.*", inline=False)
            new_embed.add_field(name="⚡ +fastgw", value="Crée un **giveaway rapide** avec une durée courte ⏱️.\n*Idéal pour des concours instantanés avec des récompenses immédiates.*", inline=False)
            new_embed.add_field(name="💎 /premium", value="Entre un **code premium** pour devenir membre **premium** et accéder à des fonctionnalités exclusives ✨.\n*Permet de débloquer des avantages supplémentaires pour améliorer ton expérience.*", inline=False)
            new_embed.add_field(name="🔍 /viewpremium", value="Affiche la **liste des serveurs premium** actuellement actifs 🔑.\n*Permet de voir quels serveurs ont accédé aux avantages premium.*", inline=False)
            new_embed.add_field(name="💎 /devenirpremium", value="Obtiens des **informations** sur la manière de devenir membre **premium** et débloquer des fonctionnalités exclusives ✨.\n*Un guide pour savoir comment accéder à l'expérience premium et ses avantages.*", inline=False)
            new_embed.set_footer(text="♥️ by Iseyg")
        elif category == "Utilitaire":
            new_embed.title = "⚙️ **Commandes Utilitaires**"
            new_embed.description = "Bienvenue dans la section modération ! 🚨\nCes commandes sont conçues pour gérer et contrôler l'activité du serveur, en assurant une expérience sûre et agréable pour tous les membres."
            new_embed.add_field(name="📊 +vc", value="Affiche les statistiques du serveur en temps réel .\n*Suivez l'évolution du serveur en direct !*.", inline=False)
            new_embed.add_field(name="🚨 +alerte @user <reason>", value="Envoie une alerte au staff en cas de comportement inapproprié (insultes, spam, etc.) .\n*Note : Si cette commande est utilisée abusivement, des sanctions sévères seront appliquées !*.", inline=False)
            new_embed.add_field(name="📶 +ping", value="Affiche la latence du bot en millisecondes.", inline=False)
            new_embed.add_field(name="⏳ +uptime", value="Affiche depuis combien de temps le bot est en ligne.", inline=False)
            new_embed.add_field(name="ℹ️ /rôle info <nom_du_rôle>", value="Affiche les informations détaillées sur un rôle spécifique.", inline=False)
            new_embed.add_field(name="ℹ💡 /idée", value="Note une idée ou une chose à faire dans ta liste perso 📝.\n*Parfait pour te rappeler d'un projet, d'une envie ou d'un objectif.*", inline=False)
            new_embed.add_field(name="📋 +listi", value="Affiche la **liste de tes idées notées** 🧾.\n*Utile pour retrouver facilement ce que tu as prévu ou pensé.*", inline=False)
            new_embed.add_field(name="💬 /suggestion", value="Propose une **suggestion ou une idée** pour améliorer **Etherya** ou le **bot** 🛠️.\n*Ton avis compte, alors n’hésite pas à participer à l’évolution du projet.*", inline=False)
            new_embed.add_field(name="📊 /sondage", value="Crée un **sondage** pour obtenir l'avis des membres du serveur 📋.\n*Parfait pour recueillir des retours ou prendre des décisions collectives.*", inline=False)
            new_embed.add_field(name="⏰ /rappel", value="Crée un **rappel personnel** pour ne rien oublier 📅.\n*Tu peux programmer des rappels pour des événements, des tâches ou des objectifs.*", inline=False)
            new_embed.add_field(name="👋 /presentation", value="Présente-toi au serveur et fais connaissance avec les membres 🌟.\n*Une manière sympa de partager tes intérêts et d'en savoir plus sur la communauté.*", inline=False)
            new_embed.add_field(name="🤖 +getbotinfo", value="Affiche des **informations détaillées** sur le bot 🛠️.\n*Comprend des données comme la version, les statistiques et les fonctionnalités du bot.*", inline=False)
            new_embed.add_field(name="👑 +alladmin", value="Affiche la **liste de tous les administrateurs** du serveur 🔑.\n*Utile pour voir les membres avec les privilèges d'administration.*", inline=False)
            new_embed.add_field(name="🔍 +snipe", value="Affiche le **dernier message supprimé** du serveur 🕵️.\n*Permet de récupérer le contenu des messages effacés récemment.*", inline=False)
            new_embed.set_footer(text="♥️ by Iseyg")
        elif category == "Modération":
            new_embed.title = "🔑 **Commandes Modération**"
            new_embed.add_field(name="🚫 +ban @user", value="Exile un membre du serveur pour un comportement inacceptable .\nL'action de bannir un utilisateur est irréversible et est utilisée pour des infractions graves aux règles du serveur.*", inline=False)
            new_embed.add_field(name="🚔 +unban @user", value="Lève le bannissement d'un utilisateur, lui permettant de revenir sur le serveur .\nUnban un utilisateur qui a été banni, après examen du cas et décision du staff..*", inline=False)
            new_embed.add_field(name="⚖️ +mute @user", value="Rend un utilisateur silencieux en l'empêchant de parler pendant un certain temps .\nUtilisé pour punir les membres qui perturbent le serveur par des messages intempestifs ou offensants.", inline=False)
            new_embed.add_field(name="🔓 +unmute @user", value="Annule le silence imposé à un utilisateur et lui redonne la possibilité de communiquer 🔊.\nPermet à un membre de reprendre la parole après une période de mute.", inline=False)
            new_embed.add_field(name="⚠️ +warn @user", value="Avertit un utilisateur pour un comportement problématique ⚠.\nUn moyen de signaler qu'un membre a enfreint une règle mineure, avant de prendre des mesures plus sévères.", inline=False)
            new_embed.add_field(name="🚪 +kick @user", value="Expulse un utilisateur du serveur pour une infraction moins grave .\nUn kick expulse temporairement un membre sans le bannir, pour des violations légères des règles.", inline=False)
            new_embed.set_footer(text="♥️ by Iseyg")
        elif category == "Bot":
            new_embed.title = "🔑 **Commandes Bot**"
            new_embed.add_field(name="🔊 /connect", value="Connecte le **bot à un canal vocal** du serveur 🎤.\n*Permet au bot de rejoindre un salon vocal pour y diffuser de la musique ou d'autres interactions.*", inline=False)
            new_embed.add_field(name="🔴 /disconnect", value="Déconnecte le **bot du canal vocal** 🎤.\n*Permet au bot de quitter un salon vocal après une session musicale ou autre interaction.*", inline=False)
            new_embed.add_field(name="🌐 /etherya", value="Affiche le **lien du serveur Etherya** pour rejoindre la communauté 🚀.\n*Permet d'accéder facilement au serveur Etherya et de rejoindre les discussions et événements.*", inline=False)
            new_embed.set_footer(text="♥️ by Iseyg")
        elif category == "Économie":
            new_embed.title = "⚖️ **Commandes Économie**"
            new_embed.description = "Gérez l’économie et la sécurité du serveur ici ! 💼"
            new_embed.add_field(name="🏰 +prison @user", value="Mets un utilisateur en prison pour taxes impayées.", inline=False)
            new_embed.add_field(name="🚔 +arrestation @user", value="Arrête un utilisateur après un braquage raté.", inline=False)
            new_embed.add_field(name="⚖️ +liberation @user", value="Libère un utilisateur après le paiement des taxes.", inline=False)
            new_embed.add_field(name="🔓 +evasion", value="Permet de s’évader après un braquage raté.", inline=False)
            new_embed.add_field(name="💰 +cautionpayer @user", value="Payez la caution d’un membre emprisonné.", inline=False)
            new_embed.add_field(name="🎫 +ticket_euro_million @user", value="Achetez un ticket Euromillion avec un combiné.", inline=False)
            new_embed.set_footer(text="♥️ by Iseyg")
        elif category == "Ludiques":
            new_embed.title = "🎉 **Commandes de Détente**"
            new_embed.description = "Bienvenue dans la section Détente ! 🎈\nCes commandes sont conçues pour vous amuser et interagir de manière légère et drôle. Profitez-en !"
            new_embed.add_field(name="🤗 +hug @user", value="Envoie un câlin à [membre] avec une image mignonne de câlin.", inline=False)
            new_embed.add_field(name="💥 +slap @user", value="Tu as giflé [membre] avec une image drôle de gifle.", inline=False)
            new_embed.add_field(name="💃 +dance @user", value="[membre] danse avec une animation rigolote.", inline=False)
            new_embed.add_field(name="💘 +flirt @user", value="Vous avez charmé [membre] avec un compliment !", inline=False)
            new_embed.add_field(name="💋 +kiss @user", value="Vous avez embrassé [membre] afin de lui démontrer votre amour !", inline=False)
            new_embed.add_field(name="🤫 +whisper @user [message]", value="[membre] a chuchoté à [ton nom] : [message].", inline=False)
            new_embed.add_field(name="🌟 +blague", value="Envoie une blague aléatoire, comme 'Pourquoi les plongeurs plongent toujours en arrière et jamais en avant ? Parce que sinon ils tombent toujours dans le bateau !'.", inline=False)
            new_embed.add_field(name="🪙 +coinflip", value="Lancez une pièce pour voir si vous gagnez ! \n*Tentez votre chance et découvrez si vous avez un coup de chance.*", inline=False)
            new_embed.add_field(name="🎲 +dice", value="Lancez un dé à 6 faces et voyez votre chance ! \n*Choisissez un numéro entre 1 et 6 et voyez si vous avez tiré le bon!*", inline=False)
            new_embed.add_field(name="🗣️ +say", value="Faites dire quelque chose au bot à la place de vous ! 🗨\n*Lancez votre message et il sera annoncé à tout le serveur !*", inline=False)
            new_embed.set_footer(text="♥️ by Iseyg")
        elif category == "Test & Défis":
            new_embed.title = "🎯 **Commandes de Tests et Défis**"
            new_embed.description = "Bienvenue dans la section Tests et Défis ! 🎲\nIci, vous pouvez évaluer les autres, tester votre compatibilité et relever des défis fun !"
            new_embed.add_field(name="🌈 +gay @user", value="Détermine le taux de gayitude d'un utilisateur .\n*Testez votre ouverture d'esprit !*.", inline=False)
            new_embed.add_field(name="😤 +racist @user", value="Détermine le taux de racisme d'un utilisateur .\n*Un test amusant à faire avec vos amis.*", inline=False)
            new_embed.add_field(name="💘 +love @user", value="Affiche le niveau de compatibilité amoureuse .\n*Testez votre compatibilité avec quelqu'un !*.", inline=False)
            new_embed.add_field(name="🐀 +rat @user", value="Détermine le taux de ratitude d'un utilisateur .\n*Vérifiez qui est le plus ‘rat’ parmi vos amis.*", inline=False)
            new_embed.add_field(name="🍆 +zizi @user", value="Évalue le niveau de zizi de l'utilisateur .\n*Un test ludique pour voir qui a le plus grand ego !*.", inline=False)
            new_embed.add_field(name="🤡 +con @user", value="Détermine le taux de connerie d'un utilisateur .\n*Un test amusant à faire avec vos amis.*", inline=False)
            new_embed.add_field(name="🤪 +fou @user", value="Détermine le taux de folie d'un utilisateur .\n*Testez l'état mental de vos amis !*.", inline=False)
            new_embed.add_field(name="💪 +testo @user", value="Détermine le taux de testostérone d'un utilisateur .\n*Testez la virilité de vos amis !*.", inline=False)
            new_embed.add_field(name="🍑 +libido @user", value="Détermine le taux de libido d'un utilisateur .\n*Testez la chaleur de vos amis sous la couette !*.", inline=False)
            new_embed.add_field(name="🪴 +pfc @user", value="Jouez à Pierre-Feuille-Ciseaux avec un utilisateur ! \n*Choisissez votre coup et voyez si vous gagnez contre votre adversaire !*.", inline=False)
            new_embed.add_field(name="🔫 +gunfight @user", value="Affrontez un autre utilisateur dans un duel de Gunfight ! \n*Acceptez ou refusez le défi et découvrez qui sera le gagnant !*", inline=False)
            new_embed.add_field(name="💀 +kill @user", value="Tuez un autre utilisateur dans un duel de force ! \n*Acceptez ou refusez le défi et découvrez qui sortira vainqueur de cette confrontation!*", inline=False)
            new_embed.add_field(name="🔄 +reverse [texte]", value="Inverser un texte et le partager avec un autre utilisateur ! \n*Lancez un défi pour voir si votre inversion sera correcte !*", inline=False)
            new_embed.add_field(name="⭐ +note @user [note sur 10]", value="Notez un autre utilisateur sur 10 ! \n*Exprimez votre avis sur leur comportement ou performance dans le serveur.*", inline=False)
            new_embed.add_field(name="🎲 +roll", value="Lance un dé pour générer un nombre aléatoire entre 1 et 500 .\n*Essayez votre chance !*.", inline=False)
            new_embed.add_field(name="🥊 +fight @user", value="Lancez un duel avec un autre utilisateur ! \n*Acceptez ou refusez le combat et découvrez qui sera le champion du serveur.*", inline=False)
            new_embed.add_field(name="⚡ +superpouvoir @user", value="Déclenche un super-pouvoir épique pour un utilisateur !\n*Donne un pouvoir aléatoire allant du cool au complètement débile, comme la téléportation, la super vitesse, ou même la création de burgers.*", inline=False)
            new_embed.add_field(name="🌿 +totem @user", value="Découvrez votre animal totem spirituel !\n*Un animal magique et spirituel vous guidera, qu’il soit un loup protecteur ou un poisson rouge distrait. Un résultat épique et amusant !*", inline=False)
            new_embed.add_field(name="🔮 +futur @user", value="Prédit l'avenir d'un utilisateur de manière totalement farfelue !\n*L'avenir peut être aussi improbable qu'un trésor caché rempli de bonbons ou une rencontre avec un extraterrestre amateur de chats.*", inline=False)
            new_embed.add_field(name="👶 +enfant @user @user", value="Crée un enfant aléatoire entre deux utilisateurs !\n*Mélangez les pseudos et les photos de profil des deux utilisateurs pour créer un bébé unique. C'est fun et surprenant !*", inline=False)
            new_embed.add_field(name="🍬 +sucre", value="Affiche le **taux de glycémie** du membre ciblé 🍭.\n*Utile pour suivre les niveaux de sucre des membres du serveur de manière ludique.*", inline=False)
            new_embed.set_footer(text="♥️ by Iseyg")
        elif category == "Crédits":
            new_embed.title = "💖 **Crédits et Remerciements**"
            new_embed.description = """
            Un immense merci à **Iseyg** pour le développement de ce bot incroyable ! 🙏  
            Sans lui, ce bot ne serait rien de plus qu'un concept. Grâce à sa passion, son travail acharné et ses compétences exceptionnelles, ce projet a pris vie et continue de grandir chaque jour. 🚀

            Nous tenons également à exprimer notre gratitude envers **toute la communauté**. 💙  
            Votre soutien constant, vos retours et vos idées font de ce bot ce qu'il est aujourd'hui. Chacun de vous, que ce soit par vos suggestions, vos contributions ou même simplement en utilisant le bot, fait une différence. 

            Merci à **tous les développeurs, contributeurs et membres** qui ont aidé à faire évoluer ce projet et l’ont enrichi avec leurs talents et leurs efforts. 🙌

            Et bien sûr, un grand merci à vous, **utilisateurs**, pour votre enthousiasme et votre confiance. Vous êtes la raison pour laquelle ce bot continue d’évoluer. 🌟

            Restons unis et continuons à faire grandir cette aventure ensemble ! 🌍
            """
            new_embed.set_footer(text="♥️ by Iseyg")

        await interaction.response.edit_message(embed=new_embed)

    select.callback = on_select  # Attacher la fonction de callback à l'élément select

    # Afficher le message avec le menu déroulant
    view = discord.ui.View()
    view.add_item(select)
    
    await ctx.send(embed=embed, view=view)
#------------------------------------------------------------------------- Commandes Fun : Flemme de tout lister
@bot.command()
async def gay(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return
    
    percentage = random.randint(0, 100)
    
    embed = discord.Embed(
        title=f"Analyse de gayitude 🌈", 
        description=f"{member.mention} est gay à **{percentage}%** !\n\n*Le pourcentage varie en fonction des pulsions du membre.*", 
        color=discord.Color.purple()
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} ♥️by Iseyg", icon_url=ctx.author.avatar.url)
    
    await ctx.send(embed=embed)

@bot.command()
async def singe(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return
    
    percentage = random.randint(0, 100)
    
    embed = discord.Embed(
        title=f"Analyse de singe 🐒", 
        description=f"{member.mention} est un singe à **{percentage}%** !\n\n*Le pourcentage varie en fonction de l'énergie primate du membre.*", 
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} 🐵 by Isey", icon_url=ctx.author.avatar.url)
    
    await ctx.send(embed=embed)

@bot.command()
async def racist(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return
    
    percentage = random.randint(0, 100)
    
    embed = discord.Embed(
        title=f"Analyse de racisme 🪄", 
        description=f"{member.mention} est raciste à **{percentage}%** !\n\n*Le pourcentage varie en fonction des pulsions du membre.*", 
        color=discord.Color.purple()
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    
    await ctx.send(embed=embed)

@bot.command()
async def sucre(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return
    
    percentage = random.randint(0, 100)
    
    embed = discord.Embed(
        title=f"Analyse de l'indice glycémique 🍬", 
        description=f"L'indice glycémique de {member.mention} est de **{percentage}%** !\n\n*Le pourcentage varie en fonction des habitudes alimentaires de la personne.*", 
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} 🍏by Iseyg", icon_url=ctx.author.avatar.url)
    
    await ctx.send(embed=embed)

@bot.command()
async def love(ctx, member: discord.Member = None):
    if not member:
        await ctx.send("Tu n'as pas mentionné de membre ! Utilise +love @membre.")
        return
    
    love_percentage = random.randint(0, 100)
    
    embed = discord.Embed(
        title="L'Amour Etheryen",
        description=f"L'amour entre {ctx.author.mention} et {member.mention} est de **{love_percentage}%** !",
        color=discord.Color.red() if love_percentage > 50 else discord.Color.blue()
    )
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    embed.set_thumbnail(url="https://img.freepik.com/photos-gratuite/silhouette-mains-coeur-contre-lumieres-ville-nuit_23-2150984259.jpg?ga=GA1.1.719997987.1741155829&semt=ais_hybrid")

    await ctx.send(embed=embed)

@bot.command()
async def rat(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return
    
    percentage = random.randint(0, 100)
    
    embed = discord.Embed(
        title=f"Analyse de radinerie 🐁", 
        description=f"{member.mention} est un rat à **{percentage}%** !\n\n*Le pourcentage varie en fonction des actes du membre.*", 
        color=discord.Color.purple()
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    
    await ctx.send(embed=embed)

@bot.command()
async def con(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return
    
    percentage = random.randint(0, 100)
    
    embed = discord.Embed(
        title="Analyse de connerie 🤡",
        description=f"{member.mention} est con à **{percentage}%** !\n\n*Le pourcentage varie en fonction des neurones actifs du membre.*",
        color=discord.Color.red()
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    
    await ctx.send(embed=embed)

@bot.command()
async def libido(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return
    
    percentage = random.randint(0, 100)
    
    embed = discord.Embed(
        title="Analyse de libido 🔥",
        description=f"{member.mention} a une libido à **{percentage}%** !\n\n*Le pourcentage varie en fonction de l'humeur et du climat.*",
        color=discord.Color.red()
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    
    await ctx.send(embed=embed)

# ID du rôle requis
role_id = 1166113718602575892

# Définir la commande +roll
@bot.command()
async def roll(ctx, x: str = None):
    # Vérifier si l'utilisateur a le rôle requis
    if role_id not in [role.id for role in ctx.author.roles]:
        embed = discord.Embed(
            title="Erreur",
            description="Vous n'avez pas le rôle requis pour utiliser cette commande.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Vérifier si x est bien précisé
    if x is None:
        embed = discord.Embed(
            title="Erreur",
            description="Vous n'avez pas précisé de chiffre entre 1 et 500.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    try:
        # Convertir x en entier
        x = int(x)
    except ValueError:
        embed = discord.Embed(
            title="Erreur",
            description="Le chiffre doit être un nombre entier.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Vérifier si x est dans les bonnes limites
    if x < 1 or x > 500:
        embed = discord.Embed(
            title="Erreur",
            description="Le chiffre doit être compris entre 1 et 500.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Générer un nombre aléatoire entre 1 et x
    result = random.randint(1, x)

    # Créer l'embed de la réponse
    embed = discord.Embed(
        title="Résultat du tirage",
        description=f"Le nombre tiré au hasard entre 1 et {x} est : **{result}**",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)
    
@bot.command()
async def zizi(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return
    
    # Générer une valeur aléatoire entre 0 et 28 cm
    value = random.randint(0, 50)

    # Créer l'embed
    embed = discord.Embed(
        title="Analyse de la taille du zizi 🔥", 
        description=f"{member.mention} a un zizi de **{value} cm** !\n\n*La taille varie selon l'humeur du membre.*", 
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)

    # Envoyer l'embed
    await ctx.send(embed=embed)

@bot.command()
async def fou(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return
    
    percentage = random.randint(0, 100)
    
    embed = discord.Embed(
        title=f"Analyse de folie 🤪", 
        description=f"{member.mention} est fou à **{percentage}%** !\n\n*Le pourcentage varie en fonction de l'état mental du membre.*", 
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    
    await ctx.send(embed=embed)

@bot.command()
async def testo(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return
    
    percentage = random.randint(0, 100)
    
    embed = discord.Embed(
        title=f"Analyse de testostérone 💪", 
        description=f"{member.mention} a un taux de testostérone de **{percentage}%** !\n\n*Le pourcentage varie en fonction des niveaux de virilité du membre.*", 
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    
    await ctx.send(embed=embed)

class PFCView(View):
    def __init__(self, player1, player2):
        super().__init__(timeout=60)
        self.choices = {}
        self.player1 = player1
        self.player2 = player2
        
        for choice in ['Pierre', 'Feuille', 'Ciseau']:
            self.add_item(PFCButton(choice, self))

    async def check_winner(self):
        if len(self.choices) == 2:
            p1_choice = self.choices[self.player1]
            p2_choice = self.choices[self.player2]
            result = determine_winner(p1_choice, p2_choice)
            
            winner_text = {
                'win': f"{self.player1.mention} a gagné !",
                'lose': f"{self.player2.mention} a gagné !",
                'draw': "Match nul !"
            }
            
            embed = discord.Embed(title="Résultat du Pierre-Feuille-Ciseaux !", description=f"{self.player1.mention} a choisi **{p1_choice}**\n{self.player2.mention} a choisi **{p2_choice}**\n\n{winner_text[result]}", color=0x00FF00)
            await self.player1.send(embed=embed)
            await self.player2.send(embed=embed)
            await self.message.edit(embed=embed, view=None)

class PFCButton(Button):
    def __init__(self, choice, view):
        super().__init__(label=choice, style=discord.ButtonStyle.primary)
        self.choice = choice
        self.pfc_view = view
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user in [self.pfc_view.player1, self.pfc_view.player2]:
            if interaction.user not in self.pfc_view.choices:
                self.pfc_view.choices[interaction.user] = self.choice
                await interaction.response.send_message(f"{interaction.user.mention} a choisi **{self.choice}**", ephemeral=True)
                if len(self.pfc_view.choices) == 2:
                    await self.pfc_view.check_winner()
            else:
                await interaction.response.send_message("Tu as déjà choisi !", ephemeral=True)
        else:
            await interaction.response.send_message("Tu ne participes pas à cette partie !", ephemeral=True)

def determine_winner(choice1, choice2):
    beats = {"Pierre": "Ciseau", "Ciseau": "Feuille", "Feuille": "Pierre"}
    if choice1 == choice2:
        return "draw"
    elif beats[choice1] == choice2:
        return "win"
    else:
        return "lose"

class AcceptView(View):
    def __init__(self, ctx, player1, player2):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.player1 = player1
        self.player2 = player2

        self.add_item(AcceptButton("✅ Accepter", discord.ButtonStyle.success, True, self))
        self.add_item(AcceptButton("❌ Refuser", discord.ButtonStyle.danger, False, self))

class AcceptButton(Button):
    def __init__(self, label, style, accept, view):
        super().__init__(label=label, style=style)
        self.accept = accept
        self.accept_view = view
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.accept_view.player2:
            return await interaction.response.send_message("Ce n'est pas à toi d'accepter ou refuser !", ephemeral=True)
        
        if self.accept:
            embed = discord.Embed(title="Pierre-Feuille-Ciseaux", description=f"{self.accept_view.player1.mention} VS {self.accept_view.player2.mention}\n\nCliquez sur votre choix !", color=0x00FF00)
            await interaction.message.edit(embed=embed, view=PFCView(self.accept_view.player1, self.accept_view.player2))
        else:
            await interaction.message.edit(content=f"Le +pfc a été refusé par {self.accept_view.player2.mention}", embed=None, view=None)

@bot.command()
async def pfc(ctx, member: discord.Member = None):
    if not member:
        return await ctx.send("Vous devez mentionner un adversaire pour jouer !")
    if member == ctx.author:
        return await ctx.send("Vous ne pouvez pas jouer contre vous-même !")
    
    embed = discord.Embed(title="Défi Pierre-Feuille-Ciseaux", description=f"{member.mention}, acceptes-tu le défi de {ctx.author.mention} ?", color=0xFFA500)
    await ctx.send(embed=embed, view=AcceptView(ctx, ctx.author, member))

@bot.command()
async def gunfight(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send('Erreur : vous devez cibler un membre !')
        return

    if member == ctx.author:
        await ctx.send('Vous ne pouvez pas vous défier vous-même !')
        return

    # Création des boutons
    accept_button = Button(label="Oui", style=discord.ButtonStyle.green)
    decline_button = Button(label="Non", style=discord.ButtonStyle.red)

    # Définir les actions des boutons
    async def accept(interaction):
        if interaction.user != member:
            await interaction.response.send_message('Ce n\'est pas votre duel !', ephemeral=True)
            return
        result = random.choice([ctx.author, member])
        winner = result.name
        await interaction.message.edit(content=f"{member.mention} a accepté le duel ! Le gagnant est {winner} !", view=None)
    
    async def decline(interaction):
        if interaction.user != member:
            await interaction.response.send_message('Ce n\'est pas votre duel !', ephemeral=True)
            return
        await interaction.message.edit(content=f"{member.mention} a refusé le duel.", view=None)

    accept_button.callback = accept
    decline_button.callback = decline

    # Création de la vue avec les boutons
    view = View()
    view.add_item(accept_button)
    view.add_item(decline_button)

    # Envoyer l'embed pour le défi
    embed = discord.Embed(
        title="Défi de Gunfight",
        description=f"{ctx.author.mention} vous défie à un duel, {member.mention}. Acceptez-vous ?",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=view)
    
@bot.command()
async def hug(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return

    # Créer l'embed
    embed = discord.Embed(
        title=f"Tu as donné un câlin à {member.name} ! 🤗",  # Utilisation de member.name pour afficher le nom simple
        description="Les câlins sont la meilleure chose au monde !",
        color=discord.Color.blue()
    )
    embed.set_image(url="https://media.tenor.com/P6FsFii7pnoAAAAM/hug-warm-hug.gif")
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)


@bot.command()
async def slap(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return

    # Créer l'embed
    embed = discord.Embed(
        title=f"Tu as giflé {member.name} !",  # Utilisation de member.name
        description="Oups, ça a dû faire mal 😱",
        color=discord.Color.red()
    )
    embed.set_image(url="https://media.tenor.com/QRdCcNbk18MAAAAM/slap.gif")
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)


@bot.command()
async def dance(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return

    # Créer l'embed
    embed = discord.Embed(
        title=f"{member.name} danse comme un pro ! 💃🕺",  # Utilisation de member.name
        description="Admirez cette danse épique !",
        color=discord.Color.green()
    )
    embed.set_image(url="https://media.tenor.com/d7ibtS6MLQgAAAAM/dancing-kid.gif")
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)


@bot.command()
async def flirt(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return

    # Créer l'embed
    embed = discord.Embed(
        title=f"Vous avez charmé {member.name} avec un sourire éclatant ! 😍",  # Utilisation de member.name
        description="Vous êtes irrésistible !",
        color=discord.Color.purple()
    )
    embed.set_image(url="https://media.tenor.com/HDdV-0Km1QAAAAAM/hello-sugar.gif")
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)


@bot.command()
async def whisper(ctx, member: discord.Member = None, *, message):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return

    # Créer l'embed
    embed = discord.Embed(
        title=f"Chuchotement de {ctx.author.name} à {member.name}",  # Utilisation de member.name et ctx.author.name
        description=f"*{message}*",
        color=discord.Color.greyple()
    )
    embed.set_footer(text=f"Un message secret entre vous deux... {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    embed.set_thumbnail(url=member.avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def troll(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return

    # Créer l'embed
    embed = discord.Embed(
        title=f"Tu as trollé {member.name} ! 😆",  # Utilisation de member.name
        description=f"Oups, {member.name} s'est fait avoir !",
        color=discord.Color.orange()
    )
    embed.set_image(url="https://media.tenor.com/7Q8TRpW2ZXkAAAAM/yeet-lol.gif")
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def kiss(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return

    # Créer l'embed
    embed = discord.Embed(
        title=f"Tu as embrassé {member.name} !",  # Utilisation de member.name
        description="Un doux baiser 💋",  
        color=discord.Color.pink()
    )
    embed.set_image(url="https://media.tenor.com/3DHc1_2PZ-oAAAAM/kiss.gif")
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def kill(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous n'avez ciblé personne !")
        return

    # Créer l'embed
    embed = discord.Embed(
        title=f"Tu as tué {member.name} !",  # Utilisation de member.name
        description="C'est la fin pour lui... 💀",  
        color=discord.Color.red()
    )
    embed.set_image(url="https://media1.tenor.com/m/4hO2HfS9fcMAAAAd/toaru-index.gif")
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)


@bot.command()
async def reverse(ctx, *, text: str = None):
    if text is None:
        await ctx.send("Tu n'as pas fourni de texte à inverser !")
        return

    reversed_text = text[::-1]  # Inverser le texte
    await ctx.send(f"Texte inversé : {reversed_text}")

@bot.command()
async def note(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Tu n'as pas précisé l'utilisateur !")
        return

    # Générer une note aléatoire entre 1 et 10
    note = random.randint(1, 10)

    # Créer l'embed
    embed = discord.Embed(
        title=f"{member.name} a reçu une note !",
        description=f"Note : {note}/10",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)


@bot.command()
async def say(ctx, *, text: str = None):
    # Vérifie si l'utilisateur a les permissions d'admin
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Tu n'as pas les permissions nécessaires pour utiliser cette commande.")
        return
    
    if text is None:
        await ctx.send("Tu n'as pas écrit de texte à dire !")
        return

    # Supprime le message originel
    await ctx.message.delete()

    # Envoie le texte spécifié
    await ctx.send(text)



@bot.command()
async def coinflip(ctx):
    import random
    result = random.choice(["Pile", "Face"])
    await ctx.send(f"Résultat du coinflip : {result}")


@bot.command()
async def dice(ctx):
    import random
    result = random.randint(1, 6)
    await ctx.send(f"Résultat du dé : {result}")


@bot.command()
async def fight(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Tu n'as ciblé personne pour te battre !")
        return

    # Simuler un combat
    import random
    result = random.choice([f"{ctx.author.name} a gagné !", f"{member.name} a gagné !", "C'est une égalité !"])

    # Créer l'embed
    embed = discord.Embed(
        title=f"Combat entre {ctx.author.name} et {member.name}",
        description=result,
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def enfant(ctx, parent1: discord.Member = None, parent2: discord.Member = None):
    if not parent1 or not parent2:
        await ctx.send("Tu dois mentionner deux membres ! Utilise `/enfant @membre1 @membre2`.")
        return
    
    # Génération du prénom en combinant les pseudos
    prenom = parent1.name[:len(parent1.name)//2] + parent2.name[len(parent2.name)//2:]
    
    # Création de l'embed
    embed = discord.Embed(
        title="👶 Voici votre enfant !",
        description=f"{parent1.mention} + {parent2.mention} = **{prenom}** 🍼",
        color=discord.Color.purple()
    )
    embed.set_footer(text=f"Prenez soin de votre bébé ! {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    
    # Ajout des photos de profil
    embed.set_thumbnail(url=parent1.avatar.url if parent1.avatar else parent2.avatar.url)
    
    await ctx.send(embed=embed)

@bot.command()
async def superpouvoir(ctx, user: discord.Member = None):
    if not user:
        user = ctx.author  # Si pas d’utilisateur mentionné, prendre l’auteur

    pouvoirs = [
        "Téléportation instantanée 🌀 - Peut se déplacer n'importe où en un clin d'œil.",
        "Contrôle du feu 🔥 - Rien ne lui résiste… sauf l'eau.",
        "Super vitesse ⚡ - Peut courir plus vite qu'un TGV, mais oublie souvent où il va.",
        "Lecture des pensées 🧠 - Peut lire dans les esprits… sauf ceux qui ne pensent à rien.",
        "Invisibilité 🫥 - Peut disparaître… mais oublie que ses vêtements restent visibles.",
        "parler aux animaux 🦜 - Mais ils n'ont pas grand-chose d'intéressant à dire.",
        "Super force 💪 - Peut soulever une voiture, mais galère à ouvrir un pot de cornichons.",
        "Métamorphose 🦎 - Peut se transformer en n'importe quoi… mais pas revenir en humain.",
        "Chance infinie 🍀 - Gagne à tous les jeux… sauf au Uno.",
        "Création de portails 🌌 - Peut ouvrir des portails… mais ne sait jamais où ils mènent.",
        "Régénération 🩸 - Guérit instantanément… mais reste chatouilleux à vie.",
        "Capacité de voler 🕊️ - Mais uniquement à 10 cm du sol.",
        "Super charisme 😎 - Convainc tout le monde… sauf sa mère.",
        "Vision laser 🔥 - Brûle tout sur son passage… y compris ses propres chaussures.",
        "Invocation de clones 🧑‍🤝‍🧑 - Mais ils n’obéissent jamais.",
        "Télékinésie ✨ - Peut déplacer des objets… mais uniquement des plumes.",
        "Création de burgers 🍔 - Magique, mais toujours trop cuits ou trop crus.",
        "Respiration sous l'eau 🐠 - Mais panique dès qu'il voit une méduse.",
        "Contrôle de la gravité 🌍 - Peut voler, mais oublie souvent de redescendre.",
        "Capacité d’arrêter le temps ⏳ - Mais uniquement quand il dort.",
        "Voyage dans le temps ⏰ - Peut voyager dans le passé ou le futur… mais toujours à la mauvaise époque.",
        "Télépathie inversée 🧠 - Peut faire entendre ses pensées aux autres… mais ils ne peuvent jamais comprendre.",
        "Manipulation des rêves 🌙 - Peut entrer dans les rêves des gens… mais se retrouve toujours dans des cauchemars.",
        "Super mémoire 📚 - Se souvient de tout… sauf des choses qu’il vient de dire.",
        "Manipulation des ombres 🌑 - Peut faire bouger les ombres… mais ne peut jamais les arrêter.",
        "Création de pluie 🍃 - Peut faire pleuvoir… mais uniquement sur ses amis.",
        "Maîtrise des plantes 🌱 - Peut faire pousser des plantes à une vitesse folle… mais elles ne cessent de pousser partout.",
        "Contrôle des rêves éveillés 💤 - Peut contrôler ses rêves quand il est éveillé… mais se retrouve toujours dans une réunion ennuyante.",
        "Maîtrise de l’éclairage ✨ - Peut illuminer n'importe quelle pièce… mais oublie d’éteindre.",
        "Création de souvenirs 🧳 - Peut créer des souvenirs… mais ceux-ci sont toujours un peu bizarres.",
        "Changement de taille 📏 - Peut grandir ou rapetisser… mais n'arrive jamais à garder une taille stable.",
        "Vision nocturne 🌙 - Peut voir dans l’obscurité… mais tout est toujours en noir et blanc.",
        "Contrôle des éléments 🤹‍♂️ - Peut manipuler tous les éléments naturels… mais uniquement quand il pleut.",
        "Phasing à travers les murs 🚪 - Peut traverser les murs… mais parfois il traverse aussi les portes.",
        "Régénération de l’esprit 🧠 - Guérit les blessures mentales… mais les oublie instantanément après."


    ]

    pouvoir = random.choice(pouvoirs)

    embed = discord.Embed(
        title="⚡ Super-Pouvoir Débloqué !",
        description=f"{user.mention} possède le pouvoir de**{pouvoir}** !",
        color=discord.Color.purple()
    )
    embed.set_footer(text=f"Utilise-le avec sagesse... ou pas. {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    
    await ctx.send(embed=embed)

@bot.command()
async def totem(ctx, member: discord.Member = None):
    if not member:
        member = ctx.author  # Si pas de membre mentionné, prendre l'auteur  

    animaux_totem = {
        "Loup 🐺": "Fidèle et protecteur, il veille sur sa meute.",
        "Renard 🦊": "Rusé et malin, il trouve toujours un moyen de s'en sortir.",
        "Hibou 🦉": "Sage et observateur, il comprend tout avant les autres.",
        "Dragon 🐉": "Puissant et imposant, il ne laisse personne indifférent.",
        "Dauphin 🐬": "Joueur et intelligent, il adore embêter les autres.",
        "Chat 🐱": "Mystérieux et indépendant, il fait ce qu’il veut, quand il veut.",
        "Serpent 🐍": "Discret et patient, il attend le bon moment pour frapper.",
        "Corbeau 🦅": "Intelligent et un peu sinistre, il voit ce que les autres ignorent.",
        "Panda 🐼": "Calme et adorable… jusqu’à ce qu’on lui prenne son bambou.",
        "Tortue 🐢": "Lente mais sage, elle gagne toujours à la fin.",
        "Aigle 🦅": "Libre et fier, il vole au-dessus de tous les problèmes.",
        "Chauve-souris 🦇": "Préférant l'obscurité, elle voit clair quand tout le monde est perdu.",
        "Tigre 🐯": "Puissant et rapide, personne ne l’arrête.",
        "Lapin 🐰": "Rapide et malin, mais fuit dès qu’il y a un problème.",
        "Singe 🐵": "Curieux et joueur, il adore faire des bêtises.",
        "Escargot 🐌": "Lent… mais au moins il arrive toujours à destination.",
        "Pigeon 🕊️": "Increvable et partout à la fois, impossible de s'en débarrasser.",
        "Licorne 🦄": "Rare et magique, il apporte de la lumière partout où il passe.",
        "Poisson rouge 🐠": "Mémoire de 3 secondes, mais au moins il ne s’inquiète jamais.",
        "Canard 🦆": "Semble idiot, mais cache une intelligence surprenante.",
        "Raton laveur 🦝": "Petit voleur mignon qui adore piquer des trucs.",
        "Lynx 🐆" : "Serré dans ses mouvements, il frappe avec précision et discrétion.",
        "Loup de mer 🌊🐺" : "Un loup qui conquiert aussi bien les océans que la terre, fier et audacieux.",
        "Baleine 🐋" : "Majestueuse et bienveillante, elle nage dans les eaux profondes avec sagesse.",
        "Léopard 🐆" : "Vif et agile, il disparaît dans la jungle avant même qu'on ait pu le voir.",
        "Ours 🐻" : "Fort et protecteur, il défend son territoire sans hésiter.",
        "Cygne 🦢" : "Gracieux et élégant, il incarne la beauté dans la tranquillité.",
        "Chameau 🐫" : "Patient et résistant, il traverse les déserts sans jamais se fatiguer.",
        "Grizzly 🐻‍❄️" : "Imposant et puissant, il est le roi des forêts froides.",
        "Koala 🐨" : "Doux et calme, il passe sa vie à dormir dans les arbres.",
        "Panthère noire 🐆" : "Silencieuse et mystérieuse, elle frappe toujours quand on s'y attend le moins.",
        "Zèbre 🦓" : "Unique et surprenant, il se distingue dans la foule grâce à ses rayures.",
        "Éléphant 🐘" : "Sage et majestueux, il marche au rythme de sa propre grandeur.",
        "Croco 🐊" : "Implacable et rusé, il attend patiemment avant de bondir.",
        "Mouflon 🐏" : "Fort et tenace, il n'a pas peur de braver les montagnes.",
        "Perroquet 🦜" : "Coloré et bavard, il ne cesse jamais de répéter ce qu'il entend.",
        "Rhinocéros 🦏" : "Imposant et robuste, il se fraye un chemin à travers tout sur son passage.",
        "Bison 🦬" : "Solide et puissant, il traverse les prairies avec une énergie inébranlable."

    }

    totem, description = random.choice(list(animaux_totem.items()))

    embed = discord.Embed(
        title=f"🌿 Totem de {member.name} 🌿",
        description=f"**{totem}** : {description}",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)

    await ctx.send(embed=embed)
    
@bot.command()
async def futur(ctx, user: discord.Member = None):
    if not user:
        user = ctx.author  # Si pas d’utilisateur mentionné, prendre l’auteur

    predicions = [
        "Dans 5 minutes, tu découvriras un trésor caché… mais il sera rempli de bonbons.",
        "L'année prochaine, tu feras une rencontre étonnante avec un extraterrestre qui adore les chats.",
        "Demain, tu auras une conversation intense avec un pigeon, et il te donnera un conseil de vie précieux.",
        "Un chat va te confier un secret qui changera le cours de ton existence… mais tu ne te souviendras pas de ce secret.",
        "Dans quelques jours, tu seras élu meilleur joueur de cache-cache, mais tu te cacheras dans une pièce vide.",
        "Lundi, tu rencontreras quelqu'un qui aime les licornes autant que toi. Vous deviendrez amis pour la vie.",
        "Dans un futur proche, tu réussiras à inventer un gâteau qui ne se mange pas, mais il sera étonnamment populaire.",
        "Bientôt, un mystérieux inconnu t'offrira un paquet cadeau. Il contiendra un élastique et une noix de coco.",
        "Dans un mois, tu vivras une aventure épique où tu devras résoudre un mystère impliquant des chaussettes perdues.",
        "Prochainement, tu seras récompensé pour avoir trouvé une solution révolutionnaire au problème de la pizza froide.",
        "Dans un futur lointain, tu seras le leader d'une civilisation intergalactique. Tes sujets seront principalement des pandas."
        "Dans 5 minutes, tu rencontreras un robot qui te demandera comment faire des pancakes… mais il n'a pas de mains.",
        "Ce week-end, tu seras choisi pour participer à un concours de danse avec des flamants roses, mais tu devras danser sans musique.",
        "Demain, un magicien te proposera un vœu… mais il te le refusera en te montrant un tour de cartes.",
        "Un perroquet va te confier un secret très important, mais tu l'oublieras dès que tu entras dans une pièce.",
        "Dans quelques jours, tu découvriras un trésor enfoui sous ta maison… mais il sera composé uniquement de petites pierres colorées.",
        "Prochainement, tu feras une rencontre étrange avec un extraterrestre qui te demandera de lui apprendre à jouer aux échecs.",
        "Dans un futur proche, tu gagneras un prix prestigieux pour avoir créé un objet du quotidien, mais personne ne saura vraiment à quoi il sert.",
        "Bientôt, tu recevras une invitation pour un dîner chez des créatures invisibles. Le menu ? Des nuages et des rayons de lune.",
        "Dans un mois, tu seras choisi pour représenter ton pays dans un concours de chant… mais tu devras chanter sous l'eau.",
        "Dans un futur lointain, tu seras une légende vivante, reconnu pour avoir inventé la première machine à fabriquer des sourires."
        "Dans 5 minutes, tu verras un nuage prendre la forme de ton visage, mais il te fera une grimace étrange.",
        "Demain, tu seras invité à une réunion secrète de licornes qui discuteront des nouvelles tendances en matière de paillettes.",
        "Prochainement, un dauphin te confiera un message codé que tu devras résoudre… mais il sera écrit en chantant.",
        "Un dragon viendra te rendre visite et te proposera de partager son trésor… mais il s’avère que ce trésor est un stock infini de bonbons à la menthe.",
        "Dans quelques jours, tu apprendras à parler couramment le langage des grenouilles, mais seulement quand il pleut.",
        "Cette semaine, un voleur masqué viendra te voler une chaussette… mais il te laissera un billet pour un concert de musique classique.",
        "Prochainement, un fantôme te demandera de l'aider à retrouver ses clés perdues… mais tu découvriras qu'il a oublié où il les a mises.",
        "Dans un futur proche, tu seras élu président d'un club de fans de légumes, et tu recevras une médaille en forme de carotte.",
        "Bientôt, tu découvriras un raccourci secret qui te permettra de voyager dans des mondes parallèles… mais il te fera revenir à ton point de départ.",
        "Dans un mois, tu recevras une lettre d'invitation à un bal masqué organisé par des robots, mais tu ne pourras pas danser car tu porteras des chaussons trop grands."

    ]

    prediction = random.choice(predicions)

    embed = discord.Embed(
        title=f"🔮 Prédiction pour {user.name} 🔮",
        description=f"**Prédiction :**\n\n{prediction}",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Le futur est incertain… mais amusant ! {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)

    await ctx.send(embed=embed)

# Liste de blagues
blagues = [
    "Pourquoi les plongeurs plongent toujours en arrière et jamais en avant ? ||Parce que sinon ils tombent toujours dans le bateau.||",
    "Pourquoi les canards sont toujours à l'heure ? ||Parce qu'ils sont dans les starting-quack !||",
    "Quel est le comble pour un électricien ? ||De ne pas être au courant.||",
    "Pourquoi les maths sont tristes ? ||Parce qu'elles ont trop de problèmes.||",
    "Que dit une imprimante à une autre imprimante ? *||'T'as du papier ?'||",
    "Pourquoi les poissons détestent l'ordinateur ? ||Parce qu'ils ont peur du net !||",
    "Comment appelle-t-on un chat qui a perdu son GPS ? ||Un chat égaré.||",
    "Pourquoi les squelettes ne se battent-ils jamais entre eux ? ||Parce qu'ils n'ont pas de cœur !||",
    "Quel est le comble pour un plombier ? ||D'avoir un tuyau percé.||",
    "Comment appelle-t-on un chien magique ? ||Un labra-cadabra !||"
]

# Commande !blague
@bot.command()
async def blague(ctx):
    # Choisir une blague au hasard
    blague_choisie = random.choice(blagues)
    # Envoyer la blague dans le salon
    await ctx.send(blague_choisie)
#------------------------------------------------------------------------- Commandes d'économie : +prison, +evasion, +arrestation, +liberation, +cautionpayer, +ticket_euro_million
# Commande +prison
@bot.command()
@commands.has_role (1355157681882664981)
async def prison(ctx, member: discord.Member = None):
    if ctx.guild.id != AUTORIZED_SERVER_ID:
        embed = discord.Embed(
            title="Commande non autorisée",
            description="Cette commande n'est pas disponible sur ce serveur.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return

    if not member:
        await ctx.send("Vous n'avez ciblé personne.")
        return

    embed = discord.Embed(
        title="La Police Etheryenne vous arrête !",
        description="Te voilà privé d'accès de l'économie !",
        color=0xffcc00
    )
    embed.set_image(url="https://i.imgur.com/dX0DSGh.jpeg")
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

    # Gestion des rôles
    role_remove = discord.utils.get(ctx.guild.roles, id=1355190216188497951)
    role_add = discord.utils.get(ctx.guild.roles, id=1359562052552622215)

    if role_remove:
        await member.remove_roles(role_remove)
    if role_add:
        await member.add_roles(role_add)

# Commande +arrestation
@bot.command()
@commands.has_role (1355157681882664981)
async def arrestation(ctx, member: discord.Member = None):
    if ctx.guild.id != AUTORIZED_SERVER_ID:
        embed = discord.Embed(
            title="Commande non autorisée",
            description="Cette commande n'est pas disponible sur ce serveur.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return

    if not member:
        await ctx.send("Vous n'avez ciblé personne.")
        return

    embed = discord.Embed(
        title="Vous avez été arrêté lors d'une tentative de braquage",
        description="Braquer les fourgons c'est pas bien !",
        color=0xff0000
    )
    embed.set_image(url="https://i.imgur.com/uVNxDX2.jpeg")
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

    # Gestion des rôles
    role_remove = discord.utils.get(ctx.guild.roles, id=1355190216188497951)
    role_add = discord.utils.get(ctx.guild.roles, id=1359562052552622215)

    if role_remove:
        await member.remove_roles(role_remove)
    if role_add:
        await member.add_roles(role_add)

# Commande +liberation
@bot.command()
@commands.has_role (1355157681882664981)
async def liberation(ctx, member: discord.Member = None):
    if ctx.guild.id != AUTORIZED_SERVER_ID:
        embed = discord.Embed(
            title="Commande non autorisée",
            description="Cette commande n'est pas disponible sur ce serveur.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return

    if not member:
        await ctx.send("Vous n'avez ciblé personne.")
        return

    embed = discord.Embed(
        title="La Police Étheryenne a décidé de vous laisser sortir de prison !",
        description="En revanche, si vous refaites une erreur c'est au cachot direct !",
        color=0x00ff00
    )
    embed.set_image(url="https://i.imgur.com/Xh7vqh7.jpeg")
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

    # Gestion des rôles
    role_add = discord.utils.get(ctx.guild.roles, id=1355190216188497951)
    role_remove = discord.utils.get(ctx.guild.roles, id=1359562052552622215)

    if role_add:
        await member.add_roles(role_add)
    if role_remove:
        await member.remove_roles(role_remove)

# Commande +evasion
@bot.command()
@commands.has_role (1357435690463531271)
async def evasion(ctx):
    if ctx.guild.id != AUTORIZED_SERVER_ID:
        embed = discord.Embed(
            title="Commande non autorisée",
            description="Cette commande n'est pas disponible sur ce serveur.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return

    member = ctx.author  # L'auteur de la commande s'évade

    embed = discord.Embed(
        title="Un joueur s'évade de prison !",
        description="Grâce à un ticket trouvé à la fête foraine !!",
        color=0x0000ff
    )
    embed.set_image(url="https://i.imgur.com/X8Uje39.jpeg")
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

    # Gestion des rôles
    role_add = discord.utils.get(ctx.guild.roles, id=1355190216188497951)
    role_remove_1 = discord.utils.get(ctx.guild.roles, id=1359562052552622215)
    role_remove_2 = discord.utils.get(ctx.guild.roles, id=1357435690463531271)

    if role_add:
        await member.add_roles(role_add)
    if role_remove_1:
        await member.remove_roles(role_remove_1)
    if role_remove_2:
        await member.remove_roles(role_remove_2)

# Commande cautionpayer
@bot.command()
@commands.has_role (1355157681882664981)
async def cautionpayer(ctx, member: discord.Member = None):
    if ctx.guild.id != AUTORIZED_SERVER_ID:
        embed = discord.Embed(
            title="Commande non autorisée",
            description="Cette commande n'est pas disponible sur ce serveur.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return

    if not member:
        await ctx.send("Vous n'avez ciblé personne.")
        return

    embed = discord.Embed(
        title="Caution payée avec succès !",
        description="Vous êtes maintenant libre de retourner dans l'économie.",
        color=0x00ff00
    )
    embed.set_image(url="https://github.com/Iseyg91/Etherya-Gestion/blob/main/1dnyLPXGJgsrcmMo8Bgi4.jpg?raw=true")
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

    # Gestion des rôles
    role_remove = discord.utils.get(ctx.guild.roles, id=1359562052552622215)
    role_remove = discord.utils.get(ctx.guild.roles, id=1357435690463531271)
    if role_remove:
        await member.remove_roles(role_remove)

# Commande ticket_euro_million
@bot.command()
async def ticket_euro_million(ctx, user: discord.Member):
    if ctx.guild.id != AUTORIZED_SERVER_ID:
        embed = discord.Embed(
            title="Commande non autorisée",
            description="Cette commande n'est pas disponible sur ce serveur.",
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return

    # Générer 5 chiffres entre 0 et 5
    numeros = [str(random.randint(0, 5)) for _ in range(5)]
    combinaison = " - ".join(numeros)

    embed_user = discord.Embed(
        title="🎟️ Ticket Euro Million",
        description=f"Voici votre combinaison, **{user.mention}** : **{combinaison}**\n\n"
                    f"Bonne chance ! 🍀",
        color=discord.Color.gold()
    )
    embed_user.set_footer(text="Ticket généré par " + ctx.author.name)
    embed_user.set_footer(text=f"♥️by Iseyg", icon_url=ctx.author.avatar.url)

    await ctx.send(embed=embed_user)

    embed_announce = discord.Embed(
        title="🎟️ Euro Million - Résultat",
        description=f"**{user.mention}** a tiré le combiné suivant : **{combinaison}**\n\n"
                    f"Commande exécutée par : **{ctx.author.mention}**",
        color=discord.Color.green()
    )
    embed_announce.set_footer(text="Ticket généré avec succès !")
    embed_announce.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)

    salon_announce = bot.get_channel(1355234774033104997)
    if salon_announce:
        await salon_announce.send(embed=embed_announce)
    else:
        await ctx.send("Erreur : Le salon d'annonce est introuvable.")

#------------------------------------------------------------------------- Commandes de Moderation : +ban, +unban, +mute, +unmute, +kick, +warn

# 🎨 Fonction pour créer un embed formaté
def create_embed(title, description, color, ctx, member=None, action=None, reason=None, duration=None):
    embed = discord.Embed(title=title, description=description, color=color, timestamp=ctx.message.created_at)
    embed.set_footer(text=f"Action effectuée par {ctx.author.name}", icon_url=ctx.author.avatar.url)
    
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)

    if member:
        embed.add_field(name="👤 Membre sanctionné", value=member.mention, inline=True)
    if action:
        embed.add_field(name="⚖️ Sanction", value=action, inline=True)
    if reason:
        embed.add_field(name="📜 Raison", value=reason, inline=False)
    if duration:
        embed.add_field(name="⏳ Durée", value=duration, inline=True)

    return embed

# 🎯 Vérification des permissions et hiérarchie
def has_permission(ctx, perm):
    return ctx.author.id == ISEY_ID or getattr(ctx.author.guild_permissions, perm, False)

def is_higher_or_equal(ctx, member):
    return member.top_role >= ctx.author.top_role

# 📩 Envoi d'un log
async def send_log(ctx, member, action, reason, duration=None):
    guild_id = ctx.guild.id
    settings = GUILD_SETTINGS.get(guild_id, {})
    log_channel_id = settings.get("sanctions_channel")

    if log_channel_id:
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            embed = create_embed("🚨 Sanction appliquée", f"{member.mention} a été sanctionné.", discord.Color.red(), ctx, member, action, reason, duration)
            await log_channel.send(embed=embed)

# 📩 Envoi d'un message privé à l'utilisateur sanctionné
async def send_dm(member, action, reason, duration=None):
    try:
        embed = create_embed("🚨 Vous avez reçu une sanction", "Consultez les détails ci-dessous.", discord.Color.red(), member, member, action, reason, duration)
        await member.send(embed=embed)
    except discord.Forbidden:
        print(f"Impossible d'envoyer un DM à {member.display_name}.")

@bot.command()
async def ban(ctx, member: discord.Member = None, *, reason="Aucune raison spécifiée"):
    if member is None:
        return await ctx.send("❌ Il manque un argument : vous devez mentionner un membre ou fournir un ID pour bannir.")

    # Si le membre fourni est une mention
    if isinstance(member, discord.Member):
        target_member = member
    else:
        # Si le membre est un ID
        target_member = get(ctx.guild.members, id=int(member))

    # Si le membre est introuvable dans le serveur
    if target_member is None:
        return await ctx.send("❌ Aucun membre trouvé avec cet ID ou mention.")

    if ctx.author == target_member:
        return await ctx.send("🚫 Vous ne pouvez pas vous bannir vous-même.")
    
    if is_higher_or_equal(ctx, target_member):
        return await ctx.send("🚫 Vous ne pouvez pas sanctionner quelqu'un de votre niveau ou supérieur.")
    
    if has_permission(ctx, "ban_members"):
        await member.ban(reason=reason)
        embed = create_embed("🔨 Ban", f"{member.mention} a été banni.", discord.Color.red(), ctx, member, "Ban", reason)
        await ctx.send(embed=embed)
        await send_log(ctx, member, "Ban", reason)
        await send_dm(member, "Ban", reason)

        # Enregistrement de la sanction
        add_sanction(ctx.guild.id, member.id, "Ban", reason)

@bot.command()
async def unban(ctx, user_id: int = None):
    if user_id is None:
        return await ctx.send("❌ Il manque un argument : vous devez spécifier l'ID d'un utilisateur à débannir.")

    if has_permission(ctx, "ban_members"):
        try:
            user = await bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            embed = create_embed("🔓 Unban", f"{user.mention} a été débanni.", discord.Color.green(), ctx, user, "Unban", "Réintégration")
            await ctx.send(embed=embed)
            await send_log(ctx, user, "Unban", "Réintégration")
            await send_dm(user, "Unban", "Réintégration")
        except discord.NotFound:
            return await ctx.send("❌ Aucun utilisateur trouvé avec cet ID.")
        except discord.Forbidden:
            return await ctx.send("❌ Je n'ai pas les permissions nécessaires pour débannir cet utilisateur.")


@bot.command()
async def kick(ctx, member: discord.Member = None, *, reason="Aucune raison spécifiée"):
    if member is None:
        return await ctx.send("❌ Il manque un argument : vous devez mentionner un membre à expulser.")

    if ctx.author == member:
        return await ctx.send("🚫 Vous ne pouvez pas vous expulser vous-même.")
    if is_higher_or_equal(ctx, member):
        return await ctx.send("🚫 Vous ne pouvez pas sanctionner quelqu'un de votre niveau ou supérieur.")
    if has_permission(ctx, "kick_members"):
        await member.kick(reason=reason)
        embed = create_embed("👢 Kick", f"{member.mention} a été expulsé.", discord.Color.orange(), ctx, member, "Kick", reason)
        await ctx.send(embed=embed)
        await send_log(ctx, member, "Kick", reason)
        await send_dm(member, "Kick", reason)

@bot.command()
async def mute(ctx, member: discord.Member = None, duration_with_unit: str = None, *, reason="Aucune raison spécifiée"):
    if member is None:
        return await ctx.send("❌ Il manque un argument : vous devez mentionner un membre à mute.")
    
    if duration_with_unit is None:
        return await ctx.send("❌ Il manque un argument : vous devez préciser une durée (ex: `10m`, `1h`, `2j`).")

    if ctx.author == member:
        return await ctx.send("🚫 Vous ne pouvez pas vous mute vous-même.")
    if is_higher_or_equal(ctx, member):
        return await ctx.send("🚫 Vous ne pouvez pas sanctionner quelqu'un de votre niveau ou supérieur.")
    if not has_permission(ctx, "moderate_members"):
        return await ctx.send("❌ Vous n'avez pas la permission de mute des membres.")
    
    # Vérification si le membre est déjà en timeout
    if member.timed_out:
        return await ctx.send(f"❌ {member.mention} est déjà en timeout.")
    
    # Traitement de la durée
    time_units = {"m": "minutes", "h": "heures", "j": "jours"}
    try:
        duration = int(duration_with_unit[:-1])
        unit = duration_with_unit[-1].lower()
        if unit not in time_units:
            raise ValueError
    except ValueError:
        return await ctx.send("❌ Format invalide ! Utilisez un nombre suivi de `m` (minutes), `h` (heures) ou `j` (jours).")

    # Calcul de la durée
    time_deltas = {"m": timedelta(minutes=duration), "h": timedelta(hours=duration), "j": timedelta(days=duration)}
    duration_time = time_deltas[unit]

    try:
        # Tente de mettre le membre en timeout
        await member.timeout(duration_time, reason=reason)
        duration_str = f"{duration} {time_units[unit]}"
        
        # Embeds et réponses
        embed = create_embed("⏳ Mute", f"{member.mention} a été muté pour {duration_str}.", discord.Color.blue(), ctx, member, "Mute", reason, duration_str)
        await ctx.send(embed=embed)
        await send_log(ctx, member, "Mute", reason, duration_str)
        await send_dm(member, "Mute", reason, duration_str)

        # Ajout des sanctions dans la base de données MongoDB
        sanction_data = {
            "guild_id": str(ctx.guild.id),
            "user_id": str(member.id),
            "action": "Mute",
            "reason": reason,
            "duration": duration_str,
            "timestamp": datetime.utcnow()
        }
        collection7.insert_one(sanction_data)  # collection7 est la collection de sanctions
        
    except discord.Forbidden:
        await ctx.send("❌ Je n'ai pas la permission de mute ce membre. Vérifiez les permissions du bot.")
    except discord.HTTPException as e:
        await ctx.send(f"❌ Une erreur s'est produite lors de l'application du mute : {e}")
    except Exception as e:
        await ctx.send(f"❌ Une erreur inattendue s'est produite : {str(e)}")

@bot.command()
async def unmute(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send("❌ Il manque un argument : vous devez mentionner un membre à démuter.")

    if has_permission(ctx, "moderate_members"):
        await member.timeout(None)
        embed = create_embed("🔊 Unmute", f"{member.mention} a été démuté.", discord.Color.green(), ctx, member, "Unmute", "Fin du mute")
        await ctx.send(embed=embed)
        await send_log(ctx, member, "Unmute", "Fin du mute")
        await send_dm(member, "Unmute", "Fin du mute")

# Fonction de vérification des permissions
async def check_permissions(ctx):
    # Vérifier si l'utilisateur a la permission "Manage Messages"
    return ctx.author.guild_permissions.manage_messages or ctx.author.id == 1166334752186433567

# Fonction pour vérifier si le membre est immunisé
async def is_immune(member):
    # Exemple de logique d'immunité (peut être ajustée)
    # Vérifie si le membre a un rôle spécifique ou une permission
    return any(role.name == "Immunité" for role in member.roles)

# Fonction pour envoyer un message de log
async def send_log(ctx, member, action, reason):
    log_channel = discord.utils.get(ctx.guild.text_channels, name="logs")  # Remplacer par le salon de log approprié
    if log_channel:
        embed = discord.Embed(
            title="Avertissement",
            description=f"**Membre :** {member.mention}\n**Action :** {action}\n**Raison :** {reason}",
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"Avertissement donné par {ctx.author}", icon_url=ctx.author.avatar.url)
        await log_channel.send(embed=embed)

# Fonction pour envoyer un message en DM au membre
async def send_dm(member, action, reason):
    try:
        embed = discord.Embed(
            title="⚠️ Avertissement",
            description=f"**Action :** {action}\n**Raison :** {reason}",
            color=discord.Color.red()
        )
        embed.set_footer(text="N'oublie pas de respecter les règles !")
        await member.send(embed=embed)
    except discord.Forbidden:
        print(f"Impossible d'envoyer un message privé à {member.name}")

@bot.command()
async def warn(ctx, member: discord.Member = None, *, reason="Aucune raison spécifiée"):
    if member is None:
        return await ctx.send("❌ Il manque un argument : vous devez mentionner un membre à avertir.")

    if ctx.author == member:
        return await ctx.send("🚫 Vous ne pouvez pas vous avertir vous-même.")
    
    if is_higher_or_equal(ctx, member):
        return await ctx.send("🚫 Vous ne pouvez pas avertir quelqu'un de votre niveau ou supérieur.")
    
    if not has_permission(ctx, "moderate_members"):
        return await ctx.send("❌ Vous n'avez pas la permission de donner des avertissements.")
    
    try:
        # Ajout du warning à la base de données
        sanction_data = {
            "guild_id": str(ctx.guild.id),
            "user_id": str(member.id),
            "action": "Warn",
            "reason": reason,
            "timestamp": datetime.utcnow()
        }

        # Tentative d'insertion dans MongoDB
        collection7.insert_one(sanction_data)
        print(f"Sanction ajoutée à la base de données pour {member.mention}")

        # Embeds et réponses
        embed = create_embed("⚠️ Avertissement donné", f"{member.mention} a reçu un avertissement pour la raison suivante :\n{reason}", discord.Color.orange(), ctx, member, "Avertissement", reason)
        await ctx.send(embed=embed)
        await send_log(ctx, member, "Warn", reason)
        await send_dm(member, "Avertissement", reason)

    except Exception as e:
        # Log de l'erreur dans la console pour faciliter le débogage
        print(f"Erreur lors de l'exécution de la commande warn : {e}")
        await ctx.send(f"❌ Une erreur s'est produite lors de l'exécution de la commande. Détails : {str(e)}")

@bot.command()
async def warnlist(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send("❌ Il manque un argument : vous devez mentionner un membre.")
    
    sanctions = collection7.find({
        "guild_id": str(ctx.guild.id),
        "user_id": str(member.id),
        "action": "Warn"
    })

    count = collection7.count_documents({
        "guild_id": str(ctx.guild.id),
        "user_id": str(member.id),
        "action": "Warn"
    })

    if count == 0:
        return await ctx.send(f"✅ {member.mention} n'a aucun avertissement.")

    embed = discord.Embed(title=f"Avertissements de {member.name}", color=discord.Color.orange())
    for sanction in sanctions:
        date = sanction["timestamp"].strftime("%d/%m/%Y à %Hh%M")
        embed.add_field(name=f"Le {date}", value=sanction["reason"], inline=False)

    await ctx.send(embed=embed)


#------------------------------------------------------------------------- Commandes Utilitaires : +vc, +alerte, +uptime, +ping, +roleinfo

# Nouvelle fonction pour récupérer le ping role et le channel id dynamiquement depuis la base de données
def get_guild_setup_data(guild_id):
    setup_data = load_guild_settings(guild_id)
    ping_role_id = setup_data.get('staff_role_id')  # Assure-toi que le champ existe dans ta base de données
    channel_id = setup_data.get('sanctions_channel_id')  # Pareil pour le channel ID
    return ping_role_id, channel_id

@bot.command()
async def alerte(ctx, member: discord.Member, *, reason: str):
    # Vérification si l'utilisateur a le rôle nécessaire pour exécuter la commande
    if access_role_id not in [role.id for role in ctx.author.roles]:
        await ctx.send("Vous n'avez pas les permissions nécessaires pour utiliser cette commande.")
        return

    # Récupération des valeurs dynamiques
    ping_role_id, channel_id = get_guild_setup_data(ctx.guild.id)

    # Obtention du salon où envoyer le message
    channel = bot.get_channel(channel_id)

    # Mentionner le rôle et l'utilisateur qui a exécuté la commande dans le message
    await channel.send(f"<@&{ping_role_id}>\n📢 Alerte émise par {ctx.author.mention}: {member.mention} - Raison : {reason}")

    # Création de l'embed
    embed = discord.Embed(
        title="Alerte Émise",
        description=f"**Utilisateur:** {member.mention}\n**Raison:** {reason}",
        color=0xff0000  # Couleur rouge
    )
    embed.set_footer(text=f"Commandé par {ctx.author.name} |♥️by Iseyg", icon_url=ctx.author.avatar.url)
    # Envoi de l'embed dans le même salon
    await channel.send(embed=embed)

sent_embed_channels = {}

@bot.command()
async def vc(ctx):
    print("Commande 'vc' appelée.")

    try:
        guild = ctx.guild
        print(f"Guild récupérée: {guild.name} (ID: {guild.id})")

        total_members = guild.member_count
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        voice_members = sum(len(voice_channel.members) for voice_channel in guild.voice_channels)
        boosts = guild.premium_subscription_count or 0
        owner_member = guild.owner
        server_invite = "https://discord.gg/X4dZAt3BME"
        verification_level = guild.verification_level.name
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        server_created_at = guild.created_at.strftime('%d %B %Y')

        embed = discord.Embed(title=f"📊 Statistiques de {guild.name}", color=discord.Color.purple())

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="👥 Membres", value=f"**{total_members}**", inline=True)
        embed.add_field(name="🟢 Membres en ligne", value=f"**{online_members}**", inline=True)
        embed.add_field(name="🎙️ En vocal", value=f"**{voice_members}**", inline=True)
        embed.add_field(name="💎 Boosts", value=f"**{boosts}**", inline=True)

        embed.add_field(name="👑 Propriétaire", value=f"<@{owner_member.id}>", inline=True)
        embed.add_field(name="🔒 Niveau de vérification", value=f"**{verification_level}**", inline=True)
        embed.add_field(name="📝 Canaux textuels", value=f"**{text_channels}**", inline=True)
        embed.add_field(name="🔊 Canaux vocaux", value=f"**{voice_channels}**", inline=True)
        embed.add_field(name="📅 Créé le", value=f"**{server_created_at}**", inline=False)
        embed.add_field(name="🔗 Lien du serveur", value=f"[{guild.name}]({server_invite})", inline=False)

        embed.set_footer(text="📈 Statistiques mises à jour en temps réel | ♥️ by Iseyg")

        await ctx.send(embed=embed)
        print("Embed envoyé avec succès.")

    except Exception as e:
        print(f"Erreur lors de l'exécution de la commande 'vc': {e}")
        await ctx.send("Une erreur est survenue lors de l'exécution de la commande.")
        return  # Empêche l'exécution du reste du code après une erreur


@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)  # Latence en ms
    embed = discord.Embed(title="Pong!", description=f"Latence: {latency}ms", color=discord.Color.green())

    await ctx.send(embed=embed)

@bot.tree.command(name="info-rôle", description="Obtenez des informations détaillées sur un rôle")
async def roleinfo(interaction: discord.Interaction, role: discord.Role):
    # Vérifier si le rôle existe
    if role is None:
        embed = discord.Embed(title="Erreur", description="Rôle introuvable.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    else:
        # Obtenir tous les rôles triés du plus haut au plus bas
        sorted_roles = sorted(interaction.guild.roles, key=lambda r: r.position, reverse=True)
        total_roles = len(sorted_roles)
        
        # Trouver la position inversée du rôle
        inverse_position = total_roles - sorted_roles.index(role)

        embed = discord.Embed(
            title=f"Informations sur le rôle: {role.name}",
            color=role.color,
            timestamp=interaction.created_at
        )
        
        embed.set_thumbnail(url=interaction.guild.icon.url)
        embed.add_field(name="ID", value=role.id, inline=False)
        embed.add_field(name="Couleur", value=str(role.color), inline=False)
        embed.add_field(name="Nombre de membres", value=len(role.members), inline=False)
        embed.add_field(name="Position dans la hiérarchie", value=f"{inverse_position}/{total_roles}", inline=False)
        embed.add_field(name="Mentionnable", value=role.mentionable, inline=False)
        embed.add_field(name="Gérer les permissions", value=role.managed, inline=False)
        embed.add_field(name="Créé le", value=role.created_at.strftime("%d/%m/%Y à %H:%M:%S"), inline=False)
        embed.add_field(name="Mention", value=role.mention, inline=False)

        embed.set_footer(text=f"Commande demandée par {interaction.user.name}", icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed)

@bot.command()
async def uptime(ctx):
    uptime_seconds = round(time.time() - start_time)
    days = uptime_seconds // (24 * 3600)
    hours = (uptime_seconds % (24 * 3600)) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    embed = discord.Embed(
        title="Uptime du bot",
        description=f"Le bot est en ligne depuis : {days} jours, {hours} heures, {minutes} minutes, {seconds} secondes",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"♥️by Iseyg", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

PRIME_IMAGE_URL = "https://cdn.gamma.app/m6u5udkwwfl3cxy/generated-images/MUnIIu5yOv6nMFAXKteig.jpg"

class DuelView(discord.ui.View):
    def __init__(self, player1, player2, prize, ctx):
        super().__init__(timeout=120)  # Augmenter le timeout à 120 secondes
        self.player1 = player1
        self.player2 = player2
        self.hp1 = 100
        self.hp2 = 100
        self.turn = player1
        self.prize = prize
        self.ctx = ctx
        self.winner = None

    async def update_message(self, interaction):
        embed = discord.Embed(title="⚔️ Duel en cours !", color=discord.Color.red())
        embed.add_field(name=f"{self.player1.display_name}", value=f"❤️ {self.hp1} PV", inline=True)
        embed.add_field(name=f"{self.player2.display_name}", value=f"❤️ {self.hp2} PV", inline=True)
        embed.set_footer(text=f"Tour de {self.turn.display_name}")
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Attaquer", style=discord.ButtonStyle.red)
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.turn:
            await interaction.response.send_message("Ce n'est pas ton tour !", ephemeral=True)
            return

        success_chance = random.random()
        if success_chance > 0.2:  # 80% chance de succès
            damage = random.randint(15, 50)
            if self.turn == self.player1:
                self.hp2 -= damage
                self.turn = self.player2
            else:
                self.hp1 -= damage
                self.turn = self.player1
        else:
            await interaction.response.send_message(f"{interaction.user.mention} rate son attaque !", ephemeral=False)
            self.turn = self.player2 if self.turn == self.player1 else self.player1

        await self.check_winner(interaction)

    @discord.ui.button(label="Esquiver", style=discord.ButtonStyle.blurple)
    async def dodge(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.turn:
            await interaction.response.send_message("Ce n'est pas ton tour !", ephemeral=True)
            return

        success = random.random() < 0.5
        if success:
            await interaction.response.send_message(f"{interaction.user.mention} esquive l'attaque avec succès !", ephemeral=False)
        else:
            damage = random.randint(15, 30)
            if self.turn == self.player1:
                self.hp1 -= damage
            else:
                self.hp2 -= damage

        await self.check_winner(interaction)
        await self.update_message(interaction)

    async def check_winner(self, interaction):
        if self.hp1 <= 0:
            self.winner = self.player2
            await self.end_duel(interaction, self.player2, self.player1)
        elif self.hp2 <= 0:
            self.winner = self.player1
            await self.end_duel(interaction, self.player1, self.player2)
        else:
            await self.update_message(interaction)

async def end_duel(self, interaction, winner, loser):
    embed = discord.Embed(title="🏆 Victoire !", description=f"{winner.mention} remporte le duel !", color=discord.Color.green())
    await interaction.response.edit_message(embed=embed, view=None)
    channel = self.ctx.guild.get_channel(BOUNTY_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)

    # Vérifier si le perdant avait une prime
    bounty_data = collection3.find_one({"guild_id": str(self.ctx.guild.id), "user_id": str(loser.id)})  # Utilisation de collection3
    if bounty_data:
        prize = bounty_data["prize"]
        if winner.id != loser.id:  # Seulement si le gagnant n'était PAS celui avec la prime
            # Ajouter la prime au chasseur
            collection3.update_one(  # Utilisation de collection3
                {"guild_id": str(self.ctx.guild.id), "user_id": str(winner.id)},
                {"$inc": {"reward": prize}}  # Ajouter la prime à la récompense du gagnant
            )

        # Supprimer la prime du joueur capturé
        collection3.update_one(  # Utilisation de collection3
            {"guild_id": str(self.ctx.guild.id), "user_id": str(loser.id)},
            {"$unset": {"prize": ""}}  # Enlever la prime du joueur capturé
        )

        # Supprimer la prime du joueur capturé (cette ligne ne doit pas être indentée davantage)
        del bounties[loser.id]

@bot.command()
async def bounty(ctx, member: discord.Member, prize: int):
    """Met une prime sur un joueur (réservé aux administrateurs)"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Tu n'as pas la permission d'exécuter cette commande.")
        return

    try:
        # Mise à jour de la prime dans la base de données
        bounty_data = {
            "guild_id": str(ctx.guild.id),
            "user_id": str(member.id),
            "prize": prize,
            "reward": 0  # Initialiser les récompenses à 0
        }

        # Insérer ou mettre à jour la prime
        collection3.update_one(
            {"guild_id": str(ctx.guild.id), "user_id": str(member.id)},
            {"$set": bounty_data},
            upsert=True  # Créer un nouveau document si l'utilisateur n'a pas de prime
        )

        embed = discord.Embed(title="📜 Nouvelle Prime !", description=f"Une prime de {prize} Ezryn Coins a été placée sur {member.mention} !", color=discord.Color.gold())
        embed.set_image(url=PRIME_IMAGE_URL)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Erreur lors de la mise à jour de la prime : {e}")


# Remplacer l'utilisation de bounties par la récupération depuis la base de données.
@bot.command()
async def capture(ctx, target: discord.Member):
    """Déclenche un duel pour capturer un joueur avec une prime"""
    # Récupérer la prime directement depuis la base de données
    bounty_data = collection3.find_one({"guild_id": str(ctx.guild.id), "user_id": str(target.id)})
    if not bounty_data:
        await ctx.send("Ce joueur n'a pas de prime sur sa tête !")
        return

    prize = bounty_data["prize"]
    view = DuelView(ctx.author, target, prize, ctx)
    embed = discord.Embed(title="🎯 Chasse en cours !", description=f"{ctx.author.mention} tente de capturer {target.mention} ! Un duel commence !", color=discord.Color.orange())
    await ctx.send(embed=embed, view=view)


@bot.command()
async def ptop(ctx):
    """Affiche le classement des primes en ordre décroissant"""
    # Récupérer toutes les primes depuis la base de données
    bounties_data = collection3.find({"guild_id": str(ctx.guild.id)})
    if not bounties_data:
        await ctx.send("📉 Il n'y a actuellement aucune prime en cours.")
        return

    sorted_bounties = sorted(bounties_data, key=lambda x: x['prize'], reverse=True)
    embed = discord.Embed(title="🏆 Classement des Primes", color=discord.Color.gold())

    for index, bounty in enumerate(sorted_bounties, start=1):
        member = ctx.guild.get_member(int(bounty['user_id']))
        if member:
            embed.add_field(name=f"#{index} - {member.display_name}", value=f"💰 **{bounty['prize']} Ezryn Coins**", inline=False)

    embed.set_thumbnail(url=PRIME_IMAGE_URL)
    await ctx.send(embed=embed)

@bot.command()
async def prime(ctx, member: discord.Member = None):
    """Affiche la prime du joueur ou de l'utilisateur"""
    member = member or ctx.author  # Par défaut, on affiche la prime du commanditaire

    # Récupérer les données de la base de données
    bounty_data = collection3.find_one({"guild_id": str(ctx.guild.id), "user_id": str(member.id)})

    if not bounty_data:
        embed = discord.Embed(title="📉 Aucune prime !", description=f"Aucune prime n'est actuellement placée sur **{member.mention}**.", color=discord.Color.red())
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)
    else:
        prize = bounty_data["prize"]
        embed = discord.Embed(title="💰 Prime actuelle", description=f"La prime sur **{member.mention}** est de **{prize} Ezryn Coins**.", color=discord.Color.green())
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)


@bot.command()
async def rewards(ctx, member: discord.Member = None):
    """Affiche les récompenses accumulées par un joueur ou par soi-même"""
    member = member or ctx.author  # Si aucun membre n'est spécifié, on affiche pour l'auteur

    # Récupérer les récompenses du joueur depuis la base de données
    bounty_data = collection3.find_one({"guild_id": str(ctx.guild.id), "user_id": str(member.id)})

    if bounty_data:
        reward = bounty_data.get("reward", 0)
    else:
        reward = 0

    embed = discord.Embed(
        title="🏅 Récompenses de chasse",
        description=f"💰 **{member.mention}** possède **{reward} Ezryn Coins** en récompenses.",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.avatar.url)
    await ctx.send(embed=embed)


@bot.command()
async def rrewards(ctx, target: discord.Member, amount: int):
    """Commande réservée aux admins pour retirer des récompenses à un joueur"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("🚫 Tu n'as pas la permission d'utiliser cette commande.")
        return

    if target.id not in hunter_rewards or hunter_rewards[target.id] < amount:
        await ctx.send(f"❌ **{target.mention}** n'a pas assez de récompenses.")
        return

    hunter_rewards[target.id] -= amount
    embed = discord.Embed(
        title="⚠️ Récompenses modifiées",
        description=f"🔻 **{amount}** Ezryn Coins retirés à **{target.mention}**.\n💰 Nouveau solde : **{hunter_rewards[target.id]}**.",
        color=discord.Color.orange()
    )
    embed.set_thumbnail(url=target.avatar.url)
    await ctx.send(embed=embed)


@bot.tree.command(name="calcul", description="Effectue une opération mathématique")
@app_commands.describe(nombre1="Le premier nombre", operation="L'opération à effectuer (+, -, *, /)", nombre2="Le deuxième nombre")
async def calcul(interaction: discord.Interaction, nombre1: float, operation: str, nombre2: float):
    await interaction.response.defer()  # ✅ Correctement placé à l'intérieur de la fonction

    if operation == "+":
        resultat = nombre1 + nombre2
    elif operation == "-":
        resultat = nombre1 - nombre2
    elif operation == "*":
        resultat = nombre1 * nombre2
    elif operation == "/":
        if nombre2 != 0:
            resultat = nombre1 / nombre2
        else:
            await interaction.followup.send("❌ Erreur : Division par zéro impossible.")
            return
    else:
        await interaction.followup.send("❌ Opération invalide. Utilisez '+', '-', '*', ou '/'.")
        return

    embed = discord.Embed(
        title="📊 Résultat du calcul",
        description=f"{nombre1} {operation} {nombre2} = **{resultat}**",
        color=discord.Color.green()
    )

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="calcul_pourcentage", description="Calcule un pourcentage d'un nombre")
@app_commands.describe(nombre="Le nombre de base", pourcentage="Le pourcentage à appliquer (ex: 15 pour 15%)")
async def calcul(interaction: discord.Interaction, nombre: float, pourcentage: float):
    await interaction.response.defer()  # ✅ Correctement placé à l'intérieur de la fonction

    resultat = (nombre * pourcentage) / 100
    embed = discord.Embed(
        title="📊 Calcul de pourcentage",
        description=f"{pourcentage}% de {nombre} = **{resultat}**",
        color=discord.Color.green()
    )

    await interaction.followup.send(embed=embed)

# Installer PyNaCl 
try:
    import nacl
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyNaCl"])

#------------------------------------------------------------------------- Commande Voice : /connect, /disconnect
# Commande /connect
@bot.tree.command(name="connect", description="Connecte le bot à un salon vocal spécifié.")
@app_commands.describe(channel="Choisissez un salon vocal où connecter le bot")
@commands.has_permissions(administrator=True)
async def connect(interaction: discord.Interaction, channel: discord.VoiceChannel):
    try:
        if not interaction.guild.voice_client:
            await channel.connect()
            embed = discord.Embed(
                title="✅ Connexion réussie !",
                description=f"Le bot a rejoint **{channel.name}**.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="⚠️ Déjà connecté",
                description="Le bot est déjà dans un salon vocal.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Erreur",
            description=f"Une erreur est survenue : `{e}`",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

# Commande /disconnect
@bot.tree.command(name="disconnect", description="Déconnecte le bot du salon vocal.")
@commands.has_permissions(administrator=True)
async def disconnect(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        embed = discord.Embed(
            title="🚫 Déconnexion réussie",
            description="Le bot a quitté le salon vocal.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title="⚠️ Pas connecté",
            description="Le bot n'est dans aucun salon vocal.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)
#------------------------------------------------------------------------------------------

# Commande pour ajouter une idée (sans restriction d'administrateur)
@bot.tree.command(name="idée", description="Rajoute une idée dans la liste")
async def ajouter_idee(interaction: discord.Interaction, idee: str):
    user_id = interaction.user.id  # Utilisation de interaction.user.id pour obtenir l'ID utilisateur
    
    # Vérifier si l'utilisateur a déjà des idées dans la base de données
    idees_data = collection8.find_one({"user_id": str(user_id)})
    
    if idees_data:
        # Si des idées existent déjà, on ajoute l'idée à la liste existante
        collection8.update_one(
            {"user_id": str(user_id)},
            {"$push": {"idees": idee}}  # Ajoute l'idée à la liste des idées existantes
        )
    else:
        # Si l'utilisateur n'a pas encore d'idées, on crée un nouveau document avec cette idée
        collection8.insert_one({
            "user_id": str(user_id),
            "idees": [idee]  # Crée une nouvelle liste d'idées avec l'idée ajoutée
        })
    
    embed = discord.Embed(title="Idée ajoutée !", description=f"**{idee}** a été enregistrée.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)


# Commande pour lister les idées
@bot.command(name="listi")
async def liste_idees(ctx):
    user_id = ctx.author.id
    
    # Chercher les idées de l'utilisateur dans la base de données
    idees_data = collection8.find_one({"user_id": str(user_id)})
    
    if not idees_data or not idees_data.get("idees"):
        embed = discord.Embed(title="Aucune idée enregistrée", description="Ajoute-en une avec /idées !", color=discord.Color.red())
    else:
        embed = discord.Embed(title="Tes idées", color=discord.Color.blue())
        for idx, idee in enumerate(idees_data["idees"], start=1):
            embed.add_field(name=f"Idée {idx}", value=idee, inline=False)
    
    await ctx.send(embed=embed)


# Commande pour supprimer une idée
@bot.tree.command(name="remove_idee", description="Supprime une de tes idées enregistrées")
async def remove_idee(interaction: discord.Interaction):
    user_id = interaction.user.id  # Utilisation de interaction.user.id pour obtenir l'ID utilisateur
    
    # Chercher les idées de l'utilisateur dans la base de données
    idees_data = collection8.find_one({"user_id": str(user_id)})
    
    if not idees_data or not idees_data.get("idees"):
        embed = discord.Embed(title="Aucune idée enregistrée", description="Ajoute-en une avec /idées !", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return

    idees = idees_data["idees"]

    # Créer un menu déroulant pour permettre à l'utilisateur de choisir une idée à supprimer
    options = [discord.SelectOption(label=f"Idée {idx+1}: {idee}", value=str(idx)) for idx, idee in enumerate(idees)]
    
    select = Select(placeholder="Choisis une idée à supprimer", options=options)
    
    # Définir l'interaction pour supprimer l'idée
    async def select_callback(interaction: discord.Interaction):
        selected_idee_index = int(select.values[0])
        idee_a_supprimer = idees[selected_idee_index]
        
        # Supprimer l'idée sélectionnée de la base de données
        collection8.update_one(
            {"user_id": str(user_id)},
            {"$pull": {"idees": idee_a_supprimer}}  # Supprime l'idée de la liste
        )
        
        embed = discord.Embed(
            title="Idée supprimée !",
            description=f"L'idée **{idee_a_supprimer}** a été supprimée.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    select.callback = select_callback

    view = View()
    view.add_item(select)
    
    embed = discord.Embed(
        title="Choisis l'idée à supprimer",
        description="Sélectionne une idée à supprimer dans le menu déroulant.",
        color=discord.Color.orange()
    )
    
    await interaction.response.send_message(embed=embed, view=view)

#--------------------------------------------------------------------------------------------
# Stockage des suggestions
suggestions = []

# Dictionnaire pour gérer le cooldown des utilisateurs
user_cooldown = {}

class SuggestionModal(discord.ui.Modal, title="💡 Nouvelle Suggestion"):
    def __init__(self):
        super().__init__()

        self.add_item(discord.ui.TextInput(
            label="💬 Votre suggestion",
            style=discord.TextStyle.long,
            placeholder="Décrivez votre suggestion ici...",
            required=True,
            max_length=500
        ))

        self.add_item(discord.ui.TextInput(
            label="🎯 Cela concerne Etherya ou le Bot ?",
            style=discord.TextStyle.short,
            placeholder="Tapez 'Etherya' ou 'Bot'",
            required=True
        ))

        self.add_item(discord.ui.TextInput(
            label="❔ Pourquoi cette suggestion ?",
            style=discord.TextStyle.paragraph,
            placeholder="Expliquez pourquoi cette idée est utile...",
            required=False
        ))

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        # Anti-spam: vérifier cooldown
        if user_id in user_cooldown and time.time() - user_cooldown[user_id] < 60:
            return await interaction.response.send_message(
                "❌ Tu dois attendre avant de soumettre une nouvelle suggestion. Patiente un peu !", ephemeral=True
            )

        user_cooldown[user_id] = time.time()  # Enregistrer le temps du dernier envoi

        suggestion = self.children[0].value.strip()  # Texte de la suggestion
        choice = self.children[1].value.strip().lower()  # Sujet (etherya ou bot)
        reason = self.children[2].value.strip() if self.children[2].value else "Non précisé"

        # Vérification du choix
        if choice in ["etherya", "eth", "e"]:
            choice = "Etherya"
            color = discord.Color.gold()
        elif choice in ["bot", "b"]:
            choice = "Le Bot"
            color = discord.Color.blue()
        else:
            return await interaction.response.send_message(
                "❌ Merci de spécifier un sujet valide : 'Etherya' ou 'Bot'.", ephemeral=True
            )

        channel = interaction.client.get_channel(SUGGESTION_CHANNEL_ID)
        if not channel:
            return await interaction.response.send_message("❌ Je n'ai pas pu trouver le salon des suggestions.", ephemeral=True)

        new_user_mention = f"<@&{SUGGESTION_ROLE}>"

        # Envoie un message de notification à l'utilisateur spécifique
        await channel.send(f"{new_user_mention} 🔔 **Nouvelle suggestion concernant {choice} !**")

        # Création de l'embed
        embed = discord.Embed(
            title="💡 Nouvelle Suggestion !",
            description=f"📝 **Proposée par** {interaction.user.mention}\n\n>>> {suggestion}",
            color=color,
            timestamp=discord.utils.utcnow()
        )

        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3039/3039569.png")  # Icône idée
        embed.add_field(name="📌 Sujet", value=f"**{choice}**", inline=True)
        embed.add_field(name="❔ Pourquoi ?", value=reason, inline=False)
        embed.set_footer(
            text=f"Envoyée par {interaction.user.display_name}",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )

        # Envoi de l'embed
        message = await channel.send(embed=embed)

        # Ajouter les réactions
        await message.add_reaction("❤️")  # Aimer l'idée
        await message.add_reaction("🔄")  # Idée à améliorer
        await message.add_reaction("✅")  # Pour
        await message.add_reaction("❌")  # Contre

        # Sauvegarde de la suggestion pour afficher avec la commande /suggestions
        suggestions.append({
            "message_id": message.id,
            "author": interaction.user,
            "suggestion": suggestion,
            "timestamp": time.time()
        })

        # Confirme l'envoi avec un message sympathique
        await interaction.response.send_message(
            f"✅ **Ta suggestion a été envoyée avec succès !**\nNous attendons les votes des autres membres... 🕒",
            ephemeral=True
        )

        # Envoi d'un message privé à l'auteur
        try:
            dm_embed = discord.Embed(
                title="📩 Suggestion envoyée !",
                description=f"Merci pour ta suggestion ! Voici les détails :\n\n**🔹 Sujet** : {choice}\n**💡 Suggestion** : {suggestion}",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            dm_embed.set_footer(text="Nous te remercions pour ton aide et tes idées ! 🙌")
            await interaction.user.send(embed=dm_embed)
        except discord.Forbidden:
            print(f"[ERREUR] Impossible d'envoyer un MP à {interaction.user.display_name}.")
            # Avertir l'utilisateur dans le salon de suggestions si DM est bloqué
            await channel.send(f"❗ **{interaction.user.display_name}**, il semble que je ne puisse pas t'envoyer un message privé. Vérifie tes paramètres de confidentialité pour autoriser les MPs.")
            
@bot.tree.command(name="suggestion", description="💡 Envoie une suggestion pour Etherya ou le Bot")
async def suggest(interaction: discord.Interaction):
    """Commande pour envoyer une suggestion"""
    await interaction.response.send_modal(SuggestionModal())

# Commande pour afficher les dernières suggestions
@bot.tree.command(name="suggestions", description="📢 Affiche les dernières suggestions")
async def suggestions_command(interaction: discord.Interaction):
    """Commande pour afficher les dernières suggestions"""
    if not suggestions:
        return await interaction.response.send_message("❌ Aucune suggestion en cours. Sois le premier à proposer une idée !", ephemeral=True)

    # Récupérer les 5 dernières suggestions
    recent_suggestions = suggestions[-5:]

    embeds = []
    for suggestion_data in recent_suggestions:
        embed = discord.Embed(
            title="💡 Suggestion",
            description=f"📝 **Proposée par** {suggestion_data['author'].mention}\n\n>>> {suggestion_data['suggestion']}",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Envoyée le {discord.utils.format_dt(discord.utils.snowflake_time(suggestion_data['message_id']), 'F')}")
        embeds.append(embed)

    # Envoi des embeds
    await interaction.response.send_message(embeds=embeds)
#-------------------------------------------------------------------------------- Sondage: /sondage

# Stockage des sondages
polls = []

# Dictionnaire pour gérer le cooldown des utilisateurs
user_cooldown = {}

class PollModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="📊 Nouveau Sondage")

        self.add_item(discord.ui.TextInput(
            label="❓ Question du sondage",
            style=discord.TextStyle.long,
            placeholder="Tapez la question du sondage ici...",
            required=True,
            max_length=500
        ))

        self.add_item(discord.ui.TextInput(
            label="🗳️ Options du sondage (séparées par des virgules)",
            style=discord.TextStyle.short,
            placeholder="Option 1, Option 2, Option 3...",
            required=True
        ))

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        # Anti-spam: vérifier cooldown
        if user_id in user_cooldown and time.time() - user_cooldown[user_id] < 60:
            return await interaction.response.send_message(
                "❌ Tu dois attendre avant de soumettre un nouveau sondage. Patiente un peu !", ephemeral=True
            )

        user_cooldown[user_id] = time.time()  # Enregistrer le temps du dernier envoi

        question = self.children[0].value.strip()  # Question du sondage
        options = [opt.strip() for opt in self.children[1].value.split(",")]  # Options du sondage

        if len(options) < 2:
            return await interaction.response.send_message(
                "❌ Tu dois fournir au moins deux options pour le sondage.", ephemeral=True
            )

        # Vérification du salon des sondages
        channel = interaction.client.get_channel(SONDAGE_CHANNEL_ID)
        if not channel:
            return await interaction.response.send_message("❌ Je n'ai pas pu trouver le salon des sondages.", ephemeral=True)

        new_user_mention = f"<@&{SONDAGE_ID}>"

        # Envoie un message de notification à l'utilisateur spécifique
        await channel.send(f"{new_user_mention} 🔔 **Nouveau sondage à répondre !**")

        # Création de l'embed pour le sondage
        avatar_url = interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url

        embed = discord.Embed(
            title="📊 Nouveau Sondage !",
            description=f"📝 **Proposé par** {interaction.user.mention}\n\n>>> {question}",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )

        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3001/3001265.png")  # Icône sondage
        embed.add_field(name="🔘 Options", value="\n".join([f"{idx + 1}. {option}" for idx, option in enumerate(options)]), inline=False)
        embed.set_footer(text=f"Envoyé par {interaction.user.display_name}", icon_url=avatar_url)

        # Envoi de l'embed
        message = await channel.send(embed=embed)

        # Ajout des réactions (limite de 10 options)
        reactions = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮", "🇯"]
        for idx in range(min(len(options), len(reactions))):
            await message.add_reaction(reactions[idx])

        # Sauvegarde du sondage pour afficher avec la commande /sondages
        polls.append({
            "message_id": message.id,
            "author": interaction.user,
            "question": question,
            "options": options,
            "timestamp": time.time()
        })

        # Confirme l'envoi avec un message sympathique
        await interaction.response.send_message(
            f"✅ **Ton sondage a été envoyé avec succès !**\nLes membres peuvent maintenant répondre en choisissant leurs options. 🕒",
            ephemeral=True
        )

        # Envoi d'un message privé à l'auteur
        try:
            dm_embed = discord.Embed(
                title="📩 Sondage envoyé !",
                description=f"Merci pour ton sondage ! Voici les détails :\n\n**❓ Question** : {question}\n**🔘 Options** : {', '.join(options)}",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            dm_embed.set_footer(text="Merci pour ta participation et tes idées ! 🙌")
            await interaction.user.send(embed=dm_embed)
        except discord.Forbidden:
            print(f"[ERREUR] Impossible d'envoyer un MP à {interaction.user.display_name}.")
            await channel.send(f"❗ **{interaction.user.display_name}**, je ne peux pas t'envoyer de message privé. Vérifie tes paramètres de confidentialité.")

@bot.tree.command(name="sondage", description="📊 Crée un sondage pour la communauté")
async def poll(interaction: discord.Interaction):
    """Commande pour créer un sondage"""
    await interaction.response.send_modal(PollModal())

# Commande pour afficher les derniers sondages
@bot.tree.command(name="sondages", description="📢 Affiche les derniers sondages")
async def polls_command(interaction: discord.Interaction):
    """Commande pour afficher les derniers sondages"""
    if not polls:
        return await interaction.response.send_message("❌ Aucun sondage en cours. Sois le premier à en créer un !", ephemeral=True)

    # Récupérer les 5 derniers sondages
    recent_polls = polls[-5:]

    embeds = []
    for poll_data in recent_polls:
        embed = discord.Embed(
            title="📊 Sondage",
            description=f"📝 **Proposé par** {poll_data['author'].mention}\n\n>>> {poll_data['question']}",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="🔘 Options", value="\n".join([f"{idx + 1}. {option}" for idx, option in enumerate(poll_data['options'])]), inline=False)
        embed.set_footer(text=f"Envoyé le {discord.utils.format_dt(discord.utils.snowflake_time(poll_data['message_id']), 'F')}")
        embeds.append(embed)

    # Envoi des embeds
    await interaction.response.send_message(embeds=embeds)

#-------------------------------------------------------------------------------- Rappel: /rappel

# Commande de rappel
@bot.tree.command(name="rappel", description="Définis un rappel avec une durée, une raison et un mode d'alerte.")
@app_commands.describe(
    duree="Durée du rappel (format: nombre suivi de 's', 'm', 'h' ou 'd')",
    raison="Pourquoi veux-tu ce rappel ?",
    mode="Où voulez-vous que je vous rappelle ceci ?"
)
@app_commands.choices(
    mode=[
        app_commands.Choice(name="Message Privé", value="prive"),
        app_commands.Choice(name="Salon", value="salon")
    ]
)
async def rappel(interaction: discord.Interaction, duree: str, raison: str, mode: app_commands.Choice[str]):
    # Vérification du format de durée
    if not duree[:-1].isdigit() or duree[-1] not in "smhd":
        await interaction.response.send_message(
            "Format de durée invalide. Utilisez un nombre suivi de 's' (secondes), 'm' (minutes), 'h' (heures) ou 'd' (jours).",
            ephemeral=True
        )
        return
    
    # Parsing de la durée
    time_value = int(duree[:-1])  # Extrait le nombre
    time_unit = duree[-1]  # Extrait l'unité de temps
    
    # Convertir la durée en secondes
    conversion = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    total_seconds = time_value * conversion[time_unit]
    
    # Limiter la durée du rappel (max 7 jours pour éviter les abus)
    max_seconds = 7 * 86400  # 7 jours
    if total_seconds > max_seconds:
        await interaction.response.send_message(
            "La durée du rappel ne peut pas dépasser 7 jours (604800 secondes).",
            ephemeral=True
        )
        return
    
    # Confirmation du rappel
    embed = discord.Embed(
        title="🔔 Rappel programmé !",
        description=f"**Raison :** {raison}\n**Durée :** {str(timedelta(seconds=total_seconds))}\n**Mode :** {mode.name}",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Je te rappellerai à temps ⏳")
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Attendre le temps indiqué
    await asyncio.sleep(total_seconds)
    
    # Création du rappel
    rappel_embed = discord.Embed(
        title="⏰ Rappel !",
        description=f"**Raison :** {raison}\n\n⏳ Temps écoulé : {str(timedelta(seconds=total_seconds))}",
        color=discord.Color.green()
    )
    rappel_embed.set_footer(text="Pense à ne pas oublier ! 😉")
    
    # Envoi en MP ou dans le salon
    if mode.value == "prive":
        try:
            await interaction.user.send(embed=rappel_embed)
        except discord.Forbidden:
            await interaction.followup.send(
                "Je n'ai pas pu t'envoyer le message en privé. Veuillez vérifier vos paramètres de confidentialité.",
                ephemeral=True
            )
    else:
        await interaction.channel.send(f"{interaction.user.mention}", embed=rappel_embed)

THUMBNAIL_URL = "https://github.com/Iseyg91/Etherya/blob/main/3e3bd3c24e33325c7088f43c1ae0fadc.png?raw=true"

# Fonction pour vérifier si une URL est valide
def is_valid_url(url):
    regex = re.compile(
        r'^(https?://)?'  # http:// ou https:// (optionnel)
        r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'  # domaine
        r'(/.*)?$'  # chemin (optionnel)
    )
    return bool(re.match(regex, url))

class EmbedBuilderView(discord.ui.View):
    def __init__(self, author: discord.User, channel: discord.TextChannel):
        super().__init__(timeout=180)
        self.author = author
        self.channel = channel
        self.embed = discord.Embed(title="Titre", description="Description", color=discord.Color.blue())
        self.embed.set_thumbnail(url=THUMBNAIL_URL)
        self.second_image_url = None
        self.message = None  # Stocke le message contenant l'embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Vous ne pouvez pas modifier cet embed.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Modifier le titre", style=discord.ButtonStyle.primary)
    async def edit_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedTitleModal(self))

    @discord.ui.button(label="Modifier la description", style=discord.ButtonStyle.primary)
    async def edit_description(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedDescriptionModal(self))

    @discord.ui.button(label="Changer la couleur", style=discord.ButtonStyle.primary)
    async def edit_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.embed.color = discord.Color.random()
        if self.message:
            await self.message.edit(embed=self.embed, view=self)
        else:
            await interaction.response.send_message("Erreur : impossible de modifier le message.", ephemeral=True)

    @discord.ui.button(label="Ajouter une image", style=discord.ButtonStyle.secondary)
    async def add_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedImageModal(self))

    @discord.ui.button(label="Ajouter 2ème image", style=discord.ButtonStyle.secondary)
    async def add_second_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedSecondImageModal(self))

    @discord.ui.button(label="Envoyer", style=discord.ButtonStyle.success)
    async def send_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        embeds = [self.embed]
        if self.second_image_url:
            second_embed = discord.Embed(color=self.embed.color)
            second_embed.set_image(url=self.second_image_url)
            embeds.append(second_embed)

        await self.channel.send(embeds=embeds)
        await interaction.response.send_message("✅ Embed envoyé !", ephemeral=True)

class EmbedTitleModal(discord.ui.Modal):
    def __init__(self, view: EmbedBuilderView):
        super().__init__(title="Modifier le Titre")
        self.view = view
        self.title_input = discord.ui.TextInput(label="Nouveau Titre", required=True)
        self.add_item(self.title_input)

    async def on_submit(self, interaction: discord.Interaction):
        self.view.embed.title = self.title_input.value
        if self.view.message:
            await self.view.message.edit(embed=self.view.embed, view=self.view)
        else:
            await interaction.response.send_message("Erreur : impossible de modifier le message.", ephemeral=True)

class EmbedDescriptionModal(discord.ui.Modal):
    def __init__(self, view: EmbedBuilderView):
        super().__init__(title="Modifier la description")
        self.view = view
        self.description = discord.ui.TextInput(label="Nouvelle description", style=discord.TextStyle.paragraph, max_length=4000)
        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        self.view.embed.description = self.description.value
        if self.view.message:
            await self.view.message.edit(embed=self.view.embed, view=self.view)
        else:
            await interaction.response.send_message("Erreur : impossible de modifier le message.", ephemeral=True)

class EmbedImageModal(discord.ui.Modal):
    def __init__(self, view: EmbedBuilderView):
        super().__init__(title="Ajouter une image")
        self.view = view
        self.image_input = discord.ui.TextInput(label="URL de l'image", required=True)
        self.add_item(self.image_input)

    async def on_submit(self, interaction: discord.Interaction):
        if is_valid_url(self.image_input.value):
            self.view.embed.set_image(url=self.image_input.value)
            await self.view.message.edit(embed=self.view.embed, view=self.view)
        else:
            await interaction.response.send_message("❌ URL invalide.", ephemeral=True)

class EmbedSecondImageModal(discord.ui.Modal):
    def __init__(self, view: EmbedBuilderView):
        super().__init__(title="Ajouter une 2ème image")
        self.view = view
        self.second_image_input = discord.ui.TextInput(label="URL de la 2ème image", required=True)
        self.add_item(self.second_image_input)

    async def on_submit(self, interaction: discord.Interaction):
        if is_valid_url(self.second_image_input.value):
            self.view.second_image_url = self.second_image_input.value
        else:
            await interaction.response.send_message("❌ URL invalide.", ephemeral=True)

@bot.tree.command(name="embed", description="Créer un embed personnalisé")
async def embed_builder(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    admin_role_id = 792755123587645461  # ID du rôle admin
    if not any(role.id == admin_role_id or role.permissions.administrator for role in interaction.user.roles):
        return await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)

    view = EmbedBuilderView(interaction.user, interaction.channel)
    response = await interaction.followup.send(embed=view.embed, view=view, ephemeral=True)
    view.message = response

# Vérifie si l'utilisateur a les permissions administrateur
async def is_admin(ctx):
    return ctx.author.guild_permissions.administrator

# Commande pour lister les utilisateurs bannis
@bot.command()
@commands.check(is_admin)
async def listban(ctx):
    bans = await ctx.guild.bans()
    if not bans:
        await ctx.send("📜 Aucun utilisateur banni.")
    else:
        banned_users = "\n".join([f"{ban_entry.user.name}#{ban_entry.user.discriminator}" for ban_entry in bans])
        await ctx.send(f"📜 Liste des bannis :\n```\n{banned_users}\n```")

# Commande pour débannir tout le monde
@bot.command(name="unbanall")  # Changement du nom de la commande
@commands.check(is_admin)
async def unbanall(ctx):  # Suppression du paramètre option
    bans = await ctx.guild.bans()
    for ban_entry in bans:
        await ctx.guild.unban(ban_entry.user)
    await ctx.send("✅ Tous les utilisateurs bannis ont été débannis !")

giveaways = {}  # Stocke les participants

class GiveawayView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.prize = " !!Giveaway !!"
        self.duration = 60  # En secondes
        self.duration_text = "60 secondes"
        self.emoji = "🎉"
        self.winners = 1
        self.channel = ctx.channel
        self.message = None  # Pour stocker l'embed message

    async def update_embed(self):
        """ Met à jour l'embed avec les nouvelles informations. """
        embed = discord.Embed(
            title="🎉 **Création d'un Giveaway**",
            description=f"🎁 **Gain:** {self.prize}\n"
                        f"⏳ **Durée:** {self.duration_text}\n"
                        f"🏆 **Gagnants:** {self.winners}\n"
                        f"📍 **Salon:** {self.channel.mention}",
            color=discord.Color.blurple()  # Utilisation d'une couleur bleue sympathique
        )
        embed.set_footer(text="Choisissez les options dans le menu déroulant ci-dessous.")
        embed.set_thumbnail(url="https://github.com/Iseyg91/Etherya-Gestion/blob/main/t%C3%A9l%C3%A9chargement%20(9).png?raw=true")  # Logo ou icône du giveaway

        if self.message:
            await self.message.edit(embed=embed, view=self)

    async def parse_duration(self, text):
        """ Convertit un texte en secondes et retourne un affichage formaté. """
        duration_seconds = 0
        match = re.findall(r"(\d+)\s*(s|sec|m|min|h|hr|heure|d|jour|jours)", text, re.IGNORECASE)

        if not match:
            return None, None

        duration_text = []
        for value, unit in match:
            value = int(value)
            if unit in ["s", "sec"]:
                duration_seconds += value
                duration_text.append(f"{value} seconde{'s' if value > 1 else ''}")
            elif unit in ["m", "min"]:
                duration_seconds += value * 60
                duration_text.append(f"{value} minute{'s' if value > 1 else ''}")
            elif unit in ["h", "hr", "heure"]:
                duration_seconds += value * 3600
                duration_text.append(f"{value} heure{'s' if value > 1 else ''}")
            elif unit in ["d", "jour", "jours"]:
                duration_seconds += value * 86400
                duration_text.append(f"{value} jour{'s' if value > 1 else ''}")

        return duration_seconds, " ".join(duration_text)

    async def wait_for_response(self, interaction, prompt, parse_func=None):
        """ Attend une réponse utilisateur avec une conversion de type si nécessaire. """
        await interaction.response.send_message(prompt, ephemeral=True)
        try:
            msg = await bot.wait_for("message", check=lambda m: m.author == interaction.user, timeout=30)
            return await parse_func(msg.content) if parse_func else msg.content
        except asyncio.TimeoutError:
            await interaction.followup.send("⏳ Temps écoulé. Réessayez.", ephemeral=True)
            return None

    @discord.ui.select(
        placeholder="Choisir un paramètre",
        options=[
            discord.SelectOption(label="🎁 Modifier le gain", value="edit_prize"),
            discord.SelectOption(label="⏳ Modifier la durée", value="edit_duration"),
            discord.SelectOption(label="🏆 Modifier le nombre de gagnants", value="edit_winners"),
            discord.SelectOption(label="💬 Modifier le salon", value="edit_channel"),
            discord.SelectOption(label="🚀 Envoyer le giveaway", value="send_giveaway"),
        ]
    )
    async def select_action(self, interaction: discord.Interaction, select: discord.ui.Select):
        value = select.values[0]

        if value == "edit_prize":
            response = await self.wait_for_response(interaction, "Quel est le gain du giveaway ?", str)
            if response:
                self.prize = response
                await self.update_embed()
        elif value == "edit_duration":
            response = await self.wait_for_response(interaction, 
                "Durée du giveaway ? (ex: 10min, 2h, 1jour)", self.parse_duration)
            if response and response[0] > 0:
                self.duration, self.duration_text = response
                await self.update_embed()
        elif value == "edit_winners":
            response = await self.wait_for_response(interaction, "Combien de gagnants ?", lambda x: int(x))
            if response and response > 0:
                self.winners = response
                await self.update_embed()
        elif value == "edit_channel":
            await interaction.response.send_message("Mentionne le salon du giveaway.", ephemeral=True)
            msg = await bot.wait_for("message", check=lambda m: m.author == interaction.user, timeout=30)
            if msg.channel_mentions:
                self.channel = msg.channel_mentions[0]
                await self.update_embed()
            else:
                await interaction.followup.send("Aucun salon mentionné.", ephemeral=True)
        elif value == "send_giveaway":
            embed = discord.Embed(
                title="🎉 Giveaway !",
                description=f"🎁 **Gain:** {self.prize}\n"
                            f"⏳ **Durée:** {self.duration_text}\n"
                            f"🏆 **Gagnants:** {self.winners}\n"
                            f"📍 **Salon:** {self.channel.mention}\n\n"
                            f"Réagis avec {self.emoji} pour participer !",
                color=discord.Color.green()  # Utilisation d'une couleur de succès pour l'envoi
            )
            embed.set_footer(text="Bonne chance à tous les participants ! 🎉")
            embed.set_thumbnail(url="https://github.com/Iseyg91/Etherya-Gestion/blob/main/t%C3%A9l%C3%A9chargement%20(8).png?raw=true")  # Logo ou icône du giveaway

            message = await self.channel.send(embed=embed)
            await message.add_reaction(self.emoji)

            giveaways[message.id] = {
                "prize": self.prize,
                "winners": self.winners,
                "emoji": self.emoji,
                "participants": []
            }

            await interaction.response.send_message(f"🎉 Giveaway envoyé dans {self.channel.mention} !", ephemeral=True)

            await asyncio.sleep(self.duration)
            await self.end_giveaway(message)

    async def end_giveaway(self, message):
        data = giveaways.get(message.id)
        if not data:
            return

        participants = data["participants"]
        if len(participants) < 1:
            await message.channel.send("🚫 Pas assez de participants, giveaway annulé.")
            return

        winners = random.sample(participants, min(data["winners"], len(participants)))
        winners_mentions = ", ".join(winner.mention for winner in winners)

        embed = discord.Embed(
            title="🏆 Giveaway Terminé !",
            description=f"🎁 **Gain:** {data['prize']}\n"
                        f"🏆 **Gagnants:** {winners_mentions}\n\n"
                        f"Merci d'avoir participé !",
            color=discord.Color.green()
        )
        embed.set_footer(text="Merci à tous ! 🎉")
        embed.set_thumbnail(url="https://github.com/Iseyg91/Etherya-Gestion/blob/main/t%C3%A9l%C3%A9chargement%20(7).png?raw=true")  # Icône ou logo de fin de giveaway

        await message.channel.send(embed=embed)
        del giveaways[message.id]


@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    message_id = reaction.message.id
    if message_id in giveaways and str(reaction.emoji) == giveaways[message_id]["emoji"]:
        if user not in giveaways[message_id]["participants"]:
            giveaways[message_id]["participants"].append(user)


@bot.command()
async def gcreate(ctx):
    view = GiveawayView(ctx)
    embed = discord.Embed(
        title="🎉 **Création d'un Giveaway**",
        description="Utilise le menu déroulant ci-dessous pour configurer ton giveaway.\n\n"
                    "🎁 **Gain:** Un cadeau mystère\n"
                    "⏳ **Durée:** 60 secondes\n"
                    "🏆 **Gagnants:** 1\n"
                    f"📍 **Salon:** {ctx.channel.mention}",
        color=discord.Color.blurple()  # Couleur de l'embed plus attractive
    )
    embed.set_footer(text="Choisis les options dans le menu déroulant ci-dessous.")
    embed.set_thumbnail(url="https://github.com/Iseyg91/Etherya-Gestion/blob/main/t%C3%A9l%C3%A9chargement%20(6).png?raw=true")  # Icône ou logo du giveaway

    view.message = await ctx.send(embed=embed, view=view)
    
@bot.command()
async def alladmin(ctx):
    """Affiche la liste des administrateurs avec un joli embed"""
    admins = [member for member in ctx.guild.members if member.guild_permissions.administrator]

    if not admins:
        embed = discord.Embed(
            title="❌ Aucun administrateur trouvé",
            description="Il semble que personne n'ait les permissions d'administrateur sur ce serveur.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Création d'un embed stylé
    embed = discord.Embed(
        title="📜 Liste des administrateurs",
        description=f"Voici les {len(admins)} administrateurs du serveur **{ctx.guild.name}** :",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    embed.set_footer(text=f"Commande demandée par {ctx.author.name}", icon_url=ctx.author.avatar.url)

    for admin in admins:
        embed.add_field(name=f"👤 {admin.name}#{admin.discriminator}", value=f"ID : `{admin.id}`", inline=False)

    await ctx.send(embed=embed)

# Dictionnaire pour stocker les messages supprimés {channel_id: deque[(timestamp, auteur, contenu)]}
sniped_messages = {}

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return  # Ignore les bots

    channel_id = message.channel.id
    timestamp = time.time()
    
    if channel_id not in sniped_messages:
        sniped_messages[channel_id] = deque(maxlen=10)  # Stocker jusqu'à 10 messages par salon
    
    sniped_messages[channel_id].append((timestamp, message.author, message.content))
    
    # Nettoyage des vieux messages après 5 minutes
    await asyncio.sleep(300)
    now = time.time()
    sniped_messages[channel_id] = deque([(t, a, c) for t, a, c in sniped_messages[channel_id] if now - t < 300])

@bot.command()
async def snipe(ctx, index: int = 1):
    channel_id = ctx.channel.id
    
    if channel_id not in sniped_messages or len(sniped_messages[channel_id]) == 0:
        await ctx.send("Aucun message récent supprimé trouvé !")
        return

    if not (1 <= index <= len(sniped_messages[channel_id])):
        await ctx.send(f"Il n'y a que {len(sniped_messages[channel_id])} messages enregistrés.")
        return

    timestamp, author, content = sniped_messages[channel_id][-index]
    embed = discord.Embed(
        title=f"Message supprimé de {author}",
        description=content,
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"Demandé par {ctx.author}")

    await ctx.send(embed=embed)

    # Si le salon est configuré
    if presentation_channel_id:
        try:
            # Envoi direct du modal pour remplir la présentation
            await interaction.response.send_modal(PresentationForm())
        except Exception as e:
            await interaction.response.send_message(f"❌ Une erreur s'est produite : {str(e)}", ephemeral=True)
    else:
        # Si aucun salon de présentation n'est configuré, avertir l'utilisateur
        await interaction.response.send_message("❌ Le salon de présentation n'est pas encore configuré. Veuillez configurer le salon via les paramètres du bot.", ephemeral=True)


# Création du formulaire (modal)
class PresentationForm(discord.ui.Modal, title="Faisons connaissance !"):
    pseudo = TextInput(label="Ton pseudo", placeholder="Ex: Jean_57", required=True)
    age = TextInput(label="Ton âge", placeholder="Ex: 18", required=True)
    passion = TextInput(label="Ta passion principale", placeholder="Ex: Gaming, Musique...", required=True)
    bio = TextInput(label="Une courte bio", placeholder="Parle un peu de toi...", style=discord.TextStyle.paragraph, required=True)

    # Ce qui se passe lorsque l'utilisateur soumet le formulaire
    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        # Charger les paramètres du serveur depuis la base de données
        guild_settings = load_guild_settings(guild_id)
        presentation_channel_id = guild_settings.get('setup', {}).get('presentation_channel')

        if presentation_channel_id:
            presentation_channel = interaction.guild.get_channel(presentation_channel_id)

            if presentation_channel:
                # Créer l'embed avec les informations soumises
                embed = discord.Embed(
                    title=f"Présentation de {interaction.user.name}",
                    description="Une nouvelle présentation vient d'être envoyée ! 🎉",
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                embed.add_field(name="👤 Pseudo", value=self.pseudo.value, inline=True)
                embed.add_field(name="🎂 Âge", value=self.age.value, inline=True)
                embed.add_field(name="🎨 Passion", value=self.passion.value, inline=False)
                embed.add_field(name="📝 Bio", value=self.bio.value, inline=False)
                embed.set_footer(text=f"ID de l'utilisateur: {interaction.user.id}")

                # Envoyer l'embed dans le salon de présentation
                await presentation_channel.send(embed=embed)
                await interaction.response.send_message("Ta présentation a été envoyée ! 🎉")
            else:
                await interaction.response.send_message("Le salon de présentation n'existe plus ou est invalide.")
        else:
            await interaction.response.send_message("Le salon de présentation n'a pas été configuré pour ce serveur.")

# Fonction de la commande /presentation
@bot.tree.command(name="presentation", description="Remplis le formulaire pour te présenter à la communauté !")
async def presentation(interaction: discord.Interaction):
    guild_id = interaction.guild.id

    # Charger les paramètres du serveur depuis la base de données
    guild_settings = load_guild_settings(guild_id)
    print(f"Guild settings for {guild_id}: {guild_settings}")  # Ajout d'un log

    # Récupérer l'ID du salon de présentation depuis les paramètres du serveur
    presentation_channel_id = guild_settings.get('setup', {}).get('presentation_channel')
    if not presentation_channel_id:
        print("Salon de présentation non trouvé dans la base de données pour le serveur")

    # Vérifier si le salon de présentation est configuré
    if presentation_channel_id:
        # Si le salon est configuré, afficher le modal de présentation
        await interaction.response.send_modal(PresentationForm())
    else:
        # Si le salon n'est pas configuré, informer l'utilisateur
        await interaction.response.send_message("Le salon de présentation n'a pas été configuré pour ce serveur.")

@bot.command()
@commands.has_permissions(administrator=True)
async def lock(ctx):
    """Empêche @everyone de parler dans le salon actuel (admin only)."""
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔒 Salon verrouillé. Seuls les rôles autorisés peuvent parler.")

@bot.command()
@commands.has_permissions(administrator=True)
async def unlock(ctx):
    """Autorise @everyone à parler dans le salon actuel (admin only)."""
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = True
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔓 Salon déverrouillé. Tout le monde peut parler à nouveau.")

# Modal pour le feedback
class FeedbackModal(discord.ui.Modal, title="Envoyer un feedback"):

    feedback_type = discord.ui.TextInput(
        label="Type (Report ou Suggestion)",
        placeholder="Ex: Report",
        max_length=20
    )

    description = discord.ui.TextInput(
        label="Description",
        placeholder="Décris ton idée ou ton problème ici...",
        style=discord.TextStyle.paragraph,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = bot.get_channel(SALON_REPORT_ID)
        role_mention = f"<@&{ROLE_REPORT_ID}>"

        # Mention du rôle
        await channel.send(content=role_mention)

        # Embed
        embed = discord.Embed(
            title="📝 Nouveau Feedback",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Type", value=self.feedback_type.value, inline=False)
        embed.add_field(name="Description", value=self.description.value, inline=False)
        embed.set_footer(text=f"Envoyé par {interaction.user}", icon_url=interaction.user.display_avatar.url)

        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Ton feedback a été envoyé avec succès !", ephemeral=True)

# Slash command
@bot.tree.command(name="feedback", description="Envoyer un report ou une suggestion")
async def feedback(interaction: discord.Interaction):
    await interaction.response.send_modal(FeedbackModal())

# Token pour démarrer le bot (à partir des secrets)
# Lancer le bot avec ton token depuis l'environnement  
keep_alive()
bot.run(token)
