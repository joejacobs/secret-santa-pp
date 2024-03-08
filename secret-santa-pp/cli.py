from pathlib import Path

import typer
from rich.console import Console

from models import Config

app = typer.Typer()
console = Console()


@app.command()
def visualise_graph(config_file_path: Path) -> None:
    with config_file_path.open() as fp:
        config = Config.validate_json(fp.read())

    console.print(config)

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
