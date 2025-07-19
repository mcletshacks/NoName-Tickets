import os
import json
import logging
import discord
import importlib

from discord import app_commands
from discord.ext import commands

logging.basicConfig(level = logging.INFO, format = "%(asctime)s %(levelname)s %(name)s: %(message)s"); log = logging.getLogger(__name__)

with open("Config.json") as f:
    Config = json.load(f)

Panel_JSN = "panel.json"

if not os.path.exists(Panel_JSN):
    with open(Panel_JSN, "w") as f:
        json.dump({}, f)

# ─── BOT SETUP ─────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.messages = True
intents.guild_messages = True

bot = commands.Bot(command_prefix = "/", intents = intents)
bot.config = Config
tree = bot.tree

# ─── LOADER ──────────────────────────────────────────────────────────────────
async def load_commands():
    for fn in os.listdir("./commands"):
        if fn.endswith(".py"):
            name = fn[:-3]
            module = importlib.import_module(f"commands.{name}")
            if hasattr(module, "setup"):
                await module.setup(bot)
                log.info(f"Loaded commands.{name}")

# ─── EVENTS ───────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    try:
        synced = await tree.sync()
        log.info(f"Synced {len(synced)} commands")
    except Exception as e:
        log.error(f"Failed to sync commands: {e}")

    ping = round(bot.latency * 1000)
    status_chan = bot.get_channel(int(Config["channels"]["logs"]))

    if status_chan:
        await status_chan.send(embed = discord.Embed(title = "Bot Online!", description = f"Ping: {ping}ms", color = discord.Color.green()))

    log.info(f"ready as {bot.user}")

@bot.event
async def on_member_remove(member):
    guild = member.guild
    cfg = bot.config
    
    for cid in cfg["categories"].values():
        cat = guild.get_channel(int(cid))

        if not cat:
            continue

        for chan in getattr(cat, "channels", []):
            if member.name.lower() in chan.name:
                tickets_cog = bot.get_cog("Tickets")

                if tickets_cog:
                    fake_inter = type("Fake", (), {"channel": chan, "guild": guild, "user": bot.user, "response": type("Resp", (), {"send_message": lambda *a, **k: None})()})()
                    await tickets_cog._close_ticket(fake_inter, reason = "user left")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
async def main():
    await load_commands()
    await bot.start(Config["token"])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())