import json
import os
from datetime import datetime, timedelta
from urllib.parse import parse_qs

import boto3

TABLE_NAME = os.environ.get("TABLE_NAME")
_AWS_REGION = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "eu-central-1"

dynamodb = boto3.resource("dynamodb", region_name=_AWS_REGION)
table = dynamodb.Table(TABLE_NAME)
translate = boto3.client("translate", region_name=_AWS_REGION)


def _query_param(event, name: str):
    """HTTP API v2: lang може бути лише в rawQueryString або з іншим регістром ключа."""
    qp = event.get("queryStringParameters") or {}
    for k, v in qp.items():
        if k and k.lower() == name.lower() and v is not None:
            return str(v).strip() or None
    mv = event.get("multiValueQueryStringParameters") or {}
    for k, vals in mv.items():
        if k and k.lower() == name.lower() and vals:
            return str(vals[0]).strip() or None
    raw = event.get("rawQueryString") or ""
    if raw:
        parsed = parse_qs(raw, keep_blank_values=True)
        for key in parsed:
            if key.lower() == name.lower() and parsed[key]:
                return (parsed[key][0] or "").strip() or None
    return None

# Короткі англомовні описи для кешу (оновлення при простроченому кеші)
_CURRENCY_EN = {
    "USD": "The United States dollar is the official currency of the United States and its territories.",
    "EUR": "The euro is the official currency of the eurozone used by many European Union member states.",
    "UAH": "The Ukrainian hryvnia is the official currency of Ukraine.",
    "GBP": "The pound sterling is the official currency of the United Kingdom.",
    "PLN": "The Polish złoty is the official currency of Poland.",
}


def _english_description_for(base: str) -> str:
    code = (base or "").strip().upper()
    return _CURRENCY_EN.get(
        code,
        f"{code} is a currency code; this description is generated in English for caching.",
    )


def handler(event, context):
    try:
        path_params = event.get("pathParameters") or {}
        base_currency = path_params.get("base")
        if not base_currency:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json; charset=utf-8"},
                "body": json.dumps(
                    {"error": "Missing path parameter: base"}, ensure_ascii=False
                ),
            }

        base_key = base_currency.strip().upper()
        lang = _query_param(event, "lang")

        response = table.get_item(Key={"id": base_key})
        item = response.get("Item")
        now = datetime.now()

        cached = False
        description_en: str
        ts: str

        fresh = (
            item
            and item.get("description")
            and (now - datetime.fromisoformat(item["updated_at"]) < timedelta(minutes=10))
        )
        if fresh:
            description_en = item["description"]
            ts = item["updated_at"]
            cached = True
        else:
            description_en = _english_description_for(base_key)
            ts = now.isoformat()
            table.put_item(
                Item={
                    "id": base_key,
                    "description": description_en,
                    "updated_at": ts,
                }
            )
            cached = False

        text_out = description_en
        if lang:
            try:
                tr = translate.translate_text(
                    Text=description_en,
                    SourceLanguageCode="en",
                    TargetLanguageCode=lang.lower(),
                )
                text_out = tr["TranslatedText"]
            except Exception as exc:
                # CloudWatch: чому спрацював fallback (IAM, мова, квоти)
                print(f"Translate fallback: {type(exc).__name__}: {exc}")
                text_out = description_en

        payload = {
            "currency": base_key,
            "description": text_out,
            "cached": cached,
            "timestamp": ts,
        }
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json; charset=utf-8"},
            "body": json.dumps(payload, ensure_ascii=False),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json; charset=utf-8"},
            "body": json.dumps({"error": str(e)}, ensure_ascii=False),
        }
