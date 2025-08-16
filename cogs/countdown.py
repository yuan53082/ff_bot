import discord
from discord.ext import commands
from datetime import datetime, date, time
import json
import os
import asyncio

CONFIG_FILE = "countdown.json"
CHANNEL_ID = int(os.getenv("COUNTDOWN_CHANNEL_ID"))
TARGET_HOUR = 15
TARGET_MINUTE = 33

class Countdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_date = None
        self.last_sent_date = None
        self.task_started = False
        self.task = None
        self.load_data()

    # 載入目標日期與最後發送日期
    def load_data(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                target_date_str = data.get("target_date")
                last_sent_str = data.get("last_sent_date")
                if target_date_str:
                    self.target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
                if last_sent_str:
                    self.last_sent_date = datetime.strptime(last_sent_str, "%Y-%m-%d").date()

    # 儲存目標日期與最後發送日期
    def save_data(self):
        data = {
            "target_date": self.target_date.strftime("%Y-%m-%d") if self.target_date else None,
            "last_sent_date": self.last_sent_date.strftime("%Y-%m-%d") if self.last_sent_date else None
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @commands.command(name="setdate")
    async def set_date_countdown(self, ctx, date_str: str):
        try:
            new_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            self.target_date = new_date
            self.last_sent_date = None  # 重設最後發送日期
            # 存檔，包含 target_date 與 last_sent_date
            data = {
                "target_date": self.target_date.strftime("%Y-%m-%d"),
                "last_sent_date": None
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            days_left = (self.target_date - date.today()).days
            await ctx.send(f"✅ 目標日期已設定為 {new_date}（剩下 {days_left} 天）")
        except ValueError:
            await ctx.send("❌ 日期格式錯誤，請使用 YYYY-MM-DD")

    async def countdown_task(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(CHANNEL_ID)
        if self.target_date is None or channel is None:
            return

        while not self.bot.is_closed():
            try:
                now = datetime.now()
                target_time_today = datetime.combine(now.date(), time(TARGET_HOUR, TARGET_MINUTE))

                # 如果當天已過指定時間，且尚未發送訊息
                if now >= target_time_today and self.last_sent_date != now.date():
                    if now.date() < self.target_date:
                        days_left = (self.target_date - now.date()).days
                        await channel.send(f"📅 距離 FFXIV EA開服 還有 {days_left} 天")
                    elif now.date() == self.target_date:
                        await channel.send(f"🎉 耶！FFXIV EA開服啦！")
                        # 到期後停止任務
                        self.last_sent_date = now.date()
                        self.save_data()
                        break
                    self.last_sent_date = now.date()
                    self.save_data()

                await asyncio.sleep(1)  # 每秒檢查一次
            except Exception as e:
                print(f"⚠️ 倒數任務發生錯誤: {e}")
                await asyncio.sleep(5)

    @commands.Cog.listener()
    async def on_ready(self):
        if self.task_started:
            return
        self.task_started = True
        channel = self.bot.get_channel(CHANNEL_ID)
        if self.target_date is None and channel:
            await channel.send("⚠️ 尚未設定目標日期，請使用 `!setdate YYYY-MM-DD` 設定")
            return

        # 如果今天還沒發過訊息且目標日期沒過，啟動倒數任務
        today = date.today()
        if self.target_date and (self.last_sent_date != today) and (today <= self.target_date):
            self.task = self.bot.loop.create_task(self.countdown_task())

async def setup(bot):
    await bot.add_cog(Countdown(bot))
