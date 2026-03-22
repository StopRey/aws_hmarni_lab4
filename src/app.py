import json
import boto3
import os
from datetime import datetime, timedelta

TABLE_NAME = os.environ.get("TABLE_NAME")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def handler(event, context):
    try:
        # Варіант 5: Кеш курсів валют
        base_currency = "USD" # Спрощено для тесту
        response = table.get_item(Key={'id': base_currency})
        item = response.get('Item')
        
        now = datetime.now()
        if item and (now - datetime.fromisoformat(item['updated_at']) < timedelta(minutes=10)):
            return {
                "statusCode": 200,
                "body": json.dumps({"currency": base_currency, "rate": item['rate'], "cached": True})
            }
        
        # Імітація оновлення з ExchangeRate-API
        new_item = {'id': base_currency, 'rate': '39.5', 'updated_at': now.isoformat()}
        table.put_item(Item=new_item)
        return {
            "statusCode": 200, 
            "body": json.dumps({"currency": base_currency, "rate": "39.5", "cached": False})
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}