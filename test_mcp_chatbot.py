from mcp_stuff.mcp_llm_engine import (
    MCP_ChatBot, 
    get_shipper_email, 
    get_courier_number, 
    get_shipment_order
)

import asyncio


async def main(query: str):
    mcp_chatbot = MCP_ChatBot()
    result = await mcp_chatbot.connect_to_server_and_run(query=query)

    shipper_email = get_shipper_email(result)
    courier_number = get_courier_number(result)
    shipment_order = get_shipment_order(result)

    print(f"Shipper email: {shipper_email}")
    print(f"Courier number: {courier_number}")
    print(f"Shipment order: {shipment_order}")

if __name__ == "__main__":
    asyncio.run(main(query="Hey, operating on the shipment id 7, I will be delayed by 3 hours. Please update the eta."))