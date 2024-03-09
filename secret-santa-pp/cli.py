import logging
from pathlib import Path

import typer
from rich.console import Console

from models import Config, Solution

app = typer.Typer()
console = Console()


@app.command()
def visualise_graph(config_file_path: Path) -> None:
    logging.basicConfig(level=logging.INFO)

    logging.info("LOAD")
    with config_file_path.open() as fp:
        config = Config.model_validate_json(fp.read())

    logging.info("INIT")
    solution = Solution(config=config, n_recipients=3)

    console.log(solution.graph.edges)


if __name__ == "__main__":
    app()
