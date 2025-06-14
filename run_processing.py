import json

from llm_function_calling.llm_engine import LLMEngine

if __name__ == "__main__":
    # Example usage
    engine = LLMEngine()
    result = engine.process_query(
        "What is up with my shipment? My bol number is 139712"
    )
    print(json.dumps(result, indent=4))
