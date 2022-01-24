import discord
from discord.ext import commands
import youtube_dl
from youtube_search import YoutubeSearch
import time
from collections import deque

class Music(commands.Cog):
  def __init__(self, client):
    self.client = client
  
  music_queue = deque([])

  def qadd(self,item):
    self.music_queue.append(item)

  def qget(self):
    return self.music_queue.popleft()

  def qcount(self):
    return len(self.music_queue)
    
  def qlist(self):
    return [self.music_queue[i] for i in range(self.qcount())]
    
  @commands.command() # TEST COMMAND
  async def test(self,ctx,*,item): # add to the queue
    self.qadd(item)
    self.qadd(item+item)
    self.qadd(item+"dwadaw")
    self.qadd(item)
    self.qadd(item+"27328163")
    await ctx.send(f"{item} added to queue.")
    await ctx.send(f"{self.qget()} retrieved from queue.")
    await ctx.send(f"Queue count is {self.qcount()}.")
    print(self.qlist())

  @commands.command(name='join', help = 'Connect the bot to a voice channel.')
  async def join(self,ctx,*,vc: discord.VoiceChannel):     
    vclient = ctx.voice_client

    # match channel query to channels in 
    if vclient is None:
      await vc.connect()
      print("Joining vc.") # debug message
    elif vclient.channel is not vc:
      await vclient.move_to(vc)
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
    vclient = ctx.voice_client
    user_vc = ctx.author.voice
    if user_vc is None and vclient is None:
      await ctx.send("You're not in a voice channel!")
      return
    elif vclient is None:
      await user_vc.channel.connect()
    
    # if ctx.author.voice is not None: # join vc if user is in channel
      
    #   if vclient is None:
    #     await vc.connect()
      # else:
      #   if vclient.is_playing(): # stop playback if song is playing (replace with queue)
      #     vclient.stop()  
      #   await vclient.move_to(vc)          

    # check if search query or url was provided
    if query.startswith('https://'):
      url = query
    else:
      results = YoutubeSearch(query, max_results=1).to_dict()
      url = 'https://www.youtube.com' + results[0]['url_suffix']

    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    YDL_OPTIONS = {'format': 'bestaudio', 'quiet': True}    

    # get song info and add to queue
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
      info = ydl.extract_info(url, download=False)
      self.qadd(info)
      # url2 = info['formats'][0]['url']
      # source = await discord.FFmpegOpusAudio.from_probe(url2,**FFMPEG_OPTIONS)
      # ctx.voice_client.play(source)
      # # await ctx.message.edit(embed=None)
      # # await ctx.send(f"Now playing: {info['title']}.\n{url}")
      # await ctx.send(f"Now playing: {info['title']}")

    # pull next song from queue and play
    song_info = self.qget()
    url2 = song_info['formats'][0]['url']
    source = await discord.FFmpegOpusAudio.from_probe(url2,**FFMPEG_OPTIONS)
    ctx.voice_client.play(source)
    await ctx.send(f"**Now playing**: {song_info['title']}")
    

  @commands.command()
  async def pause(self,ctx):
    vclient = ctx.voice_client
    if vclient is None:
      await ctx.send("Not playing anything!")
    elif vclient.is_playing():
      vclient.pause()
      await ctx.send("Paused ⏸️")
    elif vclient.is_paused():
      await ctx.send("Already paused!")
    else:
      await ctx.send("Not playing anything!")

  @commands.command()
  async def resume(self,ctx):
    vclient = ctx.voice_client
    if vclient is None:
      await ctx.send("Nothing to resume!")
    elif vclient.is_paused():
      vclient.resume()
      await ctx.send("Resuming ▶️")
    elif vclient.is_playing():
      await ctx.send("Already playing!")
    else:
      await ctx.send("Nothing to resume!")

  @commands.command(name='stop', help='Stops playback and leaves the voice channel.', aliases=['dc','disconnect'])
  async def stop(self,ctx):
    vclient = ctx.voice_client
    if vclient is None:
      await ctx.send("Not in a vc!")
    
    else:
      await vclient.disconnect()
      print("Stopping playback and leaving vc.")

def setup(client):
  client.add_cog(Music(client))