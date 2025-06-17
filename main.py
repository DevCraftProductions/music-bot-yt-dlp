import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
import functools
from concurrent.futures import ThreadPoolExecutor

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

executor = ThreadPoolExecutor()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

async def search_video(ctx, urlq):
    yt_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'default_search': 'auto',
        'noplaylist': True,
        'verbose': True
    }

    yt_search = yt_dlp.YoutubeDL(yt_opts)
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(executor, lambda: yt_search.extract_info(url=urlq, download=True))

    if 'entries' in data:
        data = data['entries'][0]

    filename = yt_search.prepare_filename(data).replace(".webm", ".mp3").replace(".m4a", ".mp3")
    return [data['title'], filename], data['webpage_url'], data['thumbnail']

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
        (info, filename), url, thumbnail = await search_video(ctx, search_query)
        source = discord.FFmpegPCMAudio(filename)

        def after_playback(error):
            if error:
                print(f'Player error: {error}')
            coro = ctx.voice_client.disconnect()
            fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
            try:
                fut.result()
            except Exception as e:
                print(f"Error disconnecting: {e}")

        ctx.voice_client.play(source, after=after_playback)
        await ctx.send(f"Now playing: {info} <{url}>")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")


@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

bot.run('YOUR_DISCORD_BOT_TOKEN')
