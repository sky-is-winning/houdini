from houdini.handlers import XTPacket
import asyncio
import random
import difflib
from houdini.plugins import IPlugin
from houdini import commands
from houdini.data.penguin import Penguin
from houdini import permissions
from houdini.data.room import Room
from houdini.data.moderator import Ban
from houdini.handlers.play.moderation import moderator_ban, moderator_kick

class Essentials(IPlugin):
    author = "Solero"
    description = "Essentials plugin"
    version = "1.0.0"

    def __init__(self, server):
        super().__init__(server)
        self.items_by_name = self.igloos_by_name = self.furniture_by_name = self.puffles_by_name = None

    async def ready(self):
        self.items_by_name = {item.name: item for item in self.server.items.values()}
        self.igloos_by_name = {igloo.name: igloo for igloo in self.server.igloos.values()}
        self.furniture_by_name = {furniture.name: furniture for furniture in self.server.furniture.values()}
        self.puffles_by_name = {puffle.name: puffle for puffle in self.server.puffles.values()}

    async def get_penguin(self, username: str):
        penguin_id = await Penguin.select('id').where(Penguin.username == username.lower()).gino.first()
        if penguin_id:
            penguin_id = int(penguin_id[0])
            return self.server.penguins_by_id.get(penguin_id)
        return None

    @commands.command('room', alias=['jr'])
    async def join_room(self, p, room: Room):
        await p.join_room(room) if room else await p.send_xt('mm', 'Room does not exist', p.id)

    @commands.command('ai')
    async def add_item(self, p, *query: str):
        await self.add_item_to_penguin(p, ' '.join(query))

    async def add_item_to_penguin(self, p, query: str):
        try:
            item = self.server.items[int(query)] if query.isdigit() else self.items_by_name[difflib.get_close_matches(query, self.items_by_name.keys(), n=1)[0]]
            await p.add_inventory(item, cost=0)
        except (IndexError, KeyError):
            await p.send_xt('mm', 'Item does not exist', p.id)

    @commands.command('ac')
    async def add_coins(self, p, amount: int = 100):
        await p.add_coins(amount, stay=True)

    @commands.command('tp')
    @permissions.has_or_moderator('essentials.tp')
    async def tp(self, p, username):
        if penguin := await self.get_penguin(username):
            await p.join_room(penguin.room)
        else:
            await p.send_xt('mm', 'Player is not Online', p.id)

    @commands.command('summon')
    @permissions.has_or_moderator('essentials.summon')
    async def summon(self, p, username):
        if penguin := await self.get_penguin(username):
            await penguin.join_room(p.room)
        else:
            await p.send_xt('mm', 'Player is not Online', p.id)

    @commands.command('ban')
    @permissions.has_or_moderator('essentials.ban')
    async def ban_penguin(self, p, player: str, message: str, duration: int = 24):
        if penguin := await self.get_penguin(player):
            if duration == 0:
                await Penguin.update.values(permaban=True).where(Penguin.username == player).gino.status()
            else:
                await moderator_ban(p, penguin.id, hours=duration, comment=message)
            await penguin.close()
        else:
            await p.send_xt('mm', 'Player is not Valid', p.id)

    @commands.command('kick')
    @permissions.has_or_moderator('essentials.kick')
    async def kick_penguin(self, p, player: str):
        if penguin := await self.get_penguin(player):
            await moderator_kick(p, penguin.id)
        else:
            await p.send_xt('mm', 'Player is not Valid', p.id)

    async def add_item_by_name(self, p, query: str, collection, collection_by_name):
        try:
            item = collection[int(query)] if query.isdigit() else collection_by_name[difflib.get_close_matches(query, collection_by_name.keys(), n=1)[0]]
            return item
        except (IndexError, KeyError):
            await p.send_xt('mm', 'Item does not exist', p.id)
            return None

    @commands.command('ag')
    async def add_igloo(self, p, *igloo_query: str):
        igloo = await self.add_item_by_name(p, ' '.join(igloo_query), self.server.igloos, self.igloos_by_name)
        if igloo:
            await p.add_igloo(igloo, cost=0)

    @commands.command('af')
    async def add_furnishings(self, p, Query: str, Units: int):
        try:
            Furniture = await self.add_item_by_name(p, Query, self.server.furniture, self.furniture_by_name)
            if Furniture:
                for _ in range(Units):
                    await p.add_furniture(Furniture, cost=0)
        except (IndexError, KeyError):
            await p.send_xt('mm', 'Furniture is Invalid', p.id)
