import redis.asyncio as redis  
from src.config import Config

JTI_EXPIRY = 3600

# token_blocklist = redis.Redis(
#     host=Config.REDIS_HOST,
#     port=Config.REDIS_PORT,
#     db=0,
#     decode_responses=True
# )

token_blocklist = redis.from_url(
   Config.REDIS_URL
)

async def add_jti_to_blocklist(jti: str) -> None:
    await token_blocklist.set(
        name=jti,
        value='',
        ex=JTI_EXPIRY
    )

async def token_in_blocklist(jti: str) -> bool:
    value = await token_blocklist.get(jti)
    return value is not None

#admin
[
    "adding users",
    "change roles",
    "crud on users",
    "book submissions",
    "crud on users",
    "crud on reviews",
    "revoking access"
]

#users
[
    "crud on their own book submissions", 
    "crud on their reviews", 
    "crud on their own accounts"
]
