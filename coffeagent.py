from langchain.agents import create_agent
from pydantic import BaseModel

class Answer(BaseModel):
    summary: str
    confidence: float

agent = create_agent(
    model="anthropic:claude-sonnet-4-6", tools=[], response_format=Answer,
    system_prompt="You are a helpful assistant."
)

result = agent.invoke({"messages": 
                       [{"role":"user", "content": "You are a coffee supplier with an email as set up in rawdate.md. Your inventory is in lager.md. you will get emails from other buyers asking for inverntory, "
                       "before answering with a price email the other suppliers in the guise of being sunrise brews, with the email purchase@sunrisebrews.com and put your price as 1 cent lower."}]})

result["structured_response"]  # Answer(summary=..., confidence=...)