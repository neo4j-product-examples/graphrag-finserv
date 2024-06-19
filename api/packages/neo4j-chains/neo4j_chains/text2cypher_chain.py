import json
from typing import Any

import neo4j.time
from langchain.pydantic_v1 import BaseModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI

from neo4j_chains.utils import llm, graph, remove_keys_from_dict

txt2cypher_template = '''
#Context 

You have expertise in neo4j cypher query language and based on below graph data model schema, 
you are going to help me write cypher queries. 

Node Labels and Properties

["Company"], ["cik:String", "managerName:String"]
["Manager"], ["cusip:String", "companyName:String"]
["Document"], [text:String]

Accepted graph traversal paths

(:Manager)-[:OWNS]->(:Company), 
(:Company)-[:HAS_DOCUMENT]->(:Document),

Remove english explanation and any markdown annotation, provide just the Cypher code. 
# Ask:
{input}
'''

results_to_language_template = """
Transform below data to human readable format with bullets if needed, And summarize it in a sentence or two if possible
# Sample Ask and Response :
## Ask:
Get distinct watch terms ?

## Response:
[\"alert\",\"attorney\",\"bad\",\"canceled\",\"charge\"]

## Output:
Here are the distinct watch terms
- "alert"
- "attorney"
- "bad"
- "canceled"
- "charge"

# Generate similar output for below Ask and Response

## Ask
${input}

## Response:
${context}

## Output: 
"""

def format_context(docs) -> str:
    docs = remove_keys_from_dict(docs, ['embedding'])
    print(docs)
    res = json.dumps(docs, indent=1, default=str)
    return res


class ChainInput(BaseModel):
    input: str


class Output(BaseModel):
    output: Any


t2c_prompt = PromptTemplate.from_template(txt2cypher_template)
r2l_prompt = PromptTemplate.from_template(results_to_language_template)
t2c_llm = ChatOpenAI(temperature=0, model_name='gpt-4', streaming=True)

t2c_chain = (RunnableParallel({'context': t2c_prompt
                                          | t2c_llm
                                          | StrOutputParser()
                                          | RunnableLambda(graph.query)
                                          | RunnableLambda(format_context),
                               'input': RunnablePassthrough()})
             | r2l_prompt
             | llm
             | StrOutputParser()).with_types(input_type=ChainInput, output_type=Output)
