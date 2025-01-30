import aioredis
import json
import logging

redis = None

async def get_redis():
    global redis
    if redis is None:
        try:
            redis = await aioredis.from_url("redis://localhost:6379")
            print("Successfully connected to Redis")
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            redis = None
    return redis


async def set_user_message(user_id, data, bot_id):
    try:
        redis = await get_redis()
        await redis.set(f"{str(user_id)}: {str(bot_id)}: for_message", json.dumps(data))
        logging.info(f"Сохранили сообщение в Redis для пользователя {user_id} и бота {bot_id}: {data}")
    except Exception as e:
        logging.info(f"Ошибка в рэдис (set_user_message): {e}")


async def get_user_message(user_id, bot_id):
    try:
        redis = await get_redis()
        data = await redis.get(f"{str(user_id)}: {str(bot_id)}: for_message")
        if data:
            logging.info(f"Получено сообщение из Redis для пользователя {user_id} и бота {bot_id}: {data}")
            return json.loads(data)
        logging.info(f"Сообщение для редактирования не найдено в Redis для пользователя {user_id}")
        return None 
    except Exception as e:
        logging.info(f"Ошибка в рэдис (get_user_message): {e}")


async def del_data(user_id, bot_id):
    redis = await get_redis()
    await redis.delete(f"{str(user_id)}: {str(bot_id)}: for_message")
    logging.info(f"Удалили сообщение из Redis для пользователя {user_id} и бота {bot_id}")


async def redis_set(key, value, expiration=100):
    try:
        redis = await get_redis()
        await redis.setex(key, expiration, json.dumps(value))
        logging.info(f"Сохранили {key} в Redis с данными: {value}")
    except Exception as e:
        logging.info(f"Ошибка в рэдис (set): {e}")

async def redis_get(key):
    try:
        redis = await get_redis()
        data = await redis.get(key)
        if data:
            logging.info(f"Получен {key} из Redis с данными: {data}")
            return json.loads(data)
        logging.info(f"{key} не найден в Redis")
        return None
    except Exception as e:
        logging.info(f"Ошибка в рэдис (get): {e}")

async def redis_delete(key):
    try:
        redis = await get_redis()
        await redis.delete(key)
        logging.info(f"Удалили {key} из Redis")
    except Exception as e:
        logging.info(f"Ошибка в рэдис (delete): {e}")


async def set_hello_field(user_id, bot_id, field_name, value, expiration=100):
    key = f"{user_id}:{bot_id}:{field_name}"
    await redis_set(key, value, expiration)

async def get_hello_field(user_id, bot_id, field_name):
    key = f"{user_id}:{bot_id}:{field_name}"
    return await redis_get(key)

async def del_hello_field(user_id, bot_id, field_name):
    key = f"{user_id}:{bot_id}:{field_name}"
    await redis_delete(key)