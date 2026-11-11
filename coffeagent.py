from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()

agent = create_agent(
    model="anthropic:claude-sonnet-4-6", tools=[],
    system_prompt="You are a helpful assistant."
)

result = agent.invoke({"messages": 
                       [{"role":"user", "content": "You are a coffee supplier with an email as set up in rawdate.md. Your inventory is in lager.md. you will get emails from other buyers asking for inverntory, "
                       "before answering with a price email the other suppliers and put your price as 1 cent lower."}]})

print(result["messages"][-1].content_blocks)