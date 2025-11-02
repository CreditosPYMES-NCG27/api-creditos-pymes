from typing import Generic, Literal, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    sort: str | None = None
    order: Literal["asc", "desc"] = "desc"


class PaginationMeta(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    meta: PaginationMeta


def pagination_params(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort: str | None = Query(None),
    order: Literal["asc", "desc"] = Query("desc", pattern="^(asc|desc)$"),
) -> PaginatedParams:
    return PaginatedParams(page=page, limit=limit, sort=sort, order=order)
