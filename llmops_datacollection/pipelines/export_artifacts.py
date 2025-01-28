from pathlib import Path

from zenml import pipeline
from zenml.client import Client

from llmops_datacollection.steps.export import serialize_artifact, to_json

@pipeline
def export_artifacts(artifact_names: list[str], output_dir: Path = Path("output")) -> None:
    """Export artifacts to JSON files.
    
    Args:
        artifact_names: Names of artifacts to export
        output_dir: Directory to save JSON files
    """
    for artifact_name in artifact_names:
        # Get artifact
        artifact = Client().get_artifact_version(name_id_or_prefix=artifact_name)
        
        # Serialize artifact data
        data = serialize_artifact(artifact=artifact, artifact_name=artifact_name)
        
        # Export to JSON
        to_json(data=data, output_path=output_dir / f"{artifact_name}.json")