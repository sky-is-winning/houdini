from houdini import handlers
from houdini.handlers import XTPacket
from datetime import datetime
import ujson

COOKIE_HANDLER_ID = "20150702"

START_PARTY = datetime(1970, 1, 1, 0, 0, 0)#date[year month day hour minute sec] for start party
END_PARTY = datetime(2035, 1, 1, 0, 0, 0)#date[year month day hour minute sec] for end party

COOKIE_HANDLER_NAME = "insideout"
PARTY_CACHE_CURRENT = "insideout"

DEFAULT_PARTY_COOKIE = {
    'msgViewedArray': [0] * 5,
    'questTaskStatus': [0] * 8,
    'communicatorMsgArray': [0] * 5,
    'hasViewedPreLoginMessage': False,
}

QUEST_LIST = [
    {
        "questTaskIndex": 0,
        "emotion": "Joy",
        "nonMemberItem": 5530,
        "memberItems": [21022, 24307]
    }, {
        "questTaskIndex": 1,
        "emotion": "Sadness",
        "nonMemberItem": 5529,
        "memberItems": [21023, 24308, 6265]
    }, {
        "questTaskIndex": 2,
        "emotion": "Anger",
        "nonMemberItem": 5531,
        "memberItems": [21021, 24306, 10358]
    }, {
        "questTaskIndex": 3,
        "emotion": "Disgust",
        "nonMemberItem": 21027,
        "memberItems": [21025, 3234, 24310, 6264]
    }, {
        "questTaskIndex": 4,
        "emotion": "Fear",
        "nonMemberItem": 21026,
        "memberItems": [21024, 24309, 6263]
    }, {
        "questTaskIndex": 5,
        "emotion": "CompletedAll",
        "nonMemberItem": 9302,
        "memberItems": [1951, 21100, 24386, 5585, 5500]
    }
]

PARTY_SETTINGS = {
    "partySettings": {
        "unlockDayIndex": 16,
        "numOfDaysInParty": 16
    },
    "questSettingList": QUEST_LIST,
    "numOfQuests": 8,
    "partyStartDate": str(START_PARTY),
    "partyEndDate": str(END_PARTY)
}

COIN_REWARDS = {
    6: 1000,
    7: 1000
}

PARTY_COOKIE_COMMAND = "partycookie"
PRE_MESSAGE_VIEWED_COMMAND = "premsgviewed"
MESSAGE_VIEWED_COMMAND = "msgviewed"
QC_MESSAGE_VIEWED_COMMAND = "qcmsgviewed"
QUEST_TASK_COMPLETE = "qtaskcomplete"

async def send_party_cookie(p):
    if p.cookie is None:
        cookie = await p.server.redis.hget(PARTY_CACHE_CURRENT, p.id)
        p.cookie = ujson.loads(ujson.dumps(DEFAULT_PARTY_COOKIE)) if cookie is None else ujson.loads(cookie)
        
        if all([p.cookie['questTaskStatus'][i] == 1 for i in range(5)]): # FML
            p.cookie['questTaskStatus'][5] = 1
    await p.server.redis.hset(PARTY_CACHE_CURRENT, p.id, ujson.dumps(p.cookie))
    await p.send_xt('partycookie', ujson.dumps(p.cookie), internal_id=82)

@handlers.handler(XTPacket(COOKIE_HANDLER_NAME, 'itransform'))
async def handle_party_transformation(p, transform_id: int):
    if transform_id not in [1000, 1001]:
        return
    p.avatar = transform_id
    await p.room.send_xt('spts', p.id, transform_id)

@handlers.handler(XTPacket(COOKIE_HANDLER_NAME, PRE_MESSAGE_VIEWED_COMMAND))
async def handle_login_message_viewed(p):
    p.cookie['hasViewedPreLoginMessage'] = True
    await send_party_cookie(p)

@handlers.handler(XTPacket(COOKIE_HANDLER_NAME, QUEST_TASK_COMPLETE))
async def handle_party_task_complete(p, task_index: int):
    coins = COIN_REWARDS.get(task_index)
    if p.cookie['questTaskStatus'][task_index] == 0 and coins is not None:
        await p.update(coins=p.coins+coins).apply()
        await p.send_xt('gtc', p.coins)
        
    p.cookie['questTaskStatus'][task_index] = 1
    if all([p.cookie['questTaskStatus'][i] == 1 for i in range(5)]):
        p.cookie['questTaskStatus'][5] = 1
        
    await send_party_cookie(p)
    
@handlers.handler(XTPacket(COOKIE_HANDLER_NAME, MESSAGE_VIEWED_COMMAND))
async def handle_party_message_viewed(p, task_index: int):
    p.cookie['msgViewedArray'][task_index] = 1
    await send_party_cookie(p)