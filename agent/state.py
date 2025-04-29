from operator import add
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.agents import AgentAction
from langchain_core.messages import AnyMessage


class GraphState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], add]
