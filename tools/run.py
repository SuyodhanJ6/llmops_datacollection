"""CLI tool for running ZenML pipelines."""

from datetime import datetime as dt
from pathlib import Path

import click
from loguru import logger

from llmops_datacollection import settings
from llmops_datacollection.pipelines import data_collection, export_artifacts


@click.command(
    help="""
LLMOps Data Collection CLI v0.1.0

Main entry point for pipeline execution.
Run ZenML pipelines for data collection and artifact export.

Examples:

  # Run data collection pipeline
  python -m tools.run --run-data-collection

  # Run data collection without cache
  python -m tools.run --run-data-collection --no-cache

  # Run artifact export
  python -m tools.run --run-export-artifacts
"""
)
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Disable caching for pipeline run"
)
@click.option(
    "--run-data-collection",
    is_flag=True,
    default=False,
    help="Run data collection pipeline"
)
@click.option(
    "--data-collection-config",
    default="data_collection.yaml",
    help="Data collection config filename"
)
@click.option(
    "--run-export-artifacts",
    is_flag=True,
    default=False,
    help="Run artifact export pipeline"
)
@click.option(
    "--export-config",
    default="export_artifacts.yaml", 
    help="Export config filename"
)
@click.option(
    "--export-settings",
    is_flag=True,
    default=False,
    help="Export settings to ZenML"
)
def main(
    no_cache: bool = False,
    run_data_collection: bool = False,
    data_collection_config: str = "data_collection.yaml",
    run_export_artifacts: bool = False,
    export_config: str = "export_artifacts.yaml",
    export_settings: bool = False,
) -> None:
    """Run ZenML pipelines for data collection."""
    assert (
        run_data_collection or
        run_export_artifacts or
        export_settings
    ), "Please specify an action to run"

    if export_settings:
        logger.info("Exporting settings to ZenML secrets")
        settings.export()
        return

    # Common pipeline arguments
    pipeline_args = {
        "enable_cache": not no_cache,
    }
    root_dir = Path(__file__).resolve().parent.parent

    if run_data_collection:
        # Run data collection pipeline
        pipeline_args["config_path"] = root_dir / "configs" / data_collection_config
        assert pipeline_args["config_path"].exists(), f"Config file not found: {pipeline_args['config_path']}"

        pipeline_args["run_name"] = f"data_collection_run_{dt.now().strftime('%Y_%m_%d_%H_%M_%S')}"

        data_collection.with_options(**pipeline_args)()
        logger.info("Data collection pipeline completed")

    if run_export_artifacts:
        # Run export artifacts pipeline
        pipeline_args["config_path"] = root_dir / "configs" / export_config
        assert pipeline_args["config_path"].exists(), f"Config file not found: {pipeline_args['config_path']}"

        pipeline_args["run_name"] = f"export_artifacts_run_{dt.now().strftime('%Y_%m_%d_%H_%M_%S')}"

        export_artifacts.with_options(**pipeline_args)()
        logger.info("Export artifacts pipeline completed")


if __name__ == "__main__":
    main()