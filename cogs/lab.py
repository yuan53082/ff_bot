import os
from dotenv import load_dotenv
from discord.ext import commands, tasks
from datetime import datetime, date
import pytz

load_dotenv()

CHANNEL_ID = int(os.getenv("LAB_CHANNEL_ID"))

class Countdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_date = date(2025, 12, 31)  # 目標日期，格式 YYYY, M, D
        self.channel_id = CHANNEL_ID # 指定頻道 ID
        self.timezone = pytz.timezone("Asia/Taipei")  # 設定時區
        self.send_countdown_message.start()

    def cog_unload(self):
        self.send_countdown_message.cancel()

    @tasks.loop(minutes=1)  # 每分鐘檢查一次
    async def send_countdown_message(self):
        now = datetime.now(self.timezone)
        # 如果是早上 10:00 並且分鐘是 0，就發送訊息
        if now.hour == 00 and now.minute == 20:
            today = date.today()
            days_left = (self.target_date - today).days
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                if days_left > 0:
                    await channel.send(f"📅 距離目標日期 {self.target_date} 還有 **{days_left} 天**！")
                elif days_left == 0:
                    await channel.send(f"🎉 今天就是目標日 {self.target_date}！")
                else:
                    await channel.send(f"⏳ 目標日 {self.target_date} 已經過了 {abs(days_left)} 天。")

    @send_countdown_message.before_loop
    async def before_send_countdown_message(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Countdown(bot))
