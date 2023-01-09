from discord import app_commands
import discord

# system
from dotenv import load_dotenv
import os
from resources import Time

# slash groups
from groups.playlists import Playlists
from groups.songs import Songs
from groups.players import Player

client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client)


def load_commands():
    tree.add_command(Playlists())
    tree.add_command(Songs(client))
    tree.add_command(Player(client))

@client.event
async def on_ready():
    load_commands()
    await tree.sync()

    print(f"[{Time.now()}] Viber is online")
    
    activity = discord.Activity(name="Music", type=discord.ActivityType.listening)
    await client.change_presence(activity=activity)



if __name__ == "__main__":
    load_dotenv()
    client.run(os.getenv("TOKEN")) # type: ignore