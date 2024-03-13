from typing import Literal

import networkx as nx
from pydantic import BaseModel, EmailStr


class Person(BaseModel):
    name: str
    email: EmailStr
    relationships: dict[str, list[str]] = {}


class Constraint(BaseModel):
    relationship: str
    comparator: Literal["one-way contains", "two-way contains", "equality"]
    limit: Literal["exclude", "low-probability", "medium-probability"]

    def meet_criterion(self, src_person: Person, dst_person: Person) -> bool:
        if (
            src_relationship := src_person.relationships.get(self.relationship)
        ) is None:
            return False

        dst_relationship = dst_person.relationships.get(self.relationship, [])

        if self.comparator == "equality":
            return src_relationship == dst_relationship

        meet_criterion = dst_person.name in src_relationship

        if self.comparator == "two-way contains":
            meet_criterion |= src_person.name in dst_relationship

        return meet_criterion


class Config(BaseModel):
    people: list[Person]
    constraints: list[Constraint]

    def update_with_graph(self, graph: nx.DiGraph, key: str) -> None:
        for person in self.people:
            person.relationships[key] = list(graph[person.name])

    def load_graph(self, key: str) -> nx.DiGraph:
        graph = nx.DiGraph()
        for person in self.people:
            if (recipients := person.relationships.get(key)) is not None:
                for recipient in recipients:
                    graph.add_edge(person.name, recipient)

        return graph
