import discord
from discord.ext import commands
import youtube_dl
from youtube_search import YoutubeSearch

class Music(commands.Cog):
  def __init__(self, client):
    self.client = client

  # @commands.command() # OLD JOIN COMMAND
  # async def join(self,ctx):
  #   if ctx.author.voice is None:
  #     await ctx.send("You're not in a voice channel!")
  #   voice_channel = ctx.author.voice.channel
  #   if ctx.voice_client is None:
  #     await voice_channel.connect()
  #   else:
  #     await ctx.voice_client.move_to(voice_channel)

  @commands.command() # TEST COMMAND
  async def test(self,ctx,channel: discord.VoiceChannel): # add to a channel 
    try:
      await channel.connect()
    except commands.errors.ChannelNotFound:
      await ctx.send("Enter a real channel!")


  @commands.command(name='join', help = 'Connect the bot to a voice channel.')
  async def join(self,ctx,*,channel: discord.VoiceChannel):     
    vcs = ctx.guild.voice_channels
    for vc in vcs:
      if vc == channel:
        if ctx.voice_client is None:
          await vc.connect()
          print("Joining vc.") # debug message
        elif ctx.voice_client.channel is not vc:
          await ctx.voice_client.move_to(vc)
          print("Moving to vc.") # debug message      
        else:
          await ctx.send("Already in that channel!")
        return
    
  @join.error
  async def join_error(self, ctx, error):
    if isinstance(error, commands.ChannelNotFound): # Handles error when someone joins bot to a non-existent channel
        await ctx.send('Enter a real channel!')


  @commands.command(name='play', help='Play a song from a youtube/soundcloud link or search phrase. Adds song to queue if one is already playing.')
  async def play(self,ctx,*,query):
    if ctx.voice_client.is_playing(): # stop playback if song is playing (replace with queue)
      ctx.voice_client.stop()

    # check if search query or url was provided
    if query.startswith('https://'):
      url = query
    else:
      results = YoutubeSearch(query, max_results=1).to_dict()
      url = 'https://www.youtube.com' + results[0]['url_suffix']

    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    YDL_OPTIONS = {'format': 'bestaudio', 'quiet': True}
    vc = ctx.voice_client

    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
      info = ydl.extract_info(url, download=False)
      url2 = info['formats'][0]['url']
      source = await discord.FFmpegOpusAudio.from_probe(url2,**FFMPEG_OPTIONS)
      vc.play(source)

  @commands.command()
  async def pause(self,ctx):
    if ctx.voice_client is None:
      await ctx.send("Not playing anything!")
    elif ctx.voice_client.is_playing():
      ctx.voice_client.pause()
      await ctx.send("Paused ⏸️")
    elif ctx.voice_client.is_paused():
      await ctx.send("Already paused!")
    else:
      await ctx.send("Not playing anything!")

  @commands.command()
  async def resume(self,ctx):
    if ctx.voice_client is None:
      await ctx.send("Nothing to resume!")
    elif ctx.voice_client.is_paused():
      ctx.voice_client.resume()
      await ctx.send("Resuming ▶️")
    elif ctx.voice_client.is_playing():
      await ctx.send("Already playing!")
    else:
      await ctx.send("Nothing to resume!")

  @commands.command(name='stop', help='Stops playback and leaves the voice channel.', aliases=['dc','disconnect'])
  async def stop(self,ctx):
    if ctx.voice_client is None:
      await ctx.send("Not in a vc!")
    
    else:
      await ctx.voice_client.disconnect()
      print("Stopping playback and leaving vc.")

def setup(client):
  client.add_cog(Music(client))