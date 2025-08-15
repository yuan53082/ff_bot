import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
import logging

load_dotenv()

# ---------- 日誌設定 ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord")

# ---------- Intents ----------
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.reactions = True
intents.message_content = True

# ---------- Bot ----------
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- on_ready ----------
@bot.event
async def on_ready():
    logger.info(f"✅ Bot 已登入為 {bot.user} (ID: {bot.user.id})")
    # 列出所有可用指令名稱
    command_names = [c for c in bot.all_commands]
    logger.info(f"目前可用指令: {command_names}")

# ---------- 重載 Cog 指令 ----------
@bot.command(name="reload")
@commands.is_owner()
async def reload_cog(ctx, cog_name: str):
    try:
        # 卸載再載入
        if f"cogs.{cog_name}" in bot.extensions:
            await bot.unload_extension(f"cogs.{cog_name}")
        await bot.load_extension(f"cogs.{cog_name}")
        await ctx.send(f"✅ 已重載模組 `{cog_name}`")
        logger.info(f"🔄 已重載模組 {cog_name}")
    except Exception as e:
        await ctx.send(f"❌ 重載 `{cog_name}` 失敗: {e}")
        logger.error(f"重載 {cog_name} 發生錯誤: {e}")

# ---------- 非同步載入所有 Cog ----------
async def load_cogs():
    cogs_folder = "./cogs"
    for filename in os.listdir(cogs_folder):
        if filename.endswith(".py"):
            cog_name = filename[:-3]
            try:
                await bot.load_extension(f"cogs.{cog_name}")
                logger.info(f"📦 已載入功能模組: {filename}")
            except commands.errors.CommandRegistrationError as e:
                logger.warning(f"⚠️ Cog {cog_name} 指令重複，跳過: {e}")
            except Exception as e:
                logger.error(f"❌ 載入 {filename} 失敗: {e}")

# ---------- 非同步主程式 ----------
async def main():
    await load_cogs()
    # 延遲確保 task 安全啟動
    await asyncio.sleep(1)
    await bot.start(os.getenv("DISCORD_TOKEN"))

# ---------- 啟動 ----------
asyncio.run(main())
