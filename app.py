"""
MIT License

Copyright (c) 2021 Janindu Malshan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# Modified by Tinura Dinith
# Removed bot parts

import os
import json
import asyncio
import youtube_dl
from pytube import YouTube
from pyrogram import Client, filters
from youtube_search import YoutubeSearch
from pytgcalls import PyTgCalls, idle, StreamType
from pytgcalls.types import Update
from pyrogram.raw.base import Update
from pytgcalls.types import (AudioPiped, AudioVideoPiped, HighQualityAudio, 
                      HighQualityVideo, LowQualityVideo, MediumQualityVideo)
from pytgcalls.types.stream import StreamAudioEnded
from helpers import QUEUE, add_to_queue, get_queue, clear_queue, pop_an_item, is_admin

# Config
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")
OWNER = os.getenv("OWNER_ID")
OWNER_ID = [int(x) for x in OWNER.split()]

bot = Client(SESSION, API_ID, API_HASH)
app = PyTgCalls(bot)
LIVE_CHATS = []

START_TEXT = """
Hi <b>{}</b> 👋
I can play music & stream videos in Telegram group voice chats. 
Make your own bot using below source code.
"""


async def skip_current_song(chat_id):
    if chat_id in QUEUE:
        chat_queue = get_queue(chat_id)
        if len(chat_queue) == 1:
            await app.leave_group_call(chat_id)
            clear_queue(chat_id)
            return 1
        else:
            title = chat_queue[1][0]
            duration = chat_queue[1][1]
            link = chat_queue[1][2]
            playlink = chat_queue[1][3]
            type = chat_queue[1][4]
            Q = chat_queue[1][5]
            thumb = chat_queue[1][6]
            if type == "Audio":
                await app.change_stream(
                    chat_id,
                    AudioPiped(
                        playlink,
                    ),
                )
            elif type == "Video":
                if Q == "high":
                    hm = HighQualityVideo()
                elif Q == "mid":
                    hm = MediumQualityVideo()
                elif Q == "low":
                    hm = LowQualityVideo()
                else:
                    hm = MediumQualityVideo()
                await app.change_stream(
                    chat_id, AudioVideoPiped(playlink, HighQualityAudio(), hm)
                )
            pop_an_item(chat_id)
            await bot.send_photo(chat_id, photo = thumb,
                                 caption = f"▶️ <b>Now playing:</b> [{title}]({link}) | `{type}` \n\n⏳ <b>Duration:</b> {duration}")
            return [title, link, type, duration, thumb]
    else:
        return 0


async def skip_item(chat_id, lol):
    if chat_id in QUEUE:
        chat_queue = get_queue(chat_id)
        try:
            x = int(lol)
            title = chat_queue[x][0]
            chat_queue.pop(x)
            return title
        except Exception as e:
            print(e)
            return 0
    else:
        return 0


@app.on_stream_end()
async def on_end_handler(_, update: Update):
    if isinstance(update, StreamAudioEnded):
        chat_id = update.chat_id
        await skip_current_song(chat_id)


@app.on_closed_voice_chat()
async def close_handler(client: PyTgCalls, chat_id: int):
    if chat_id in QUEUE:
        clear_queue(chat_id)
        

async def yt_video(link):
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "-g",
        "-f",
        "best[height<=?720][width<=?1280]",
        f"{link}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        return 1, stdout.decode().split("\n")[0]
    else:
        return 0, stderr.decode()
    

async def yt_audio(link):
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "-g",
        "-f",
        "bestaudio",
        f"{link}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        return 1, stdout.decode().split("\n")[0]
    else:
        return 0, stderr.decode()


            

@bot.on_message(filters.command("start", prefixes=".") & (filters.outgoing|filters.user(OWNER_ID)))
async def start_private(_, message):
    msg = START_TEXT.format(message.from_user.mention)
    await message.reply_text(text = msg)
    
    
@bot.on_message(filters.command(["play", "vplay"] ,prefixes=".") & ~filters.private & (filters.outgoing|filters.user(OWNER_ID)))
async def video_play(_, message):
    await message.delete()
    user_id = message.from_user.id
    state = message.command[0].lower()
    try:
        query = message.text.split(None, 1)[1]
    except:
        return await message.reply_text(f"<b>Usage:</b> <code>/{state} [query]</code>")
    chat_id = message.chat.id
    if chat_id in LIVE_CHATS:
        return await message.reply_text("❗️Please send <code>/stop</code> to end current live streaming before play songs or videos.")
    
    m = await message.reply_text("🔄 Processing...")
    if state == "play":
        damn = AudioPiped
        ded = yt_audio
        doom = "Audio"
    elif state == "vplay":
        damn = AudioVideoPiped
        ded = yt_video
        doom = "Video"
    if "low" in query:
        Q = "low"
    elif "mid" in query:
        Q = "mid"
    elif "high" in query:
        Q = "high"
    else:
        Q = "0"
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        link = f"https://youtube.com{results[0]['url_suffix']}"
        thumb = results[0]["thumbnails"][0]
        duration = results[0]["duration"]
        yt = YouTube(link)
        cap = f"▶️ <b>Now playing:</b> [{yt.title}]({link}) | `{doom}` \n\n⏳ <b>Duration:</b> {duration}"
        try:
            ydl_opts = {"format": "bestvideo[height<=720]+bestaudio/best[height<=720]"}
            ydl = youtube_dl.YoutubeDL(ydl_opts)
            info_dict = ydl.extract_info(link, download=False)
            p = json.dumps(info_dict)
            a = json.loads(p)
            playlink = a['formats'][1]['manifest_url']
        except:
            ice, playlink = await ded(link)
            if ice == "0":
                return await m.edit("❗️YTDL ERROR !!!")               
    except Exception as e:
        return await m.edit(str(e))
    
    try:
        if chat_id in QUEUE:
            position = add_to_queue(chat_id, yt.title, duration, link, playlink, doom, Q, thumb)
            caps = f"#️⃣ [{yt.title}]({link}) <b>queued at position {position}</b> \n\n⏳ <b>Duration:</b> {duration}"
            await message.reply_photo(thumb, caption=caps)
            await m.delete()
        else:            
            await app.join_group_call(
                chat_id,
                damn(playlink),
                stream_type=StreamType().pulse_stream
            )
            add_to_queue(chat_id, yt.title, duration, link, playlink, doom, Q, thumb)
            await message.reply_photo(thumb, caption=cap)
            await m.delete()
    except Exception as e:
        return await m.edit(str(e))
    
    
@bot.on_message(filters.command(["saudio", "svideo"] ,prefixes=".") & ~filters.private & (filters.outgoing|filters.user(OWNER_ID)))
@is_admin
async def stream_func(_, message):
    await message.delete()
    state = message.command[0].lower()
    try:
        link = message.text.split(None, 1)[1]
    except:
        return await message.reply_text(f"<b>Usage:</b> <code>/{state} [link]</code>")
    chat_id = message.chat.id
    
    if state == "saudio":
        damn = AudioPiped
        emj = "🎵"
    elif state == "svideo":
        damn = AudioVideoPiped
        emj = "🎬"
    m = await message.reply_text("🔄 Processing...")
    try:
        if chat_id in QUEUE:
            return await m.edit("❗️Please send <code>/stop</code> to end voice chat before live streaming.")
        elif chat_id in LIVE_CHATS:
            await app.change_stream(
                chat_id,
                damn(link)
            )
            await m.edit(f"{emj} Started streaming: [Link]({link})", disable_web_page_preview=True)
        else:    
            await app.join_group_call(
                chat_id,
                damn(link),
                stream_type=StreamType().pulse_stream)
            await m.edit(f"{emj} Started streaming: [Link]({link})", disable_web_page_preview=True)
            LIVE_CHATS.append(chat_id)
    except Exception as e:
        return await m.edit(str(e))


@bot.on_message(filters.command("skip" ,prefixes=".") & ~filters.private & (filters.outgoing|filters.user(OWNER_ID)))
@is_admin
async def skip(_, message):
    await message.delete()
    chat_id = message.chat.id
    if len(message.command) < 2:
        op = await skip_current_song(chat_id)
        if op == 0:
            await message.reply_text("❗️Nothing in the queue to skip.")
        elif op == 1:
            await message.reply_text("❗️Empty queue, stopped streaming.")
    else:
        skip = message.text.split(None, 1)[1]
        out = "🗑 <b>Removed the following song(s) from the queue:</b> \n"
        if chat_id in QUEUE:
            items = [int(x) for x in skip.split(" ") if x.isdigit()]
            items.sort(reverse=True)
            for x in items:
                if x == 0:
                    pass
                else:
                    hm = await skip_item(chat_id, x)
                    if hm == 0:
                        pass
                    else:
                        out = out + "\n" + f"<b>#️⃣ {x}</b> - {hm}"
            await message.reply_text(out)
            
            
@bot.on_message(filters.command(["playlist", "queue"] ,prefixes=".") & ~filters.private & (filters.outgoing|filters.user(OWNER_ID)))
@is_admin
async def playlist(_, message):
    chat_id = message.chat.id
    if chat_id in QUEUE:
        chat_queue = get_queue(chat_id)
        if len(chat_queue) == 1:
            await message.delete()
            await message.reply_text(
                f"▶️ <b>Now playing:</b> [{chat_queue[0][0]}]({chat_queue[0][2]}) | `{chat_queue[0][4]}`",
                disable_web_page_preview=True,
            )
        else:
            out = f"<b>📃 Player queue:</b> \n\n▶️ <b>Now playing:</b> [{chat_queue[0][0]}]({chat_queue[0][2]}) | `{chat_queue[0][4]}` \n"
            l = len(chat_queue)
            for x in range(1, l):
                title = chat_queue[x][0]
                link = chat_queue[x][2]
                type = chat_queue[x][4]
                out = out + "\n" + f"<b>#️⃣ {x}</b> - [{title}]({link}) | `{type}` \n"
            await message.reply_text(out, disable_web_page_preview=True)
    else:
        await message.reply_text("❗Nothing is playing.")
    

@bot.on_message(filters.command("stop" ,prefixes=".") & ~filters.private & (filters.outgoing|filters.user(OWNER_ID)))
@is_admin
async def end(_, message):
    await message.delete()
    chat_id = message.chat.id
    if chat_id in LIVE_CHATS:
        await app.leave_group_call(chat_id)
        LIVE_CHATS.remove(chat_id)
        return await message.reply_text("⏹ Stopped streaming.")
        
    if chat_id in QUEUE:
        await app.leave_group_call(chat_id)
        clear_queue(chat_id)
        await message.reply_text("⏹ Stopped streaming.")
    else:
        await message.reply_text("❗Nothing is playing.")
        

@bot.on_message(filters.command("pause" ,prefixes=".") & ~filters.private & (filters.outgoing|filters.user(OWNER_ID)))
@is_admin
async def pause(_, message):
    await message.delete()
    chat_id = message.chat.id
    if chat_id in QUEUE:
        try:
            await app.pause_stream(chat_id)
            await message.reply_text("⏸ Paused streaming.")
        except:
            await message.reply_text("❗Nothing is playing.")
    else:
        await message.reply_text("❗Nothing is playing.")
        
        
@bot.on_message(filters.command("resume" ,prefixes=".") & ~filters.private & (filters.outgoing|filters.user(OWNER_ID)))
@is_admin
async def resume(_, message):
    await message.delete()
    chat_id = message.chat.id
    if chat_id in QUEUE:
        try:
            await app.resume_stream(chat_id)
            await message.reply_text("⏸ Resumed streaming.")
        except:
            await message.reply_text("❗Nothing is playing.")
    else:
        await message.reply_text("❗Nothing is playing.")
        
        
@bot.on_message(filters.command("mute" ,prefixes=".") & ~filters.private & (filters.outgoing|filters.user(OWNER_ID)))
@is_admin
async def mute(_, message):
    await message.delete()
    chat_id = message.chat.id
    if chat_id in QUEUE:
        try:
            await app.mute_stream(chat_id)
            await message.reply_text("🔇 Muted streaming.")
        except:
            await message.reply_text("❗Nothing is playing.")
    else:
        await message.reply_text("❗Nothing is playing.")
        
        
@bot.on_message(filters.command("unmute" ,prefixes=".") & ~filters.private & (filters.outgoing|filters.user(OWNER_ID)))
@is_admin
async def unmute(_, message):
    await message.delete()
    chat_id = message.chat.id
    if chat_id in QUEUE:
        try:
            await app.unmute_stream(chat_id)
            await message.reply_text("🔊 Unmuted streaming.")
        except:
            await message.reply_text("❗Nothing is playing.")
    else:
        await message.reply_text("❗Nothing is playing.")
        
        
@bot.on_message(filters.command("restart" ,prefixes="."))
async def restart(_, message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return
    await message.reply_text("🛠 <i>Restarting Music Player...</i>")
    os.system(f"kill -9 {os.getpid()} && python3 app.py")
            

app.start()
print("Started")
idle()
