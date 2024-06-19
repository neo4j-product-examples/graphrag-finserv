from typing import Dict

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langserve import add_routes
from neo4j_chains.qa_chain import qa_chain, qa_chain_vector_only
from neo4j_chains.text2cypher_chain import t2c_chain

app = FastAPI()


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


add_routes(app, qa_chain, path="/assistant")

add_routes(app, qa_chain_vector_only, path="/assistant-vector-only")

add_routes(app, t2c_chain, path="/text2cypher")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
