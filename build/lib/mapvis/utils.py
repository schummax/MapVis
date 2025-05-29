"""Utility functions for MapVis."""

import csv
from typing import Dict, List, Tuple
from pathlib import Path


def load_mapping_from_csv(filepath: str,
                          source_col: str = "source",
                          target_col: str = "target",
                          delimiter: str = ',') -> Dict[str, str]:
    """
    Load mapping dictionary from CSV/TSV file.

    Args:
        filepath: Path to CSV/TSV file
        source_col: Column name for source labels
        target_col: Column name for target/consensus labels
        delimiter: Delimiter character (',' for CSV, '\t' for TSV)

    Returns:
        Dictionary mapping source to target labels
    """
    mapping = {}
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delimiter)

        if source_col not in reader.fieldnames or target_col not in reader.fieldnames:
            raise ValueError(
                f"Required columns '{source_col}' and/or '{target_col}' not found in file")

        for row in reader:
            mapping[row[source_col].strip()] = row[target_col].strip()

    return mapping


def load_mapping_from_tsv(filepath: str,
                          source_col: str = "source",
                          target_col: str = "target") -> Dict[str, str]:
    """
    Convenience function to load mapping from TSV file.

    Args:
        filepath: Path to TSV file
        source_col: Column name for source labels
        target_col: Column name for target/consensus labels

    Returns:
        Dictionary mapping source to target labels
    """
    return load_mapping_from_csv(filepath, source_col, target_col, delimiter='\t')


def get_consensus_mapping(dataset1_mapping: Dict[str, str],
                          dataset2_mapping: Dict[str, str]) -> Dict[str, Tuple[List[str], List[str]]]:
    """
    Create consensus mapping from two dataset mappings.

    Returns:
        Dictionary with consensus as key and tuple of (dataset1_labels, dataset2_labels) as value
    """
    consensus_map = {}

    # Get all unique consensus labels
    all_consensus = set(dataset1_mapping.values()) | set(
        dataset2_mapping.values())

    for consensus in all_consensus:
        d1_labels = [k for k, v in dataset1_mapping.items() if v == consensus]
        d2_labels = [k for k, v in dataset2_mapping.items() if v == consensus]
        consensus_map[consensus] = (d1_labels, d2_labels)

    return consensus_map


def get_feature_operations(dataset1_mapping: Dict[str, str],
                           dataset2_mapping: Dict[str, str]) -> Dict[str, Tuple[str, str]]:
    """
    Determine operations needed for feature mappings.

    Returns:
        Dictionary with consensus as key and tuple of (rna_operation, protein_operation) as value
    """
    operations = {}
    consensus_map = get_consensus_mapping(dataset1_mapping, dataset2_mapping)

    for consensus, (d1_features, d2_features) in consensus_map.items():
        rna_op = "sum()" if len(d1_features) > 1 else ""
        prot_op = "max()" if len(d2_features) > 1 else ""
        operations[consensus] = (rna_op, prot_op)

    return operations


def sort_mappings_by_presence(consensus_map: Dict[str, Tuple[List[str], List[str]]]) -> List[str]:
    """
    Sort consensus labels by presence in both datasets.

    Mappings present in both datasets come first, followed by those in only one dataset.

    Args:
        consensus_map: Dictionary from get_consensus_mapping

    Returns:
        Sorted list of consensus labels
    """
    both_datasets = []
    one_dataset = []

    for consensus, (d1_labels, d2_labels) in consensus_map.items():
        if d1_labels and d2_labels:
            both_datasets.append(consensus)
        else:
            one_dataset.append(consensus)

    # Sort each group alphabetically
    both_datasets.sort()
    one_dataset.sort()

    return both_datasets + one_dataset
