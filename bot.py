import discord
import os
import logging
from discord.ext import commands
from dotenv import load_dotenv

# 載入 .env
load_dotenv()

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord")

# 啟用需要的 Intents
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.reactions = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"✅ Bot 已登入為 {bot.user} (ID: {bot.user.id})")

# 載入 cogs 資料夾下所有 .py
for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")
        logger.info(f"📦 已載入功能模組: {filename}")

# -------- 加入 !reload 指令 --------
@bot.command(name="reload")
@commands.is_owner()  # 只有 Bot 擁有者可用
async def reload_cog(ctx, cog_name: str):
    """重載指定 Cog，例如: !reload reaction_roles"""
    try:
        bot.unload_extension(f"cogs.{cog_name}")
        bot.load_extension(f"cogs.{cog_name}")
        await ctx.send(f"✅ 已重載模組 `{cog_name}`")
        logger.info(f"🔄 已重載模組 {cog_name}")
    except Exception as e:
        await ctx.send(f"❌ 重載 `{cog_name}` 失敗: {e}")
        logger.error(f"重載 {cog_name} 發生錯誤: {e}")

# 啟動 Bot
bot.run(os.getenv("DISCORD_TOKEN"))