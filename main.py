# === Configuration ===
DISCORD_BOT_TOKEN = 'YOUR_DISCORD_BOT_TOKEN_HERE'
AUDIO_DIR = './discordbotaudio'
AUDIO_QUALITY = '128'  # in kbps
COMMAND_PREFIX = '!'

import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
import functools
from concurrent.futures import ThreadPoolExecutor
from collections import deque

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

executor = ThreadPoolExecutor()
os.makedirs(AUDIO_DIR, exist_ok=True)

music_queues = {}

def get_queue(guild_id):
    if guild_id not in music_queues:
        music_queues[guild_id] = deque()
    return music_queues[guild_id]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

def get_cached_filename(title):
    for ext in ['.mp3']:
        path = os.path.join(AUDIO_DIR, f'{title}{ext}')
        if os.path.isfile(path):
            return path
    return None

async def download_audio(ctx, urlq):
    yt_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': AUDIO_QUALITY,
        }],
        'default_search': 'auto',
        'noplaylist': True,
        'verbose': True,
        'outtmpl': os.path.join(AUDIO_DIR, '%(title)s.%(ext)s')
    }

    yt_search = yt_dlp.YoutubeDL(yt_opts)
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(executor, lambda: yt_search.extract_info(url=urlq, download=True))

    filename = yt_search.prepare_filename(data).replace(".webm", ".mp3").replace(".m4a", ".mp3")
    return data, filename

async def play_next(ctx):
    queue = get_queue(ctx.guild.id)
    if queue:
        info = queue.popleft()
        try:
            title = info.get('title') or info.get('id')
            url = info.get('url') or info.get('webpage_url') or info.get('original_url')
        except Exception as e:
            await ctx.send(f"Error extracting song info: {str(e)}")
            return

        filename = get_cached_filename(title)
        if not filename:
            await ctx.send("Now loading...")
            _, filename = await download_audio(ctx, url)

        source = discord.FFmpegPCMAudio(filename)

        def after_playback(error):
            if error:
                print(f'Player error: {error}')
            bot.loop.call_soon_threadsafe(asyncio.create_task, play_next(ctx))

        ctx.voice_client.play(source, after=after_playback)
        await ctx.send(f"Now playing: {title} <{url}>")
    else:
        if ctx.voice_client and ctx.voice_client.is_connected():
            await ctx.voice_client.disconnect()

@bot.command()
async def play(ctx, *, search_query):
    if ctx.author.voice is None:
        await ctx.send("You need to be in a voice channel to use this command.")
        return

    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await voice_channel.connect()
    elif ctx.voice_client.channel != voice_channel:
        await ctx.voice_client.move_to(voice_channel)

    try:
        yt_opts = {
            'quiet': True,
            'skip_download': True,
            'default_search': 'auto',
            'extract_flat': 'in_playlist',
            'force_generic_extractor': True
        }
        yt_search = yt_dlp.YoutubeDL(yt_opts)
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(executor, lambda: yt_search.extract_info(search_query, download=False))

        entries = info['entries'] if 'entries' in info else [info]

        queue = get_queue(ctx.guild.id)
        for entry in entries:
            if entry:
                queue.append(entry)

        if not ctx.voice_client.is_playing():
            await play_next(ctx)
        else:
            await ctx.send(f"Queued {len(entries)} track(s).")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.command()
async def stop(ctx):
    queue = get_queue(ctx.guild.id)
    queue.clear()
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped current track.")
    else:
        await ctx.send("No track is currently playing.")

@bot.command()
async def queue(ctx):
    queue = get_queue(ctx.guild.id)
    if not queue:
        await ctx.send("The queue is empty.")
    else:
        message = "**Current Queue:**\n"
        for i, item in enumerate(list(queue)[:20]):
            title = item.get('title') or item.get('id', 'Unknown')
            message += f"{i+1}. {title}\n"
        if len(queue) > 20:
            message += f"...and {len(queue) - 20} more."
        await ctx.send(message)

bot.run(DISCORD_BOT_TOKEN)
