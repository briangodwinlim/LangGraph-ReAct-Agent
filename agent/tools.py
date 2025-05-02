from langchain.tools import tool
from langchain_core.tools import Tool
from langchain_mcp_adapters.client import MultiServerMCPClient


@tool()
def greet_user(name: str) -> str:    
    '''Greets the user by name.'''
    return f'Hello {name}!'


def get_current_time(*args, **kwargs):
    import datetime
    now = datetime.datetime.now()
    return now.strftime('%I:%M %p')


TOOLS = [
    Tool(
        name='Time',
        func=get_current_time,
        description='Useful for when you need to know the current time.',
    ),
    greet_user,
]


# if __name__ == '__main__':
#     import asyncio
    
#     # run `python ../mcpo.py` with time tools in mcpo server
#     async def main():
#         async with MultiServerMCPClient(
#             {
#                 'time': {
#                     'url': 'http://localhost:8001/sse',
#                     'transport': 'sse',
#                 }
#             }
#         ) as client:
#             time_tools = client.get_tools()
#             result = await time_tools[0].ainvoke(input={'timezone': 'Asia/Tokyo'})  # tool_get_current_time_post
#             print(result)
    
#     asyncio.run(main())
