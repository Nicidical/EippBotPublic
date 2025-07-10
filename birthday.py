import discord
from discord.ext import commands
import json
import os
from datetime import datetime

BIRTHDAY_FILE = "birthdays.json"
GUILD_ID = 1317562987216896090
CHANNEL_ID = 1358470170191986842
ROLE_NAME = "Birthdays"

def load_birthdays():
    if not os.path.exists(BIRTHDAY_FILE):
        return {"birthdays": {}, "last_checked": None}
    with open(BIRTHDAY_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"birthdays": {}, "last_checked": None}

def save_birthdays(data):
    with open(BIRTHDAY_FILE, "w") as f:
        json.dump(data, f, indent=4)

class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.check_birthdays_on_startup())

    @commands.command(
        name="registerbday",
        help="Register your birthday (e.g. June 15). Only works in the Speed Tours server. Join here: https://discord.gg/vnyC7EzqYv"
    )
    async def registerbday(self, ctx, month: str, day: int):
        if ctx.guild.id != GUILD_ID:
            return await ctx.send("❌ You can only register your birthday in the main server.")

        try:
            month_cap = month.capitalize()
            date_obj = datetime.strptime(f"{month_cap} {day}", "%B %d")
            formatted_date = date_obj.strftime("%m-%d")
        except ValueError:
            return await ctx.send("❌ Invalid date. Please use format like `June 15`.")

        data = load_birthdays()
        data["birthdays"][str(ctx.author.id)] = formatted_date
        save_birthdays(data)

        role = discord.utils.get(ctx.guild.roles, name=ROLE_NAME)
        if not role:
            role = await ctx.guild.create_role(name=ROLE_NAME)

        await ctx.author.add_roles(role)
        await ctx.send(f"✅ Birthday registered as **{month_cap} {day}** and {ROLE_NAME} role given!")

    @commands.command(name="bdaycheck", help="Check if today is someone's birthday.")
    async def bdaycheck(self, ctx):
        await self.send_birthday_message(ctx.guild)

    @commands.command(name="bdaylist", help="Show the list of registered birthdays.")
    async def bdaylist(self, ctx):
        data = load_birthdays()
        birthdays = data.get("birthdays", {})
        if not birthdays:
            return await ctx.send("🎂 No birthdays have been registered yet.")

        embed = discord.Embed(title="🎂 Birthday List", color=0xf5a9b8)
        for user_id, date in sorted(birthdays.items(), key=lambda x: x[1]):
            member = ctx.guild.get_member(int(user_id))
            name = member.name if member else f"User ID {user_id}"
            embed.add_field(name=name, value=date, inline=False)

        await ctx.send(embed=embed)

    async def check_birthdays_on_startup(self):
        await self.bot.wait_until_ready()
        guild = self.bot.get_guild(GUILD_ID)
        if guild:
            await self.send_birthday_message(guild)

    async def send_birthday_message(self, guild):
        channel = guild.get_channel(CHANNEL_ID)
        if not channel:
            return

        today = datetime.now().strftime("%m-%d")
        data = load_birthdays()

        if data.get("last_checked") == today:
            print("Lmao, almost double pinged you.")
            await channel.send("I have already pinged for today's birthdays.")
            return

        birthdays = data.get("birthdays", {})
        birthday_users = [
            guild.get_member(int(uid)) for uid, date in birthdays.items()
            if date == today and guild.get_member(int(uid)) is not None
        ]

        if not birthday_users:
            await channel.send("🎉 No birthdays today!")
            data["last_checked"] = today
            save_birthdays(data)
            return

        role = discord.utils.get(guild.roles, name=ROLE_NAME)
        mention_list = ", ".join(member.mention for member in birthday_users)
        await channel.send(f"🎂 Happy Birthday {mention_list}! {role.mention} wishes you an amazing day! 🎉")

        data["last_checked"] = today
        save_birthdays(data)

async def setup(bot):
    await bot.add_cog(Birthday(bot))
