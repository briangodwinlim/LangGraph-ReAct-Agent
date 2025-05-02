import inspect
import requests
import argparse
from typing import Any, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools.base import Tool
from pydantic import BaseModel, Field, create_model
from mcp.server.fastmcp.utilities.func_metadata import ArgModelBase, FuncMetadata


class MCPOServer:
    def __init__(self, url):
        self.url = url.strip('/')
        response = requests.get(self.url + '/openapi.json')
        response.raise_for_status()
        self.spec = response.json()
        self.created_models = {}

    def resolve_schema_ref(self, ref):
        node = self.spec
        for part in ref.lstrip('#/').split('/'):
            node = node.get(part)
            if node is None:
                raise ValueError(f'Reference {ref} not found in spec')
        return node

    def schema_to_fields(self, name, schema):
        if '$ref' in schema:
            schema = self.resolve_schema_ref(schema['$ref'])
            
        if schema.get('type') == 'object':
            model_name = f'{name}_object'
            if model_name not in self.created_models:
                fields = {}
                for prop, prop_schema in schema.get('properties', {}).items():
                    field_type, default = self.schema_to_fields(prop, prop_schema)
                    required = prop in schema.get('required', [])
                    fields[prop] = (field_type, Field(... if required else default, description=prop_schema.get('description')))
                self.created_models[model_name] = create_model(model_name, **fields, __base__=ArgModelBase)
            return self.created_models[model_name], Field(..., description=schema.get('description'))
        
        elif schema.get('type') == 'array':
            item_schema = schema.get('items', {})
            item_type, _ = self.schema_to_fields(f'{name}_item', item_schema)
            default = schema.get('default', [])
            return List[item_type], Field(default, description=schema.get('description'))
        
        else:
            TYPE_MAP = {'string': str, 'integer': int, 'number': float, 'boolean': bool}
            py_type = TYPE_MAP.get(schema.get('type'), Any)
            if (not schema.get('nullable', False)) and (name not in schema.get('required', [])):
                py_type = Optional[py_type]
            default = schema.get('default')
            return py_type, Field(default, description=schema.get('description'))

    def serialize_payload(self, data):
        if isinstance(data, BaseModel):
            return data.model_dump()
        elif isinstance(data, list):
            return [self.serialize_payload(i) for i in data]
        elif isinstance(data, dict):
            return {k: self.serialize_payload(v) for k, v in data.items()}
        else:
            return data

    def create_function(self, path, method):
        def fn(**payload):
            headers = {'Content-Type': 'application/json'}
            payload = self.serialize_payload(payload)
            response = requests.request(method, self.url + path, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        return fn

    def get_mcp_tools(self):
        server_tools = {}
        for path, methods in self.spec.get('paths', {}).items():
            for method, info in methods.items():
                schema = info.get('requestBody', {}).get('content', {}).get('application/json', {}).get('schema')
                
                if not schema:
                    continue

                fn = self.create_function(path, method)
                is_async = inspect.iscoroutinefunction(fn)
                tool_id = info.get('operationId') or path.strip('/')
                request_model, _ = self.schema_to_fields(path.strip('/'), schema)
                request_model.__name__ = f'{path.strip('/').replace('/', '_')}_{method}_request'
                fn_metadata = FuncMetadata(arg_model=request_model)
                parameters = fn_metadata.arg_model.model_json_schema()
                server_tools[tool_id] = Tool(
                    fn=fn,
                    name=tool_id,
                    description=info['description'],
                    parameters=parameters,
                    fn_metadata=fn_metadata,
                    is_async=is_async,
                    context_kwarg=None,
                )
                                
        return server_tools


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(
        'MCP HTTP-SSE server wrapping MCPO',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    argparser.add_argument('--mcpo-url', type=str, default='http://localhost:8000/time', help='MCPO server url')
    argparser.add_argument('--name', type=str, default='MCPO proxy HTTP-SSE server', help='MCP server name')
    argparser.add_argument('--host', type=str, default='0.0.0.0', help='MCP server host')
    argparser.add_argument('--port', type=int, default=8001, help='MCP server port number')
    args = argparser.parse_args()
    
    mcp = FastMCP(args.name)
    mcp.settings.host = args.host
    mcp.settings.port = args.port

    server_tools = MCPOServer(args.mcpo_url).get_mcp_tools()
    for tool in server_tools.values():
        mcp._tool_manager._tools[tool.name] = tool

    mcp.run(transport='sse')
