import discord
import os
import json
import asyncio
from discord.ext import commands
from flask import Flask
from threading import Thread
import random
import time
import aiohttp
import urllib.parse

with open('token.txt', 'r') as file:
    TOKEN = file.read().strip()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = commands.Bot(command_prefix="$", intents=intents)

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

server_config = {}

def load_config():
    global server_config
    if not os.path.exists('config.json'):
        with open('config.json', 'w') as file:
            json.dump({}, file)  
    with open('config.json', 'r') as file:
        try:
            server_config = json.load(file)  
        except json.JSONDecodeError:
            print("Config file is empty or invalid. Initializing with default values.")
            server_config = {}

def save_config():
    print(f"Saving config.")
    with open('config.json', 'w') as file:
        json.dump(server_config, file, indent=4)

with open('config.json', 'r') as f:
    config = json.load(f)
client.config = config

OWNER_ID = 906931274587988059
CHANNEL_ID = 1392752732238254191

async def is_owner(ctx):
    return ctx.author.id == OWNER_ID

client.is_owner = is_owner

@client.event
async def on_ready():
    load_config()
    await client.load_extension("games")
    await client.load_extension("rng")   
    await client.load_extension("setup") 
    await client.load_extension("misc") 
    await client.load_extension("commandlist")
    await client.load_extension("eippu")
    await client.load_extension("birthday")
    print(f'Logged in as {client.user}')

    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f'EiERPPBot is now online!')
    else:
        print(f"❗ Could not find the channel with ID {CHANNEL_ID}.")

@client.command()
@commands.is_owner() 
async def shutdown(ctx):
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("EippBot shutting down...")
    await client.close()


@client.command(name='invite')
async def invite(ctx):
    invite_url = "https://discord.com/oauth2/authorize?client_id=1344585204127498271&permissions=8&integration_type=0&scope=bot"
    
    embed = discord.Embed(
        title="Invite Me!",
        description=f"[Click here to add me to your server!]({invite_url})",
        color=0xf5a9b8
    )
    await ctx.send(embed=embed)

client.run(TOKEN)
