import json
import os
from collections import OrderedDict
from typing import Dict, List

from langchain_community.graphs import Neo4jGraph
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")
llm = ChatOpenAI(temperature=0, model_name='gpt-4o', streaming=True)
small_llm = ChatOpenAI(temperature=0, model_name='gpt-4o', streaming=True)
graph = Neo4jGraph()


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


def remove_keys_from_dict(x, keys_to_remove):
    if isinstance(x, dict):
        x_clean = dict()
        for k, v in x.items():
            if k not in keys_to_remove:
                x_clean[k] = remove_keys_from_dict(v, keys_to_remove)
    elif isinstance(x, list):
        x_clean = [remove_keys_from_dict(i, keys_to_remove) for i in x]
    else:
        x_clean = x
    return x_clean