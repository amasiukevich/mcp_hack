import json
import os
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

# Import the function handler if available
try:
    from llm_function_calling.functions import function_handler
except ImportError:
    from functions import function_handler

load_dotenv()

# Handle SSL certificates for macOS
if sys.platform == "darwin" and os.environ.get("ADD_ADHOC_CERT") == "true":
    os.environ["REQUESTS_CA_BUNDLE"] = "/opt/homebrew/etc/openssl@3/cert.pem"
    os.environ["SSL_CERT_FILE"] = "/opt/homebrew/etc/openssl@3/cert.pem"


class LLMEngine:
    """A class for handling LLM function calling."""

    def __init__(
        self,
        model_name: str = "gpt-4.1-mini",
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
    ):
        """Initialize the LLM engine.

        Args:
            model_name: The name of the model to use
            api_key: OpenAI API key (defaults to environment variable)
            system_prompt: Custom system prompt (defaults to standard prompt)
            functions: List of function descriptions (defaults to function_handler.descriptions)
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)

        # Set default system prompt if none provided
        if system_prompt is None:
            self.system_prompt = """
            You are a helpful assistant.
            You will be given a task and a list of available tools to complete the task.
            You will need to execute the tools to complete the task.
            You will need to return the result of the tools in a human readable format.
            You will need to be concise and to the point.
            
            If you need to use a tool - make sure to generate a tool name along with the arguments.
            If you need to use multiple tools - make sure to generate a list of tool names along with the arguments.
            """
        else:
            self.system_prompt = system_prompt

        # Use provided functions or default to function_handler if available
        self.functions = functions
        if self.functions is None and function_handler is not None:
            self.functions = function_handler.descriptions

        self.conversation_history = []
        if self.system_prompt:
            self.conversation_history.append(
                {"role": "system", "content": self.system_prompt}
            )

    def execute_function_calls(self, response: Any) -> List[Dict[str, Any]]:
        """Execute function calls from LLM response.

        Args:
            response: The response from the LLM

        Returns:
            List of input messages with function call results
        """
        input_messages = []

        for tool_call in response.output:
            if tool_call.type != "function_call":
                continue

            input_messages.append(
                {
                    "type": "function_call",
                    "call_id": tool_call.call_id,
                    "name": tool_call.name,
                    "arguments": tool_call.arguments,
                }
            )

            name = tool_call.name
            args = json.loads(tool_call.arguments)

            # Execute the function if function_handler is available
            if function_handler is not None:
                result = function_handler.execute_function(name, args)

                input_messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": result,
                    }
                )
            else:
                # If no function handler, return placeholder
                input_messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": {"error": "Function handler not available"},
                    }
                )

        return input_messages

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query using the LLM and execute any function calls.

        Args:
            query: The user query string

        Returns:
            Dictionary containing the result of function execution
        """
        # Add user query to conversation history
        self.conversation_history.append({"role": "user", "content": query})

        # Generate LLM response
        response = self.client.responses.create(
            model=self.model_name,
            input=self.conversation_history,
            tools=self.functions,
        )

        # Execute function calls
        results_of_execution = self.execute_function_calls(response)

        # Add results to conversation history
        self.conversation_history.extend(results_of_execution)

        # Return the output of the last function call
        if results_of_execution and len(results_of_execution) > 1:
            return results_of_execution[1].get("output", {})

        return {"error": "No function calls executed"}

    def reset_conversation(self) -> None:
        """Reset the conversation history."""
        self.conversation_history = []
        if self.system_prompt:
            self.conversation_history.append(
                {"role": "system", "content": self.system_prompt}
            )


if __name__ == "__main__":
    # Example usage
    engine = LLMEngine()
    result = engine.process_query(
        "What is up with my shipment? My bol number is 139712"
    )
    print(json.dumps(result, indent=4))
