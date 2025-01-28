from typing import Any

from pydantic import BaseModel
from typing_extensions import Annotated
from zenml import get_step_context, step

@step
def serialize_artifact(artifact: Any, artifact_name: str) -> Annotated[dict, "serialized_artifact"]:
    """Serialize artifact to dictionary format.
    
    Args:
        artifact: Artifact to serialize
        artifact_name: Name of artifact
        
    Returns:
        dict: Serialized artifact data
    """
    serialized_artifact = _serialize_artifact(artifact)

    if serialize_artifact is None:
        raise ValueError("Artifact is None")
    elif not isinstance(serialized_artifact, dict):
        serialized_artifact = {"artifact_data": serialized_artifact}

    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="serialized_artifact", 
        metadata={"artifact_name": artifact_name}
    )

    return serialized_artifact

def _serialize_artifact(artifact: list | dict | BaseModel | str | int | float | bool | None):
    """Recursively serialize artifact data.
    
    Args:
        artifact: Data to serialize
        
    Returns:
        Serialized data in basic Python types
    """
    if isinstance(artifact, list):
        return [_serialize_artifact(item) for item in artifact]
    elif isinstance(artifact, dict):
        return {key: _serialize_artifact(value) for key, value in artifact.items()}
    elif isinstance(artifact, BaseModel):
        return artifact.model_dump()
    else:
        return artifact