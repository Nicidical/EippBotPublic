import discord
from discord.ext import commands
import json
import asyncio

class CommandList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="commandlist", help="Shows all available commands.")
    async def commandlist(self, ctx):
        with open("commandlist.json", "r") as file:
            data = json.load(file)

        all_commands = data.get("commands", [])

        commands_per_page = 7
        paginated = [
            all_commands[i:i + commands_per_page]
            for i in range(0, len(all_commands), commands_per_page)
        ]

        if not paginated:
            return await ctx.send("❌ No commands found in the command list.")

        current_page = 0

        def generate_embed(page_index):
            embed = discord.Embed(
                title=f"🤖 Bot Commands — Page {page_index + 1}/{len(paginated)}",
                description="Here's a list of commands you can use:",
                color=0xf5a9b8
            )
            for cmd in paginated[page_index]:
                embed.add_field(name=f"`{cmd['name']}`", value=cmd['description'], inline=False)
            embed.set_footer(text=f"Page {page_index + 1}/{len(paginated)} — Use ⬅️ or ➡️ to navigate.")
            return embed

        message = await ctx.send(embed=generate_embed(current_page))
        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")

        def check(reaction, user):
            return (
                user == ctx.author and 
                str(reaction.emoji) in ["⬅️", "➡️"] and 
                reaction.message.id == message.id
            )

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                if str(reaction.emoji) == "➡️":
                    current_page = (current_page + 1) % len(paginated)
                elif str(reaction.emoji) == "⬅️":
                    current_page = (current_page - 1) % len(paginated)

                await message.edit(embed=generate_embed(current_page))
                await message.remove_reaction(reaction.emoji, user)

            except asyncio.TimeoutError:
                break

    @commands.command(name="addeippbotcommand", help='Add a command to the command list (owner only).')
    async def addeippbotcommand(self, ctx, name: str, description: str):
        if not await self.bot.is_owner(ctx):
            return await ctx.send("You are not authorized to use this command.")

        with open("commandlist.json", "r") as f:
            data = json.load(f)

        if any(cmd["name"].lower() == name.lower() for cmd in data["commands"]):
            return await ctx.send("❌ A command with that name already exists.")

        data["commands"].append({
            "name": name,
            "description": description
        })

        with open("commandlist.json", "w") as f:
            json.dump(data, f, indent=2)

        await ctx.send(f"✅ Added command `{name}`.")

    @commands.command(name="updateeippbotcommand", help="Update a command's description (owner only).")
    async def updateeippbotcommand(self, ctx, name: str, new_description: str):
        if not await self.bot.is_owner(ctx):
            return await ctx.send("You are not authorized to use this command.")

        with open("commandlist.json", "r") as f:
            data = json.load(f)

        for cmd in data["commands"]:
            if cmd["name"].lower() == name.lower():
                cmd["description"] = new_description
                with open("commandlist.json", "w") as f:
                    json.dump(data, f, indent=2)
                return await ctx.send(f"✅ Updated command `{name}`.")

        await ctx.send("❌ Command not found.")

    @commands.command(name="deleteeippbotcommand", help="Delete a command from the list (owner only).")
    async def deleteeippbotcommand(self, ctx, name: str):
        if not await self.bot.is_owner(ctx):
            return await ctx.send("You are not authorized to use this command.")

        with open("commandlist.json", "r") as f:
            data = json.load(f)

        before = len(data["commands"])
        data["commands"] = [cmd for cmd in data["commands"] if cmd["name"].lower() != name.lower()]
        after = len(data["commands"])

        if before == after:
            return await ctx.send("❌ Command not found.")

        with open("commandlist.json", "w") as f:
            json.dump(data, f, indent=2)

        await ctx.send(f"🗑️ Deleted command `{name}`.")

    @commands.command(name="renameeippbotcommand", help="Rename an existing bot command (owner only).")
    async def renameeippbotcommand(self, ctx, old_name: str, new_name: str):
        if not await self.bot.is_owner(ctx):
            return await ctx.send("You are not authorized to use this command.")

        with open("commandlist.json", "r") as f:
            data = json.load(f)

        if any(cmd["name"].lower() == new_name.lower() for cmd in data["commands"]):
            return await ctx.send("❌ A command with the new name already exists.")

        for cmd in data["commands"]:
            if cmd["name"].lower() == old_name.lower():
                cmd["name"] = new_name
                with open("commandlist.json", "w") as f:
                    json.dump(data, f, indent=2)
                return await ctx.send(f"✏️ Renamed command `{old_name}` to `{new_name}`.")

        await ctx.send("❌ Command not found.")

async def setup(bot):
    await bot.add_cog(CommandList(bot))
