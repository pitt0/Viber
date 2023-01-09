import discord

from .player import MusicPlayer
from resources import GUILD_ID


__all__ = ("Players",)


# Classes
class Players(dict[GUILD_ID, MusicPlayer]):
    
    async def load(self, interaction: discord.Interaction, default: discord.VoiceChannel | None = None) -> MusicPlayer:
        assert interaction.guild is not None
        channel: discord.VoiceChannel

        if interaction.guild.id in self:
            if self[interaction.guild.id].voice_client is not None:
                return self[interaction.guild.id]
            
            if default is None:
                for vc in interaction.guild.voice_channels:
                    if vc.name.lower() == "viber":
                        default = vc
                        break
                else:
                    default = interaction.guild.voice_channels[0]
            await self[interaction.guild.id].connect(default)

        
        for channel in interaction.guild.voice_channels:
            if channel in interaction.client.voice_clients:
                self[interaction.guild.id] = MusicPlayer.load(interaction.guild, default or channel) # type: ignore
                break
        else:
            channel = default or interaction.user.voice.channel # type: ignore[valid-type]
            self[interaction.guild.id] = await MusicPlayer.create(interaction.guild, channel)

        return self[interaction.guild.id]
