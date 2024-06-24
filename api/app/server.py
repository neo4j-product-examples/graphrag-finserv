from typing import Dict

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langserve import add_routes
from neo4j_chains.qa_chat import qa_chain as qa_chat, qa_chain_vector_only as qa_chat_vector_only
from neo4j_chains.qa_completion import qa_chain, qa_chain_vector_only, qa_context, qa_context_vector_only
from neo4j_chains.text2cypher_chain import t2c_chain

app = FastAPI()


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


add_routes(app, qa_chat, path="/chat")

add_routes(app, qa_chat_vector_only, path="/chat-vector-only")

add_routes(app, qa_chain, path="/completion")
add_routes(app, qa_context, path="/completion-context")

add_routes(app, qa_chain_vector_only, path="/completion-vector-only")
add_routes(app, qa_context_vector_only, path="/completion-context-vector-only")

add_routes(app, t2c_chain, path="/text2cypher")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
