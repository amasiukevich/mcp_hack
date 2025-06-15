import asyncio

from mcp_stuff.mcp_llm_engine import (
    MCP_ChatBot,
    get_courier_number,
    get_shipment_order,
    get_shipment_info,
    get_shipper_email,
    get_tool_result
)
from mcp_stuff.reply_handler import (
    SHIPMENT_SECTION_ONE,
    TEMPLATE_SUPPLIER_SHIPMENT_INFO,
    TEMPLATE_ALL_SHIPMENTS_INFO,
    get_reply_shipper
)

async def main(query: str):

    mcp_chatbot = MCP_ChatBot()
    result = await mcp_chatbot.connect_to_server_and_run(query=query)

    processed_result = get_shipment_info(result)

    shipper_email = get_shipper_email(result)
    courier_number = get_courier_number(result)

    print(f"Shipper email: {shipper_email}")
    print(f"Courier number: {courier_number}")

    reply = get_reply_shipper(processed_result)
    print(reply)

if __name__ == "__main__":

    # QUERY = "Hey, operating on the shipment id 7, I will be delayed by 3 hours. Please update the eta."
    # QUERY_EMAIL_NEGATIVE = "Email: amasiukevich@outlook.com. What is up with my shipment order 7?"
    QUERY_EMAIL_POSITIVE_ONE = "Email: mclark@bryant.com. What is up with my shipment order 5?"
    # QUERY_EMAIL_POSITIVE_MULTIPLE = "Email: mclark@bryant.com. What is up with my shipments?"

    asyncio.run(
        main(
            query= QUERY_EMAIL_POSITIVE_ONE
        )
    )
