from functions import function_handler
from openai import OpenAI
from dotenv import load_dotenv
import os
import json


load_dotenv()

MODEL_NAME = "gpt-4.1-mini"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = f"""
    You are a helpful assistant operating as a customer service agent for a shipping company.
    You will be given a task and a list of available tools to complete the task.
    You will need to execute the tools to complete the task.
    You will need to return the result of the tools in a human readable format.
    You will need to be concise and to the point.
    
    If you need to use a tool - make sure to generate a tool name along with the arguments.
    If you need to use multiple tools - make sure to generate a list of tool names along with the arguments.
"""

def execute_function_calls(response):

    """
    Executes the function calls in the response.
    Args:
        response: The response from the LLM
    Returns:
        input_messages: A list of input messages to be used in the next response
    """

    input_messages = [{
        "type": "function_call",
        "call_id": response.output[0].call_id,
        "name": response.output[0].name,
        "arguments": response.output[0].arguments
    }]
    
    for tool_call in response.output:
        print(tool_call)
        if tool_call.type != "function_call":
            continue
        
        name = tool_call.name
        args = json.loads(tool_call.arguments)

        result = function_handler.execute_function(name, args)
        
        input_messages.append({
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": result
        })
    
    return input_messages

if __name__ == "__main__":

    query = "What is up with my shipment? My bol number is 139712"

    conversation_history = []
    
    user_input = input("Enter your task:")
    conversation_history.append({"role": "user", "content": query})

    response = client.responses.create(
        model=MODEL_NAME,
        input=conversation_history,
        tools=function_handler.descriptions,
    )
    
    results_of_execution = execute_function_calls(response)
    conversation_history.append(results_of_execution)

    print(json.dumps(results_of_execution[1]['output'], indent=4))
    breakpoint()