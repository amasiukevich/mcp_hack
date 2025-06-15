from fastapi import FastAPI, HTTPException

from gmail_integration.gmail_client import GmailClient
from mcp_stuff.functions import get_shipments_by_courier_contact
from mcp_stuff.mcp_llm_engine import (
    MCP_ChatBot,
    get_shipment_info,
    get_shipment_order,
    get_shipper_email,
)
from reply_handler import (
    TEMPLATE_EMAIL_UPDATE_ETA,
    TEMPLATE_SUPPLIER_SHIPMENT_INFO,
    TEMPLATE_TG_UPDATE_ETA,
)

app = FastAPI()
chatbot = MCP_ChatBot()

gmail_client = GmailClient(
    credentials_file="gmail_integration/credentials.json",
    token_file="gmail_integration/token.json",
)


@app.post("/query")
async def process_query(query: str):
    try:
        result = await chatbot.connect_to_server_and_run(query=query)
        if result:
            result = TEMPLATE_SUPPLIER_SHIPMENT_INFO.format(**get_shipment_info(result))
            return {"response": result}
        else:
            return {
                "response": "No shipment info found. Please specify the shipment id or BOL id."
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_courier_shipments")
async def get_courier_shipments(contact_number: str):
    try:

        result = get_shipments_by_courier_contact(contact_number)

        filtered_shipments = []

        for shipment in result:
            shpmt = shipment.to_dict()
            filtered_shipments.append(
                {
                    "shipment_id": shpmt["shipment_id"],
                    "shipment_status": shpmt["shipment_status"],
                    "eta": shpmt["eta"],
                    "delivery_date": shpmt["delivery_date"],
                    "dest_address": shpmt["dest_address"],
                    "source_address": shpmt["source_address"],
                }
            )
        return {"response": filtered_shipments}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/courier_shipment_updates")
async def courier_shipment_updates(phone_number: str, shipment_query: str):
    try:
        result = await chatbot.connect_to_server_and_run(query=shipment_query)

        shipper_email = get_shipper_email(result)
        # courier_number = get_courier_number(result)
        shipment_order = get_shipment_order(result)

        message_supplier = TEMPLATE_EMAIL_UPDATE_ETA.format(shipment_id=shipment_order)
        message_courier = TEMPLATE_TG_UPDATE_ETA.format(shipment_id=shipment_order)

        gmail_client.send_email(
            to_email=shipper_email,
            subject="Shipment Update",
            body=message_supplier,
        )
        print(f"Sent email to {shipper_email}")

        return {"response": message_courier}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
