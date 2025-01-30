from dotenv import load_dotenv

import logging
import json
import aiohttp
import os

load_dotenv()

API_TOKEN_SANDBOX = os.getenv("API_TOKEN_SANDBOX")
API_URL_FOR_CHECK = "https://api.imeicheck.net/v1/checks"
API_URL_FOR_SERVICE = "https://api.imeicheck.net/v1/services"

async def get_service_id():
    try:
        headers = {
            'Authorization': f"Bearer {API_TOKEN_SANDBOX}",
            'Content-Type': 'application/json'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL_FOR_SERVICE, headers=headers) as response:
                data = await response.json()
                return [str(item["id"]) for item in data]
    except Exception as e:
        logging.error(f"Ошибка в get_service_id: {e}", exc_info=True)
        return None

async def check_imei(imei: str):
    try:
        service_id = int((await get_service_id())[0])

        headers = {
            "Authorization": f"Bearer {API_TOKEN_SANDBOX}",
            "Content-Type": "application/json"
        }
        body = json.dumps({
            "deviceId": imei,
            "serviceId": service_id
        })
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL_FOR_CHECK, headers=headers, data=body) as response:
                if response.status == 422:
                    return {"message": 'Простите, но вы используете неправильный service_id'}
                
                if response.status != 201:
                    text = await response.text()
                    logging.error(f"Ошибка запроса IMEI: {response.status}, {text}")
                    return None
                
                return await response.json()
    except Exception as e:
        logging.error(f"Ошибка в check_imei: {e}", exc_info=True)
        return None
