import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import aiohttp
import json
import os
import pytz
import logging

CONFIG_FILE = "earthquake_last.json"
USAGE_FILE = "earthquake_usage.json"
CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID"))
API_KEY = os.getenv("CWA_API_KEY")  # 你在環境變數設定的授權碼
CHECK_INTERVAL = 5
TARGET_CITIES = ["新北市", "新竹市", "臺中市"]
tz = pytz.timezone("Asia/Taipei")
logger = logging.getLogger("discord")


class Earthquake(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_eq_no = None
        self.usage = {"date": "", "count": 0, "flow": 0}  # 紀錄每日使用量
        self.load_last_eq()
        self.load_usage()
        logger.info(f"✅ {self.__class__.__name__} 模組已初始化")

    def cog_unload(self):
        if self.earthquake_loop.is_running():
            self.earthquake_loop.cancel()
            logger.info("🛑 Earthquake loop 已取消")

    def load_last_eq(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.last_eq_no = data.get("last_eq_no")
        else:
            self.last_eq_no = None

    def save_last_eq(self, eq_no):
        self.last_eq_no = eq_no
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_eq_no": eq_no}, f, ensure_ascii=False, indent=2)

    def load_usage(self):
        if os.path.exists(USAGE_FILE):
            with open(USAGE_FILE, "r", encoding="utf-8") as f:
                self.usage = json.load(f)
        else:
            self.usage = {"date": "", "count": 0, "flow": 0}

    def save_usage(self):
        with open(USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.usage, f, ensure_ascii=False, indent=2)

    async def fetch_earthquake(self):
        # 使用最新顯著有感地震報告 API
        url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0015-001?Authorization={API_KEY}&sort=-OriginTime&limit=1"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        logger.error(f"❌ 地震資料抓取失敗，HTTP {resp.status}")
                        return None
                    data = await resp.json()
                    return data
        except Exception as e:
            logger.error(f"❌ 抓取地震資料發生錯誤: {e}")
            return None

    @tasks.loop(seconds=CHECK_INTERVAL, reconnect=True)
    async def earthquake_loop(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(CHANNEL_ID)
        if not channel:
            logger.warning("⚠️ 找不到頻道 ID")
            return

        # 每天重置使用量
        today = datetime.now(tz).strftime("%Y-%m-%d")
        if self.usage.get("date") != today:
            self.usage = {"date": today, "count": 0, "flow": 0}
            self.save_usage()

        data = await self.fetch_earthquake()
        if not data:
            logger.info("⏰ 未抓到地震資料")
            return

        eq_list = data.get("records", {}).get("Earthquake", [])
        if not eq_list:
            logger.info("⏰ Earthquake list 為空")
            return

        latest_eq = eq_list[0]
        eq_no = latest_eq.get("EarthquakeNo")
        epicenter_info = latest_eq.get("EarthquakeInfo", {}).get("Epicenter", {})
        location_text = epicenter_info.get("Location", "")

        logger.info(f"⏰ 檢查中：最新地震編號={eq_no}, 震央={location_text}, last_sent={self.last_eq_no}")

        # 判斷是否已發送過
        if eq_no == self.last_eq_no:
            logger.info("⚠️ 已發送過此地震訊息，跳過")
            return

        # 取得各城市震度資訊
        intensity_info = latest_eq.get("Intensity", {}).get("ShakingArea", [])
        city_intensity = {}
        
        for area in intensity_info:
            county_names = area.get("CountyName", "")
            area_value = area.get("AreaIntensity")
            for c in county_names.split("、"):
                c = c.strip()
                for target in TARGET_CITIES:
                    if target.replace("台","臺") == c.replace("台","臺"):
                        city_intensity[target] = area_value
        
        # 取得報告顏色
        report_color_name = latest_eq.get("ReportColor", "綠色")
        color_map = {
            "綠色": 0x00FF00,
            "黃色": 0xFFFF00,
            "紅色": 0xFF0000
        }
        embed_color = color_map.get(report_color_name, 0xFF4500)
        
        # 取得地震圖
        report_image = latest_eq.get("ReportImageURI", "")
        
        # 建立 embed 訊息
        embed = discord.Embed(
            title=f"🌏 地震速報 ({report_color_name})",
            description=(
                f"震央：{location_text}\n"
                f"規模：{latest_eq.get('EarthquakeInfo', {}).get('EarthquakeMagnitude', {}).get('MagnitudeValue')} "
                f"{latest_eq.get('EarthquakeInfo', {}).get('EarthquakeMagnitude', {}).get('MagnitudeType')}"
            ),
            url=latest_eq.get("Web", ""),
            color=embed_color
        )
        
        for city in TARGET_CITIES:
            intensity = city_intensity.get(city, "無感")
            embed.add_field(name=f"{city}震度", value=intensity, inline=True)
        
        if report_image:
            embed.set_image(url=report_image)
        
        embed.set_footer(text=f"來源: 中央氣象署 | 編號 {eq_no}")
        await channel.send(embed=embed)
        self.save_last_eq(eq_no)

        # 更新使用量
        self.usage["count"] += 1
        self.usage["flow"] += 1
        self.save_usage()

        logger.info("✅ 地震訊息已發送")

    @earthquake_loop.before_loop
    async def before_earthquake_loop(self):
        logger.info("🔄 Earthquake loop 準備啟動，等待 bot ready...")
        await self.bot.wait_until_ready()
        logger.info("🔄 Earthquake loop 已啟動")

    @earthquake_loop.error
    async def earthquake_loop_error(self, error):
        logger.error(f"❌ Earthquake loop 發生錯誤: {error}")

    @commands.command(name="eq")
    async def debug_earthquake(self, ctx):
        """手動測試抓最新地震"""
        data = await self.fetch_earthquake()
        if not data:
            await ctx.send("❌ 未抓到地震資料")
            return

        eq_list = data.get("records", {}).get("Earthquake", [])
        if not eq_list:
            await ctx.send("❌ Earthquake list 為空")
            return

        latest_eq = eq_list[0]
        eq_no = latest_eq.get("EarthquakeNo")
        epicenter_info = latest_eq.get("EarthquakeInfo", {}).get("Epicenter", {})
        location_text = epicenter_info.get("Location", "")

        # 取得報告顏色
        report_color_name = latest_eq.get("ReportColor", "綠色")

        # 根據報告顏色設定 embed 顏色
        color_map = {
            "綠色": 0x00FF00,
            "黃色": 0xFFFF00,
            "紅色": 0xFF0000
        }
        embed_color = color_map.get(report_color_name, 0xFF4500)  # 預設橘色

        # 取得各城市震度資訊
        intensity_info = latest_eq.get("Intensity", {}).get("ShakingArea", [])
        city_intensity = {}

        for area in intensity_info:
            county_names = area.get("CountyName", "")
            area_value = area.get("AreaIntensity")
            for c in county_names.split("、"):
                c = c.strip()
                for target in TARGET_CITIES:
                    if target.replace("台","臺") == c.replace("台","臺"):
                        city_intensity[target] = area_value

        # 取得地震圖
        report_image = latest_eq.get("ReportImageURI", "")

        # 建立 embed 訊息
        embed = discord.Embed(
            title=f"🌏 地震速報 ({report_color_name})",
            description=(
                f"震央：{location_text}\n"
                f"規模：{latest_eq.get('EarthquakeInfo', {}).get('EarthquakeMagnitude', {}).get('MagnitudeValue')} "
                f"{latest_eq.get('EarthquakeInfo', {}).get('EarthquakeMagnitude', {}).get('MagnitudeType')}"
            ),
            url=latest_eq.get("Web", ""),
            color=embed_color
        )

        for city in TARGET_CITIES:
            intensity = city_intensity.get(city, "無感")
            embed.add_field(name=f"{city}震度", value=intensity, inline=True)

        if report_image:
            embed.set_image(url=report_image)

        embed.set_footer(text=f"來源: 中央氣象署 | 編號 {eq_no}")
        await ctx.send(embed=embed)


async def setup(bot):
    cog = Earthquake(bot)
    await bot.add_cog(cog)
    if not cog.earthquake_loop.is_running():
        cog.earthquake_loop.start()
