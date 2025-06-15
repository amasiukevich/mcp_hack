from fastapi import FastAPI, HTTPException

from mcp_stuff.mcp_llm_engine import MCP_ChatBot

app = FastAPI()


@app.post("/query")
async def process_query(query: str):
    try:
        chatbot = MCP_ChatBot()
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
