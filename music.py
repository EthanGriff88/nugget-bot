import discord
from discord.ext import commands
import youtube_dl
from youtube_search import YoutubeSearch
import asyncio
import time
import re
from collections import deque

URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

class QueueIsEmpty(commands.CommandError):
  pass

class QueueIsFull(commands.CommandError):
  pass

class NoVoiceClient(commands.CommandError):
  pass

class AlreadyConnectedToChannel(commands.CommandError):
  pass

class WrongVoiceChannel(commands.CommandError):
  pass

class AlreadyPaused(commands.CommandError):
  pass

class AlreadyPlaying(commands.CommandError):
  pass

class InvalidCommand(commands.CommandError):
  pass

class MusicQueue:
  """A queue that stores the songs to be played."""
  def __init__(self):
    self._queue = deque([])
    self.MAXLEN = 10

  def add(self,item):
    if self.count() >= self.MAXLEN:
      raise QueueIsFull
    self._queue.append(item)

  def get(self,index=0):
    if not self._queue:
      raise QueueIsEmpty
    return self._queue[index]

  def pop(self):
    if not self._queue:
      raise QueueIsEmpty
    return self._queue.popleft()

  def count(self):
    return len(self._queue)

  def is_empty(self):
    return self.count() == 0
    
  def list(self):
    if not self._queue:
      raise QueueIsEmpty
    return [self._queue[i] for i in range(self.count())]

  def upcoming(self):
    if not self._queue:
      raise QueueIsEmpty
    newlist = self.list()
    newlist.pop(0)
    return newlist

  def clear(self):
    self._queue.clear()

class Music(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.volume_max = 0.5
    self.music_queue = {}
    self.setup()

  def setup(self): # initiate queue for each guild
    for guild in self.client.guilds:
      self.music_queue[guild.id] = MusicQueue()
    
  @commands.command(name='test', hidden='true', brief='brief', description='description', help='help') # TEST COMMAND
  async def test(self,ctx,*,item): # add to the queue
    self.music_queue[ctx.guild.id].add(item)
    await ctx.send(f"{item} added to queue.")
    await ctx.send(f"{self.music_queue[ctx.guild.id].get()} retrieved from queue.")
    await ctx.send(f"Queue count is {self.music_queue[ctx.guild.id].count()}.")
    await ctx.send(f"List of items:\n{self.music_queue[ctx.guild.id].list()}")
    # if ctx.voice_client.source is None:
    #   print(f"{ctx.voice_client.source}")

  @commands.command(name='join', help ='Connect the bot to a voice channel.', aliases=['connect'])
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
      raise AlreadyConnectedToChannel
    return

  @join.error
  async def join_error(self, ctx, error):
    print(f"Error in Join - {error.__class__.__name__}: {error}")

    if isinstance(error, commands.MissingRequiredArgument):
      await ctx.send("Enter a channel to join, nugget!")
    elif isinstance(error, commands.ChannelNotFound): # Handles error when someone joins bot to a non-existent channel
      await ctx.send('Enter a real channel, nugget!')
    elif isinstance(error, AlreadyConnectedToChannel):
      await ctx.send("Already in that channel, nugget!")
    else:
      await ctx.send("Something went wrong, nugget!")

  @commands.command(name='song', aliases=['nowplaying','np','currentsong'], help='Get the current song name.')
  async def song(self,ctx):
    song = self.music_queue[ctx.guild.id].get()

    if song['duration'] < 3600:
      song_length = time.strftime("%M:%S",time.gmtime(song['duration']))
    else:
      song_length = time.strftime("%H:%M:%S",time.gmtime(song['duration']))

    embed = discord.Embed(
      colour=ctx.author.colour,
      title='Now Playing:',
      description = f"{song['title']} **[{song_length}]**\n{song['webpage_url']}"
    )
    embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

    
    # embed.add_field(name="Now Playing:", value=song['title']+f" **[{song_length}]**", inline=False)
    
    
    await ctx.send(embed=embed)

  @song.error
  async def song_error(self, ctx, error):
    print(f"Error in NowPlaying - {error.__class__.__name__}: {error}")

    if isinstance(error, QueueIsEmpty):
      await ctx.send("Not playing anything, nugget!")
    else:
      await ctx.send("An error occured, nugget!")

  @commands.command(name='queue', aliases=['q','que'], help='List the current song queue.')
  async def queue(self,ctx):
    NEWLINE = '\n'
    queue = self.music_queue[ctx.guild.id]
    song = queue.get()
    embed = discord.Embed(
      title="Queue",
      colour=ctx.author.colour
    )

    if song['duration'] < 3600:
      song_length = time.strftime("%M:%S",time.gmtime(song['duration']))
    else:
      song_length = time.strftime("%H:%M:%S",time.gmtime(song['duration']))
      
    embed.add_field(name="Now Playing:", value=song['title']+f" **[{song_length}]**\n{song['webpage_url']}", inline=False)

    if queue.count() > 1:
      embed.add_field(
        name="Next Up:",
        value=NEWLINE.join(str(i+1)+". "+x['title'] for i,x in enumerate(queue.upcoming())),
        inline=False
      )
    
    embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

    await ctx.send(embed=embed)

  @queue.error
  async def queue_error(self, ctx, error):
    print(f"Error in Queue - {error.__class__.__name__}: {error}")

    if isinstance(error, QueueIsEmpty):
      await ctx.send("Queue empty, nugget!")
    else:
      await ctx.send("An error occured, nugget!")

  @commands.command(name='play', brief='Play a song from youtube/soundcloud.', help='Play a song from youtube/soundcloud. Adds song to queue if one is already playing.')
  async def play(self,ctx,*,query):    
    # Check if user is in vc
    if ctx.author.voice is None and ctx.voice_client is None:
      raise NoVoiceClient
    elif ctx.author.voice is None:
      raise WrongVoiceChannel
    elif ctx.voice_client is None:
      await ctx.author.voice.channel.connect()
    elif ctx.voice_client.channel.id is not ctx.author.voice.channel.id: # REENABLE BOTH OF THESE IFS AFTER TESTING WITHOUT VC
      raise WrongVoiceChannel  

    self.curr_ctx = ctx # FOR DEBUGGING

    # tell user that bot is searching
    wait_msg = await ctx.send("Searching for the song, this won't take longer than a whiskey delta...")

    # check if search query or url was provided
    query = query.strip("<>")
    if not re.match(URL_REGEX, query):
      results = YoutubeSearch(query, max_results=1).to_dict() # LATER IMPLEMENT MULTIPLE SEARCH RESULTS
      url = 'https://www.youtube.com' + results[0]['url_suffix']
    else:
      url = query

    YDL_OPTIONS = {'format': 'bestaudio'}    

    # get song info and add to queue
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
      info = await self.client.loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
      self.music_queue[ctx.guild.id].add(info)
      print("Song added to queue.")
      await wait_msg.delete() # delete searching message

      if self.music_queue[ctx.guild.id].count()==1 and not ctx.voice_client.is_playing(): # run play_song if this is the first song
        await(self.play_song(ctx))
      else:
        await ctx.send(f"{info['title']} added to the queue.")

  @play.error
  async def play_error(self, ctx, error):
    print(f"Error in Play - {error.__class__.__name__}: {error}")

    if isinstance(error, commands.MissingRequiredArgument):
      await ctx.send("Enter something to play, nugget!")
    elif isinstance(error, youtube_dl.utils.UnsupportedError): # Handles error when invalid link is given
      await ctx.send('Invalid URL, nugget!')
    elif isinstance(error, NoVoiceClient):
      await ctx.send("You're not in a vc, nugget!")
    elif isinstance(error, WrongVoiceChannel):
      await ctx.send("You must be in my vc, nugget!")
    elif isinstance(error, QueueIsFull):
      await ctx.send("Queue full! Wait until the next song plays, nugget!")
    else:
      await ctx.send("Something went wrong, nugget!")
  
  async def play_song(self,ctx):
    # pull song from queue and play 
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    info = self.music_queue[ctx.guild.id].get()
    # await ctx.send(f"**Now playing**: {info['title']}\n{info['webpage_url']}")
    await self.song(ctx) # use embed instead
    url2 = info['formats'][0]['url']
    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url2,**FFMPEG_OPTIONS))
    source.volume = self.volume_max
    # ctx.voice_client.play(source, after=lambda error: self.client.loop.create_task(self.play_next(ctx,error)))
    ctx.voice_client.play(source, after=self.after)
    print("Playing song.")
  
  def after(self,error):
    coro = self.play_next()
    fut = asyncio.run_coroutine_threadsafe(coro, self.client.loop)
    try:
      fut.result()
    except:
      if error is not None:
        print(f"Error running coroutine: {error}")

  # async def play_next(self,ctx,error):
  async def play_next(self):
    # if error is not None:
    #   print(f"Error running coroutine from play_next: {error}")
    
    self.music_queue[self.curr_ctx.guild.id].pop() # remove previous song

    if not self.music_queue[self.curr_ctx.guild.id].is_empty(): # check if queue is empty first
      await self.play_song(self.curr_ctx) # play next song
    else:
      print("Inactivity timer start.")
      await asyncio.sleep(120) # BAD IMPLEMENTATION AS IT CONTINUES COUNTING AFTER NEW PLAY COMMAND, FIX THIS (use asyncio Create/Destroy Task)
      print("Inactivity timer stop.")
      # if not ctx.voice_client.is_playing():
      if self.music_queue[self.curr_ctx.guild.id].is_empty():
        print("Leaving vc due to inactivity.")
        await self.curr_ctx.voice_client.disconnect()
  
  def check_same_vc(self,ctx): 
    '''Checks if user is in same vc as the bot. Raises NoVoiceClient or WrongVoiceChannel respectively.'''
    if ctx.voice_client is None:
      raise NoVoiceClient
    
    if ctx.author.voice is None or ctx.voice_client.channel.id is not ctx.author.voice.channel.id:
      raise WrongVoiceChannel

  @commands.command(name='volume', help='Change the player volume from 0-100%. Default is 50%', aliases=['vol'])
  async def volume(self,ctx,volume_perc):
    if not 0 <= float(volume_perc) <= 100:
      print(f"Invalid volume given.")
      return await ctx.send("Enter a number from 0-100, nugget!")      

    volume_dec = float(volume_perc)/100
    self.volume_max = volume_dec
    if not self.music_queue[ctx.guild.id].is_empty():
      ctx.voice_client.source.volume = volume_dec

    print(f"Volume set to {volume_perc}%")
    await ctx.send(f"Volume set to {volume_perc}%")

  @volume.error
  async def volume_error(self, ctx, error):
    print(f"Error in Volume - {error.__class__.__name__}: {error}")

    if isinstance(error, commands.MissingRequiredArgument):
      await ctx.send("Enter something to play, nugget!")
    else:
      await ctx.send("Something went wrong, nugget!")

  @commands.command(name='skip', help='Skips the current song.') # later add forceskip, checking for admin privilege (or similar), and voteskip
  async def skip(self,ctx):
    self.check_same_vc(ctx) # check user is in same vc
    if self.music_queue[ctx.guild.id].is_empty():
      raise QueueIsEmpty
    else:
      if ctx.author.guild_permissions.administrator or 'DJ' in [roles.name for roles in ctx.author.roles]: # forceskip if admin or dj
        ctx.voice_client.stop()
        await ctx.send("Song skipped!")
        print("Song skipped")
      else: # voteskip if normie
        member_count = len(ctx.voice_client.channel.members)
        # SEND A MESSAGE TO VOTESKIP, LET MEMBERS IN THE VC REACT TO THE MESSAGE, IF MORE THAN 50% SKIP, THEN SKIP, OTHERWISE DON'T


  @skip.error
  async def skip_error(self, ctx, error):
    print(f"Error in Skip - {error.__class__.__name__}: {error}")
    if isinstance(error, NoVoiceClient) or isinstance(error, QueueIsEmpty):
      await ctx.send("Not playing anything, nugget!")
    elif isinstance(error, WrongVoiceChannel):
      await ctx.send("You must be in my vc, nugget!")
    else:
      await ctx.send("Something went wrong, nugget!")

  @commands.command(name='pause', help='Pauses the current song.')
  async def pause(self,ctx):
    self.check_same_vc(ctx) # check user is in same vc
    if ctx.voice_client.is_paused():
      raise AlreadyPaused
    elif self.music_queue[ctx.guild.id].is_empty():
      raise QueueIsEmpty
    elif ctx.voice_client.is_playing():
      ctx.voice_client.pause()
      await ctx.send("Paused ⏸️")
      print("Client Paused")
    else:
      raise InvalidCommand

  @pause.error
  async def pause_error(self, ctx, error):
    print(f"Error in Pause - {error.__class__.__name__}: {error}")
    if isinstance(error, NoVoiceClient) or isinstance(error, QueueIsEmpty):
      await ctx.send("Not playing anything, nugget!")
    elif isinstance(error, WrongVoiceChannel):
      await ctx.send("You must be in my vc, nugget!")
    elif isinstance(error, AlreadyPaused):
      await ctx.send("Already paused, nugget!")
    else:
      await ctx.send("Something went wrong, nugget!")

  @commands.command(name='resume', help="Resumes a paused song.")
  async def resume(self,ctx):
    self.check_same_vc(ctx) # check user is in same vc
    if ctx.voice_client.is_playing():
      raise AlreadyPlaying
    elif self.music_queue[ctx.guild.id].is_empty():
      raise QueueIsEmpty
    elif ctx.voice_client.is_paused():
      ctx.voice_client.resume()
      await ctx.send("Resuming ▶️")
      print("Client Resuming")
    else:
      raise InvalidCommand

  @resume.error
  async def resume_error(self, ctx, error):
    print(f"Error in Pause - {error.__class__.__name__}: {error}")
    if isinstance(error, NoVoiceClient) or isinstance(error, QueueIsEmpty):
      await ctx.send("Nothing to resume, nugget!")
    elif isinstance(error, WrongVoiceChannel):
      await ctx.send("You must be in my vc, nugget!")
    elif isinstance(error, AlreadyPlaying):
      await ctx.send("Already playing, nugget!")
    else:
      await ctx.send("Something went wrong, nugget!")

  @commands.command(name='stop', help='Stops playback and leaves the voice channel.', aliases=['dc','disconnect','leave'])
  async def stop(self,ctx):
    self.check_same_vc(ctx) # check user is in same vc
    print("Stopping playback and leaving vc.")
    await ctx.voice_client.disconnect()
    self.music_queue[ctx.guild.id].clear()

  @stop.error
  async def stop_error(self,ctx,error):
    print(f"Error in Pause - {error.__class__.__name__}: {error}")
    if isinstance(error, NoVoiceClient) or isinstance(error, QueueIsEmpty):
      await ctx.send("Not playing anything, nugget!")
    elif isinstance(error, WrongVoiceChannel):
      await ctx.send("You must be in my vc, nugget!")
    

def setup(client):
  client.add_cog(Music(client))