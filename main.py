import discord
from discord.ext import commands
import os
import music
import general

# enable logging
import logging
logging.basicConfig(level=logging.INFO)

# setup cogs
cogs = [music, general]

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
client.run('OTMyMDg2NTI0MDAxMDAxNTg3.YeN3OA.-CI1gwuYZiR99m7gNOirAJDbHWo') # bot token, hidden in env var



"""
client = discord.Client()
@client.event
async def on_ready():
  print("Logged in as {0.user}".format(client))

@client.event
async def on_message(message):
  if message.author == client.user:
    return

  if message.content.startswith("$hello"):
    await message.channel.send("Hello!")
"""

