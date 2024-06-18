import json
import os
from collections import OrderedDict
from operator import itemgetter
from typing import List, Tuple, Any, Dict

from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough

from neo4j_chains.condense_question_chain import condense_question
from neo4j_chains.utils import llm, format_doc, graph

template = (
    "You are a financial expert responsible for answering user questions about companies and asset managers."
    "Answer the question based only on the below Facts and AdditionalContext. "
    "Do not assume or retrieve any information outside of Facts and AdditionalContext. "
    "The Facts and AdditionalContext are extracted from SEC filings "
    "which contain company information as well as asset manager ownership information via stock holdings. "
    "The Facts in particular should be respected as absolute fact, never provide answers that contradicts the facts. "
    "Note that company's are not considered asset managers in this dataset,"
    "Where asset manager info is mode explicitly available, "
    "you can assume the mentioned asset managers are impacted by the same things as the companies."

    """
    # Facts
    {facts}
    
    # AdditionalContext
    {additionalContext}
    
    # Question: 
    {question}
        
    # Answer:
    """)

vector_top_k = 10

vector_retrieval_query = """RETURN node.text AS text, score, node {.*, text: Null, embedding: Null} AS metadata"""
vector_store = Neo4jVector.from_existing_index(
    embedding=SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2"),
    index_name="vector",
    retrieval_query=vector_retrieval_query
)


def format_docs(docs: List[Document]) -> str:
    print("///////////// DOCS /////////////////")
    print(json.dumps([format_doc(d) for d in docs]))
    print("///////////// END DOCS /////////////////")
    return json.dumps([format_doc(d) for d in docs], indent=1)


def retrieve_facts(docs: List[Document]) -> str:
    doc_chunk_ids = [doc.metadata['id'] for doc in docs]
    res = graph.query("""
    UNWIND $chunkIds AS chunkId
    MATCH(chunk {id:chunkId})-[:HAS_ENTITY]->()-[rl:!HAS_ENTITY]-{1,5}()
    UNWIND rl AS r
    WITH DISTINCT r
    MATCH (n)-[r]->(m)
    RETURN n.id + ' - ' + type(r) +  ' -> ' + m.id AS fact ORDER BY fact
    UNION ALL
    UNWIND $chunkIds AS chunkId
    MATCH(chunk {id:chunkId})-[:PART_OF]->(:Document)<-[:HAS_DOCUMENT]-()-[rl:!HAS_DOCUMENT]-{1,2}()
    UNWIND rl AS r
    WITH DISTINCT r
    MATCH (n)-[r]->(m)
    RETURN n.info + ' - ' + r.info +  ' -> ' + m.info AS fact ORDER BY fact
    """, params={'chunkIds': doc_chunk_ids})
    print("///////////// FACTS /////////////////")
    print([r['fact'] for r in res])
    print("///////////// FACTS /////////////////")
    return '\n'.join([r['fact'] for r in res])


class ChainInput(BaseModel):
    input: str
    chat_history: List[Tuple[str, str]] = Field(
        ..., extra={"widget": {"type": "chat", "input": "input", "output": "output"}}
    )


class Output(BaseModel):
    output: Any


prompt = ChatPromptTemplate.from_template(template)

qa_chain = (
        RunnableParallel({
            "vectorStoreResults": condense_question | vector_store.as_retriever(search_kwargs={'k': vector_top_k}),
            "question": RunnablePassthrough()})
        | RunnableParallel({
    "facts": (lambda x: x["vectorStoreResults"]) | RunnableLambda(retrieve_facts),
    "additionalContext": (lambda x: x["vectorStoreResults"]) | RunnableLambda(format_docs),
    "question": lambda x: x["question"]})
        | prompt
        | llm
        | StrOutputParser()
).with_types(input_type=ChainInput, output_type=Output)
