import logging
import os
import aiohttp
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
import discord
import json

CHANNEL_ID = int(os.getenv("NEWS_CHANNEL_ID"))
logger = logging.getLogger("init")
DATA_FILE = "latest_news.json"  # 存最後公告的檔案

class News(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.latest_url = self.load_latest_url()  # 從 JSON 讀取
        logger.info(f"✅ {self.__class__.__name__} 模組已初始化")
        
        # 啟動 loop
        if not self.check_news.is_running():
            self.check_news.start()
            logger.info("🔄 News loop 已啟動")

    def cog_unload(self):
        # reload 或卸載時停止 loop
        if self.check_news.is_running():
            self.check_news.cancel()
            logger.info("🛑 News loop 已取消")

    def load_latest_url(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("latest_url")
            except Exception as e:
                logger.error(f"❌ 讀取最新公告檔案失敗: {e}")
        return None

    def save_latest_url(self, url):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump({"latest_url": url}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 儲存最新公告檔案失敗: {e}")

    async def fetch_latest_news(self):
        url = "https://www.ffxiv.com.tw/web/index.aspx"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")

            latest_item = soup.select_one(".nav_news .sub_nav ul li a p")
            if latest_item:
                link_tag = latest_item.parent
                link = link_tag.get("href", "")
                title = latest_item.get_text(strip=True)
                if link.startswith("/"):
                    link = "https://www.ffxiv.com.tw" + link
                return title, link
        except Exception as e:
            logger.error(f"❌ 抓取最新公告時發生錯誤: {e}")
        return None, None

    @tasks.loop(minutes=10)
    async def check_news(self):
        channel = self.bot.get_channel(CHANNEL_ID)
        if not channel:
            return

        title, latest = await self.fetch_latest_news()
        if latest and latest != self.latest_url:
            self.latest_url = latest
            self.save_latest_url(latest)  # 更新 JSON

            embed = discord.Embed(
                title="📰 最新公告",
                description=title,
                url=latest,
                color=0xFFD700
            )
            embed.set_footer(text="資料來源: FFXIV 繁體中文版官方網站")
            await channel.send(embed=embed)

    @commands.command(name="news")
    async def debug_news(self, ctx):
        """手動抓取最新公告"""
        title, latest = await self.fetch_latest_news()
        if latest:
            # 更新 JSON 避免手動抓也重複發送
            if latest != self.latest_url:
                self.latest_url = latest
                self.save_latest_url(latest)

            embed = discord.Embed(
                title="📰 最新公告",
                description=title,
                url=latest,
                color=0xFFD700
            )
            embed.set_footer(text="資料來源: FFXIV 繁體中文版官方網站")
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ 沒找到最新公告")

async def setup(bot):
    await bot.add_cog(News(bot))
