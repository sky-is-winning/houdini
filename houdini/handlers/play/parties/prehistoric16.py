from houdini import handlers
from houdini.handlers import XTPacket
from datetime import datetime
import ujson

COOKIE_HANDLER_ID = "20151100"

START_PARTY = datetime(1970, 1, 1, 0, 0, 0)#date[year month day hour minute sec] for start party
END_PARTY = datetime(2035, 1, 1, 0, 0, 0)#date[year month day hour minute sec] for end party

COOKIE_HANDLER_NAME = "party"
PARTY_CACHE_CURRENT = "prehistoric16"

DEFAULT_PARTY_COOKIE = {
    'msgViewedArray': [0] * 16,
    'communicatorMsgArray': [0] * 16,
    'questTaskStatus': [0] * 16
}

PARTY_SETTINGS = {
    "partySettings": {
        "unlockDayIndex": 16,
        "numOfDaysInParty": 16
    },
    "partyStartDate": str(START_PARTY),
    "partyEndDate": str(END_PARTY)
}

PARTY_COOKIE_ID = "partycookie"
MESSAGE_VIEWED_COMMAND = "msgviewed"
QC_MESSAGE_VIEWED_COMMAND = "qcmsgviewed"
QUEST_TASK_COMPLETE = "qtaskcomplete"
QUEST_TASK_UPDATE = "qtupdate"

async def send_party_cookie(p):
    if p.cookie is None:
        cookie = await p.server.redis.hget(PARTY_CACHE_CURRENT, p.id)
        p.cookie = ujson.loads(ujson.dumps(DEFAULT_PARTY_COOKIE)) if cookie is None else ujson.loads(cookie)
    await p.server.redis.hset(PARTY_CACHE_CURRENT, p.id, ujson.dumps(p.cookie))
    await p.send_xt('partycookie', ujson.dumps(p.cookie), internal_id=82)

@handlers.handler(XTPacket(COOKIE_HANDLER_NAME, PARTY_COOKIE_ID))
async def handle_party_cookie(p):
    await send_party_cookie(p)

@handlers.handler(XTPacket(COOKIE_HANDLER_NAME, QC_MESSAGE_VIEWED_COMMAND))
async def handle_party_qc_message_viewed(p, task_index: int):
    p.cookie['communicatorMsgArray'][task_index] = 1
    await send_party_cookie(p)

@handlers.handler(XTPacket(COOKIE_HANDLER_NAME, QUEST_TASK_COMPLETE))
async def handle_party_task_complete(p, task_index: int):        
    p.cookie['questTaskStatus'][task_index] = 1
    await send_party_cookie(p)

@handlers.handler(XTPacket(COOKIE_HANDLER_NAME, QUEST_TASK_UPDATE))
async def handle_party_task_update(p, coins: int):
    await p.update(coins=p.coins+coins).apply()
    await p.send_xt('gtc', p.coins)
    
@handlers.handler(XTPacket(COOKIE_HANDLER_NAME, MESSAGE_VIEWED_COMMAND))
async def handle_party_message_viewed(p, task_index: int):
    p.cookie['msgViewedArray'][task_index] = 1
    await send_party_cookie(p)