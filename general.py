import discord
from discord.ext import commands
import asyncio
from random import choice

class NoVoiceClient(commands.CommandError):
  pass

class General(commands.Cog):
  def __init__(self, client):
    self.client = client

  @commands.command(name='hello', help='Howdy!', aliases=['hi'])
  async def hello(self,ctx):
    msgs = ["Well howdy, nugget!","I'm on it, blackshoe!","Consider yourself spanked, nugget!"]
    await ctx.send(choice(msgs))

  @commands.Cog.listener()
  async def on_member_join(self, member):
    greetings = ["Delta Sierra at 12 o'clock!","I've got a bogey on my tail!","It's a Charlie Foxtrot!"]
    guild = member.guild
    if guild.system_channel is not None:
      msg = choice(greetings)
      await guild.system_channel.send(f"{msg} Howdy {member.mention}!")

  @commands.command(name='status', help='Change the bot\'s activity message in discord.\
                    \n\nTypes:\n0 - Playing\n1 - Streaming\n2 - Listening to\n3 - Watching'\
                    , aliases=['presence'])
  @commands.is_owner()
  async def status(self, ctx, type: int, *, activity: str):
    await self.client.change_presence(activity = discord.Activity(name=activity, type = discord.ActivityType(type)))
    await ctx.send(f"Status updated to {discord.ActivityType(type).name} {activity}.")
    print(f"Status updated to {discord.ActivityType(type).name} {activity}.")

  @status.error
  async def status_error(self, ctx, error):
    print(f"Error in Status - {error.__class__.__name__}: {error}")

    if isinstance(error, commands.MissingRequiredArgument):
      await ctx.send("You forgot something, nugget! Try again!")
    elif isinstance(error, ValueError): 
      await ctx.send("Enter a valid input, nugget!")
    elif isinstance(error, commands.BadArgument):
      await ctx.send("Enter a valid input, nugget!")
    elif isinstance(error, commands.CheckFailure):
      await ctx.send("We've got an imposter among us ඞඞඞඞඞ (You can't do that, nugget!)")
    else:
      await ctx.send("Something went wrong, nugget!")


  @commands.command(name='spank', aliases=['timeout'], help='Spank a bad nugget for specified time, default 1 minute. Use @user or "user" to specify the bad nugget.')
  @commands.has_guild_permissions(mute_members=True)
  async def spank(self, ctx, user: discord.Member, time = 1):
    if user.voice is None:
      raise NoVoiceClient
    else:
      if time == 1:
        print(f"Spanking {user} for {time} minute.")
        msg = await ctx.send(f"Consider yourself spanked, {user.mention}! Come back in {time} minute.")
      else:
        print(f"Spanking {user} for {time} minutes.")
        msg = await ctx.send(f"Consider yourself spanked, {user.mention}! Come back in {time} minutes.")
      await user.edit(reason="Spanked!", mute = True)
      vc = user.voice.channel
      await user.move_to(ctx.guild.afk_channel) # ADD CHECK IF AFK CHANNEL EXISTS
      
      reactions = ["🤣","🗿","💯"]
      for emoji in reactions: 
          await msg.add_reaction(emoji)

      await asyncio.sleep(time*60)
      print(f"Unspanking {user}.")
      await user.edit(mute = False) # unmute after specified time
      await user.move_to(vc)

  @spank.error
  async def spank_error(self, ctx, error):
    print(f"Error in Spank - {error.__class__.__name__}: {error}")

    if isinstance(error, commands.MissingRequiredArgument):
      await ctx.send("You forgot something, nugget! Try again!")
    elif isinstance(error, commands.MemberNotFound): 
      await ctx.send('Enter a real user, nugget!')
    elif isinstance(error, NoVoiceClient):
      await ctx.send("They ain't speaking, nugget!")
    elif isinstance(error, commands.CheckFailure):
      await ctx.send("We've got an imposter among us ඞඞඞඞඞ (You can't do that, nugget!)")
    elif isinstance(error, commands.BadArgument):
      await ctx.send("Fix your command, nugget!")
    else:
      # await ctx.send("Something went wrong!")
      pass

  @commands.command(name='ping', help='Ping the bot and return the latency in ms.')
  async def ping(self, ctx):
    await ctx.send(f"Pong! {round(self.client.latency*1000)}ms")
  
def setup(client):
  client.add_cog(General(client))