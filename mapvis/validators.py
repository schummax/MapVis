"""Input validation functions for MapVis."""

from typing import Dict, Any


def validate_mapping_dict(mapping: Any, name: str) -> None:
    """Validate that input is a proper mapping dictionary."""
    if not isinstance(mapping, dict):
        raise TypeError(
            f"{name} must be a dictionary, got {type(mapping).__name__}")

    if not mapping:
        raise ValueError(f"{name} cannot be empty")

    for key, value in mapping.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError(f"All keys and values in {name} must be strings")

        if not key.strip() or not value.strip():
            raise ValueError(f"Empty keys or values not allowed in {name}")


def validate_celltype_mappings(dataset1_mapping: Dict[str, str],
                               dataset2_mapping: Dict[str, str]) -> None:
    """Validate celltype mapping inputs."""
    validate_mapping_dict(dataset1_mapping, "dataset1_mapping")
    validate_mapping_dict(dataset2_mapping, "dataset2_mapping")

    # Check that consensus labels are consistent
    consensus1 = set(dataset1_mapping.values())
    consensus2 = set(dataset2_mapping.values())

    if not consensus1.intersection(consensus2):
        raise ValueError("No common consensus labels found between datasets")


def validate_feature_mappings(dataset1_mapping: Dict[str, str],
                              dataset2_mapping: Dict[str, str]) -> None:
    """Validate feature mapping inputs."""
    validate_mapping_dict(dataset1_mapping, "dataset1_mapping")
    validate_mapping_dict(dataset2_mapping, "dataset2_mapping")
