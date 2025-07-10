import discord
from discord.ext import commands
import random
import json
import asyncio
import aiohttp
import urllib.parse

BOWL = "\U0001f963"  # 🥣
SIZE = 9
SHARD = -1
SHARD_LIMIT = 4

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_random_pokemon_name(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://pokeapi.co/api/v2/pokemon?limit=1000") as resp:
                data = await resp.json()
                pokemon = random.choice(data["results"])
                return pokemon["name"].lower()

    @commands.command()
    async def whosthatpokemon(self, ctx):
        pokemon_name = await self.get_random_pokemon_name()  
        display = [":black_large_square:" if c != ' ' else ' ' for c in pokemon_name]
        guessed_letters = set()
        lives = 7
        player = ctx.author

        def format_display():
            return ' '.join(display)

        def create_embed():
            embed = discord.Embed(
                title="Who's That Pokémon?",
                description=f"{format_display()}",
                color=discord.Color.gold()
            )
            embed.add_field(name="Lives", value=f"{lives} ❤️", inline=False)
            embed.add_field(name="Guessed Letters", value=", ".join(sorted(guessed_letters)) or "None", inline=False)
            embed.set_author(name=f"{player.name}'s game", icon_url=player.display_avatar.url)
            return embed

        def check(m):
            return m.author == player and m.channel == ctx.channel

        game_msg = await ctx.send(embed=create_embed())

        while lives > 0:
            try:
                guess_msg = await self.bot.wait_for('message', check=check, timeout=600.0)
            except asyncio.TimeoutError:
                await ctx.send(f"⏰ Time's up! The Pokémon was **{pokemon_name.title()}**.")
                return

            guess = guess_msg.content.lower().strip()

            if len(guess) == 1:
                if guess in guessed_letters:
                    await ctx.send(f"You already guessed `{guess}`!")
                    continue
                guessed_letters.add(guess)
                if guess in pokemon_name:
                    for i, letter in enumerate(pokemon_name):
                        if letter == guess:
                            display[i] = letter
                    if ''.join(display) == pokemon_name:
                        embed = discord.Embed(
                            title="🎉 You got it!",
                            description=f"It's **{pokemon_name.title()}**!",
                            color=discord.Color.green()
                        )
                        image_name = pokemon_name.lower().replace("♀", "-f").replace("♂", "-m").replace(".", "").replace(" ", "-")
                        embed.set_image(url=f"https://img.pokemondb.net/artwork/{urllib.parse.quote(image_name)}.jpg")
                        await game_msg.edit(embed=embed)
                        return
                else:
                    lives -= 1
            elif guess == pokemon_name:
                embed = discord.Embed(
                    title="🎉 You got it!",
                    description=f"It's **{pokemon_name.title()}**!",
                    color=discord.Color.green()
                )
                image_name = pokemon_name.lower().replace("♀", "-f").replace("♂", "-m").replace(".", "").replace(" ", "-")
                embed.set_image(url=f"https://img.pokemondb.net/artwork/{urllib.parse.quote(image_name)}.jpg")
                await game_msg.edit(embed=embed)
                return
            else:
                lives -= 1

            await game_msg.edit(embed=create_embed())

        embed = discord.Embed(
            title="💀 Game Over",
            description=f"The Pokémon was **{pokemon_name.title()}**.",
            color=discord.Color.red()
        )
        embed.set_image(url="https://cdn.discordapp.com/emojis/848239838377148456.webp?size=128")
        await game_msg.edit(embed=embed)

    @commands.command()
    async def voltorbflip(self, ctx):
        try:
            with open("gamecorner.json", "r") as file:
                players = json.load(file)
        except FileNotFoundError:
            players = []

        player = next((p for p in players if p["user_id"] == str(ctx.author.id)), None)
        if player is None:
            player = {"user_id": str(ctx.author.id), "username": ctx.author.name, "coins": 0, "level": 1}
            players.append(player)

        level_data = {
            1: [(3, 1, 6), (0, 3, 6), (5, 0, 6), (2, 2, 6), (4, 1, 6)],
            2: [(1, 3, 7), (6, 0, 7), (3, 2, 7), (0, 4, 7), (5, 1, 7)],
            3: [(2, 3, 8), (7, 0, 8), (4, 2, 8), (1, 4, 8), (6, 1, 8)],
            4: [(3, 3, 8), (0, 5, 8), (8, 0, 10), (5, 2, 10), (2, 4, 10)],
            5: [(7, 1, 10), (4, 3, 10), (1, 5, 10), (9, 0, 10), (6, 2, 10)],
            6: [(3, 4, 10), (0, 6, 10), (8, 1, 10), (5, 3, 10), (2, 5, 10)],
            7: [(7, 2, 10), (4, 4, 10), (1, 6, 13), (9, 1, 13), (6, 3, 10)],
            8: [(0, 7, 10), (8, 2, 10), (5, 4, 10), (2, 6, 10), (7, 3, 10)]
        }

        board_size = 5
        choice = random.choice(level_data[player["level"]])
        twos, threes, voltorbs = choice
        hidden_board = [[1 for _ in range(board_size)] for _ in range(board_size)]
        positions = [(r, c) for r in range(board_size) for c in range(board_size)]
        random.shuffle(positions)

        for _ in range(voltorbs):
            r, c = positions.pop()
            hidden_board[r][c] = 'V'
        for _ in range(threes):
            r, c = positions.pop()
            hidden_board[r][c] = 3
        for _ in range(twos):
            r, c = positions.pop()
            hidden_board[r][c] = 2

        revealed = [[False for _ in range(board_size)] for _ in range(board_size)]
        coins = 0
        first_guess = True

        def format_board():
            rows = []
            header = "    1  2  3  4  5"
            for r in range(board_size):
                row_str = chr(65 + r) + "  "
                for c in range(board_size):
                    if revealed[r][c]:
                        val = hidden_board[r][c]
                        row_str += {
                            1: "1️⃣ ", 2: "2️⃣ ", 3: "3️⃣ ", 'V': "💣 "
                        }[val]
                    else:
                        row_str += "⬛ "
                row_sum = sum(val if isinstance(val, int) else 0 for val in hidden_board[r])
                vol_count = sum(1 for val in hidden_board[r] if val == 'V')
                row_str += f"| {row_sum}  {'💣'*vol_count}"
                rows.append(row_str)

            col_sums = []
            col_vols = []
            for c in range(board_size):
                total = 0
                bombs = 0
                for r in range(board_size):
                    val = hidden_board[r][c]
                    if isinstance(val, int):
                        total += val
                    elif val == 'V':
                        bombs += 1
                col_sums.append(f"{total:2}")
                col_vols.append(f"{bombs:2}")

            footer1 = "⬇  " + " ".join(col_sums)
            footer2 = "💣 " + " ".join(col_vols)

            return f"```\n{header}\n" + "\n".join(rows) + f"\n{footer1}\n{footer2}\nTotal coins: {coins}```"

        embed = discord.Embed(
            title=f"Voltorb Flip – Level {player['level']}",
            description=format_board(),
            color=0xf5a9b8
        )
        embed.set_author(name=f"{ctx.author.name}'s game", icon_url=ctx.author.display_avatar.url)
        message = await ctx.send(embed=embed)

        total_specials = twos + threes
        revealed_specials = 0

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        while True:
            try:
                guess_msg = await self.bot.wait_for('message', check=check, timeout=300.0)
            except asyncio.TimeoutError:
                embed.description += "\n⏰ Time's up!"
                await message.edit(embed=embed)
                return

            guess = guess_msg.content.upper().strip()
            if guess == "QUIT":
                embed.description = format_board() + f"\n❌ You quit. Coins earned: {coins}"
                await message.edit(embed=embed)
                player["coins"] += coins
                player["level"] = 1
                with open("gamecorner.json", "w") as f:
                    json.dump(players, f, indent=4)
                return

            if len(guess) == 2 and guess[0] in "ABCDE" and guess[1] in "12345":
                r = ord(guess[0]) - 65
                c = int(guess[1]) - 1
            else:
                await ctx.send("Invalid format. Use like 'A1', 'C3', etc.")
                continue

            if revealed[r][c]:
                await ctx.send("That tile is already revealed!")
                continue

            revealed[r][c] = True
            value = hidden_board[r][c]

            if value == 'V':
                embed.description = format_board() + "\n💥 You hit a Voltorb! You earned 0 coins."
                await message.edit(embed=embed)
                player["coins"] += coins
                player["level"] = 1
                with open("gamecorner.json", "w") as f:
                    json.dump(players, f, indent=4)
                return
            elif isinstance(value, int):
                if first_guess:
                    coins = value
                    first_guess = False
                else:
                    coins *= value
                if value in [2, 3]:
                    revealed_specials += 1
                if revealed_specials == total_specials:
                    embed.description = format_board() + f"\n🎉 You win! Coins earned: {coins}"
                    await message.edit(embed=embed)
                    player["coins"] += coins
                    if player["level"] < 8:
                        player["level"] += 1
                    with open("gamecorner.json", "w") as f:
                        json.dump(players, f, indent=4)
                    return

            embed.description = format_board()
            await message.edit(embed=embed)
            await guess_msg.delete()
    
    @commands.command()
    async def leaderboard(self, ctx):

        try:
            with open("gamecorner.json", "r") as file:
                players = json.load(file)
        except FileNotFoundError:
            await ctx.send("No players found.")
            return

        players.sort(key=lambda x: x["coins"], reverse=True)

        players_per_page = 10
        total_pages = (len(players) + players_per_page - 1) // players_per_page  
        current_page = 1

        def format_leaderboard(page):
            start_index = (page - 1) * players_per_page
            end_index = min(page * players_per_page, len(players))
            page_players = players[start_index:end_index]

            leaderboard = ""
            for i, player in enumerate(page_players, start=start_index + 1):
                leaderboard += f"{i}. {player['username']} - {player['coins']} coins\n"
            
            return leaderboard

        embed = discord.Embed(
            title="Leaderboard",
            description=format_leaderboard(current_page),
            color=0xf5a9b8
        )
        embed.set_footer(text=f"Page {current_page}/{total_pages}")

        message = await ctx.send(embed=embed)

        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in ["⬅️", "➡️"]

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=120.0)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                return
            
            if str(reaction.emoji) == "➡️" and current_page < total_pages:
                current_page += 1
            elif str(reaction.emoji) == "⬅️" and current_page > 1:
                current_page -= 1

            embed.description = format_leaderboard(current_page)
            embed.set_footer(text=f"Page {current_page}/{total_pages}")
            await message.edit(embed=embed)

            await message.remove_reaction(reaction, user)

    @commands.command()
    async def addcoins(self, ctx, member: discord.Member, amount: int):
        if not await self.bot.is_owner(ctx):
            return await ctx.send("You are not authorized.")

        try:
            with open("gamecorner.json", "r") as file:
                players = json.load(file)
        except FileNotFoundError:
            players = []

        player = next((p for p in players if p["user_id"] == str(member.id)), None)
        if player is None:
            player = {"user_id": str(member.id), "username": member.name, "coins": 0, "level": 1}
            players.append(player)

        player["coins"] += amount
        await ctx.send(f"Added {amount} coins to {member.name}. They now have {player['coins']} coins.")

        with open("gamecorner.json", "w") as file:
            json.dump(players, file, indent=4)

    @commands.command()
    async def removecoins(self, ctx, member: discord.Member, amount: int):
        if not await self.bot.is_owner(ctx):
            return await ctx.send("You are not authorized.")

        try:
            with open("gamecorner.json", "r") as file:
                players = json.load(file)
        except FileNotFoundError:
            players = []

        player = next((p for p in players if p["user_id"] == str(member.id)), None)
        if player is None:
            return await ctx.send(f"{member.name} does not have any coins recorded.")

        player["coins"] = max(0, player["coins"] - amount)
        await ctx.send(f"Removed {amount} coins from {member.name}. They now have {player['coins']} coins.")

        with open("gamecorner.json", "w") as file:
            json.dump(players, file, indent=4)

    @commands.command()
    async def setcoins(self, ctx, member: discord.Member, amount: int):
        if not await self.bot.is_owner(ctx):
            return await ctx.send("You are not authorized.")

        if amount < 0:
            return await ctx.send("Coins amount cannot be negative.")

        try:
            with open("gamecorner.json", "r") as file:
                players = json.load(file)
        except FileNotFoundError:
            players = []

        player = next((p for p in players if p["user_id"] == str(member.id)), None)
        if player is None:
            player = {"user_id": str(member.id), "username": member.name, "coins": amount, "level": 1}
            players.append(player)
        else:
            player["coins"] = amount

        await ctx.send(f"Set {member.name}'s coins to {amount}.")

        with open("gamecorner.json", "w") as file:
            json.dump(players, file, indent=4)

    @commands.command(name="soupsweeper", help="Starts a game of SoupSweeper! You can specify how many soup bowls (5–10).")
    async def soupsweeper(self, ctx, num_soups: int = 10):
        if num_soups < 5 or num_soups > 10:
            await ctx.send(f"❌ Invalid number of soup bowls. Please choose a number between **5** and **10**.")
            return

        field = [[0] * SIZE for _ in range(SIZE)]
        final_field = ""

        self.set_shards(field, num_soups)
        start_row, start_col = self.determine_start_coords(field)

        for row in range(SIZE):
            for col in range(SIZE):
                emote = self.translate_to_emote(field[row][col])
                final_field += emote if (row, col) == (start_row, start_col) else f"||{emote}||"
            final_field += "\n"

        embed = discord.Embed(
            title="🥣 SoupSweeper",
            description=final_field,
            color=0xf5a9b8  
        )
        embed.set_footer(text=f"Try not to uncover a soup bowl! ({num_soups} bowls hidden)")

        await ctx.send(embed=embed)

    def set_shards(self, field, max_shards):
        shard_count = 0
        while shard_count < max_shards:
            row, col = random.randint(0, SIZE - 1), random.randint(0, SIZE - 1)
            if not self.can_be_placed(row, col, field):
                continue
            field[row][col] = SHARD
            shard_count += 1
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = row + dr, col + dc
                    if self.is_valid_pos(nr, nc) and field[nr][nc] != SHARD:
                        field[nr][nc] += 1

    def can_be_placed(self, row, col, field):
        if field[row][col] == SHARD:
            return False
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = row + dr, col + dc
                if self.is_valid_pos(nr, nc) and field[nr][nc] == SHARD_LIMIT:
                    return False
        return True

    def is_valid_pos(self, row, col):
        return 0 <= row < SIZE and 0 <= col < SIZE

    def determine_start_coords(self, field):
        while True:
            row, col = random.randint(0, SIZE - 1), random.randint(0, SIZE - 1)
            if field[row][col] == 0:
                return row, col

    def translate_to_emote(self, num):
        emotes = {
            SHARD: BOWL,
            0: "0️⃣",
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣",
            7: "7️⃣",
            8: "8️⃣"
        }
        return emotes.get(num, "⬜")

async def setup(bot):
    await bot.add_cog(Games(bot))
