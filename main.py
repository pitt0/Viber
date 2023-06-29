from discord import app_commands
import discord

# system
from dotenv import load_dotenv
import os

# slash groups
from groups.playlists import Playlists, Advices, Favourites
from groups.songs import Songs
from groups.players import Player
from groups.reminder import Reminder

client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client)


def load_commands() -> None:
    tree.add_command(Playlists())
    tree.add_command(Advices())
    tree.add_command(Favourites())
    tree.add_command(Songs(client))
    tree.add_command(Player(client))
    tree.add_command(Reminder(client))
    

@client.event
async def on_ready() -> None:
    load_commands()
    await tree.sync()
    
    activity = discord.Activity(name="Music", type=discord.ActivityType.listening)
    await client.change_presence(activity=activity)



if __name__ == "__main__":
    load_dotenv()
    client.run(os.getenv("TOKEN", ""))