from mcp_stuff.mcp_llm_engine import MCP_ChatBot
import asyncio

async def main(query: str):
    mcp_chatbot = MCP_ChatBot()
    await mcp_chatbot.connect_to_server_and_run(query=query)


if __name__ == "__main__":
    asyncio.run(main(query="What is the eta of shipment 7?"))