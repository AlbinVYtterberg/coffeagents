from langchain.agents import create_agent
agent = create_agent(
    model="claude-sonnet-4-6", tools=[...],
    system_prompt="You are a helpful assistant."
)
result = agent.invoke({"messages": [{"content": "<PROMPT>"}]})
print(result["messages"][-1].content_blocks[0]["text"])


you sell stuff to cafe:s
Using langchain, set up an agent that:
- sees its storage in lager.md 