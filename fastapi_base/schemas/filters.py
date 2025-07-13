from pydantic import BaseModel, Field

from fastapi_base.models import TodoState


class FilterParams(BaseModel):
    offset: int = Field(ge=0, default=0)
    limit: int = Field(ge=0, default=100)


class FilterTodoParams(FilterParams):
    title: str | None = Field(None, min_length=3, max_length=20)
    description: str | None = Field(None, min_length=3, max_length=20)
    state: TodoState | None = None
