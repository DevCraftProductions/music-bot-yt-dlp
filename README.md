## A basic python script that utilizes yt-dlp to create a simple, yet very effective Discord bot.

This script runs a Discord bot that listens for YouTube links, downloads their respective videos as an audio file at a configurable quality (default 128kbps), then broadcasts the file to your discord server's voice channel.

The bot will store all downloaded audio to a configurable location (default "./discordbotaudio")

This bot will continue to work indefinitely, regardless of how YouTube's API and stance on audio bots may change, as long as you keep your pip dependencies updated.

It is recommended to run this bot with a residential IP address, as YouTube has been known to block ranges of datacenter IPs.

## This script has the following pip dependencies:<br/>
**<sub>discord.py<br/>
yt-dlp<br/>
ffmpeg-python<br/>
PyNaCl</sub>**

## Installlation:
1. Clone this repository
2. Run "pip install -r requirements.txt"
3. Put your Discord bot key in the top of the script, everything else is optional to change. It really is that easy.

## Commands:
!play <YouTube Video/Playlist Link><br/>
!stop<br/>
!skip<br/>
!queue<br/>
