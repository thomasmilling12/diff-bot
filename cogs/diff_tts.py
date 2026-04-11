from __future__ import annotations

import asyncio
import os
import re
import tempfile
from collections import deque
from typing import Optional

import discord
from discord.ext import commands

GUILD_ID          = 850386896509337710
NO_MIC_CHANNEL_ID = 1485684651849679058
TTS_VOICE         = "en-US-AriaNeural"
MAX_TTS_CHARS     = 300
MAX_QUEUE         = 15
IDLE_DISCONNECT_S = 60


class DiffTTS(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._queues:     dict[int, deque[tuple[str, str]]] = {}
        self._processing: set[int] = set()

    def _q(self, gid: int) -> deque[tuple[str, str]]:
        if gid not in self._queues:
            self._queues[gid] = deque()
        return self._queues[gid]

    def _best_vc(self, guild: discord.Guild) -> Optional[discord.VoiceChannel]:
        best, best_n = None, 0
        for vc in guild.voice_channels:
            n = sum(1 for m in vc.members if not m.bot)
            if n > best_n:
                best_n, best = n, vc
        return best if best_n > 0 else None

    async def _process_queue(self, guild: discord.Guild) -> None:
        gid = guild.id
        q   = self._q(gid)
        while q:
            text, speaker = q.popleft()
            vc = guild.voice_client
            if not vc or not vc.is_connected():
                break

            if vc.is_playing():
                await asyncio.sleep(0.5)
                q.appendleft((text, speaker))
                continue

            tmp_path = None
            done     = asyncio.Event()
            try:
                import edge_tts
                tts = edge_tts.Communicate(f"{speaker}: {text}", TTS_VOICE)
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    tmp_path = f.name
                await tts.save(tmp_path)

                def _after(err):
                    if tmp_path:
                        try:
                            os.unlink(tmp_path)
                        except Exception:
                            pass
                    self.bot.loop.call_soon_threadsafe(done.set)

                vc.play(discord.FFmpegPCMAudio(tmp_path), after=_after)
                await done.wait()
            except Exception as e:
                print(f"[TTS] play error: {e}")
                if tmp_path:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
                await asyncio.sleep(0.3)

        self._processing.discard(gid)
        await asyncio.sleep(IDLE_DISCONNECT_S)
        vc = guild.voice_client
        if vc and not vc.is_playing() and gid not in self._processing:
            try:
                await vc.disconnect()
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if not message.guild or message.guild.id != GUILD_ID:
            return
        if message.channel.id != NO_MIC_CHANNEL_ID:
            return

        text = message.clean_content.strip()
        if not text or text.startswith(("/", "!", ".")):
            return

        text = re.sub(r"https?://\S+", "link", text)
        text = text[:MAX_TTS_CHARS]

        guild     = message.guild
        target_vc = self._best_vc(guild)
        if not target_vc:
            return

        vc = guild.voice_client
        if not vc:
            try:
                vc = await target_vc.connect()
            except Exception as e:
                print(f"[TTS] connect error: {e}")
                return
        elif vc.channel.id != target_vc.id:
            try:
                await vc.move_to(target_vc)
            except Exception:
                pass

        q = self._q(guild.id)
        if len(q) < MAX_QUEUE:
            q.append((text, message.author.display_name))

        if guild.id not in self._processing:
            self._processing.add(guild.id)
            asyncio.create_task(self._process_queue(guild))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DiffTTS(bot))
