NoName Tickets V1 - Quick Start

Project Info:
Advanced Discord Ticket Bot made for one of our customers

Credits:
https://discordlookup.com/user/1364146935975378985

========================
Commands
========================

/setup         - Run this in the channel where you want the ticket panel.
/reset         - Deletes the old ticket panel so you can use /setup again.

/close         - Closes the current ticket channel (only useable by support role)
/request-close - Asks the user to confirm close the ticket using a button.

========================
Config
========================

channels:
  logs        - ID of the channel where the bot logs startup and ticket creation / close
  transcripts - ID of the channel where closed ticket transcripts are sent

roles:
  support-role - ID of the staff role to be pinged in new tickets and is able to use close and request-close
  media-rejected - ID of the role users get when staff denies their media applcation (also makes them not be able to make another application)
  media-accepted - ID of the role users get when staff accepts their media applcation (also makes them not be able to make another application)

categories:
  Use your ticket categories IDs here

========================
Setup Instructions
========================

IMPORTANT!
-> Enable all Intents for the bot in the Developer Portal (under Bot > Privileged Gateway Intents)

1. Install dependencies:
   pip install -U discord

2. Configure the bot:
   - Open config.json
   - Paste your bot token
   - Fill in the channel, category and role IDs under "channels", "roles", and "categories"

3. Start the bot.

4. In your desired channel, use:
/setup

The ticket panel will appear, and users can begin opening tickets

========================
Support
========================

If you run into issues:
- Make sure the bot has Manage Channels and Read/Send permissions simplest would be Administrator
- DM ww_gen0093048
