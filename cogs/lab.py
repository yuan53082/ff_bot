import discord
from discord.ext import commands, tasks
from datetime import datetime, date
import json
import os

CONFIG_FILE = "lab_countdown.json"
CHANNEL_ID = int(os.getenv("LAB_CHANNEL_ID"))

class Lab(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_date = self.load_date()
        self.daily_countdown_lab = self.daily_countdown_lab_task
        # task 不在 __init__ 啟動，等 Bot ready 後啟動

    # 載入日期
    def load_date(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return datetime.strptime(data["target_date"], "%Y-%m-%d").date()
        return None

    # 儲存日期
    def save_date(self, date_str):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"target_date": date_str}, f, ensure_ascii=False, indent=4)

    # Discord 指令（名稱唯一）
    @commands.command(name="lab_setdate")
    async def set_date_lab(self, ctx, date_str: str):
        """設定 Lab 倒數目標日期 (格式: YYYY-MM-DD)"""
        try:
            new_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            self.target_date = new_date
            self.save_date(date_str)
            await ctx.send(f"✅ Lab 目標日期已設定為 {new_date}")
        except ValueError:
            await ctx.send("❌ 日期格式錯誤，請使用 YYYY-MM-DD")

    # 每天早上 10:00 發送倒數
    @tasks.loop(minutes=1)
    async def daily_countdown_lab_task(self):
        if self.target_date is None:
            return
        now = datetime.now()
        if now.hour == 10 and now.minute == 0:
            days_left = (self.target_date - now.date()).days
            channel = self.bot.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(f"📅 Lab 倒數: 距離 {self.target_date} 還有 {days_left} 天")

    # Bot ready 後啟動 task
    @commands.Cog.listener()
    async def on_ready(self):
        if not self.daily_countdown_lab.is_running():
            self.daily_countdown_lab.start()

async def setup(bot):
    await bot.add_cog(Lab(bot))
