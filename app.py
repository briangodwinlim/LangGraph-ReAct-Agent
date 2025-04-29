import gradio as gr
from agent import graph
from langchain_core.messages import HumanMessage


def invoke_graph(message, history, model, id):
    config = {'configurable': {'thread_id': id, 'model': model}}
    response = graph.invoke({'messages': [HumanMessage(content=message)]}, config=config)
    return response['messages'][-1].log.split('Final Answer:')[-1]


with gr.Blocks(theme=gr.themes.Soft(), title='LangGraph ReAct Agent') as demo:
    gr.HTML('<h1 style="text-align: center; margin-bottom: 1rem">LangGraph ReAct Agent</h1>')
    gr.Markdown('A simple ReAct Agent built with LangGraph')
    conversation_id = gr.State()
    
    model = gr.Dropdown(
        choices=['gemma3:4b', 'gemma3:27b', 'deepseek-r1:8b'],
        label='Model Name',
    )
    chatbot = gr.Chatbot(
        type='messages',
        label='ReAct Agent',
        scale=1,
        autoscroll=True,
        height=400,
        show_copy_button=False,
    )
    textbox = gr.Textbox(
        type='text',
        placeholder='Enter a message',
        label='Message',
        scale=7,
        autofocus=True,
        autoscroll=True,
        submit_btn=True,
        stop_btn=True,
    )
    gr.ChatInterface(
        fn=invoke_graph, 
        type='messages', 
        chatbot=chatbot,
        textbox=textbox,
        additional_inputs=[model, conversation_id],
        editable=False,
        autofocus=True,
        autoscroll=True,
        submit_btn=True,
        stop_btn=True,        
    )


if __name__ == '__main__':
    demo.launch()
