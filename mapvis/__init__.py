"""
MapVis: A package for visualizing cell type and feature mappings.
"""

from .visualizer import create_celltype_mapping_table, create_feature_mapping_table

__all__ = [
    'create_celltype_mapping_table',
    'create_feature_mapping_table'
]

__version__ = "0.1.0"

