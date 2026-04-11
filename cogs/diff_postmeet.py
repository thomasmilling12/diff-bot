import discord
from discord.ext import commands
from datetime import datetime, timezone

HOST_POSTERS = 1091157191895023626
MEET_INFO    = 1266933655486332999
EVERYONE_CH  = 1047335231826436166
PS5_ROLE     = 1485668852921798849
COLOR        = 0xE91E63
LOGO         = "https://media.discordapp.net/attachments/1107375326625005719/1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm=2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a&=&format=webp&quality=lossless&width=1376&height=917"

USAGE = (
    "**Usage:** `!postmeet @host | date | time | class`\n"
    "**Example:** `!postmeet @Frostyy | April 18, 2026 | 9:00pm EST | Open Class`\n"
    "Attach your Canva poster to the message. Add a 5th field for notes."
)

class PostMeetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not message.guild or message.channel.id != HOST_POSTERS:
            return
        if message.content.startswith("!"):
            return
        images = [a for a in message.attachments if a.content_type and a.content_type.startswith("image/")]
        if not images:
            return
        caption = message.content.strip()
        parts = caption.split("|", 1) if caption else []
        date_part = parts[0].strip() if parts else "TBA"
        time_part = parts[1].strip() if len(parts) > 1 else ""
        embed = discord.Embed(title="DIFF Meet Announcement", color=COLOR, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Host", value=message.author.mention, inline=True)
        embed.add_field(name="Date & Time", value=caption or "See poster", inline=False)
        embed.set_footer(text="DIFF Meets")
        embed.set_thumbnail(url=LOGO)
        try:
            await message.create_thread(name=(caption[:80] or "Meet Poster"), auto_archive_duration=10080)
        except Exception:
            pass
        try:
            await message.reply(embed=embed, mention_author=False)
        except Exception:
            pass
        try:
            info_ch = self.bot.get_channel(MEET_INFO)
            if info_ch:
                files = []
                for a in images[:4]:
                    try:
                        files.append(await a.to_file())
                    except Exception:
                        pass
                await info_ch.send(content=f"New poster from {message.author.mention}:", files=files, embed=embed, allowed_mentions=discord.AllowedMentions.none())
        except Exception:
            pass

    @commands.command(name="postmeet")
    @commands.guild_only()
    async def postmeet(self, ctx, *, args=""):
        try:
            fields = [f.strip() for f in args.split("|")]
            if len(fields) < 4:
                return await ctx.reply(USAGE, mention_author=False)
            host = ctx.message.mentions[0] if ctx.message.mentions else None
            date, time_str, class_name = fields[1], fields[2], fields[3]
            notes = fields[4] if len(fields) >= 5 else None
            img_atts = [a for a in ctx.message.attachments if a.content_type and a.content_type.startswith("image/")]
            image_url = img_atts[0].url if img_atts else None

            embed = discord.Embed(title="DIFF Meet Announcement", color=COLOR, timestamp=datetime.now(timezone.utc))
            if host:
                embed.add_field(name="Host", value=host.mention, inline=True)
            embed.add_field(name="Class", value=class_name, inline=True)
            embed.add_field(name="Date & Time", value=f"{date}  •  {time_str}", inline=False)
            if notes:
                embed.add_field(name="Notes", value=notes, inline=False)
            if image_url:
                embed.set_image(url=image_url)
            embed.set_footer(text="DIFF Meets • Host Poster")
            embed.set_thumbnail(url=LOGO)

            poster_ch = self.bot.get_channel(HOST_POSTERS)
            if not poster_ch:
                return await ctx.reply("Host posters channel not found.", mention_author=False)

            files = []
            for a in img_atts[:4]:
                try:
                    files.append(await a.to_file())
                except Exception:
                    pass

            send_kw = dict(content=f"**{date}** | **{time_str}**", embed=embed)
            if files:
                send_kw["files"] = files
            poster_msg = await poster_ch.send(**send_kw)

            try:
                await poster_msg.create_thread(name=f"{date} — {class_name}"[:80], auto_archive_duration=10080)
            except Exception:
                pass

            info_ch = self.bot.get_channel(MEET_INFO)
            if info_ch:
                try:
                    await info_ch.send(embed=embed)
                except Exception:
                    pass

            everyone_ch = self.bot.get_channel(EVERYONE_CH)
            if everyone_ch:
                try:
                    await everyone_ch.send(content=f"<@&{PS5_ROLE}>", embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
                except Exception:
                    pass

            confirm = await ctx.reply(f"Done! Posted in <#{HOST_POSTERS}>.", mention_author=False)
            try:
                await ctx.message.delete()
            except Exception:
                pass
            try:
                await confirm.delete(delay=15)
            except Exception:
                pass
        except Exception as e:
            try:
                await ctx.reply(f"Error: {e}", mention_author=False)
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(PostMeetCog(bot))
