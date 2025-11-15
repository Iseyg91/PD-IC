import discord
from discord.ext import commands, tasks
from discord import app_commands, Embed, ButtonStyle, Interaction, TextStyle
from discord.app_commands import Choice, autocomplete
from discord.ui import Button, View, Select, Modal, TextInput
from discord.utils import get
from functools import wraps
import os
import io
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
from motor.motor_asyncio import AsyncIOMotorClient
import psutil
import pytz
import platform
import logging
from typing import Optional, List
import matplotlib.pyplot as plt
from discord import ui
from discord import app_commands, Interaction, ui

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
collection = db['ether_eco']  #Stock les Bal
collection2 = db['ether_daily']  #Stock les cd de daily
collection3 = db['ether_slut']  #Stock les cd de slut
collection4 = db['ether_crime']  #Stock les cd de slut
collection5 = db['ether_collect'] #Stock les cd de collect
collection6 = db['ether_work'] #Stock les cd de Work
collection7 = db['ether_inventory'] #Stock les inventaires
collection8 = db['info_cf'] #Stock les Info du cf
collection9 = db['info_logs'] #Stock le Salon logs
collection10 = db['info_bj'] #Stock les Info du Bj
collection11 = db['info_rr'] #Stock les Info de RR
collection12 = db['info_roulette'] #Stock les Info de SM
collection13 = db['info_sm'] #Stock les Info de SM
collection14 = db['ether_rob'] #Stock les cd de Rob
collection15 = db['anti_rob'] #Stock les rôle anti-rob
collection16 = db['ether_boutique'] #Stock les Items dans la boutique
collection17 = db['joueur_ether_inventaire'] #Stock les items de joueurs
collection18 = db['ether_effects'] #Stock les effets
collection19 = db['ether_badge'] #Stock les bagde
collection20 = db['inventaire_badge'] #Stock les bagde des joueurs
collection21 = db['daily_badge'] #Stock les cd des daily badge
collection22 = db['start_date'] #Stock la date de commencemant des rewards
collection23 = db['joueur_rewards'] #Stock ou les joueurs sont
collection24 = db['cd_renforcement'] #Stock les cd
collection25 = db['cd_emission'] #Stock les cd
collection26 = db['cd_manipulation'] #Stock les cd
collection27 = db['cd_materialisation'] #Stock les cd
collection28 = db['cd_transformation'] #Stock les cd
collection29 = db['cd_specialisation'] #Stock les cd
collection30 = db['cd_haki_attaque'] #Stock les cd
collection31 = db['cd_haki_subis'] #Stock les cd
collection32 = db['ether_quetes'] #Stock les quetes
collection33 = db['inventory_collect'] #Stock les items de quetes
collection34 = db['collect_items'] #Stock les items collector
collection35 = db['ether_guild'] #Stock les Guild
collection36 = db['guild_inventaire'] #Stock les inventaire de Guild
collection39 = db['cd_capture_ether'] #Stock les cd d'attaque
collection40 = db['cd_bombe'] #Stock les cd des bombes
collection41 = db['cd_gura'] #Stock les cd de seismes
collection42 = db['cd_glace'] #Stock les cd d'attaque de glace
collection43 = db['glace_subis'] #Stock le cd avant de retirer le rôle de subis de glace
collection44 = db['cd_tenebre'] #Stock les cd de Yami
collection45 = db['cd_protection_tenebre'] #Stock le temps de protection de Yami
collection46 = db['cd_gear_second'] #Stock le cd des Gear Second
collection47 = db['cd_gear_fourth'] #Stock les cd des Gear Fourth
collection48 = db['cd_use_fourth'] #Stock les cd des utilisation du Gear Fourth
collection49 = db['cd_royaume_nika'] #Stock le cd des utilisation du Royaume
collection50 = db['cd_acces_royaume'] #Stock le cd d'acces au Royaume
collection51 = db['cd_nika_collect'] #Stock le cd de reutilisation du Nika Collect
collection52 = db['cd_eveil_attaque'] #Stock le cd de reutilisation du Nika Eveil
collection53 = db['cd_eveil_subis'] #Stock le cd de soumission du Nika Eveil
collection54 = db['cd_bourrasque'] #Stock le cd de reutilisation du Uo Uo no Mi
collection55 = db['cd_bourrasque_subis'] #Stock le cd de soumission du Uo Uo no Mi
collection56 = db['cd_tonnerre_attaque'] #Stock les cd de reutillisation du Tonnerre Divin
collection57 = db['cd_tonnerre_subis'] #Stock les cd de soumission du Tonnerre Divin
collection58 = db['cd_eveil_uo'] #Stock les cd d'eveil du Dragon
collection59 = db['message_jour'] #Stock les message des membres chaque jour
collection60 = db['cd_wobservation'] #Stock les cd de W Observation
collection61 = db['cd_observation']
collection62 = db['ether_ticket'] 

def load_guild_settings(guild_id):
    ether_eco_data = collection.find_one({"guild_id": guild_id}) or {}
    ether_daily_data = collection2.find_one({"guild_id": guild_id}) or {}
    ether_slut_data = collection3.find_one({"guild_id": guild_id}) or {}
    ether_crime_data = collection4.find_one({"guild_id": guild_id}) or {}
    ether_collect = collection5.find_one({"guild_id": guild_id}) or {}
    ether_work_data = collection6.find_one({"guild_id": guild_id}) or {}
    ether_inventory_data = collection7.find_one({"guild_id": guild_id}) or {}
    info_cf_data = collection8.find_one({"guild_id": guild_id}) or {}
    info_logs_data = collection9.find_one({"guild_id": guild_id}) or {}
    info_bj_data = collection10.find_one({"guild_id": guild_id}) or {}
    info_rr_data = collection11.find_one({"guild_id": guild_id}) or {}
    info_roulette_data = collection12.find_one({"guild_id": guild_id}) or {}
    info_sm_roulette_data = collection13.find_one({"guild_id": guild_id}) or {}
    ether_rob_data = collection14.find_one({"guild_id": guild_id}) or {}
    anti_rob_data = collection15.find_one({"guild_id": guild_id}) or {}
    ether_boutique_data = collection16.find_one({"guild_id": guild_id}) or {}
    joueur_ether_inventaire_data = collection17.find_one({"guild_id": guild_id}) or {}
    ether_effects_data = collection18.find_one({"guild_id": guild_id}) or {}
    ether_badge_data = collection19.find_one({"guild_id": guild_id}) or {}
    inventaire_badge_data = collection20.find_one({"guild_id": guild_id}) or {}
    daily_badge_data = collection21.find_one({"guild_id": guild_id}) or {}
    start_date_data = collection22.find_one({"guild_id": guild_id}) or {}
    joueur_rewards_data = collection23.find_one({"guild_id": guild_id}) or {}
    cd_renforcement_data = collection24.find_one({"guild_id": guild_id}) or {}
    cd_emission_data = collection25.find_one({"guild_id": guild_id}) or {}
    cd_manipultation_data = collection26.find_one({"guild_id": guild_id}) or {}
    cd_materialisation_data = collection27.find_one({"guidl_id": guild_id}) or {}
    cd_transformation_data = collection28.find_one({"guild_id": guild_id}) or {}
    cd_specialisation_data = collection29.find_one({"guild_id": guild_id}) or {}
    cd_haki_attaque_data = collection30.find_one({"guild_id": guild_id}) or {}
    cd_haki_subis_data = collection31.find_one({"guild_id": guild_id}) or {}
    ether_quetes_data = collection32.find_one({"guild_id": guild_id}) or {}
    inventory_collect_data = collection33.find_one({"guild_id": guild_id}) or {}
    collect_items_data = collection34.find_one({"guild_id": guild_id}) or {}
    ether_guild_data = collection35.find_one({"guild_id": guild_id}) or {}
    guild_inventaire_data = collection36.find_one({"guild_id": guild_id}) or {}
    cd_capture_ether_data = collection39.find_one({"guild_id": guild_id}) or {}
    cd_bombe_data = collection40.find_one({"guild_id": guild_id}) or {}
    cd_gura_data = collection41.find_one({"guild_id": guild_id}) or {}
    cd_glace_data = collection42.fing_one({"guild_id": guild_id}) or {}
    glace_subis_data = collection43.find_one({"guild_id": guild_id}) or {}
    cd_tenebre_data = collection44.find_one({"guild_id": guild_id}) or {}
    cd_protection_tenebre_data = collection45.find_one({"guild_id": guild_id}) or {}
    cd_gear_second_data = collection46.find_one({"guild_id": guild_id}) or {}
    cd_gear_fourth_data = collection47.find_one({"guild_id": guild_id}) or {}
    cd_use_fourth_data = collection48.find_one({"guild_id": guild_id}) or {}
    cd_royaume_nika_data = collection49.find_one({"guild_id": guild_id}) or {}
    cd_acces_royaume_data = collection50.find_one({"guild_id": guild_id}) or {}
    cd_nika_collect_data = collection51.find_one({"guild_id": guild_id}) or {}
    cd_eveil_attaque_data = collection52.find_one({"guild_id": guild_id}) or {}
    cd_eveil_subis_data = collection53.find_one({"guild_id": guild_id}) or {}
    cd_bourrasque_data = collection54.find_one({"guild_id": guild_id}) or {}
    cd_bourrasque_subis_data = collection55.find_one({"guild_id": guild_id}) or {}
    cd_tonnerre_attaque_data = collection56.find_one({"guild_id": guil_id}) or {}
    cd_tonnerre_subis_data = collection57.find_one({"guild_id": guild_id}) or {}
    cd_eveil_uo_data = collection58.find_one({"guild_id": guild_id}) or {}
    message_jour_data = collection59.find_one({"guild_id": guild_id}) or {}
    cd_wobservation_data = collection60.find_one({"guild_id": guild_id}) or {}
    cd_observation_data = collection61.find_one({"guild_id": guild_id}) or {}
    ether_ticket_data = collection62.find_one({"guild_id": guild_id}) or {}
    
    # Débogage : Afficher les données de setup
    print(f"Setup data for guild {guild_id}: {setup_data}")

    combined_data = {
        "ether_eco": ether_eco_data,
        "ether_daily": ether_daily_data,
        "ether_slut": ether_slut_data,
        "ether_crime": ether_crime_data,
        "ether_collect": ether_collect_data,
        "ether_work": ether_work_data,
        "ether_inventory": ether_inventory_data,
        "info_cf": info_cf_data,
        "info_logs": info_logs_data,
        "info_bj": info_bj_data,
        "info_rr": info_rr_data,
        "info_roulette": info_roulette_data,
        "info_sm": info_sm_data,
        "ether_rob": ether_rob_data,
        "anti_rob": anti_rob_data,
        "ether_boutique": ether_boutique_data,
        "joueur_ether_inventaire": joueur_ether_inventaire_data,
        "ether_effects": ether_effects_data,
        "ether_badge": ether_badge_data,
        "inventaire_badge": inventaire_badge_data,
        "daily_badge": daily_badge_data,
        "start_date": start_date_data,
        "joueur_rewards": joueur_rewards_data,
        "cd_renforcement": cd_renforcement_data,
        "cd_emission": cd_emission_data,
        "cd_manipultation": cd_manipultation_data,
        "cd_materialisation": cd_materialisation_data,
        "cd_transformation" : cd_transformation_data,
        "cd_specialisation" : cd_specialisation_data,
        "cd_haki_attaque": cd_haki_attaque_data,
        "cd_haki_subis": cd_haki_subis_data,
        "ether_quetes": ether_quetes_data,
        "inventory_collect": inventory_collect_data,
        "collect_items": collect_items_data,
        "ether_guild": ether_guild_data,
        "guild_inventaire": guild_inventaire_data,
        "cd_capture_ether": cd_capture_ether_data,
        "cd_bombe": cd_bombe_data,
        "cd_gura": cd_gura_data,
        "cd_glace": cd_glace_data,
        "glace_subis": glace_subis_data,
        "cd_tenebre": cd_tenebre_data,
        "cd_protection_tenebre": cd_protection_tenebre_data,
        "cd_gear_second": cd_gear_second_data,
        "cd_gear_fourth": cd_gear_fourth_data,
        "cd_use_fourth": cd_use_fourth_data,
        "cd_royaume_nika": cd_royaume_nika_data,
        "cd_acces_royaume": cd_acces_royaume_data,
        "cd_nika_collect": cd_nika_collect_data,
        "cd_eveil_attaque": cd_eveil_attaque_data,
        "cd_eveil_subis": cd_eveil_subis_data,
        "cd_bourrasque": cd_bourrasque_data,
        "cd_bourrasque_subis": cd_bourrasque_subis_data,
        "cd_tonnerre_attaque": cd_tonnerre_attaque_data,
        "cd_tonnerre_subis": cd_tonnerre_subis_data,
        "cd_eveil_uo": cd_eveil_uo_data,
        "message_jour": message_jour_data,
        "cd_wobservation": cd_wobservation_data,
        "cd_observation": cd_observation_data,
        "ether_ticket": ether_ticket_data
    }

    return combined_data

# --- Initialisation au démarrage ---
@bot.event
async def on_ready():
    print(f"{bot.user.name} est connecté.")
    bot.loop.create_task(start_background_tasks())
    bot.uptime = time.time()
    activity = discord.Activity(
        type=discord.ActivityType.streaming,
        name="Etherya",
        url="https://discord.com/oauth2/authorize?client_id=1356693934012891176"
    )
    await bot.change_presence(activity=activity, status=discord.Status.online)

    print(f"🎉 **{bot.user}** est maintenant connecté et affiche son activité de stream avec succès !")
    print("📌 Commandes disponibles 😊")
    for command in bot.commands:
        print(f"- {command.name}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Commandes slash synchronisées : {[cmd.name for cmd in synced]}")
    except Exception as e:
        print(f"❌ Erreur de synchronisation des commandes slash : {e}")

# --- Gestion globale des erreurs ---
@bot.event
async def on_error(event, *args, **kwargs):
    print(f"Une erreur s'est produite : {event}")
    embed = discord.Embed(
        title="❗ Erreur inattendue",
        description="Une erreur s'est produite lors de l'exécution de la commande. Veuillez réessayer plus tard.",
        color=discord.Color.red()
    )
    try:
        await args[0].response.send_message(embed=embed)
    except Exception:
        pass

# Token pour démarrer le bot (à partir des secrets)
# Lancer le bot avec ton token depuis l'environnement  
keep_alive()
bot.run(token)
