import os
import json
import asyncio
import logging
import discord

from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select
from discord import PermissionOverwrite

log = logging.getLogger(__name__)

Panel_JSN = "panel.json"

if not os.path.exists(Panel_JSN):
    open(Panel_JSN, "w").write("{}")

# ─── SETUP CORE ─────────────────────────────────────────────────────────────────
class MediaBtns(discord.ui.View):
    def __init__(self, user_id, cog, chan):
        super().__init__(timeout = None)
        self.user_id = user_id
        self.cog = cog
        self.chan = chan

    @discord.ui.button(label = "Accept", style = discord.ButtonStyle.green, custom_id = "accept_media")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        accepted_role = interaction.guild.get_role(int(self.cog.bot.config["roles"]["media-accepted"]))
        support_role = interaction.guild.get_role(int(self.cog.bot.config["roles"]["support-role"]))
        user = discord.utils.get(self.chan.members, id = self.user_id)

        if not user:
            user = self.chan.guild.get_member(self.user_id)
        
        if not user:
            await interaction.response.send_message("User not found in this channel", ephemeral = True)
            return

        if support_role in interaction.user.roles:
            curr_name = self.chan.name
            char, rest = curr_name.split("-", 1) if "-" in curr_name else (curr_name, "")

            await self.chan.edit(name = f"accepted-{rest}")
            await self.chan.send(content = user.mention, embed = discord.Embed(title = "Media Application Accepted", description = f"{interaction.user.mention} has accepted the media application!"))
            await interaction.response.send_message("application marked as accepted, you may now proceed by providing more information", ephemeral = True)

            if accepted_role:
                try:
                    await user.add_roles(accepted_role, reason = "Media Application accepted")
                    print("debug: added accept role")
                except Exception as e:
                    await self.chan.send(f"cant add role: {e}")
            else:
                await self.chan.send("accept role not found")

            self.locked = True

            for item in self.children:
                item.disabled = True

            await interaction.message.edit(view = self)
        else:
            await interaction.response.send_message("no permissions!", ephemeral = True)

    @discord.ui.button(label = "Deny", style = discord.ButtonStyle.red, custom_id = "deny_media")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        denied_role = interaction.guild.get_role(int(self.cog.bot.config["roles"]["media-rejected"]))
        support_role = interaction.guild.get_role(int(self.cog.bot.config["roles"]["support-role"]))
        user = discord.utils.get(self.chan.members, id = self.user_id)
        
        if not user:
            user = self.chan.guild.get_member(self.user_id)
        
        if not user:
            await interaction.response.send_message("User not found in this channel", ephemeral = True)
            return

        if support_role in interaction.user.roles:
            curr_name = self.chan.name
            char, rest = curr_name.split("-", 1) if "-" in curr_name else (curr_name, "")
        
            await self.chan.edit(name = f"denied-{rest}")
            await self.chan.send(content = user.mention, embed = discord.Embed(title = "Media Application Denied", description = f"{interaction.user.mention} has denied this media application.\nticket will stay open for 12h for questions then close automaticlly", color = discord.Color.red()))
            await interaction.response.send_message("application marked as denied, ticket will close automaticlly in 12h!", ephemeral = True)
            await self.cog._auto_close_ticket(self.chan, 43200, "Denied (12h expired)")

            if denied_role:
                try:
                    await user.add_roles(denied_role, reason = "Media Application denied")
                    print("debug: added deny role")
                except Exception as e:
                    await self.chan.send(f"cant add role: {e}")
            else:
                await self.chan.send("denied role not found")

            self.locked = True
            
            for item in self.children:
                item.disabled = True

            await interaction.message.edit(view = self)
        else:
            await interaction.response.send_message("no permission", ephemeral = True)

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(self.TicketButtons(self))

    async def _auto_close_ticket(self, chan, delay, reason):
        await asyncio.sleep(delay)

        if chan and chan.guild:
            tickets_cog = chan.guild.get_cog("Tickets")

            if tickets_cog:
                fake_inter = type("Fake", (), {"channel": chan, "guild": chan.guild, "user": chan.guild.me, "response": type("Resp", (), {"send_message": lambda *a, **k: None})()})()
                await tickets_cog._close_ticket(fake_inter, reason = reason)

    @app_commands.command(name = "setup", description = "Post Tickets Panel in this channel")
    async def setup_command(self, interaction: discord.Interaction):
        chan = interaction.channel

        with open(Panel_JSN) as f:
            panel = json.load(f)

        if panel.get("message_id"):
            exists = self.bot.get_channel(panel["channel_id"])
            await interaction.response.send_message(f"ticket panel already exists in {exists.mention} you can use /reset to reset", ephemeral = True)
            return

        embed = discord.Embed(title = "Open a Ticket", description = "Select ticket type below", color = discord.Color.blurple())
        view = self.TicketButtons(self)
        msg = await chan.send(embed = embed, view = view)

        with open(Panel_JSN, "w") as f:
            json.dump({"channel_id": chan.id, "message_id": msg.id}, f)

        await interaction.response.send_message(
            f"ticket panel sent in {chan.mention} successfully", ephemeral = False)
        
        await asyncio.sleep(2)
        await (await interaction.original_response()).delete()

        log.info(f"ticket panel sent to {chan.id} requested by {interaction.user.id}")

    # ─── DROPDOWN ────────────────────────────────────────────────────────────

    class TicketButtons(View):
        def __init__(self, cog):
            super().__init__(timeout = None)
            self.cog = cog

        @discord.ui.button(label = "Support", style = discord.ButtonStyle.blurple, custom_id = "ticket_support")
        async def support(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.cog._create_standard_ticket(interaction, "Support")

        @discord.ui.button(label = "Purchase", style = discord.ButtonStyle.green, custom_id = "ticket_purchase")
        async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.cog._create_standard_ticket(interaction, "Purchase")

        @discord.ui.button(label = "Media", style = discord.ButtonStyle.gray, custom_id = "ticket_media")
        async def media(self, interaction: discord.Interaction, button: discord.ui.Button):
            user = interaction.user
            guild = interaction.guild
            denied_role = guild.get_role(int(self.cog.bot.config["roles"]["media-rejected"]))
            accepted_role = guild.get_role(int(self.cog.bot.config["roles"]["media-accepted"]))

            if denied_role and denied_role in user.roles:
                await interaction.response.send_message("You have been denied for media. You cannot submit another application", ephemeral = True)
                return
            elif accepted_role and accepted_role in user.roles:
                await interaction.response.send_message("You have already been accepted for media. You cannot submit another application", ephemeral = True)
                return

            try:
                await user.send("Welcome to the Media Application! Please answer those questions to continue:")
            except discord.Forbidden:
                await interaction.response.send_message("I couldnt DM you. Please enable DMs from server members and try again!\nGo to: Server > Right click > Privacy Settings > Allow DMs from server members", ephemeral = True)
                return

            await interaction.response.send_message("Check your DMs! Please complete your application there", ephemeral = True)
            await self.cog._handle_media_application_dm(user, guild)

        @discord.ui.button(label = "Other", style = discord.ButtonStyle.red, custom_id = "ticket_other")
        async def other(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.cog._create_standard_ticket(interaction, "Other")


    # class TicketDropdown(View):
        # def __init__(self, cog):
        #     super().__init__(timeout = None)
        #     self.cog = cog

        # @discord.ui.select(
        #     custom_id = "ticket_select",
        #     placeholder = "Select ticket type",
        #     min_values = 1,
        #     max_values = 1,
        #     options = [
        #         discord.SelectOption(label = "Support", value = "Support"),
        #         discord.SelectOption(label = "Purchase", value = "Purchase"),
        #         discord.SelectOption(label = "Media", value = "Media"),
        #         discord.SelectOption(label = "Other", value = "Other")
        #     ]
        # )

        # async def select_callback(self, interaction: discord.Interaction, select: Select):
        #     kind = select.values[0]
        #     user = interaction.user
        #     guild = interaction.guild

        #     cfg = self.cog.bot.config
        #     prefixes = [k.lower().replace(' ', '-') for k in cfg["categories"].keys()]

        #     for cid in cfg["categories"].values():
        #         cat = guild.get_channel(int(cid))

        #         if not cat:
        #             continue

        #         for chan in getattr(cat, "channels", []):
        #             if any(chan.name.startswith(pref) for pref in prefixes) and user.name.lower() in chan.name:
        #                 await interaction.response.send_message("You already have an open ticket", ephemeral = True)
        #                 return

        #     if kind == "Media":
        #         denied_role = guild.get_role(int(self.cog.bot.config["roles"]["media-rejected"]))
        #         accepted_role = guild.get_role(int(self.cog.bot.config["roles"]["media-accepted"]))

        #         if denied_role and denied_role in user.roles:
        #             await interaction.response.send_message("You have been denied for media. You cannot submit another application", ephemeral = True)
        #             return
        #         elif accepted_role and accepted_role in user.roles:
        #             await interaction.response.send_message("You have already been accepted for media. You cannot submit another application", ephemeral = True)
        #             return

        #         try:
        #             await user.send("Welcome to the Media Application! Please answer those questions to continue:")
        #         except discord.Forbidden:
        #             await interaction.response.send_message("I couldnt DM you. Please enable DMs from server members and try again!\nGo to: Server > Right click > Privacy Settings > Allow DMs from server members", ephemeral = True)
        #             return

        #         await interaction.response.send_message("Check your DMs! Please complete your application there", ephemeral = True)
        #         await self.cog._handle_media_application_dm(user, guild)
        #         return

        #     await self.cog._create_standard_ticket(interaction, kind)

    # ─── MEDIA APP TICKET ─────────────────────────────────────────────────
    async def _handle_media_application_dm(self, user, guild):
        questions = [
            "How old are you?",
            "How many videos per week can you post (1–8+)?",
            "How many years experience in editing/making videos do you have (1–10+)?",
            "Whats your YouTube channel URL?",
            "Whats your TikTok channel URL (optional)?",
            "Do you understand you can get denied for the smallest things (yes/no)?",
            "Do you understand you cant ask about your application (yes/no)?"
        ]

        answers = []
        dm = await user.create_dm()
        bot = self.bot

        for q in questions:
            embed = discord.Embed(description = q, color = discord.Color.blurple())
            
            await dm.send(embed = embed)

            def check(m):
                return m.author.id == user.id and isinstance(m.channel, discord.DMChannel)
            
            try:
                msg = await bot.wait_for("message", check = check, timeout = 300.0)
                answers.append(msg.content.strip())
            except asyncio.TimeoutError:
                await dm.send("You took too long to complete the application")
                return

        cfg = bot.config
        role = guild.get_role(int(cfg["roles"]["support-role"]))
        category = guild.get_channel(int(cfg["categories"]["Media"]))

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel = False),
            user: discord.PermissionOverwrite(view_channel = True, send_messages = True, attach_files = True),
            role: discord.PermissionOverwrite(view_channel = True, send_messages = True, attach_files = True),
            guild.me: discord.PermissionOverwrite(view_channel = True)
        }

        chan = await guild.create_text_channel(name = f"media-{user.name}", category = category, overwrites = overwrites)
        app_embed = discord.Embed(title = "Media Application", color = discord.Color.blurple())
        logs_chan = guild.get_channel(int(cfg["channels"]["logs"]))

        for idx, q in enumerate(questions):
            app_embed.add_field(name = q, value = answers[idx], inline = False)

        await chan.send(content = f"{user.mention} {role.mention}", embed = app_embed, view = MediaBtns(user.id, self, chan))
        await dm.send(f"Your media ticket has been created: {chan.mention}\nPlease wait for staff review")
        
        if logs_chan:
            log_embed = discord.Embed(title = "Media Ticket Opened", description = "A media ticket has been created", color = discord.Color.green())
            log_embed.add_field(name = "User", value = user.mention, inline = True)
            log_embed.add_field(name = "Channel", value = chan.mention, inline = True)
            
            await logs_chan.send(embed = log_embed)

    # ─── NRML TICKET ──────────────────────────────────────────────────────
    async def _create_standard_ticket(self, interaction: discord.Interaction, kind: str):
        user = interaction.user
        guild = interaction.guild
        cfg = self.bot.config

        role = guild.get_role(int(cfg["roles"]["support-role"]))
        category = guild.get_channel(int(cfg["categories"].get(kind, 0)))

        overwrites = {
            guild.default_role: PermissionOverwrite(view_channel = False),
            user: PermissionOverwrite(view_channel = True, send_messages = True, attach_files = True),
            role: PermissionOverwrite(view_channel = True, send_messages = True, attach_files = True),
            guild.me: PermissionOverwrite(view_channel = True)
        }

        chan = await guild.create_text_channel(name = f"{kind.lower()}-{user.name}", category = category, overwrites = overwrites)
        logs_chan = guild.get_channel(int(cfg["channels"]["logs"]))

        if kind == "Purchase":
            embed = discord.Embed(title = "Purchase Ticket", description = "Please describe what you want to buy", color = discord.Color.blurple())
        elif kind == "Support":
            embed = discord.Embed(title = f"{kind} Ticket", description = "Please describe your issue", color = discord.Color.blurple())
        else:
            embed = discord.Embed(title = f"{kind} Ticket", description = "Please describe what you want", color = discord.Color.blurple())

        await chan.send(content = f"{user.mention} {role.mention}", embed = embed)

        if logs_chan:
            log_embed = discord.Embed(title = "Ticket Opened", description = f"{kind} ticket opened", color = discord.Color.green())
            log_embed.add_field(name = "User", value = user.mention, inline = True)
            log_embed.add_field(name = "Channel", value = chan.mention, inline = True)
            log_embed.add_field(name = "Type", value = kind, inline = True)

            await logs_chan.send(embed = log_embed)

        await interaction.response.send_message(f"your ticket has been created {chan.mention}", ephemeral = True)
        log.info(f"{kind} ticket {chan.id} opened by {user.id}")

# ─── ADD CMD ───────────────────────────────────────────────────────────────────
async def setup(bot):
    await bot.add_cog(Ticket(bot))