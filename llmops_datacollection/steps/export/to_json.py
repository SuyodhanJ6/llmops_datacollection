from pathlib import Path

from typing_extensions import Annotated
from zenml import step
import json

@step
def to_json(data: Annotated[dict, "serialized_artifact"], 
           output_path: Annotated[Path, "output_path"]) -> Annotated[Path, "exported_file_path"]:
    """Export data to JSON file.
    
    Args:
        data: Data to export
        output_path: Path to save JSON file
        
    Returns:
        Path: Path to exported JSON file
    """
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write data to JSON file
    with output_path.open('w') as f:
        json.dump(data, f, indent=2)
        
    return output_path