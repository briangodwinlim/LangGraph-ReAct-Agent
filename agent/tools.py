from langchain.tools import tool
from langchain_core.tools import Tool


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
