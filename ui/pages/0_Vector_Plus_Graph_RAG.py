import asyncio
import json
from typing import Dict

import streamlit as st
from PIL import Image
from langserve import RemoteRunnable

st.set_page_config(layout="wide")

st.title("Vector & Graph RAG")
st.subheader("US Security and Exchange Commission (SEC) Knowledge Graph")
st.markdown(":gray[GraphRAG combines vectors with structured data to improve response quality]")

prompt = st.text_input("Ask a question about SEC data", value="")

col1, col2 = st.columns(2)
with col1:
    st.markdown("### Baseline RAG (vector only)")
    with st.expander("Vector only search can lack full context:"):
        vec_only = Image.open('./images/vector-only.png')
        st.markdown("#### Relationships are ignored")
        st.image(vec_only)
        v = Image.open('./images/vector-only1.png')
        st.markdown("#### Sample Doc Chunk")
        st.image(v)
with col2:
    st.markdown("### GraphRAG (vector + graph)")
    with st.expander("Vector+Graph extracts full context:"):
        schema = Image.open('./images/schema.png')
        st.markdown("#### Relationships make retrieval context-rich")
        st.image(schema)
        vg = Image.open('./images/vector-graph.png')
        st.markdown("#### Sample Doc Chunk")
        st.image(vg)


class StreamHandler:
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def new_token(self, token: str) -> None:
        self.text += token
        self.container.markdown(self.text, unsafe_allow_html=True)


async def get_chain_response(input: str, url: str, stream_handler: StreamHandler):
    remote_runnable = RemoteRunnable(url)
    async for data in remote_runnable.astream(input):
        stream_handler.new_token(data)


def generate_response(input: str, use_graphrag: bool = False):
    url = "http://api:8080/completion-vector-only/"
    if use_graphrag:
        url = "http://api:8080/completion/"
    stream_handler = StreamHandler(st.empty())
    # Create an event loop: this is needed to run asynchronous functions
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Run the asynchronous function within the event loop
    loop.run_until_complete(get_chain_response(input, url, stream_handler))
    # Close the event loop
    loop.close()


def format_json_context(context, use_graphrag: bool = False):
    if use_graphrag:
        facts = json.dumps(context["facts"].split("\n"), indent=1)
        context_json_str = f'{{"documentContext":{context["additionalContext"]}, "graphFacts":{facts}}}'
    else:
        context_json_str = context['context']
    return context_json_str


def get_context(input: str, use_graphrag: bool = False):
    url = "http://api:8080/completion-context-vector-only/"
    if use_graphrag:
        url = "http://api:8080/completion-context/"
    remote_runnable = RemoteRunnable(url)
    response = remote_runnable.invoke(input)
    print(response)
    return format_json_context(response, use_graphrag)


if prompt:
    with col1:
        status = st.status("Generating response 🤖")
        with st.expander('__Response:__', True):
            generate_response(prompt, False)
        status.update(label="Finished!", state="complete", expanded=False)
        with st.expander("__Context used to answer this prompt:__"):
            st.json(get_context(prompt, False))
    with col2:
        status = st.status("Generating response 🤖")
        with st.expander('__Response:__', True):
            generate_response(prompt, True)
        status.update(label="Finished!", state="complete", expanded=False)
        with st.expander("__Context used to answer this prompt:__"):
            st.json(get_context(prompt, True))
st.markdown("---")

st.markdown("""
<style>
  table {
    width: 100%;
    border-collapse: collapse;
    border: none !important;
    font-family: "Source Sans Pro", sans-serif;
    color: rgba(49, 51, 63, 0.6);
    font-size: 0.9rem;
  }

  tr {
    border: none !important;
  }
  
  th {
    text-align: center;
    colspan: 3;
    border: none !important;
    color: #0F9D58;
  }
  
  th, td {
    padding: 2px;
    border: none !important;
  }
</style>

<table>
  <tr>
    <th colspan="3">Sample Questions to try out</th>
  </tr>
  <tr>
    <td>Which companies and asset managers are most affected during covid?</td>
    <td>Which companies and asset managers are vulnerable to chip shortage?</td>
    <td>Which asset managers have investments in outside USA? Explain with evidence</td>
  </tr>
  <tr>
    <td>Which asset managers are exposed to defense industries based on the companies they own shares in?</td>
    <td>Which company sells analytics solutions?</td>
    <td>If I have to invest in commodities, what are the list of asset managers to look into?</td>
  </tr>
  <tr>
    <td></td>
    <td></td>
  </tr>
</table>
""", unsafe_allow_html=True)
