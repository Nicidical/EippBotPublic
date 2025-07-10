import discord
from discord.ext import commands
import random
import json

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="test", help="Test command.")
    async def test(self, ctx):
        await ctx.send("Test deez nuts lmao.")

    @commands.command(name='permission')
    async def permission(self, ctx):
        bot_member = ctx.guild.me
        permissions = bot_member.guild_permissions

        perms_list = [f"✅ {name.replace('_', ' ').title()}" if value else f"❌ {name.replace('_', ' ').title()}"
                      for name, value in permissions]
        perms_chunks = [perms_list[i:i + 10] for i in range(0, len(perms_list), 10)]
        embed = discord.Embed(title=f"Permissions for {bot_member.display_name} in **{ctx.guild.name}**", color=0x7289DA)

        for i, chunk in enumerate(perms_chunks):
            embed.add_field(name=f"Permissions Part {i + 1}", value="\n".join(chunk), inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="opentospecs", help="Opens the current channel to spectators.")
    async def opentospecs(self, ctx):
        server_config = self.bot.config
        server_id = str(ctx.guild.id)

        if server_id not in server_config or 'category_id' not in server_config[server_id]:
            await ctx.send("Category ID is not set for this server. Please configure it first.")
            return

        category_id = server_config[server_id]['category_id']
        if ctx.channel.category_id != category_id:
            await ctx.send("This command can only be used in channels under the specified category.")
            return

        spectator_role_id = server_config[server_id].get('spectator_role')
        if not spectator_role_id:
            await ctx.send("Spectator role is not set for this server. Please configure it first.")
            return

        spectator_role = discord.utils.get(ctx.guild.roles, id=spectator_role_id)
        if not spectator_role:
            await ctx.send("The spectator role is missing or invalid.")
            return

        try:
            await ctx.channel.set_permissions(spectator_role, read_messages=True)
            await ctx.send(f"Spectators can now view this channel: {ctx.channel.mention}")
        except discord.Forbidden:
            await ctx.send("I lack the permissions to modify channel settings.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="lock", help="Adds a lock emote to the current channel name.")
    async def lock_channel(self, ctx):
        server_config = self.bot.config
        server_id = str(ctx.guild.id)

        if server_id not in server_config or 'category_id' not in server_config[server_id]:
            await ctx.send("Category ID is not set for this server. Please configure it first.")
            return

        category_id = server_config[server_id]['category_id']
        if ctx.channel.category_id != category_id:
            await ctx.send("This command can only be used in channels under the specified category.")
            return

        try:
            if ctx.channel.name.endswith("🔒"):
                await ctx.send("This channel is already locked.")
            else:
                new_name = ctx.channel.name + "🔒"
                await ctx.channel.edit(name=new_name)
                await ctx.send(f"Channel locked: {ctx.channel.mention}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to rename this channel.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="unlock", help="Removes the lock emote from the current channel name.")
    async def unlock_channel(self, ctx):
        server_config = self.bot.config
        server_id = str(ctx.guild.id)

        if server_id not in server_config or 'category_id' not in server_config[server_id]:
            await ctx.send("Category ID is not set for this server. Please configure it first.")
            return

        category_id = server_config[server_id]['category_id']
        if ctx.channel.category_id != category_id:
            await ctx.send("This command can only be used in channels under the specified category.")
            return

        try:
            if ctx.channel.name.endswith("🔒"):
                new_name = ctx.channel.name[:-1]
                await ctx.channel.edit(name=new_name)
                await ctx.send(f"Channel unlocked: {ctx.channel.mention}")
            else:
                await ctx.send("This channel is not locked.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to rename this channel.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="soup")
    async def soup(self, ctx):
        await ctx.send("Soup time!")

    @commands.command(name="edward")
    async def edward(self, ctx):
        await ctx.send("https://cdn.discordapp.com/emojis/1334416241317646438.webp?size=128")

    @commands.command(name="earthquake")
    async def earthquake(self, ctx):
        await ctx.send("KO! Saberslasher11 eliminated with Blaziken.")

    @commands.command(name="IPAddress", help="Generates a fake IP address for a mentioned user.")
    async def ip_address(self, ctx, member: discord.Member):
        num1 = random.randint(0, 255)
        num2 = random.randint(0, 255)
        num3 = random.randint(0, 255)
        num4 = random.randint(0, 255)
        ipaddress = f"{member.display_name}'s IP Address is: {num1}.{num2}.{num3}.{num4}"
        await ctx.send(ipaddress)

    @commands.command(name="talkhere")
    async def talkhere(self, ctx, channel_id: int, *, message: str):
        if not await self.bot.is_owner(ctx):
            return await ctx.send("You are not authorized to use this command.")
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete messages.")
            return
        except discord.HTTPException:
            await ctx.send("Failed to delete the message. Please try again.")
            return

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            await ctx.send("Could not find the specified channel. Make sure I'm in that channel.")
            return

        await channel.send(message)

async def setup(bot):
    await bot.add_cog(Misc(bot))
