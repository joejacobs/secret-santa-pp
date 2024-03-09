import logging
from pathlib import Path
from typing import Optional

import typer

from models import Config, Solution

app = typer.Typer()


@app.command()
def generate_solution(
    config_file_path: Path = typer.Argument(help="Path to the config file."),
    n_recipients: int = typer.Argument(default=1, help="Number of recipients."),
    solution_key: Optional[str] = typer.Argument(
        default=None,
        help=(
            "Relationship key to use when storing the solution in the config "
            "file. If unspecified, we won't store the solution."
        ),
    ),
    display: bool = typer.Argument(
        default=False, help="Plot and display the solution."
    ),
) -> None:
    """Generate a new secret santa solution."""

    logging.info(f"Loading config file: {config_file_path}")
    with config_file_path.open() as fp:
        config = Config.model_validate_json(fp.read())

    logging.info(f"Generating solution ({n_recipients} recipients)")
    solution = Solution.generate(config=config, n_recipients=n_recipients)

    if solution_key is not None:
        logging.info(f"Saving solution (key: {solution_key})")

    if display is True:
        logging.info("Displaying solution")
        solution.display()


@app.command()
def display_solution(
    config_file_path: Path = typer.Argument(help="Path to the config file."),
    solution_key: str = typer.Argument(
        help="The key under which the solution is stored in the config file.",
    ),
) -> None:
    """Visualise an existing santa solution."""

    logging.info(f"Loading config file: {config_file_path}")
    with config_file_path.open() as fp:
        config = Config.model_validate_json(fp.read())

    logging.info(f"Loading solution (key: {solution_key})")
    solution = Solution.load(config=config, solution_key=solution_key)

    logging.info("Displaying solution")
    solution.display()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app()
