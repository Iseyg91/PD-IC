import discord
from discord.ext import commands
import random
import asyncio
import os
from pymongo import MongoClient

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        mongo_uri = os.getenv("MONGO_DB")
        self.client = MongoClient(mongo_uri)
        self.db = self.client['Cass-Eco2']
        self.collection = self.db['level_system']
        print("✅ Connexion MongoDB établie pour le système de niveau.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        guild_id = str(message.guild.id)

        # Tu peux ajuster ça : XP gagné aléatoirement entre 1 et 4
        xp_gagne = random.randint(1, 4)

        data = self.collection.find_one({"user_id": user_id, "guild_id": guild_id})

        if not data:
            # Nouveau joueur
            new_data = {
                "user_id": user_id,
                "guild_id": guild_id,
                "xp": xp_gagne,
                "level": 1
            }
            self.collection.insert_one(new_data)
        else:
            # Ancien joueur
            new_xp = data["xp"] + xp_gagne
            new_level = data["level"]

            # Système de niveau : exponentiel pour ralentir
            next_level_xp = 100 + (data["level"] * 40)

            if new_xp >= next_level_xp:
                new_xp -= next_level_xp
                new_level += 1
                await message.channel.send(f"🎉 {message.author.mention} est maintenant niveau {new_level} !")

            self.collection.update_one(
                {"user_id": user_id, "guild_id": guild_id},
                {"$set": {"xp": new_xp, "level": new_level}}
            )

    @commands.command(name="rank")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id)
        guild_id = str(ctx.guild.id)

        data = self.collection.find_one({"user_id": user_id, "guild_id": guild_id})
        if not data:
            await ctx.send(f"{member.mention} n'a pas encore de niveau.")
        else:
            await ctx.send(f"📊 {member.mention} est niveau {data['level']} avec {data['xp']} XP.")

async def setup(bot):
    await bot.add_cog(LevelSystem(bot))
