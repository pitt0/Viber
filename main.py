import discord
from discord.ext import commands

# system
import os
from dotenv import load_dotenv


bot = commands.Bot('!', intents=discord.Intents.all())



@bot.event
async def on_ready() -> None:
    activity = discord.Activity(name="Music", type=discord.ActivityType.listening)
    await bot.change_presence(activity=activity)


@bot.command(name='sync')
async def sync_tree(*_) -> None:
    await bot.tree.sync()



if __name__ == "__main__":
    load_dotenv()
    bot.run(os.getenv("TOKEN", ""))