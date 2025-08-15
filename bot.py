import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord")

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.reactions = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
#
@bot.event
async def on_ready():
    logger.info(f"✅ Bot 已登入為 {bot.user} (ID: {bot.user.id})")
    logger.info(f"目前可用指令: {[c.name for c in bot.commands]}")

# 重載指令
@bot.command(name="reload")
@commands.is_owner()
async def reload_cog(ctx, cog_name: str):
    try:
        await bot.unload_extension(f"cogs.{cog_name}")
        await bot.load_extension(f"cogs.{cog_name}")
        await ctx.send(f"✅ 已重載模組 `{cog_name}`")
        logger.info(f"🔄 已重載模組 {cog_name}")
    except Exception as e:
        await ctx.send(f"❌ 重載 `{cog_name}` 失敗: {e}")
        logger.error(f"重載 {cog_name} 發生錯誤: {e}")

# 非同步載入所有 Cog
async def main():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            logger.info(f"📦 已載入功能模組: {filename}")
    await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())
