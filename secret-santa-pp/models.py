from typing import Literal
from pydantic import BaseModel, EmailStr


class Config(BaseModel):
    people: dict[str, "Person"]
    limits: list["LimitCriterion"]


class Person(BaseModel):
    email: EmailStr
    relationships: dict[str, list[str]] = {}


class LimitCriterion(BaseModel):
    relationship: str
    comparator: Literal["one-way contains", "two-way contains", "equality"]
    limit: Literal["exclude", "low-probability", "medium-probability"]
