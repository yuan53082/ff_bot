import discord
from discord.ext import commands, tasks
import aiohttp
from bs4 import BeautifulSoup
import os

CHANNEL_ID = int(os.getenv("NEWS_CHANNEL_ID"))

class FFXIVNews(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.latest_url = None  # 紀錄已通知過的最新連結
        self.check_news.start()

    async def fetch_latest_news(self):
        url = "https://www.ffxiv.com.tw/web/index.aspx"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                html = await resp.text()
        soup = BeautifulSoup(html, "html.parser")

        # 找到「最新公告」區塊的第一則公告
        latest_announcement = soup.select_one("#latestNewsList li a")  # 根據網頁結構選擇器
        if latest_announcement:
            link = latest_announcement["href"]
            # 如果是相對連結，補上完整網址
            if link.startswith("/"):
                link = "https://www.ffxiv.com.tw" + link
            return link
        return None

    @tasks.loop(minutes=10)
    async def check_news(self):
        channel = self.bot.get_channel(CHANNEL_ID)
        if not channel:
            return

        latest = await self.fetch_latest_news()
        if latest and latest != self.latest_url:
            self.latest_url = latest
            await channel.send(f"📰 最新公告: {latest}")

    @check_news.before_loop
    async def before_check_news(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(FFXIVNews(bot))
