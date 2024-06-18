import json
import os
from collections import OrderedDict
from typing import Dict, List

from langchain_community.graphs import Neo4jGraph
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")
llm = ChatOpenAI(temperature=0.5, model_name='gpt-4o', streaming=True) # turn temperature up for a creative marketer
small_llm = ChatOpenAI(temperature=0, model_name='gpt-4o', streaming=True)
print(os.getenv("NEO4J_URI"))
print(os.getenv("NEO4J_PASSWORD"))
graph = Neo4jGraph(url='bolt://localhost:7687')


def format_doc(doc: Document) -> Dict:
    res = OrderedDict()
    res['text'] = doc.page_content
    res.update(doc.metadata)
    return res


def format_docs(docs: List[Document]) -> str:
    return json.dumps([format_doc(d) for d in docs], indent=1)


def format_res_dicts(d: Dict) -> Dict:
    res = dict()
    for k, v in d.items():
        if k != "metadata":
            res[k] = v
    for k, v in d['metadata'].items():
        if v is not None:
            res[k] = v
    return res
