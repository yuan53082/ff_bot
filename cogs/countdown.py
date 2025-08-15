import discord
from discord.ext import commands, tasks
from datetime import datetime, date
import json
import os

CONFIG_FILE = "countdown.json"
CHANNEL_ID = int(os.getenv("COUNTDOWN_CHANNEL_ID"))  # 可換成不同頻道

class Countdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_date = self.load_date()
        self.daily_countdown_task = self.daily_countdown_loop

    def load_date(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return datetime.strptime(data["target_date"], "%Y-%m-%d").date()
        return None

    def save_date(self, date_str):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"target_date": date_str}, f, ensure_ascii=False, indent=4)

    @commands.command(name="setdate")
    async def set_date_countdown(self, ctx, date_str: str):
        """設定倒數目標日期"""
        try:
            new_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            self.target_date = new_date
            self.save_date(date_str)
            await ctx.send(f"✅目標日期已設定為 {new_date}")
        except ValueError:
            await ctx.send("❌ 日期格式錯誤，請使用 YYYY-MM-DD")

    @tasks.loop(minutes=1)
    async def daily_countdown_loop(self):
        if self.target_date is None:
            return
        now = datetime.now()
        if now.hour == 10 and now.minute == 0:
            days_left = (self.target_date - now.date()).days
            channel = self.bot.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(f"📅 距離 FFXIV EA開服 還有 {days_left} 天")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.daily_countdown_task.is_running():
            self.daily_countdown_task.start()

async def setup(bot):
    await bot.add_cog(Countdown(bot))
