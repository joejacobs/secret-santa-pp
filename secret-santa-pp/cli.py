import logging
from pathlib import Path

import networkx as nx
import typer
from matplotlib import pyplot as plt
from rich.console import Console

from models import PeopleGraph

app = typer.Typer()
console = Console()


@app.command()
def visualise_graph(config_file_path: Path) -> None:
    with config_file_path.open() as fp:
        people = PeopleGraph.model_validate_json(fp.read())

    logging.info("INIT")
    people.random_init()

    logging.info("SOLVE")
    people.solve("2023", 3)

    options = {
        "font_size": 36,
        "node_color": "white",
        "edgecolors": "black",
    }
    nx.draw(people.graph, **options)
    plt.show()

    """
    graph = SecretSantaGraph(
        people_data,
        args.n_recipients,
        exclusion_criteria=exclusion,
        low_prob_criteria=low_prob,
        medium_prob_criteria=med_prob,
    )
    """


if __name__ == "__main__":
    app()
