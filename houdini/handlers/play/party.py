import ujson

from houdini import handlers
from houdini.handlers import XTPacket
from houdini.handlers.play.navigation import handle_join_server
from importlib import import_module

party_modules = ["insideout", "waddleon", "puffle16", "prehistoric16"]

parties_data = {}

for party in party_modules:
    # Dynamically import the party module
    party_module = import_module(f'houdini.handlers.play.parties.{party}')
    
    # Initialize party data
    parties_data[party] = {}
    parties_data[party]['COOKIE_HANDLER_ID'] = getattr(party_module, 'COOKIE_HANDLER_ID')
    parties_data[party]['PARTY_SETTINGS'] = getattr(party_module, 'PARTY_SETTINGS')
    parties_data[party]['PARTY_CACHE_CURRENT'] = getattr(party_module, 'PARTY_CACHE_CURRENT')
    parties_data[party]['DEFAULT_PARTY_COOKIE'] = getattr(party_module, 'DEFAULT_PARTY_COOKIE')

# CONSTANTS

PARTY_COOKIE_COMMAND = "partycookie"
PRE_MESSAGE_VIEWED_COMMAND = "premsgviewed"
MESSAGE_VIEWED_COMMAND = "msgviewed"
QC_MESSAGE_VIEWED_COMMAND = "qcmsgviewed"
QUEST_TASK_COMPLETE = "qtaskcomplete"

# END OF CONSTANTS

@handlers.handler(XTPacket('party', 'transform'))
async def handle_party_transformation(p, transform_id: int):
    p.avatar = transform_id
    await p.room.send_xt('spts', p.id, transform_id)

async def send_party_cookie(p):
    PARTY_CACHE_CURRENT = parties_data[p.current_party]['PARTY_CACHE_CURRENT']
    DEFAULT_PARTY_COOKIE = parties_data[p.current_party]['DEFAULT_PARTY_COOKIE']

    if p.cookie is None:
        cookie = await p.server.redis.hget(PARTY_CACHE_CURRENT, p.id)
        p.cookie = ujson.loads(ujson.dumps(DEFAULT_PARTY_COOKIE)) if cookie is None else ujson.loads(cookie)
    await p.server.redis.hset(PARTY_CACHE_CURRENT, p.id, ujson.dumps(p.cookie))
    await p.send_xt('partycookie', ujson.dumps(p.cookie), internal_id=82)

@handlers.handler(XTPacket('party', 'setcurrentparty'), after= handle_join_server)
@handlers.allow_once
async def handle_get_partysettings(p, party_id: str):
    p.current_party = party_id
    if (party_id not in parties_data):
        return await p.send_xt('activefeatures')
    
    COOKIE_HANDLER_ID = parties_data[party_id]['COOKIE_HANDLER_ID']
    await p.send_xt('activefeatures', COOKIE_HANDLER_ID)
        
@handlers.handler(XTPacket('party', 'setcurrentparty'), after=handle_join_server, pre_login=True)
@handlers.allow_once
async def handle_party_cookie(p, party_id: str):
    if (party_id not in parties_data):
        return await p.send_xt('partyservice')
    
    PARTY_SETTINGS = parties_data[party_id]['PARTY_SETTINGS']
    
    await p.send_xt('partyservice', ujson.dumps(PARTY_SETTINGS), internal_id=2)
    await send_party_cookie(p)