from agent.tools import TOOLS
from agent.prompts import PROMPT
from agent.state import GraphState
from agent.utils import create_agent
from agent.config import ConfigSchema

import os
import mlflow
from langchain_ollama import ChatOllama
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.agents import AgentAction, AgentFinish


from dotenv import load_dotenv
load_dotenv()

tool_map = {tool.name: tool for tool in TOOLS}


def invoke_agent(state, config):
    llm = ChatOllama(model=config['configurable'].get('model', 'gemma3:4b'), base_url=os.getenv('OLLAMA_BASE_URL'))
    agent = create_agent(llm, TOOLS, PROMPT)  
    response = agent.plan(input=state['messages'][-1], 
                          intermediate_steps=state['intermediate_steps'],
                          chat_history=state['messages'],
                          )
    return {'messages': [response]}


def route_agent(state):
    if isinstance(state['messages'][-1], AgentFinish):
        return 'end'
    return 'tools'


def invoke_tools(state, config):
    response = []
    tool_calls = state['messages'][-1]
    tool_calls = [tool_calls] if isinstance(tool_calls, AgentAction) else tool_calls 
    for tool_call in tool_calls:
        tool = tool_map[tool_call.tool]
        observation = tool.run(tool_call.tool_input, verbose=False)
        response.append((tool_call, observation))
    return {'intermediate_steps': response}


workflow = StateGraph(state_schema=GraphState, config_schema=ConfigSchema)
workflow.add_node('agent', invoke_agent)
workflow.add_node('tools', invoke_tools)
workflow.add_edge(START, 'agent')
workflow.add_conditional_edges('agent', route_agent, {'end': END, 'tools': 'tools'})
workflow.add_edge('tools', 'agent')

memory = InMemorySaver()
graph = workflow.compile(name='ReAct Agent', checkpointer=memory)

mlflow.models.set_model(graph)