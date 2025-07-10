import discord
from discord.ext import commands
import asyncio
import random
import json

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="makeserver", help="Deletes all channels and makes a template eipp server.")
    @commands.has_permissions(administrator=True)
    async def makeserver(self, ctx):
        if ctx.author.id != ctx.guild.owner_id:
            await ctx.send("You must be the server owner to use this command.")
            return

        warning_msg = await ctx.send(
            "⚠️ **This will delete all current channels in the server.**\n"
            "Do you wish to proceed? Type `Yes` or `No`."
        )

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

        try:
            response = await self.bot.wait_for("message", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("⏳ Confirmation timed out. Operation cancelled.")
            return

        if response.content.lower() != "yes":
            await ctx.send("❌ Operation cancelled.")
            return

        server = ctx.guild

        try:
            for channel in server.channels:
                await channel.delete()
            for category in server.categories:
                await category.delete()

            roles = {
                "Host": discord.Permissions(administrator=True),
                "Player": discord.Permissions(),
                "Spectator": discord.Permissions(),
                "Eliminated": discord.Permissions(),
                "Bot": discord.Permissions()
            }

            role_ids = {}
            for role_name, perms in roles.items():
                role = await server.create_role(name=role_name, permissions=perms)
                role_ids[role_name.lower()] = role.id

            categories = {
                "Announcements": [
                    ("announcements", {
                        server.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                        role_ids["host"]: discord.PermissionOverwrite(send_messages=True)
                    }),
                    ("eipp-rules", {
                        server.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                        role_ids["host"]: discord.PermissionOverwrite(send_messages=True)
                    }),
                    ("bans", {
                        server.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                        role_ids["host"]: discord.PermissionOverwrite(send_messages=True)
                    }),
                    ("twist-info", {
                        server.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                        role_ids["host"]: discord.PermissionOverwrite(send_messages=True)
                    }),
                ],
                "Text Channels": [
                    ("general", {
                        server.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        role_ids["player"]: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                        role_ids["spectator"]: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                        role_ids["eliminated"]: discord.PermissionOverwrite(read_messages=True, send_messages=False)
                    }),
                    ("rule-discussion", {
                        server.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        role_ids["player"]: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                        role_ids["spectator"]: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                        role_ids["eliminated"]: discord.PermissionOverwrite(read_messages=True, send_messages=False)
                    }),
                ],
                "Game Chat": [
                    ("player-chat", {
                        role_ids["player"]: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        role_ids["spectator"]: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                        role_ids["eliminated"]: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                        server.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False)
                    }),
                    ("spectator-chat", {
                        role_ids["spectator"]: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        role_ids["player"]: discord.PermissionOverwrite(read_messages=False),
                        server.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False)
                    }),
                    ("graveyard", {
                        role_ids["spectator"]: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        role_ids["eliminated"]: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        role_ids["player"]: discord.PermissionOverwrite(read_messages=False),
                        server.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False)
                    }),
                ],
                "The Game": [
                    ("season-1", {
                        role_ids["host"]: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        role_ids["player"]: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                        role_ids["spectator"]: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                        role_ids["eliminated"]: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                        server.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False)
                    }),
                ],
                "Hosts": [
                    ("host-chat", {
                        role_ids["host"]: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        server.default_role: discord.PermissionOverwrite(read_messages=False)
                    }),
                    ("logs", {
                        role_ids["host"]: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        server.default_role: discord.PermissionOverwrite(read_messages=False)
                    }),
                ],
                "Confessionals": []
            }

            category_ids = {}
            general_channel = None

            for category_name, channels in categories.items():
                category = await server.create_category(category_name)
                category_ids[category_name.lower().replace(" ", "_")] = category.id

                for channel_name, overwrites in channels:
                    channel_overwrites = {}

                    for role_id, perms in overwrites.items():
                        if role_id == server.default_role:
                            channel_overwrites[server.default_role] = perms
                        else:
                            role = server.get_role(role_id)
                            if role:
                                channel_overwrites[role] = perms

                    channel = await category.create_text_channel(channel_name, overwrites=channel_overwrites)

                    if channel_name == "general":
                        general_channel = channel

            if general_channel:
                await server.edit(system_channel=general_channel)

            self.bot.config[str(server.id)] = {
                "server_name": server.name,
                "host_role": role_ids["host"],
                "player_role": role_ids["player"],
                "spectator_role": role_ids["spectator"],
                "eliminated_role": role_ids["eliminated"],
                "bot_role": role_ids["bot"],
                "category_id": category_ids.get("confessionals", None)
            }

            with open("config.json", "w") as f:
                json.dump(self.bot.config, f, indent=4)

        except discord.Forbidden:
            await ctx.send("I lack the permissions to create roles or channels.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="setcategory", help="Set the confessional category. (Admin only)")
    @commands.has_permissions(administrator=True)
    async def setcategory(self, ctx, category_id: int):
        server_id = str(ctx.guild.id)
        if server_id not in self.bot.config:
            self.bot.config[server_id] = {}
            self.bot.config[server_id]['server_name'] = ctx.guild.name
        self.bot.config[server_id]['category_id'] = category_id
        with open("config.json", "w") as f:
            json.dump(self.bot.config, f, indent=4)
        await ctx.send(f"Confessional category set to {category_id}.")

    @commands.command(name="setrole", help="Set a specific role. (Admin only)")
    @commands.has_permissions(administrator=True)
    async def setrole(self, ctx, role_name: str, role_id: int):
        allowed_roles = ["host", "player", "spectator", "eliminated", "bot"]

        role_name = role_name.lower()
        if role_name not in allowed_roles:
            await ctx.send(f"Invalid role name. Only the following roles are allowed: {', '.join(allowed_roles)}")
            return

        server_id = str(ctx.guild.id)
        config_key = role_name + "_role"

        if server_id not in self.bot.config:
            self.bot.config[server_id] = {}
            self.bot.config[server_id]['server_name'] = ctx.guild.name

        self.bot.config[server_id][config_key] = role_id
        with open("config.json", "w") as f:
            json.dump(self.bot.config, f, indent=4)
        await ctx.send(f"{role_name.capitalize()} role set to {role_id}.")

    @commands.command(name="confessional", help="Creates a confessional channel for a specified user.")
    @commands.has_guild_permissions(administrator=True)
    async def confessional(self, ctx, user: discord.Member):
        server_id = str(ctx.guild.id)
        config = self.bot.config

        if server_id not in config:
            await ctx.send("Server configuration is missing. Please set the necessary roles and category first.")
            return

        required_settings = ['host_role', 'category_id', 'bot_role', 'player_role', 'spectator_role']
        missing_config = [key for key in required_settings if key not in config[server_id]]
        if missing_config:
            await ctx.send(f"Missing configuration for: {', '.join(missing_config)}.")
            return

        host_role_id = config[server_id]["host_role"]
        category_id = config[server_id]["category_id"]
        bot_role_id = config[server_id]["bot_role"]
        player_role_id = config[server_id]["player_role"]
        spectator_role_id = config[server_id]["spectator_role"]

        host_role = discord.utils.get(ctx.guild.roles, id=host_role_id)
        if host_role not in ctx.author.roles:
            await ctx.send("You do not have permission to use this command.")
            return

        try:
            category = discord.utils.get(ctx.guild.categories, id=category_id)
            existing_channel = discord.utils.get(category.channels, name=user.name)

            if existing_channel:
                await ctx.send(f"{user.mention} already has a confessional channel: {existing_channel.mention}.")
                return

            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                host_role: discord.PermissionOverwrite.from_pair(discord.Permissions.all(), discord.Permissions.none()),
                discord.utils.get(ctx.guild.roles, id=bot_role_id): discord.PermissionOverwrite.from_pair(discord.Permissions.all(), discord.Permissions.none()),
                discord.utils.get(ctx.guild.roles, id=spectator_role_id): discord.PermissionOverwrite(read_messages=False, send_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True),
                discord.utils.get(ctx.guild.roles, id=player_role_id): discord.PermissionOverwrite(read_messages=False, send_messages=False),
            }

            channel = await category.create_text_channel(name=user.name, overwrites=overwrites)
            await ctx.send(f"Confessional channel created for {user.mention}.")

            role_to_add = ctx.guild.get_role(player_role_id)
            try:
                await user.add_roles(role_to_add)
                await ctx.send(f"Player role has been added to {user.mention}.")
            except discord.Forbidden:
                await ctx.send("I do not have permission to assign that role. Perhaps check that the Bot role is higher than the other roles?")
            except Exception as e:
                await ctx.send(f"Failed to add role: {e}")

        except discord.Forbidden:
            await ctx.send("I do not have permission to create channels.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="groupconfessional", help="Creates a confessional channel for multiple users with a custom name.")
    @commands.has_guild_permissions(administrator=True)
    async def groupconfessional(self, ctx, channel_name: str, *users: discord.Member):
        server_id = str(ctx.guild.id)
        config = self.bot.config

        if server_id not in config:
            await ctx.send("Server configuration is missing. Please set the necessary roles and category first.")
            return

        required_settings = ['host_role', 'category_id', 'bot_role', 'player_role', 'spectator_role']
        missing_config = [key for key in required_settings if key not in config[server_id]]
        if missing_config:
            await ctx.send(f"Missing configuration for: {', '.join(missing_config)}.")
            return

        host_role_id = config[server_id]["host_role"]
        category_id = config[server_id]["category_id"]
        bot_role_id = config[server_id]["bot_role"]
        player_role_id = config[server_id]["player_role"]
        spectator_role_id = config[server_id]["spectator_role"]

        host_role = discord.utils.get(ctx.guild.roles, id=host_role_id)
        if host_role not in ctx.author.roles:
            await ctx.send("You do not have permission to use this command.")
            return

        try:
            category = discord.utils.get(ctx.guild.categories, id=category_id)
            existing_channel = discord.utils.get(category.channels, name=channel_name)

            if existing_channel:
                await ctx.send(f"A channel named '{channel_name}' already exists: {existing_channel.mention}.")
                return

            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                host_role: discord.PermissionOverwrite.from_pair(discord.Permissions.all(), discord.Permissions.none()),
                discord.utils.get(ctx.guild.roles, id=bot_role_id): discord.PermissionOverwrite.from_pair(discord.Permissions.all(), discord.Permissions.none()),
                discord.utils.get(ctx.guild.roles, id=spectator_role_id): discord.PermissionOverwrite(read_messages=False, send_messages=False),
                discord.utils.get(ctx.guild.roles, id=player_role_id): discord.PermissionOverwrite(read_messages=False, send_messages=False),
            }

            for user in users:
                overwrites[user] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)

            channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)
            await ctx.send(f"Confessional channel '{channel_name}' created for {', '.join(user.mention for user in users)}.")

            role_to_add = ctx.guild.get_role(player_role_id)
            if role_to_add:
                for user in users:
                    await user.add_roles(role_to_add)
                await ctx.send(f"Player role has been added to {', '.join(user.mention for user in users)}.")

        except discord.Forbidden:
            await ctx.send("I do not have permission to create channels.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="deleteconfessionals", help="Deletes all confessional channels in the category. Requires host role. Prompts for confirmation.")
    async def deleteconfessionals(self, ctx):
        server_id = str(ctx.guild.id)
        config = self.bot.config

        if server_id not in config:
            await ctx.send("Server configuration not found.")
            return

        if 'host_role' not in config[server_id] or 'category_id' not in config[server_id]:
            await ctx.send("Host role or category ID not set for this server. Please configure them first.")
            return

        host_role_id = config[server_id]['host_role']
        category_id = config[server_id]['category_id']

        host_role = discord.utils.get(ctx.guild.roles, id=host_role_id)
        if host_role not in ctx.author.roles:
            await ctx.send("You do not have permission to use this command. Host role required.")
            return

        await ctx.send("Are you sure you want to delete all confessionals? Type 'Yes' to confirm.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'yes'

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("Deletion cancelled: Confirmation timeout.")
            return

        category = discord.utils.get(ctx.guild.categories, id=category_id)
        if category is None:
            await ctx.send("Confessionals category not found.")
            return

        try:
            for channel in category.channels:
                await channel.delete()
            await ctx.send("All confessionals have been deleted.")
        except discord.Forbidden:
            await ctx.send("I do not have permission to delete channels in this category.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="uploademotes", help="Upload emotes by attaching images.")
    @commands.has_permissions(administrator=True)
    async def uploademotes(self, ctx):
        if not ctx.message.attachments:
            await ctx.send("Please attach images to upload as emotes.")
            return

        for attachment in ctx.message.attachments:
            if not attachment.filename.lower().endswith(('png', 'jpg', 'jpeg', 'gif')):
                await ctx.send(f"{attachment.filename} is not a supported image file.")
                continue

            emote_name = attachment.filename.split('.')[0][:32].replace(" ", "_")

            try:
                img_data = await attachment.read()
                emote = await ctx.guild.create_custom_emoji(name=emote_name, image=img_data)
                await ctx.send(f"Uploaded emote: {emote_name} ({emote})")
            except discord.HTTPException as e:
                await ctx.send(f"Failed to upload `{emote_name}`: {str(e)}")

        await ctx.send("Finished uploading emotes.")

    @commands.command(name="deleteallemotes", help="Deletes all custom emotes in the server. Host-only command.")
    async def deleteallemotes(self, ctx):
        guild_id = str(ctx.guild.id)
        config = self.bot.config

        if guild_id not in config:
            await ctx.send("Server configuration not found.")
            return

        host_role_id = config[guild_id].get("host_role")
        host_role = discord.utils.get(ctx.guild.roles, id=host_role_id)

        if host_role not in ctx.author.roles:
            await ctx.send("Only hosts can use this command.")
            return

        if not ctx.guild.emojis:
            await ctx.send("This server has no custom emotes.")
            return

        await ctx.send("⚠️ Are you sure you want to delete **ALL custom emotes**? Type `Yes` to confirm.")

        def check(m):
            return m.author == ctx.author and m.content.strip().lower() == "yes"

        try:
            confirmation = await self.bot.wait_for("message", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("Timed out. Emote deletion cancelled.")
            return

        deleted = 0
        for emoji in ctx.guild.emojis:
            try:
                await emoji.delete()
                deleted += 1
            except discord.Forbidden:
                await ctx.send(f"❌ Could not delete emote `{emoji.name}` due to missing permissions.")
            except discord.HTTPException:
                await ctx.send(f"⚠️ Failed to delete `{emoji.name}`. Skipping.")

        await ctx.send(f"✅ Deleted {deleted} emotes.")

    @commands.command(name="playerlist", help="Lists all players with the player role, randomized, and mentions them. Host role required.")
    async def playerlist(self, ctx):
        server_id = str(ctx.guild.id)
        config = self.bot.config

        if server_id not in config:
            await ctx.send("Server configuration not found.")
            return

        if 'host_role' not in config[server_id] or 'player_role' not in config[server_id]:
            await ctx.send("Host role or player role not set for this server. Please configure them first.")
            return

        host_role = discord.utils.get(ctx.guild.roles, id=config[server_id]['host_role'])
        if host_role not in ctx.author.roles:
            await ctx.send("You do not have permission to use this command. Host role required.")
            return

        player_role = discord.utils.get(ctx.guild.roles, id=config[server_id]['player_role'])
        players = [m for m in ctx.guild.members if player_role in m.roles]

        if not players:
            await ctx.send("No players with the player role found. I guess no one is fighting a gorilla then.")
            return

        random.shuffle(players)
        message = "Here's some of the 100 people I nominate to fight 1 gorilla:\n"
        message += "\n".join([m.mention for m in players])

        await ctx.send(message)

    @commands.command(name="updateplayerlist", help="Updates the last posted player list by the bot.")
    async def updateplayerlist(self, ctx):
        server_id = str(ctx.guild.id)
        config = self.bot.config

        if server_id not in config:
            await ctx.send("Server configuration not found.")
            return

        if 'host_role' not in config[server_id] or 'player_role' not in config[server_id]:
            await ctx.send("Host role or player role not set for this server. Please configure them first.")
            return

        host_role = discord.utils.get(ctx.guild.roles, id=config[server_id]['host_role'])
        if host_role not in ctx.author.roles:
            await ctx.send("You do not have permission to use this command. Host role required.")
            return

        player_role = discord.utils.get(ctx.guild.roles, id=config[server_id]['player_role'])
        players = [m for m in ctx.guild.members if player_role in m.roles]

        if not players:
            await ctx.send("No players with the player role found.")
            return

        random.shuffle(players)
        updated_message = "Players:\n" + "\n".join([m.mention for m in players])

        async for msg in ctx.channel.history(limit=100):
            if msg.author == ctx.guild.me and msg.content.startswith("Players:"):
                await msg.edit(content=updated_message)
                await ctx.send("Player list has been updated.", delete_after=10)
                return

        await ctx.send("No previous player list message found to update.")

    @commands.command(name="addspecs", help="Adds the spectator role to all members without the player role. Host role required.")
    async def addspecs(self, ctx):
        server_id = str(ctx.guild.id)
        config = self.bot.config

        if server_id not in config:
            await ctx.send("Server configuration not found.")
            return

        if 'host_role' not in config[server_id] or 'player_role' not in config[server_id] or 'spectator_role' not in config[server_id]:
            await ctx.send("Host role, player role, or spectator role not set for this server. Please configure them first.")
            return

        host_role_id = config[server_id]['host_role']
        player_role_id = config[server_id]['player_role']
        spectator_role_id = config[server_id]['spectator_role']

        host_role = discord.utils.get(ctx.guild.roles, id=host_role_id)
        if host_role not in ctx.author.roles:
            await ctx.send("You do not have permission to use this command. Host role required.")
            return

        player_role = discord.utils.get(ctx.guild.roles, id=player_role_id)
        spectator_role = discord.utils.get(ctx.guild.roles, id=spectator_role_id)

        if player_role is None or spectator_role is None:
            await ctx.send("Player role or spectator role not found.")
            return

        members_to_update = [
            member for member in ctx.guild.members
            if player_role not in member.roles and host_role not in member.roles
        ]

        if not members_to_update:
            await ctx.send("No eligible members found to receive the spectator role.")
            return

        await ctx.send(f"Adding spectator role to {len(members_to_update)} members. This may take a moment...")

        try:
            for member in members_to_update:
                await member.add_roles(spectator_role)
            await ctx.send("Spectator role added to all eligible members.")
        except discord.Forbidden:
            await ctx.send("I do not have permission to add roles to members. Check if the Bot role is higher than Player and Spectator roles.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="close", help="Removes all game related roles to close off a season.")
    @commands.has_permissions(administrator=True)
    async def close(self, ctx):
        server_id = str(ctx.guild.id)
        config = self.bot.config

        if server_id not in config:
            await ctx.send("Server configuration not found. Please run the setup commands first.")
            return

        role_keys = ["player_role", "eliminated_role", "spectator_role"]
        roles_to_remove = [
            discord.utils.get(ctx.guild.roles, id=config[server_id].get(key)) for key in role_keys
        ]

        if not all(roles_to_remove):
            missing = [k for k, r in zip(role_keys, roles_to_remove) if r is None]
            await ctx.send(f"One or more roles are missing: {', '.join(missing)}")
            return

        await ctx.send("Removing Player, Spectator and Eliminated roles from all server members. This may take a moment.")

        removed_count = 0
        try:
            for member in ctx.guild.members:
                to_remove = [r for r in roles_to_remove if r in member.roles]
                if to_remove:
                    await member.remove_roles(*to_remove)
                    removed_count += len(to_remove)
            await ctx.send(f"Game over! A total of {removed_count} roles have been removed from members.")
        except discord.Forbidden:
            await ctx.send("I lack the permissions to modify roles for some members.")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {e}")

    @commands.command(name="addrole", help="Creates a new role with the specified name and hex color. (Admin only)")
    @commands.has_permissions(administrator=True)
    async def addrole(self, ctx, role_name: str, hex_color: str):
        if not hex_color.startswith("#") or len(hex_color) != 7:
            await ctx.send("Invalid hex color format. Use the format `#RRGGBB`.")
            return

        try:
            color = discord.Color(int(hex_color[1:], 16))
            role = await ctx.guild.create_role(name=role_name, color=color)
            await ctx.send(f"Role `{role.name}` created successfully with color `{hex_color}`!")
        except discord.Forbidden:
            await ctx.send("I lack the required permissions to create roles.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @addrole.error
    async def addrole_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need to be an administrator to use this command.")

async def setup(bot):
    await bot.add_cog(Setup(bot))
