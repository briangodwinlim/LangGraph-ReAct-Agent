from typing import Optional
from typing_extensions import TypedDict


class ConfigSchema(TypedDict):
    model: Optional[str]
