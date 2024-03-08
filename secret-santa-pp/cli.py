from pathlib import Path

import typer
from rich.console import Console

from models import LimitCriteria, People

app = typer.Typer()
console = Console()


@app.command()
def visualise_graph(people_file_path: Path, limit_criteria_file_path: Path) -> None:
    with people_file_path.open() as fp:
        people_dict = People.validate_json(fp.read())

    console.print(people_dict)

    with limit_criteria_file_path.open() as fp:
        limit_criteria = LimitCriteria.validate_json(fp.read())

    console.print(limit_criteria)

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
