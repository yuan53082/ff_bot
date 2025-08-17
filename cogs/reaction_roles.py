import discord
import os
import logging
import traceback
from discord.ext import commands



# 從 .env 讀取設定並轉型成 int
SERVER_ID = int(os.getenv("SERVER_ID"))
CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
MESSAGE_ID = int(os.getenv("REACTION_ROLES_MESSAGE_ID"))
logger = logging.getLogger("discord")

# 表情 → 角色對應
REACTIONROLE_MAP = {
    ("FF_01", 1403316910518435850): 1405806092121931858,
    ("FF_02", 1403321377561378837): 1405806687926878220,
    ("FF_03", 1403321429310832670): 1405806808047681586,
}

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info(f"✅ {self.__class__.__name__} 模組已初始化")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        try:
            if payload.message_id != MESSAGE_ID or payload.channel_id != CHANNEL_ID:
                return

            emoji_key = (payload.emoji.name, payload.emoji.id)
            role_id = REACTIONROLE_MAP.get(emoji_key)

            if role_id:
                guild = self.bot.get_guild(SERVER_ID)
                if not guild:
                    return

                try:
                    member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
                except discord.NotFound:
                    return

                role = guild.get_role(role_id)

                if role and member and not member.bot:
                    await member.add_roles(role)
                    logger.info(f"➕ 已分配身分組 {role.name} 給 {member.display_name}")

        except Exception as e:
            logger.error(f"分配身分組時發生錯誤: {e}")
            traceback.print_exc()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        try:
            if payload.message_id != MESSAGE_ID or payload.channel_id != CHANNEL_ID:
                return

            emoji_key = (payload.emoji.name, payload.emoji.id)
            role_id = REACTIONROLE_MAP.get(emoji_key)

            if role_id:
                guild = self.bot.get_guild(SERVER_ID)
                if not guild:
                    return

                try:
                    member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
                except discord.NotFound:
                    return

                role = guild.get_role(role_id)

                if role and member:
                    await member.remove_roles(role)
                    logger.info(f"➖ 已移除身分組 {role.name} 從 {member.display_name}")

        except Exception as e:
            logger.error(f"移除身分組發生錯誤: {e}")
            traceback.print_exc()

# Cog 載入入口
async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
