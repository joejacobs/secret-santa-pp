import copy
import io
import json
from collections import Counter

import networkx
import numpy as np
import openopt
import random
from matplotlib import pyplot as plt

from models import People, Person


def _solve_tsp(graph):
    prob = openopt.TSP(graph)
    soln = prob.solve("sa")
    return soln


def _validate_criteria(criteria):
    valid_criteria_types = ["1-way contains", "2-way contains", "equality"]

    for _, c_type in criteria:
        assert c_type in valid_criteria_types


class SecretSantaGraph(object):
    _medium_prob_criteria = None
    _exclusion_criteria = None
    _low_prob_criteria = None
    _n_recipients = None
    _people_data = None
    _ss_graph = None

    def __init__(
        self,
        people_data: People,
        n_recipients,
        exclusion_criteria=[],
        low_prob_criteria=[],
        medium_prob_criteria=[],
    ):
        # validate inputs
        assert n_recipients > 0
        assert people_data

        for name in people_data:
            assert "email" in people_data[name]

        _validate_criteria(medium_prob_criteria)
        _validate_criteria(exclusion_criteria)
        _validate_criteria(low_prob_criteria)

        # store for later use if everything is good
        self._medium_prob_criteria = medium_prob_criteria
        self._exclusion_criteria = exclusion_criteria
        self._low_prob_criteria = low_prob_criteria
        self._n_recipients = n_recipients
        self._people_data = people_data

    def _criteria_met(self, c_key, c_type, name1, name2):
        people = self._people_data

        if "contains" in c_type:
            # "1-way contains" and "2-way contains" criteria
            if c_key in people[name1] and name2 in people[name1][c_key]:
                return True
            elif "2-way" in c_type:
                # "2-way contains" criteria
                if c_key in people[name2] and name1 in people[name2][c_key]:
                    return True
        elif "equality" in c_type:
            # "equality" criteria
            if c_key in people[name1] and c_key in people[name2]:
                if people[name1][c_key] == people[name2][c_key]:
                    return True

        return False

    def _generate_rand_graph(self, participants):
        # participants must not be empty
        assert participants

        # all participants must be in the people data dictionary
        for name in participants:
            assert name in self._people_data

        # copy and shuffle list of participants
        nodes = copy.deepcopy(participants)
        random.shuffle(nodes)
        edges = []

        # generate edges with random weights
        for name1 in nodes:
            for name2 in nodes:
                # we don't need to create self-linking nodes
                if name1 == name2:
                    continue

                add = True
                weight = random.randint(1, 10)

                # exclude edge if necessary
                for c_key, c_type in self._exclusion_criteria:
                    if self._criteria_met(c_key, c_type, name1, name2):
                        add = False

                # increase edge weight as necessary
                if add:
                    for c_key, c_type in self._low_prob_criteria:
                        if self._criteria_met(c_key, c_type, name1, name2):
                            weight += random.randint(20, 40)

                    for c_key, c_type in self._medium_prob_criteria:
                        if self._criteria_met(c_key, c_type, name1, name2):
                            weight += random.randint(5, 10)

                    # store edge
                    edges.append((name1, name2, weight))

        # construct weighted directed graph
        rand_graph = networkx.DiGraph()
        rand_graph.add_nodes_from(nodes)
        rand_graph.add_weighted_edges_from(edges)

        for node in rand_graph.nodes_iter():
            # ensure the number of edges in/out of a node is at least the
            # number of recipients
            assert rand_graph.in_degree(node) >= self._n_recipients
            assert rand_graph.out_degree(node) >= self._n_recipients

            # all in/out edges must be to unique nodes
            edges = rand_graph.out_edges(node)
            counter = Counter([edge[1] for edge in edges])
            assert np.all(np.array(list(counter.values())) == 1)

        return rand_graph

    def _verify_solution(self):
        assert self._ss_graph

        for node in self._ss_graph.nodes_iter():
            # we must have the right number of in and out edges for each node
            assert self._ss_graph.in_degree(node) == self._n_recipients
            assert self._ss_graph.out_degree(node) == self._n_recipients

            # all in/out edges must be to unique nodes
            edges = self._ss_graph.out_edges(node)
            counter = Counter([edge[1] for edge in edges])
            assert np.all(np.array(list(counter.values())) == 1)

        # ensure all exclusion criteria are met
        for u, v in self._ss_graph.edges_iter():
            for c_key, c_type in self._exclusion_criteria:
                assert not self._criteria_met(c_key, c_type, u, v)

    def add_to_people_data(self, key):
        assert self._ss_graph

        for gifter in self._ss_graph.nodes_iter():
            edges = self._ss_graph.out_edges(gifter)
            self._people_data[gifter][key] = [edge[1] for edge in edges]

        return self._people_data

    def draw_solution(self):
        assert self._ss_graph

        nodes = self._ss_graph.nodes()
        labels = {n: n for n in nodes}

        pos = networkx.shell_layout(self._ss_graph)
        networkx.draw_networkx_nodes(self._ss_graph, pos)
        networkx.draw_networkx_labels(self._ss_graph, pos, labels=labels)
        networkx.draw_networkx_edges(self._ss_graph, pos)

        plt.show()

    def get_solution_arr(self):
        assert self._ss_graph
        out_lst = []

        for gifter in self._ss_graph.nodes_iter():
            out_edges = self._ss_graph.out_edges(gifter)
            recipients = [e[1] for e in out_edges]
            out_lst.append((gifter, recipients))

        return out_lst

    def load_solution(self, fpath):
        assert not self._ss_graph

        with io.open(fpath, mode="r", encoding="utf-8") as fp:
            d = json.load(fp)

        self._ss_graph = networkx.DiGraph()
        self._ss_graph.add_nodes_from(d["nodes"])
        self._ss_graph.add_weighted_edges_from(d["edges"])
        self._verify_solution()

    def run_solver(self, participants):
        assert not self._ss_graph

        # generate random graph
        rand_graph = self._generate_rand_graph(participants)

        # run tsp solver once to get 1 recipient for everyone
        soln = _solve_tsp(copy.deepcopy(rand_graph))

        # add soln edges to secret santa solution graph
        self._ss_graph = networkx.DiGraph()
        self._ss_graph.add_nodes_from(soln.nodes)
        self._ss_graph.add_edges_from(soln.Edges)

        for _ in range(self._n_recipients - 1):
            # generate another temporary graph (removing edges that are already
            # in the secret santa solution) and solve it to get more recipients
            tmp_rand_graph = networkx.DiGraph()
            tmp_rand_graph.add_nodes_from(rand_graph.nodes())

            for u, v in rand_graph.edges_iter():
                # don't add edge if it exists in the secret santa solution
                if self._ss_graph.has_edge(u, v):
                    continue

                # get weight and add edge to temporary graph
                weight = rand_graph.get_edge_data(u, v)
                tmp_rand_graph.add_edge(u, v, weight)

            soln = _solve_tsp(tmp_rand_graph)
            self._ss_graph.add_edges_from(soln.Edges)

        self._verify_solution()

    def save_solution(self, fpath):
        assert self._ss_graph

        d = {}
        d["nodes"] = self._ss_graph.nodes()
        d["edges"] = self._ss_graph.edges(data=True)

        with io.open(fpath, mode="w+", encoding="utf-8") as fp:
            json.dump(d, fp)
