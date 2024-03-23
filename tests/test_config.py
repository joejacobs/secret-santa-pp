from dataclasses import dataclass

from networkx import DiGraph
import pytest

from secret_santa_pp.config import ComparatorType

from tests.helper.config import MockConfig, MockConstraint, MockPerson


@dataclass
class RelationshipParams:
    relationships1: dict[str, list[str]]
    relationships2: dict[str, list[str]]


@pytest.mark.parametrize(
    ("relationship_params", "comparator", "expected_result"),
    [
        *[
            (relationship_params, comparator, False)
            for comparator in [
                "one-way contains",
                "two-way contains",
                "either contains",
                "equality",
            ]
            for relationship_params in [
                # empty relationships
                RelationshipParams(relationships1={}, relationships2={}),
                # relationship missing from one
                RelationshipParams(relationships1={}, relationships2={"key": []}),
                RelationshipParams(relationships1={"key": []}, relationships2={}),
                RelationshipParams(
                    relationships1={"other-key": []}, relationships2={"key": []}
                ),
                RelationshipParams(
                    relationships1={"key": []}, relationships2={"other-key": []}
                ),
                # relationships missing from both
                RelationshipParams(
                    relationships1={"other-key": []}, relationships2={"other-key": []}
                ),
                # both relationships empty
                RelationshipParams(
                    relationships1={"key": []}, relationships2={"key": []}
                ),
            ]
        ],
        # one-way contains relationship
        *[
            (
                relationship_tuple,
                comparator,
                comparator in ["one-way contains", "either contains"],
            )
            for comparator in [
                "one-way contains",
                "two-way contains",
                "either contains",
                "equality",
            ]
            for relationship_tuple in [
                RelationshipParams(
                    relationships1={
                        "key": ["person-2", "person-3"],
                        "other-key": ["person-3"],
                    },
                    relationships2={"other-key": ["person-2"]},
                ),
                RelationshipParams(
                    relationships1={
                        "key": ["person-2", "person-3"],
                        "other-key": ["person-3"],
                    },
                    relationships2={"key": [], "other-key": ["person-3"]},
                ),
                RelationshipParams(
                    relationships1={
                        "key": ["person-2", "person-3"],
                        "other-key": ["person-3"],
                    },
                    relationships2={"key": ["person-3"], "other-key": ["person-3"]},
                ),
            ]
        ],
        # two-way contains relationship
        *[
            (
                relationship_tuple,
                comparator,
                comparator
                in ["one-way contains", "two-way contains", "either contains"],
            )
            for comparator in [
                "one-way contains",
                "two-way contains",
                "either contains",
                "equality",
            ]
            for relationship_tuple in [
                RelationshipParams(
                    relationships1={
                        "key": ["person-2", "person-3"],
                        "other-key": ["person-3"],
                    },
                    relationships2={
                        "key": ["person-1", "person-3"],
                        "other-key": ["person-3"],
                    },
                )
            ]
        ],
        # equality relationship
        *[
            (relationship_tuple, comparator, comparator == "equality")
            for comparator in [
                "one-way contains",
                "two-way contains",
                "either contains",
                "equality",
            ]
            for relationship_tuple in [
                RelationshipParams(
                    relationships1={
                        "key": ["person-3", "person-4"],
                        "other-key": ["person-2"],
                    },
                    relationships2={
                        "key": ["person-3", "person-4"],
                        "other-key": ["person-1"],
                    },
                )
            ]
        ],
    ],
)
def test_constraint_meet_criterion(
    relationship_params: RelationshipParams,
    comparator: ComparatorType,
    expected_result: bool,
):
    person1 = MockPerson(
        name="person-1", relationships=relationship_params.relationships1
    ).get_model()
    person2 = MockPerson(
        name="person-2", relationships=relationship_params.relationships2
    ).get_model()

    constraint = MockConstraint(
        relationship_key="key", comparator=comparator
    ).get_model()

    assert constraint.meet_criterion(person1, person2) == expected_result


def test_config_update_from_graph():
    config = MockConfig(
        people=[
            MockPerson(name=str(i), relationships={"key": ["99"]}) for i in range(10)
        ]
    ).get_model()

    path = [str(i) for i in range(5)] + [str(i) for i in range(2)]
    src_dst_list_map = {
        i: [j, k] for i, j, k in zip(path[:-2], path[1:-1], path[2:], strict=True)
    }

    graph: DiGraph[str] = DiGraph()
    for src, dst_list in src_dst_list_map.items():
        for dst in dst_list:
            graph.add_edge(src, dst)  # pyright: ignore [reportUnknownMemberType]

    config.update_from_graph(graph, "new-key")

    for person in config.people:
        if (dst_list := src_dst_list_map.get(person.name)) is None:
            assert "new-key" not in person.relationships
        else:
            assert person.relationships["new-key"] == dst_list


def test_config_load_graph():
    path = [str(i) for i in range(5)] + [str(i) for i in range(2)]
    src_dst_list_map = {
        i: [j, k] for i, j, k in zip(path[:-2], path[1:-1], path[2:], strict=True)
    }

    config = MockConfig(
        people=[
            *[
                MockPerson(
                    name=str(i),
                    relationships={
                        "key": ["99"],
                        "graph-key": src_dst_list_map.get(str(i), []),
                    },
                )
                for i in range(10)
            ],
            *[
                MockPerson(name=str(i), relationships={"key": ["99"]})
                for i in range(10, 15)
            ],
        ]
    ).get_model()

    graph = config.load_graph("graph-key")

    assert len(graph.nodes) == len(src_dst_list_map)
    for node in graph.nodes:
        assert list(graph[node]) == src_dst_list_map[node]
