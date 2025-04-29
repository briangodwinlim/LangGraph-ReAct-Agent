from langchain.agents.agent import RunnableAgent
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools.render import render_text_description
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser


def create_agent(llm, tools, prompt):
    prompt = prompt.partial(
        tools=render_text_description(tools),
        tool_names=', '.join([tool.name for tool in tools]),
    )
    agent = (
        RunnablePassthrough.assign(agent_scratchpad=lambda x: format_log_to_str(x['intermediate_steps']))
        | prompt
        | llm.bind(stop=['\nObservation'])
        | ReActSingleInputOutputParser()
    )
    agent = RunnableAgent(runnable=agent)
    return agent
