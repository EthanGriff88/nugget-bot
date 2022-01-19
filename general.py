import discord
from discord.ext import commands

class General(commands.Cog):
  def __init__(self, client):
    self.client = client

  @commands.command()
  async def hello(self,ctx):
    await ctx.send("Hello!")
  
def setup(client):
  client.add_cog(General(client))