from discord import app_commands
import discord

# system
import datetime
from dotenv import load_dotenv
import os
import pytz

# slash groups
from groups.playlists import Playlists
from groups.advices import AdviceList
from groups.player import Player

client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client)


def load_commands():
    tree.add_command(Playlists())
    tree.add_command(AdviceList(client))
    tree.add_command(Player(client))

@client.event
async def on_ready():
    load_commands()
    await tree.sync()

    now = datetime.datetime.now(tz=pytz.timezone('Europe/Rome'))
    print(f"[{now.strftime('%H:%M:%S')}] Viber is online")
    
    activity = discord.Activity(name='Music', type=discord.ActivityType.listening)
    await client.change_presence(activity=activity)



if __name__ == '__main__':
    load_dotenv()
    client.run(os.getenv('TOKEN'))