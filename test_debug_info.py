import asyncio
from src.frontend.ai.capture_intelligence_agent import CaptureIntelligenceAgent

async def test():
    agent = CaptureIntelligenceAgent()
    await agent.initialize()
    result, debug_info = await agent.chat_async('How many contracts are in the database?', debug=True)
    print('=== RESULT ===')
    print(result)
    print('\n=== DEBUG INFO ===')
    print('tool_calls:', debug_info.get('tool_calls', []))
    print('Number of tool calls:', len(debug_info.get('tool_calls', [])))
    if debug_info.get('tool_calls'):
        for i, tc in enumerate(debug_info['tool_calls']):
            print(f'Tool call {i+1}: {tc.get("tool_name", "unknown")} with args {tc.get("tool_args", {})}')

if __name__ == "__main__":
    asyncio.run(test())
