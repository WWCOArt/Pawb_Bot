import random
import asyncio
from twitchio.ext import commands

from bot_data import BotData

class CommandsCharacters(commands.Component):
    def __init__(self, bot_data: BotData):
        self.bot_data = bot_data
    
    @commands.command()
    async def eisuke(self, context: commands.Context):
        await context.send("Eisuke Ma'VerIlloria, one of my oldest characters. Michievous and in control of a reality-altering ability, he just wants to have fun and make things into a game. https://toyhou.se/278301.eisuke-ma-verilloria")

    @commands.command(aliases=["saodevereaux"])
    async def sao(self, context: commands.Context):
        await context.send("A kitsune who's got a swarm of nanites within them that cause her to involuntarily alter her surroundings. Examples of her can be found at: https://toyhou.se/9789272.sao-devereaux/gallery")

    @commands.command()
    async def aota(self, context: commands.Context):
        await context.send("Aota (short for All of the Above) is a design by FalloutFox that is a comibnation of Sphinx Ryu, Dragon Ryu, and Tiger Ryu. Examples of them can be found here: https://toyhou.se/10440583.aota-all-of-the-above-/gallery")

    @commands.command(aliases=["sierra"])
    async def ria(self, context: commands.Context):
        await context.send("Sierra Lyons is my fursona! They're normally a sphinx/maned wolf hybrid, but can also take on a few other forms, including a dragon, fox, skunk, demon, and glitch saber.")
    
    @commands.command()
    async def kat(self, context: commands.Context):
        await context.send("Kat is a genderfluid Tiger/Lion/Dragon hybrid whose real body is a humanoid cloud of nanites, controlled by 7 floating processing orbs. Examples can be found here: https://toyhou.se/13066401.kat")

    @commands.command()
    async def kat(self, context: commands.Context):
        await context.send("Kat is a genderfluid Tiger/Lion/Dragon hybrid whose real body is a humanoid cloud of nanites, controlled by 7 floating processing orbs. Also a robot wizard werewolf. Examples can be found here: https://toyhou.se/13066401.kat")

    @commands.command()
    async def chris(self, context: commands.Context):
        await context.send("Chris Phoenix is a Chimera werewolf character of mine. Unlike most of my characters, he ages in real time as time passes. https://toyhou.se/278850.christopher-phoenix/gallery")

    @commands.command()
    async def kwilson(self, context: commands.Context):
        await context.send("Wilson Green, a giant wolf created by a test-gone-wrong at Aperture Sciences. He started as a joke, but I got attached. https://toyhou.se/11440521.wilson-green/gallery")