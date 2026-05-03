import json
import boto3
import uuid
from decimal import Decimal

# ================= CONVERT DECIMALS =================
def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj

# ================= DYNAMODB =================
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://host.docker.internal:4566',
    region_name='us-east-1'
)

table = dynamodb.Table('orders')

# ================= RESPONSE HELPER =================
def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }

# ================= LAMBDA HANDLER =================
def lambda_handler(event, context):
    print("EVENT:", event)

    try:
        method = event.get("httpMethod")

        # ================= POST =================
        if method == "POST":
            body = json.loads(event.get("body") or "{}")

            if not body.get("product") or not body.get("quantity"):
                return response(400, {"error": "product and quantity required"})

            item = {
                "orderId": str(uuid.uuid4()),
                "product": body["product"],
                "quantity": body["quantity"]
            }

            table.put_item(Item=item)

            return response(201, item)

        # ================= GET =================
        elif method == "GET":
            db_response = table.scan()
            items = convert_decimals(db_response.get("Items", []))

            return response(200, items)

        # ================= DELETE =================
        elif method == "DELETE":
            body = json.loads(event.get("body") or "{}")

            order_id = body.get("orderId")

            if not order_id:
                return response(400, {"error": "orderId is required"})

            table.delete_item(
                Key={"orderId": order_id}
            )

            return response(200, {"message": "Order deleted"})

        # ================= UNKNOWN =================
        else:
            return response(400, {"error": "Unsupported method"})

    except Exception as e:
        print("ERROR:", str(e))
        return response(500, {"error": str(e)})