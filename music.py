import discord
from discord.ext import commands
import youtube_dl

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

  @commands.command(name='join', help = 'Connect the bot to a voice channel.')
  async def join(self,ctx,channel=str): # add to a channel 
    print(ctx.guild.voice_channels)

    vcs = ctx.guild.voice_channels
    for vc in vcs:
      if vc.name == channel:
        await vc.connect()

  @commands.command()
  async def play(self,ctx,url):
    ctx.voice_client.stop()

    # youtube_dl.utils.bug_reports_message = lambda: ''

    # ytdl_format_options = {
    #     'format': 'bestaudio/best',
    #     'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    #     'restrictfilenames': True,
    #     'noplaylist': True,
    #     'nocheckcertificate': True,
    #     'ignoreerrors': False,
    #     'logtostderr': False,
    #     'quiet': True,
    #     'no_warnings': True,
    #     'default_search': 'auto',
    #     'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
    # }

    # ffmpeg_options = {
    #     'options': '-vn'
    # }

    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    YDL_OPTIONS = {'format': "bestaudio", 'quiet': True}
    vc = ctx.voice_client

    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
      info = ydl.extract_info(url, download=False)
      url2 = info['formats'][0]['url']
      source = await discord.FFmpegOpusAudio.from_probe(url2,**FFMPEG_OPTIONS)
      vc.play(source)

  @commands.command()
  async def pause(self,ctx):
    await ctx.voice_client.pause()
    await ctx.send("Paused")

  @commands.command()
  async def resume(self,ctx):
    await ctx.voice_client.resume()
    await ctx.send("Resumed")

  @commands.command()
  async def stop(self,ctx):
    if ctx.voice_client is None:
      await ctx.send("Not playing!")
    
    elif ctx.voice_client.is_playing():
      await ctx.voice_client.disconnect()

  # alias for dc
  # dc = disconnect() 

def setup(client):
  client.add_cog(Music(client))