import discord
from discord.ext import commands
import logging
import os

CHANNEL_ID = int(os.getenv("LAB_CHANNEL_ID"))
# 從 .env 讀取設定並轉型成 int
GUILD_ID = int(os.getenv("LAB_GUILD_ID"))
CHANNEL_ID = int(os.getenv("LAB_CHANNEL_ID"))
MESSAGE_ID = int(os.getenv("LAB_MESSAGE_ID"))

# 建立 logger
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)

class TemplateCog(commands.Cog):
    """通用模組模板"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # 初始化變數
        self.some_data = None
        self.initialized = False

        # 初始化完成訊息
        logger.info(f"✅ {self.__class__.__name__} 模組已初始化")

    @commands.Cog.listener()
    async def on_ready(self):
        """Bot 上線後執行"""
        if not self.initialized:
            self.initialized = True
            logger.info(f"🔹 {self.__class__.__name__} on_ready 已執行")

    @commands.command(name="ping")
    async def ping_command(self, ctx):
        """示範指令"""
        await ctx.send("🏓 Pong!")
        logger.info(f"指令 ping 被 {ctx.author} 呼叫")

# Cog 載入函式
async def setup(bot: commands.Bot):
    await bot.add_cog(TemplateCog(bot))
    logger.info(f"📦 {TemplateCog.__name__} 已加入 Bot")
