from typing import Annotated, List
from pydantic import BaseModel, Field
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

class CandidateState(BaseModel):
    turn_count:int = Field(default=0)
    messages: Annotated[List[BaseMessage], add_messages] = Field(default_factory=list)
    strengths:str = Field(default="")
    weaknesses:str = Field(default="")
