"""
test_agent_basic.py

Manual test script for Capture Intelligence Agent MCP tool integration.
Run this script to test agent responses and debug info for basic database queries.
Delete after successful testing to keep codebase clean.
"""


# Suppress all logging to terminal except WARNING and above
import logging
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
formatter = logging.Formatter('%(levelname)s: %(message)s')
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

import asyncio
from src.frontend.ai.capture_intelligence_agent import CaptureIntelligenceAgent

async def test_agent_basic():
    # Create a fresh agent instance instead of using the cached one
    agent = CaptureIntelligenceAgent()
    await agent.initialize()
    
    # Test: Contract count query
    user_prompt = "How many contracts are in the database?"
    result, debug_info = await agent.chat_async(user_prompt, debug=True)
    print("\n=== Contract Count Test ===")
    print(f"User Prompt: {user_prompt}")
    print(f"Final LLM Response:\n{result}\n")

    # High-level tool call summary
    tool_calls = debug_info.get("tool_calls", [])
    if tool_calls:
        print("--- Tool Calls ---")
        for i, call in enumerate(tool_calls, 1):
            tool_name = call.get("tool_name", "?")
            args = call.get("args", {})
            # Show only the first 100 chars of result for brevity
            result_str = str(call.get("result", ""))
            if len(result_str) > 100:
                result_str = result_str[:100] + "..."
            print(f"{i}. {tool_name}({args}) -> {result_str}")
    else:
        print("--- Tool Calls ---\nNone")

    # # Test: Table schema query
    # user_prompt2 = "Describe the schema for the contracts table."
    # result2, debug_info2 = await agent.chat_async(user_prompt2, debug=True)
    # print("\n=== Table Schema Test ===")
    # print("Agent Response:\n", result2)
    # print("\n--- Debug Info ---")
    # for key, value in debug_info2.items():
    #     print(f"{key}: {value}\n")

    # # Test: Spending trends by agency (last 5 years)
    # user_prompt3 = "Show me a chart of spending trends by agency for the last 5 years."
    # result3, debug_info3 = await agent.chat_async(user_prompt3, debug=True)
    # print("\n=== Spending Trends Test ===")
    # print("Agent Response:\n", result3)
    # print("\n--- Debug Info ---")
    # for key, value in debug_info3.items():
    #     print(f"{key}: {value}\n")

    # # Test: Expiring contracts in next 90 days
    # user_prompt4 = "Which contracts are expiring in the next 90 days?"
    # result4, debug_info4 = await agent.chat_async(user_prompt4, debug=True)
    # print("\n=== Expiring Contracts Test ===")
    # print("Agent Response:\n", result4)
    # print("\n--- Debug Info ---")
    # for key, value in debug_info4.items():
    #     print(f"{key}: {value}\n")

    # # Test: Ambiguous prompt handling
    # user_prompt5 = "Show me the top performers."
    # result5, debug_info5 = await agent.chat_async(user_prompt5, debug=True)
    # print("\n=== Ambiguous Prompt Test ===")
    # print("Agent Response:\n", result5)
    # print("\n--- Debug Info ---")
    # for key, value in debug_info5.items():
    #     print(f"{key}: {value}\n")

if __name__ == "__main__":
    asyncio.run(test_agent_basic())
