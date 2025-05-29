"""Core functionality for MapVis."""

import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from .validators import validate_mapping_dict, validate_celltype_mappings, validate_feature_mappings
from .visualization import style_celltype_table, style_feature_table
from .utils import get_consensus_mapping, get_feature_operations, sort_mappings_by_presence


class MapVisualizer:
    """Main class for creating mapping visualizations."""

    def __init__(self):
        self.color_palette = {}
        self._generate_default_palette()

    def _generate_default_palette(self):
        """Generate default color palette for consensus labels."""
        import matplotlib.pyplot as plt
        colors = plt.cm.Set3(range(12))
        # Use hex format for compatibility with both HTML and matplotlib
        self.color_palette = {f"color_{i}": f"#{int(c[0]*255):02x}{int(c[1]*255):02x}{int(c[2]*255):02x}"
                              for i, c in enumerate(colors)}

    def visualize_celltype_mapping(self,
                                   dataset1_mapping: Dict[str, str],
                                   dataset2_mapping: Dict[str, str],
                                   dataset1_name: str = "Dataset 1",
                                   dataset2_name: str = "Dataset 2",
                                   color_map: Optional[Dict[str, str]] = None):
        """
        Create styled table for celltype mapping visualization.

        Args:
            dataset1_mapping: Dictionary mapping dataset1 celltypes to consensus
            dataset2_mapping: Dictionary mapping dataset2 celltypes to consensus
            dataset1_name: Name for dataset 1 column
            dataset2_name: Name for dataset 2 column
            color_map: Optional dictionary mapping consensus labels to colors (hex format)

        Returns:
            Styled pandas DataFrame
        """
        # Validate inputs
        validate_celltype_mappings(dataset1_mapping, dataset2_mapping)

        # Get consensus mapping and sort
        consensus_map = get_consensus_mapping(
            dataset1_mapping, dataset2_mapping)
        sorted_consensus = sort_mappings_by_presence(consensus_map)

        # Create DataFrame
        data = []
        for consensus in sorted_consensus:
            d1_labels, d2_labels = consensus_map[consensus]
            data.append({
                dataset1_name: "\n".join(d1_labels) if d1_labels else "",
                "Consensus": consensus,
                dataset2_name: "\n".join(d2_labels) if d2_labels else ""
            })

        df = pd.DataFrame(data)

        # Apply styling
        return style_celltype_table(df, consensus_map, self.color_palette, color_map)

    def visualize_feature_mapping(self,
                                  dataset1_mapping: Dict[str, str],
                                  dataset2_mapping: Dict[str, str],
                                  dataset1_name: str = "Dataset 1 (RNA)",
                                  dataset2_name: str = "Dataset 2 (Protein)",
                                  color_map: Optional[Dict[str, str]] = None):
        """
        Create styled table for feature mapping visualization.

        Args:
            dataset1_mapping: Dictionary mapping dataset1 features to consensus
            dataset2_mapping: Dictionary mapping dataset2 features to consensus
            dataset1_name: Name for dataset 1 column
            dataset2_name: Name for dataset 2 column
            color_map: Optional dictionary mapping consensus labels to colors (hex format)

        Returns:
            Styled pandas DataFrame
        """
        # Validate inputs
        validate_feature_mappings(dataset1_mapping, dataset2_mapping)

        # Get consensus mapping and operations
        consensus_map = get_consensus_mapping(
            dataset1_mapping, dataset2_mapping)
        sorted_consensus = sort_mappings_by_presence(consensus_map)
        operations = get_feature_operations(dataset1_mapping, dataset2_mapping)

        # Create DataFrame with merged cells
        data = []
        for consensus in sorted_consensus:
            d1_features, d2_features = consensus_map[consensus]
            rna_op, prot_op = operations.get(consensus, ("", ""))

            data.append({
                dataset1_name: "\n".join(d1_features) if d1_features else "",
                "RNA Operation": rna_op,
                "Consensus": consensus,
                "Protein Operation": prot_op,
                dataset2_name: "\n".join(d2_features) if d2_features else ""
            })

        df = pd.DataFrame(data)

        # Apply styling
        return style_feature_table(df, consensus_map, self.color_palette, color_map)

    def export_to_image(self, styled_table, filename: str,
                        table_conversion: str = 'chrome',
                        dpi: int = 150):
        """
        Export styled table to image file.

        Args:
            styled_table: Styled pandas DataFrame (output from visualize_* methods)
            filename: Output filename (should end with .png, .jpg, etc.)
            table_conversion: Backend to use ('chrome', 'matplotlib', 'selenium')
            dpi: DPI for image export

        Requires:
            pip install dataframe-image
        """
        try:
            import dataframe_image as dfi
        except ImportError:
            raise ImportError(
                "dataframe-image package is required for image export. "
                "Install it with: pip install dataframe-image"
            )

        dfi.export(styled_table, filename,
                   table_conversion=table_conversion,
                   dpi=dpi)

    def export_to_image_simple(self, df: pd.DataFrame, filename: str, dpi: int = 150):
        """
        Export DataFrame as simple table image (without styling) using matplotlib.

        This is useful when Chrome is not available and you need a basic table export.

        Args:
            df: The DataFrame to export (unstyle data from styled_table.data)
            filename: Output filename
            dpi: DPI for image export
        """
        import matplotlib.pyplot as plt
        from pandas.plotting import table

        # Create figure and axis
        fig, ax = plt.subplots(figsize=(10, len(df) * 0.5 + 1))
        ax.axis('tight')
        ax.axis('off')

        # Create table
        tbl = table(ax, df, loc='center', cellLoc='center')
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(10)
        tbl.scale(1, 1.5)

        # Save
        plt.savefig(filename, dpi=dpi, bbox_inches='tight', pad_inches=0.1)
        plt.close()
