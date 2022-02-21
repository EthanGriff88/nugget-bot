import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import music
import general
import degen

load_dotenv()

# enable logging
import logging
logging.basicConfig(level=logging.INFO)

# setup cogs
cogs = [music, general, degen]

# create client
client = commands.Bot(command_prefix='?', intents = discord.Intents.all())

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print("Now I'm all spooled up!")
    print('------')
    # await client.change_presence(activity = discord.Game('Fortnite'))
    await client.change_presence(activity = discord.Activity(name='Spanked Nuggets', type = discord.ActivityType.watching))

async def setup():
  await client.wait_until_ready()
  for i in range(len(cogs)):
    cogs[i].setup(client)

client.loop.create_task(setup())
client.run(os.getenv("TOKEN")) # bot token, hidden in env var

