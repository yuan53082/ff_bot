from datetime import datetime
import logging
import os
import aiohttp
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
import discord
import json
import pytz

CHANNEL_ID = int(os.getenv("CHAT_CHANNEL_ID"))
logger = logging.getLogger("init")
DATA_FILE = "latest_news.json"  # 存最後公告的檔案

class News(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.latest_url = self.load_latest_url()  # 從 JSON 讀取
        logger.info(f"✅ {self.__class__.__name__} 模組已初始化")

        # 啟動 loop
        if not self.news_loop.is_running():
            self.news_loop.start()

    def cog_unload(self):
        # reload 或卸載時停止 loop
        if self.news_loop.is_running():
            self.news_loop.cancel()
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

    # ---------- Loop ----------
    @tasks.loop(minutes=10, reconnect=True)
    async def news_loop(self):
        channel = self.bot.get_channel(CHANNEL_ID)
        if not channel:
            return
    
        now = datetime.now(pytz.timezone("Asia/Taipei"))
        logger.info(f"⏰ News 檢查中：{now}, 最新公告 URL={self.latest_url}")
    
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
            logger.info(f"✅ 發送最新公告訊息：{latest}")

    @news_loop.before_loop
    async def before_news_loop(self):
        logger.info("🔄 News loop 準備啟動，等待 bot ready...")
        await self.bot.wait_until_ready()
        logger.info("🔄 News 倒數 loop 已啟動")

    @news_loop.error
    async def news_loop_error(self, error):
        logger.error(f"❌ News loop 發生錯誤: {error}")

    # ---------- 手動抓取指令 ----------
    @commands.command(name="news")
    async def debug_news(self, ctx):
        """手動抓取最新公告"""
        title, latest = await self.fetch_latest_news()
        if latest:
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

# ---------- Cog Setup ----------
async def setup(bot):
    await bot.add_cog(News(bot))
