### Creating an MCP client

import json
import logging
import os
from typing import List, Optional

import nest_asyncio
from anthropic import Anthropic
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

nest_asyncio.apply()

load_dotenv()

MODEL_NAME = "claude-3-5-haiku-20241022"
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add a console handler to display logs
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class MCP_ChatBot:

    def __init__(self):
        # Initialize session and client objects
        self.session: ClientSession = None

        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.available_tools: List[dict] = []

    async def process_query(self, query) -> str:
        messages = [{"role": "user", "content": query}]

        response = self.anthropic.messages.create(
            max_tokens=2024,
            model=MODEL_NAME,
            tools=self.available_tools,
            messages=messages,
        )

        process_query = True

        while process_query:
            assistant_content = []
            for content in response.content:
                if content.type == "text":
                    logger.info(content.text)
                    assistant_content.append(content)
                    if len(response.content) == 1:
                        process_query = False
                elif content.type == "tool_use":
                    assistant_content.append(content)
                    messages.append({"role": "assistant", "content": assistant_content})
                    tool_id = content.id
                    tool_args = content.input
                    tool_name = content.name

                    logger.info(f"Calling tool {tool_name} with args {tool_args}")

                    # Call a tool
                    # result = execute_tool(tool_name, tool_args)

                    result = await self.session.call_tool(
                        tool_name, arguments=tool_args
                    )

                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": result.content,
                                }
                            ],
                        }
                    )
                    response = self.anthropic.messages.create(
                        max_tokens=2024,
                        model=MODEL_NAME,
                        tools=self.available_tools,
                        messages=messages,
                    )

                    if (
                        len(response.content) == 1
                        and response.content[0].type == "text"
                    ):
                        # logger.info(response.content[0].text)
                        process_query = False
                    
        return messages

    async def chat_loop(self):
        """Run an interactive chat loop"""

        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                await self.process_query(query)
                print("\n")

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def connect_to_server_and_run(self, query: str) -> list[dict]:
        # Create server parameters for stdio connection
        server_params = StdioServerParameters(
            command="python3",  # Executable
            args=["-m", "mcp_stuff.mcp_code"],  # Optional command line arguments
            env=None,  # Optional environment variables
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                # Initialize the connection
                await session.initialize()

                # List available tools
                response = await session.list_tools()

                tools = response.tools
                tools_names = [tool.name for tool in tools]
                logger.info(f"\nConnected to server with tools: {tools_names}")
            
                self.available_tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                    for tool in response.tools
                ]

                return await self.process_query(query=query)


def get_tool_result(messages: list[dict]) -> dict:

    tool_result_candidates = [
        result
        for message in messages
        for result in message["content"]
        if isinstance(message["content"], list) and isinstance(result, dict)
    ]

    tool_results = [tool_result for tool_result in tool_result_candidates[0]['content']]

    tool_result = [json.loads(tool_result.text) for tool_result in tool_results]

    if not tool_result:
        return None

    return tool_result


def get_shipper_email(messages: List[dict]) -> Optional[str]:
    """
    Get the shipper email from the messages.
    """

    tool_result = get_tool_result(messages)

    if not tool_result:
        return None

    return tool_result[0].get("shipper", {}).get("email")


def get_courier_number(messages: List[dict]) -> Optional[str]:
    """
    Get the courier number from the messages.
    """

    tool_result = get_tool_result(messages)

    if not tool_result:
        return None

    return tool_result[0].get("courier", {}).get("contact_number")


def get_shipment_order(messages: List[dict]) -> Optional[str]:
    """
    Get the shipment order from the messages.
    """

    tool_result = get_tool_result(messages)

    if not tool_result:
        return None

    return tool_result[0].get("shipment_id")


def get_shipment_info(messages: List[dict]) -> Optional[dict]:
    """
    Get the shipment info from the messages.
    """

    tool_results = get_tool_result(messages)

    if not tool_results:
        return None

    return [{
        "shipment_id": tool_result.get("shipment_id"),
        "shipment_status": tool_result.get("shipment_status"),
        "eta": tool_result.get("eta"),
        "delivery_date": tool_result.get("delivery_date"),
        "source_address": tool_result.get("source_address"),
        "dest_address": tool_result.get("dest_address"),
    } for tool_result in tool_results]

