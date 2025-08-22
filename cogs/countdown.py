import discord
from discord.ext import commands, tasks
from datetime import datetime, date, time
import json
import os
import pytz
import logging

CONFIG_FILE = "countdown.json"
CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID"))
TARGET_HOUR = 10
TARGET_MINUTE = 0
tz = pytz.timezone("Asia/Taipei")
logger = logging.getLogger("discord")


class Countdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_date = None
        self.last_sent_date = None
        self.prompted_for_date = False
        self.load_data()
        logger.info(f"✅ {self.__class__.__name__} 模組已初始化")

    def cog_unload(self):
        if self.countdown_loop.is_running():
            self.countdown_loop.cancel()
            logger.info(f"🛑 {self.__class__.__name__} 倒數 loop 已取消")

    # 載入設定
    def load_data(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    target_date_str = data.get("target_date")
                    last_sent_str = data.get("last_sent_date")
                    if target_date_str:
                        self.target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
                    if last_sent_str:
                        self.last_sent_date = datetime.strptime(last_sent_str, "%Y-%m-%d").date()
            except Exception as e:
                logger.error(f"❌ 讀取設定檔失敗: {e}")
        else:
            logger.warning(f"⚠️ 設定檔不存在，啟動後會提示設定目標日期")

    def save_data(self):
        data = {
            "target_date": self.target_date.strftime("%Y-%m-%d") if self.target_date else None,
            "last_sent_date": self.last_sent_date.strftime("%Y-%m-%d") if self.last_sent_date else None
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"❌ 儲存設定檔失敗: {e}")

    @commands.command(name="setdate")
    async def set_date_countdown(self, ctx, date_str: str):
        try:
            new_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            self.target_date = new_date
            self.last_sent_date = None
            self.prompted_for_date = False
            self.save_data()
            days_left = (self.target_date - date.today()).days
            await ctx.send(f"✅ 目標日期已設定為 {new_date}（剩下 {days_left} 天）")
        except ValueError:
            await ctx.send("❌ 日期格式錯誤，請使用 YYYY-MM-DD")

    @tasks.loop(minutes=1, reconnect=True)
    async def countdown_loop(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(CHANNEL_ID)
        if not channel:
            logger.warning(f"⚠️ 找不到頻道 ID={CHANNEL_ID}")
            return

        now = datetime.now(tz)
        logger.info(f"⏰ EA開服倒數檢查中：{now}, 目標日期={self.target_date}, 最後發送訊息時間={self.last_sent_date}")

        # 🔄 每次檢查時重新讀 JSON，避免外部手動修改後 bot 不知道
        self.load_data()

        if not self.target_date:
            if not self.prompted_for_date:
                await channel.send("⚠️ 目標日期尚未設定，請使用指令 `!setdate YYYY-MM-DD`")
                self.prompted_for_date = True
            return
        self.prompted_for_date = False

        # ✅ 僅在「10:00整」發送，避免過了時間就一直觸發
        if now.hour >= TARGET_HOUR and now.minute == TARGET_MINUTE:
            if self.last_sent_date != now.date():
                if now.date() < self.target_date:
                    days_left = (self.target_date - now.date()).days
                    await channel.send(f"📅 距離 FFXIV EA開服 還有 {days_left} 天")
                elif now.date() == self.target_date:
                    await channel.send("🎉 耶！FFXIV EA開服啦！")

                self.last_sent_date = now.date()
                self.save_data()
                logger.info(f"✅ 倒數訊息已發送，日期：{self.last_sent_date}")

    @countdown_loop.before_loop
    async def before_countdown_loop(self):
        logger.info(f"🔄 倒數 loop 準備啟動，等待 bot ready...")
        await self.bot.wait_until_ready()
        logger.info(f"🔄 倒數 loop 已啟動")

    @countdown_loop.error
    async def countdown_loop_error(self, error):
        logger.error(f"❌ 倒數 loop 發生錯誤: {error}")


async def setup(bot):
    cog = Countdown(bot)
    await bot.add_cog(cog)
    if not cog.countdown_loop.is_running():
        cog.countdown_loop.start()
