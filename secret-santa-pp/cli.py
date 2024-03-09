from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from models import Config, Solution

app = typer.Typer()
console = Console()


@app.command()
def generate_solution(
    config_file_path: Annotated[Path, typer.Argument(help="Path to the config file.")],
    n_recipients: Annotated[int, typer.Option(help="Number of recipients.")] = 1,
    solution_key: Annotated[
        Optional[str],
        typer.Option(
            help=(
                "Relationship key to use when storing the solution in the config "
                "file. If unspecified, we won't store the solution."
            ),
        ),
    ] = None,
    display: Annotated[
        bool, typer.Option(help="Plot and display the solution.")
    ] = False,
) -> None:
    """Generate a new secret santa solution."""

    console.log(f"Loading config file: {config_file_path}")
    with config_file_path.open() as fp:
        config = Config.model_validate_json(fp.read())

    console.log(f"Generating solution ({n_recipients} recipients)")
    solution = Solution.generate(config=config, n_recipients=n_recipients)

    if solution_key is not None:
        console.log(f"Saving solution (key: {solution_key})")

    if display is True:
        console.log("Displaying solution")
        solution.display()


@app.command()
def display_solution(
    config_file_path: Path = typer.Argument(help="Path to the config file."),
    solution_key: str = typer.Argument(
        help="The key under which the solution is stored in the config file.",
    ),
) -> None:
    """Visualise an existing santa solution."""

    console.log(f"Loading config file: {config_file_path}")
    with config_file_path.open() as fp:
        config = Config.model_validate_json(fp.read())

    console.log(f"Loading solution (key: {solution_key})")
    solution = Solution.load(config=config, solution_key=solution_key)

    console.log("Displaying solution")
    solution.display()


if __name__ == "__main__":
    app()
