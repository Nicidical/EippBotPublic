import discord
from discord.ext import commands
import random
import time
import json

cooldowns = {}

class RNG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll", help="Rolls a random number between 1 and the specified number.")
    @commands.has_guild_permissions(send_messages=True)
    async def roll(self, ctx, number: int):
        try:
            guild_id = str(ctx.guild.id)
            server_config = self.bot.config.get(guild_id)

            if not server_config:
                await ctx.send("Server configuration not found.")
                return

            host_role_id = server_config.get("host_role")

            if number <= 0:
                await ctx.send("Please provide a positive integer.")
                return

            host_role = discord.utils.get(ctx.guild.roles, id=host_role_id)
            if host_role in ctx.author.roles:
                roll_result = random.randint(1, number)
                embed = discord.Embed(
                    title="🎲 Roll Result 🎲",
                    description=f"You rolled a **{roll_result}** (1-{number}).",
                    color=0xf5a9b8
                )
                await ctx.send(embed=embed)
            else:
                user_id = ctx.author.id
                current_time = time.time()
                if user_id in cooldowns and current_time - cooldowns[user_id] < 300:
                    remaining_time = int(300 - (current_time - cooldowns[user_id]))
                    await ctx.send(f"Please wait {remaining_time} seconds before using this command again.")
                    return

                cooldowns[user_id] = current_time
                roll_result = random.randint(1, number)
                embed = discord.Embed(
                    title="🎲 Roll Result 🎲",
                    description=f"You rolled a **{roll_result}** (1-{number}).",
                    color=0xf5a9b8
                )
                await ctx.send(embed=embed)

        except ValueError:
            await ctx.send("Please provide a valid integer.")
        except commands.MissingRequiredArgument:
            await ctx.send("Please specify a number to roll.")

    @commands.command(name="multihit", help="Simulates multiple hit moves with accuracy and optional flinch chance.")
    @commands.has_guild_permissions(send_messages=True)
    async def multihit(self, ctx, hits: int, accuracy: int, flinch_chance: int = 0):
        if hits <= 0 or hits > 10:
            await ctx.send("Please enter a number of hits between 1 and 10.")
            return
        if accuracy <= 0 or accuracy > 100:
            await ctx.send("Please enter an accuracy between 1 and 100.")
            return
        if flinch_chance < 0 or flinch_chance > 100:
            await ctx.send("Please enter a flinch chance between 0 and 100.")
            return

        guild_id = str(ctx.guild.id)
        server_config = self.bot.config.get(guild_id)

        if not server_config:
            await ctx.send("Server configuration not found.")
            return

        host_role_id = server_config.get("host_role")
        host_role = discord.utils.get(ctx.guild.roles, id=host_role_id)

        is_host = host_role in ctx.author.roles
        user_id = ctx.author.id
        current_time = time.time()

        if not is_host:
            if user_id in cooldowns and current_time - cooldowns[user_id] < 300:
                remaining = int(300 - (current_time - cooldowns[user_id]))
                await ctx.send(f"Please wait {remaining} seconds before using this command again.")
                return
            cooldowns[user_id] = current_time

        results = []
        flinch_occurred = False
        successful_hits = 0

        for i in range(hits):
            hit_roll = random.randint(1, 100)
            if hit_roll > accuracy:
                results.append(f"Roll {i + 1}: **{hit_roll}** (Missed)")
                break

            hit_result = f"Roll {i + 1}: **{hit_roll}**"
            if flinch_chance > 0 and not flinch_occurred:
                flinch_roll = random.randint(1, 100)
                hit_result += f" (Flinch Roll: {flinch_roll})"
                if flinch_roll <= flinch_chance:
                    results.append(hit_result)
                    results.append("**Flinch!** No further flinch rolls.")
                    flinch_occurred = True
                else:
                    results.append(hit_result)
            else:
                results.append(hit_result)

            successful_hits += 1

        embed = discord.Embed(
            title="🎯 Multihit Simulation 🎯",
            description="\n".join(results),
            color=0xf5a9b8
        )
        embed.add_field(name="Summary", value=f"Total successful hits: **{successful_hits}**")

        if flinch_occurred:
            embed.add_field(name="Effect", value="The opponent flinched and couldn't move!")

        await ctx.send(embed=embed)

    @commands.command(name="metronome", help="Calls a random move Metronome can select.")
    async def metronome(self, ctx):
        try:
            with open("metronome.txt", "r", encoding="utf-8") as file:
                moves = [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            return await ctx.send("❌ `metronome.txt` not found.")

        if not moves:
            return await ctx.send("❌ No moves found in `metronome.txt`.")

        selected_move = random.choice(moves)
        await ctx.send(f"🎲 **The Pokémon waggles its finger... It uses `{selected_move}`!**")

    @commands.command(name='makelearnset')
    async def makelearnset(self, ctx, count: int):
        try:
            with open('metronome.txt', 'r', encoding='utf-8') as file:
                moves = [line.strip() for line in file if line.strip()]

            if count <= 0:
                await ctx.send("Please enter a number greater than 0.")
                return

            if count > len(moves):
                await ctx.send(f"There are only {len(moves)} moves available.")
                return

            selected_moves = random.sample(moves, count)
            selected_moves.sort()

            move_text = '\n'.join(selected_moves)

            embed = discord.Embed(
                title=f"🎲 Learnset Generator ({count} Moves)",
                description=f"```{move_text}```",
                color=0xf5a9b8
            )

            await ctx.send(embed=embed)

        except FileNotFoundError:
            await ctx.send("Could not find `metronome.txt`.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(RNG(bot))
