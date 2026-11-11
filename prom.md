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
- send mail to other suppliers (suppliers.md) to figure out their price
- set prices to a fractionally lower price then the other suppliers
- receive mail from cafe (cafe.md is the only ok mailadresses), give them a price suggestion that is fractionally lower then the lowest other supplier
- when cafe buys from us, note how much they bought, who bought it, when, and what price
- calculate earnings

- keep checking the other suppliers prices
- never sell below our buy-price
