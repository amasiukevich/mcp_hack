from fastapi import FastAPI, HTTPException

from mcp_stuff.mcp_llm_engine import MCP_ChatBot

app = FastAPI()

chatbot = MCP_ChatBot()


@app.post("/query")
async def process_query(query: str):
    try:
        result = await chatbot.connect_to_server_and_run(query=query)
        return {"response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/get_courier_shipments")
async def get_courier_shipments(contact_number: str):
    try:
        from database.couriers_updates import get_shipments_by_courier_contact

        result = get_shipments_by_courier_contact(contact_number)

        filtered_shipments = []

        for shipment in result:
            shpmt = shipment.to_dict()
            filtered_shipments.append({
                "shipment_id": shpmt["shipment_id"],
                "shipment_status": shpmt["shipment_status"],
                "eta": shpmt["eta"],
                "delivery_date": shpmt["delivery_date"],
                "dest_address": shpmt["dest_address"],
                "source_address": shpmt["source_address"],
            })
        return {"response": filtered_shipments}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/courier_shipment_updates")
async def courier_shipment_updates(phone_number: str, shipment_query: str):
    try:
        # result = await chatbot.connect_to_server_and_run(query=query)
        result = "Updated shipment eta to 2025-06-27 18:24:32.121214"
        # TODO: Send email notification to the shipper here
        return {"response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
