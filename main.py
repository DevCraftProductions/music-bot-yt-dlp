# === Configuration ===
DISCORD_BOT_TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
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

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

executor = ThreadPoolExecutor()
os.makedirs(AUDIO_DIR, exist_ok=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

async def search_video(ctx, urlq):
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

    if 'entries' in data:
        data = data['entries'][0]

    filename = yt_search.prepare_filename(data).replace(".webm", ".mp3").replace(".m4a", ".mp3")
    return data, filename

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
            'noplaylist': True
        }
        yt_search = yt_dlp.YoutubeDL(yt_opts)
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(executor, lambda: yt_search.extract_info(search_query, download=False))
        if 'entries' in info:
            info = info['entries'][0]
        title = info['title']
        filename = os.path.join(AUDIO_DIR, f"{title}.mp3")

        if os.path.exists(filename):
            source = discord.FFmpegPCMAudio(filename)
            voice_client = ctx.voice_client
        else:
            loading_msg = await ctx.send("Now loading...")
            info, filename = await search_video(ctx, search_query)
            source = discord.FFmpegPCMAudio(filename)
            voice_client = ctx.voice_client
            await loading_msg.delete()

        def after_playback(error):
            if error:
                print(f'Player error: {error}')
            if voice_client and voice_client.is_connected():
                bot.loop.call_soon_threadsafe(asyncio.create_task, voice_client.disconnect())

        voice_client.play(source, after=after_playback)
        await ctx.send(f"Now playing: {info['title']} <{info['webpage_url']}>")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

bot.run(DISCORD_BOT_TOKEN)
