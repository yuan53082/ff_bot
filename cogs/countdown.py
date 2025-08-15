from discord.ext import commands, tasks
from datetime import datetime, date
import json
import os
from dotenv import load_dotenv

load_dotenv()

CHANNEL_ID = int(os.getenv("COUNTDOWN_CHANNEL_ID"))
CONFIG_FILE = "countdown_config.json"

class Countdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_date = self.load_date()
        self.daily_countdown.start()

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
    async def set_date(self, ctx, date_str: str):
        """設定倒數目標日期 (格式: YYYY-MM-DD)"""
        try:
            new_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            self.target_date = new_date
            self.save_date(date_str)
            await ctx.send(f"✅ 目標日期已設定為 {new_date}")
        except ValueError:
            await ctx.send("❌ 日期格式錯誤，請使用 YYYY-MM-DD")

    @tasks.loop(minutes=1)
    async def daily_countdown(self):
        if self.target_date is None:
            return
        now = datetime.now()
        if now.hour == 10 and now.minute == 0:  # 每天早上 10:00
            channel = self.bot.get_channel(CHANNEL_ID)
            if channel:
                days_left = (self.target_date - now.date()).days
                await channel.send(f"📅 距離FFXIV EA還有 **{days_left} 天**")

    @daily_countdown.before_loop
    async def before_daily_countdown(self):
        await self.bot.wait_until_ready()
        # 第一次啟動提醒
        if self.target_date is None:
            channel = self.bot.get_channel(CHANNEL_ID)
            if channel:
                await channel.send("⚠️ 尚未設定目標日期，請使用 `!setdate YYYY-MM-DD` 設定")

async def setup(bot):
    await bot.add_cog(Countdown(bot))
