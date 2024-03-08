from typing import Literal
from pydantic import BaseModel, EmailStr, TypeAdapter


class Person(BaseModel):
    email: EmailStr
    relationships: list[tuple[str, str]] = []


class LimitCriterion(BaseModel):
    relationship: str
    comparator: Literal["one-way contains", "two-way contains", "equality"]
    limit: Literal["exclude", "low-probability", "medium-probability"]


People = TypeAdapter(dict[str, Person])
LimitCriteria = TypeAdapter(list[LimitCriterion])
