import os
import json
import logging
import discord

from discord.ext import commands
from discord import app_commands

log = logging.getLogger(__name__)

# ─── RESET CORE ─────────────────────────────────────────────────────────────────
class Reset(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name = "reset", description = "Deletes / Resets ticket panel")
    @app_commands.checks.has_permissions(manage_channels = True)
    async def reset(self, interaction: discord.Interaction):
        with open("panel.json") as f: panel = json.load(f)

        chan_id = panel.get("channel_id")
        message_id = panel.get("message_id")

        if not chan_id or not message_id:
            await interaction.response.send_message("no ticket panel to reset", ephemeral = True)
            return

        chan = self.bot.get_channel(int(chan_id))

        if chan:
            try:
                msg = await chan.fetch_message(int(message_id))
                await msg.delete()
            except discord.NotFound:
                pass

        with open("panel.json", "w") as f: json.dump({}, f)

        await interaction.response.send_message("ticket panel has been reset", ephemeral = False)
        log.info(f"ticket panel reset done. requested by {interaction.user.id}")

# ─── ADD CMD ───────────────────────────────────────────────────────────────────
async def setup(bot):
    await bot.add_cog(Reset(bot))