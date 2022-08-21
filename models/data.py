from typing import TypeAlias

import discord

from .player import MusicPlayer


__all__ = (
    'Players',
)

GUILD_ID: TypeAlias = int

class Players:

    players: dict[GUILD_ID, MusicPlayer] = {}

    def __getitem__(self, key):
        return self.players.__getitem__(key)

    def __contains__(self, value):
        return value in self.players
    
    async def load(self, interaction: discord.Interaction, default: discord.VoiceChannel | None = None) -> MusicPlayer:
        assert interaction.guild is not None
        channel: discord.VoiceChannel

        if interaction.guild.id in self.players:
            if self.players[interaction.guild.id].voice_client is not None:
                return self.players[interaction.guild.id]
            
            if default is None:
                for vc in interaction.guild.voice_channels:
                    if vc.name.lower() == 'viber':
                        default = vc
                        break
                else:
                    default = interaction.guild.voice_channels[0]
            await players[interaction.guild.id].connect(default) # type: ignore

        
        for channel in interaction.guild.voice_channels:
            if channel in interaction.client.voice_clients:
                self.players[interaction.guild.id] = MusicPlayer.load(interaction.guild, default or channel) # type: ignore
                break
        else:
            channel = default or interaction.user.voice.channel # type: ignore[valid-type]
            self.players[interaction.guild.id] = await MusicPlayer.create(interaction.guild, channel)

        return self.players[interaction.guild.id]
