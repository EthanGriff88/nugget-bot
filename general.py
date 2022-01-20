import discord
from discord.ext import commands

class General(commands.Cog):
  def __init__(self, client):
    self.client = client

  @commands.command()
  async def hello(self,ctx):
    await ctx.send("Hello!")

  @commands.command(name='presence', help='Change the bot\'s activity message in discord.\n\nTypes:\n0 - Playing\n1 - Streaming\n2 - Listening to\n3 - Watching')
  async def presence(self,ctx,type: int,*,activity: str):
    try:
      await self.client.change_presence(activity = discord.Activity(name=activity, type = discord.ActivityType(type)))
      await ctx.send(f"Presence updated to {discord.ActivityType(type).name} {activity}.")
      print(f"Presence updated to {discord.ActivityType(type).name} {activity}.")
    except ValueError:
      await ctx.send("Enter a valid input, nugget!")
  
def setup(client):
  client.add_cog(General(client))