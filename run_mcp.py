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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
