import discord
from discord.ext import commands
import json

EIPPU_SECTIONS = {
    "sylvieon": "Sylvieon's Eippus 💖",
    "upcoming": "Upcoming Eippus! 💖",
    "ongoing": "Ongoing Eippus! 💖",
    "other": "Other Eippus! 💖"
}

def load_shoutout_data():
    with open("shoutout.json", "r") as f:
        return json.load(f)

def save_shoutout_data(data):
    with open("shoutout.json", "w") as f:
        json.dump(data, f, indent=4)

class Eippu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="eippulist", help="View Sylvieon's and friends' Eippus.")
    async def eippulist(self, ctx):
        data = load_shoutout_data()
        pages = []

        entries_per_page = 5

        for section, title in EIPPU_SECTIONS.items():
            section_entries = data.get(section, [])
            num_section_pages = max(1, (len(section_entries) + entries_per_page - 1) // entries_per_page)

            for page_index in range(num_section_pages):
                embed = discord.Embed(
                    title=title.split(" 💖")[0] + (f" {page_index + 1}" if num_section_pages > 1 else ""),
                    color=0xf5a9b8
                )

                if len(section_entries) == 0 and section in ["ongoing", "upcoming"]:
                    msg = "Wow, there are no ongoing Eippus! Check back later." if section == "ongoing" \
                        else "No upcoming Eippus are listed yet! Stay tuned for announcements."
                    embed.description = msg
                else:
                    embed.description = {
                        "sylvieon": "Come check out my other Eipps!",
                        "upcoming": "Plenty of other cool Eippus coming soon! Be sure to join quick before they start!",
                        "ongoing": "These games are going on right now! Feel free to spectate.",
                        "other": "These may have concluded and are awaiting a new season. Stay tuned!"
                    }[section]

                    start = page_index * entries_per_page
                    end = start + entries_per_page
                    for e in section_entries[start:end]:
                        embed.add_field(name=f"`{e['name']}`", value=f"{e['description']} \n{e['link']}", inline=False)

                pages.append(embed)

        current_page = 0
        message = await ctx.send(embed=pages[current_page])
        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=120.0, check=check)

                if str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
                    current_page += 1
                    await message.edit(embed=pages[current_page])
                elif str(reaction.emoji) == "⬅️" and current_page > 0:
                    current_page -= 1
                    await message.edit(embed=pages[current_page])

                await message.remove_reaction(reaction, user)

            except Exception:
                break

    @commands.command(name="addeippu", help="Add a new Eippu to the list (owner only).")
    async def addeippu(self, ctx, section: str, name: str, description: str, link: str):
        if not await self.bot.is_owner(ctx):
            return await ctx.send("You are not authorized to use this command.")

        section = section.lower()
        if section not in EIPPU_SECTIONS:
            return await ctx.send(f"Invalid section. Choose from: {', '.join(EIPPU_SECTIONS)}")

        data = load_shoutout_data()
        data.setdefault(section, []).append({
            "name": name,
            "description": description,
            "link": link
        })
        save_shoutout_data(data)
        await ctx.send(f"✅ Added `{name}` to `{section}`.")

    @commands.command(name="updateeippu", help="Update an existing Eippu entry.")
    async def updateeippu(self, ctx, section: str, name: str, new_description: str = None, new_link: str = None):
        if not await self.bot.is_owner(ctx):
            return await ctx.send("You are not authorized.")

        section = section.lower()
        if section not in EIPPU_SECTIONS:
            return await ctx.send("Invalid section name.")

        data = load_shoutout_data()
        entry = next((e for e in data.get(section, []) if e["name"].lower() == name.lower()), None)

        if entry:
            if new_description:
                entry["description"] = new_description
            if new_link:
                entry["link"] = new_link
            save_shoutout_data(data)
            await ctx.send(f"✅ Updated `{name}` in `{section}`.")
        else:
            await ctx.send("❌ Entry not found.")

    @commands.command(name="moveeippu", help="Move an Eippu from one section to another.")
    async def moveeippu(self, ctx, from_section: str, to_section: str, name: str):
        if not await self.bot.is_owner(ctx):
            return await ctx.send("You are not authorized.")

        from_section, to_section = from_section.lower(), to_section.lower()
        if from_section not in EIPPU_SECTIONS or to_section not in EIPPU_SECTIONS:
            return await ctx.send("Invalid section name.")

        data = load_shoutout_data()
        entry = next((e for e in data.get(from_section, []) if e["name"].lower() == name.lower()), None)

        if entry:
            data[from_section].remove(entry)
            data.setdefault(to_section, []).append(entry)
            save_shoutout_data(data)
            await ctx.send(f"✅ Moved `{name}` from `{from_section}` to `{to_section}`.")
        else:
            await ctx.send("❌ Entry not found.")

    @commands.command(name="deleteeippu", help="Delete an Eippu from a section.")
    async def deleteeippu(self, ctx, section: str, name: str):
        if not await self.bot.is_owner(ctx):
            return await ctx.send("You are not authorized.")

        section = section.lower()
        if section not in EIPPU_SECTIONS:
            return await ctx.send("Invalid section name.")

        data = load_shoutout_data()
        before_count = len(data.get(section, []))
        data[section] = [e for e in data.get(section, []) if e["name"].lower() != name.lower()]
        after_count = len(data[section])

        if before_count != after_count:
            save_shoutout_data(data)
            await ctx.send(f"🗑️ Deleted `{name}` from `{section}`.")
        else:
            await ctx.send("❌ Entry not found.")

    @commands.command(name="renameeippu", help="Rename an existing Eippu (owner only).")
    async def renameeippu(self, ctx, section: str, old_name: str, new_name: str):
        if not await self.bot.is_owner(ctx):
            return await ctx.send("You are not authorized.")

        section = section.lower()
        if section not in EIPPU_SECTIONS:
            return await ctx.send("Invalid section name.")

        data = load_shoutout_data()
        entry = next((e for e in data.get(section, []) if e["name"].lower() == old_name.lower()), None)

        if entry:
            entry["name"] = new_name
            save_shoutout_data(data)
            await ctx.send(f"✏️ Renamed `{old_name}` to `{new_name}` in `{section}`.")
        else:
            await ctx.send("❌ Entry not found.")

async def setup(bot):
    await bot.add_cog(Eippu(bot))
