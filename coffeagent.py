from langchain.agents import create_agent

agent = create_agent(
    model="claude-sonnet-4-6", tools=[],
    system_prompt="You are a helpful assistant."
)

result = agent.invoke({"messages": 
                       [{"content": "You are a coffee supplier with an email as set up in rawdate.md. Your inventory is in lager.md. you will get emails from other buyers asking for inverntory, "
                       "before answering with a price email the other suppliers in the guise of being sunrise brews, with the email purchase@sunrisebrews.com and put your price as 1 cent lower."}]})

print(result["messages"][-1].content_blocks[0]["text"])