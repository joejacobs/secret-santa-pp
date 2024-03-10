from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Literal

import networkx as nx
from matplotlib import pyplot as plt
from pydantic import BaseModel, ConfigDict, EmailStr


class Person(BaseModel):
    name: str
    email: EmailStr
    relationships: dict[str, list[str]] = {}


class Constraint(BaseModel):
    relationship: str
    comparator: Literal["one-way contains", "two-way contains", "equality"]
    limit: Literal["exclude", "low-probability", "medium-probability"]

    def meet_criterion(self, src_person: Person, dst_person: Person) -> bool:
        src_relationship = src_person.relationships.get(self.relationship)
        if src_relationship is None:
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


def tsp_solver(graph: nx.DiGraph, weight: str) -> list[str]:
    return nx.approximation.simulated_annealing_tsp(
        graph, "greedy", weight=weight, max_iterations=100, N_inner=1000
    )


class Solution(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: Config
    n_recipients: int
    graph: nx.DiGraph = nx.DiGraph()

    @classmethod
    def generate(cls, config: Config, n_recipients: int) -> "Solution":
        solution = cls(config=config, n_recipients=n_recipients)
        solution._init_graph()
        solution._generate_solution()
        return solution

    @classmethod
    def load(cls, config: Config, solution_key: str) -> "Solution":
        graph = config.load_graph(solution_key)
        if len(graph.edges) == 0:
            msg = f"Solution key not found: {solution_key}."
            raise LookupError(msg)

        return cls(
            graph=graph,
            config=config,
            n_recipients=len(graph[list(graph.nodes)[0]]),
        )

    def _init_graph(self) -> None:
        n_people = len(self.config.people)
        for id1 in range(n_people):
            person1 = self.config.people[id1]

            for id2 in range(id1 + 1, n_people):
                person2 = self.config.people[id2]

                if (weight := self._get_edge_weight(person1, person2)) > 0:
                    self.graph.add_edge(person1.name, person2.name, weight=weight)

                if (weight := self._get_edge_weight(person2, person1)) > 0:
                    self.graph.add_edge(person2.name, person1.name, weight=weight)

    def _get_edge_weight(self, src_person: Person, dst_person: Person) -> int:
        weight = 1

        if len(src_person.relationships) == 0:
            return weight

        for constraint in self.config.constraints:
            if constraint.meet_criterion(src_person, dst_person):
                if constraint.limit == "exclude":
                    return -1

                if constraint.limit == "low-probability":
                    weight += 4
                elif constraint.limit == "medium-probability":
                    weight += 2

        return weight

    def _generate_solution(self) -> None:
        final_graph = nx.DiGraph()
        init_graph = deepcopy(self.graph)
        for _ in range(self.n_recipients):
            tsp_path = nx.approximation.traveling_salesman_problem(
                deepcopy(init_graph), cycle=True, method=tsp_solver
            )

            for src, dst in zip(tsp_path[:-1], tsp_path[1:]):
                final_graph.add_edge(src, dst, weight=self.graph[src][dst]["weight"])
                init_graph.remove_edge(src, dst)

        for node in final_graph.nodes:
            if (
                final_graph.in_degree(node) != self.n_recipients
                or final_graph.out_degree(node) != self.n_recipients
            ):
                msg = f"Invalid solution: {final_graph.edges}"
                raise RuntimeError(msg)

        self.graph = final_graph

    def display(self) -> None:
        pos = nx.shell_layout(self.graph)
        nx.draw(self.graph, pos, node_size=1000, font_size=16)
        nx.draw_networkx_labels(self.graph, pos)
        plt.show()


class TemplateManager(BaseModel):
    common_template_data: dict[str, str] = {}

    def __init__(
        self,
        event_name: str | None = None,
        event_date: date | None = None,
    ) -> None:
        common_template_data = {
            "days_to_christmas": self._get_days_delta_text(
                self._get_christmas_date(), "Christmas"
            ),
            "year": f"{date.today().year}",
        }

        if event_name is not None:
            common_template_data["event_name"] = event_name

        if event_date is not None:
            common_template_data["event_date"] = event_date.strftime("%A, %d %B %Y")

        if event_name is not None and event_date is not None:
            common_template_data["days_to_event"] = self._get_days_delta_text(
                event_date, event_name
            )

        super().__init__(common_template_data=common_template_data)

    def _get_days_delta_text(self, event_date: date, event_name: str) -> str:
        days_delta = (event_date - date.today()).days
        return f"{days_delta} days to {event_name}"

    def _get_christmas_date(self) -> date:
        return date(self._get_current_year(), 12, 25)

    def _get_current_year(self) -> int:
        return date.today().year

    def populate(
        self,
        template_data: dict[str, str],
        text: str,
    ) -> str:
        combined_template_data = template_data | self.common_template_data
        return text.format(**combined_template_data)


class EmailMessage(BaseModel):
    subject: str
    message_html: str | None
    message_text: str | None
    template_manager: TemplateManager

    def __init__(
        self,
        template_manager: TemplateManager,
        subject: str,
        html_template: Path | None,
        text_template: Path | None,
    ) -> None:
        message_html = None
        if html_template is not None:
            with html_template.open() as fp:
                message_html = fp.read()

        message_text = None
        if text_template is not None:
            with text_template.open() as fp:
                message_text = fp.read()

        if message_html is None and message_text is None:
            msg = "Either HTML Template or Text Template must be specified"
            raise RuntimeError(msg)

        super().__init__(
            template_manager=template_manager,
            subject=subject,
            message_html=message_html,
            message_text=message_text,
        )

    def get_subject(self, template_data: dict[str, str]) -> str:
        return self.template_manager.populate(template_data, self.subject)

    def get_message_html(self, template_data: dict[str, str]) -> str | None:
        return (
            None
            if self.message_html is None
            else self.template_manager.populate(template_data, self.message_html)
        )

    def get_message_text(self, template_data: dict[str, str]) -> str | None:
        return (
            None
            if self.message_text is None
            else self.template_manager.populate(template_data, self.message_text)
        )
