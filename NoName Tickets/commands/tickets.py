import io
import logging
import discord

from discord.ext import commands
from discord import app_commands
from discord.ui import View, button, Button

log = logging.getLogger(__name__)

# ─── TICKETS CORE ────────────────────────────────────────────────────────────────
class CloseTicketView(View):
    def __init__(self, ticket_user_id, cog):
        super().__init__(timeout = None)
        self.ticket_user_id = ticket_user_id
        self.cog = cog

    @button(label = "Close Ticket", style = discord.ButtonStyle.red, custom_id = "close_ticket")
    async def close(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ticket_user_id:
            await interaction.response.send_message("Only the person who opened the ticket can close it.", ephemeral = True)
            return
        
        await self.cog._close_ticket(interaction)

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_ticket_opener(self, chan):
        async for msg in chan.history(oldest_first = True, limit = 10):
            if msg.author == self.bot.user and msg.mentions:
                for user in msg.mentions:
                    if not user.bot:
                        return user
                    
        return None

    # ─── REQUEST CLOSE CMD ───────────────────────────────────────────────────────────
    @app_commands.command(name = "request-close", description = "Request user to close the Ticket")
    async def request_close(self, interaction: discord.Interaction):
        chan = interaction.channel
        ticket_user = await self.get_ticket_opener(chan)
        support_role = interaction.guild.get_role(int(self.bot.config["roles"]["support-role"]))
        
        if support_role not in interaction.user.roles:
            await interaction.response.send_message("You do not have permission to request the close of tickets", ephemeral = True)
            return
        
        if not ticket_user:
            await interaction.response.send_message("Could not get the ticket owner.", ephemeral = True)
            return

        embed = discord.Embed(title = "Ticket Marked as Solved", description = f"{ticket_user.mention}, your ticket has been marked as solved!\n\n" f"If your issue or request is resolved, you can click the button below to close this ticket. " f"If not you can continue chatting here.", color = discord.Color.green())

        view = CloseTicketView(ticket_user.id, self)
        current_name = chan.name
        prefix, rest = current_name.split("-", 1)

        await chan.send(content = f"{ticket_user.mention}", embed = embed, view = view)
        await interaction.response.send_message("ticket was marked as solved!", ephemeral = True)
        await chan.edit(name = f"solved-{rest}")
        log.info(f"close requested in {chan.id} by {interaction.user.id}")

    # ─── CLOSE CMD ─────────────────────────────────────────────────────────────────
    @app_commands.command(name = "close", description = "Close this ticket")
    async def close(self, interaction: discord.Interaction, reason: str = "Closed"):
        support_role = interaction.guild.get_role(int(self.bot.config["roles"]["support-role"]))
        
        if support_role not in interaction.user.roles:
            await interaction.response.send_message("You do not have permission to close tickets", ephemeral = True)
            return
        
        await self._close_ticket(interaction, reason = reason)

    # ─── ACTUAL TICKET CLOSING ──────────────────────────────────────────────────────
    async def _close_ticket(self, interaction: discord.Interaction, reason = "Closed"):
        transcripts_id = self.bot.config["channels"].get("transcripts")
        chan = interaction.channel
        buf = io.StringIO()

        logs_chan = interaction.guild.get_channel(int(self.bot.config["channels"]["logs"]))
        transcripts_chan = interaction.guild.get_channel(int(transcripts_id))

        prefixes = [k.lower() for k in self.bot.config["categories"].keys()]
        prefixes += ["solved-", "accepted-", "denied-"]

        if not any(chan.name.startswith(pref) for pref in prefixes):
            await interaction.response.send_message("This command only works in ticket channels", ephemeral = True)
            return

        async for m in chan.history(oldest_first = True, limit = None):
            buf.write(f"[{m.created_at.isoformat()}] {m.author.display_name}: {m.content}\n")
            for att in m.attachments:
                buf.write(f"[Attachment: {att.filename}] {att.url}\n")
                
        buf.seek(0)

        if transcripts_id and str(transcripts_id).isdigit():
            if transcripts_chan:
                await transcripts_chan.send(file = discord.File(buf, filename = f"{chan.name}-transcript.txt"))

        if logs_chan:
            closer = getattr(interaction, "user", None)

            if closer and hasattr(closer, "mention"):
                closer_val = closer.mention
            else:
                closer_val = "Automatic"
        
            embed = discord.Embed(title = "Ticket Closed", color = discord.Color.red())
            embed.add_field(name = "Ticket Name", value = getattr(chan, "name", "unknown"), inline = True)
            embed.add_field(name = "Closed by", value = closer_val, inline = True)
            embed.add_field(name = "Reason", value = reason, inline = True)

            await logs_chan.send(embed = embed)

        try:
            await interaction.response.send_message(f"Closing ticket... reason: {reason}", ephemeral = False)
        except Exception:
            pass

        try:
            await chan.delete()
        except Exception:
            pass

        log.info(f"ticket channel {chan.id} closed by {getattr(interaction, 'user', 'Automatic')} ({reason})")


# ─── ADD CMDS ───────────────────────────────────────────────────────────────────
async def setup(bot):
    await bot.add_cog(Tickets(bot))