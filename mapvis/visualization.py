"""Visualization styling functions for MapVis."""

import pandas as pd
from typing import Dict, List, Tuple, Optional


def style_celltype_table(df: pd.DataFrame,
                         consensus_map: Dict[str, Tuple[List[str], List[str]]],
                         default_palette: Dict[str, str],
                         color_map: Optional[Dict[str, str]] = None):
    """Apply styling to celltype mapping table."""
    styled = df.style

    # Use custom color map if provided, otherwise generate from default palette
    if color_map:
        consensus_colors = color_map
    else:
        consensus_colors = {}
        for i, consensus in enumerate(consensus_map.keys()):
            color_key = f"color_{i % len(default_palette)}"
            consensus_colors[consensus] = default_palette[color_key]

    # Apply background colors
    def apply_colors(row):
        consensus = row["Consensus"]
        color = consensus_colors.get(consensus, "white")
        return [f"background-color: {color}; opacity: 0.7"] * len(row)

    styled = styled.apply(apply_colors, axis=1)

    # Add borders and formatting
    styled = styled.set_properties(**{
        'border': '1px solid black',
        'text-align': 'center',
        'padding': '8px',
        'white-space': 'pre-line'  # This enables newline rendering
    })

    # Style the column headers
    styled = styled.set_table_styles([
        {'selector': 'th',
         'props': [('text-align', 'center'),
                   ('font-weight', 'bold'),
                   ('background-color', '#f0f0f0'),
                   ('border', '1px solid black'),
                   ('padding', '10px')]}
    ])

    # Hide index
    styled = styled.hide()

    return styled


def style_feature_table(df: pd.DataFrame,
                        consensus_map: Dict[str, Tuple[List[str], List[str]]],
                        default_palette: Dict[str, str],
                        color_map: Optional[Dict[str, str]] = None):
    """Apply styling to feature mapping table."""
    styled = df.style

    # Use custom color map if provided, otherwise generate from default palette
    if color_map:
        consensus_colors = color_map
    else:
        consensus_colors = {}
        for i, consensus in enumerate(consensus_map.keys()):
            color_key = f"color_{i % len(default_palette)}"
            consensus_colors[consensus] = default_palette[color_key]

    # Apply background colors based on consensus groups
    def apply_colors(row):
        consensus = row["Consensus"]
        color = consensus_colors.get(consensus, "white")
        return [f"background-color: {color}; opacity: 0.7"] * len(row)

    styled = styled.apply(apply_colors, axis=1)

    # Add borders and formatting
    styled = styled.set_properties(**{
        'border': '1px solid black',
        'text-align': 'center',
        'padding': '8px',
        'white-space': 'pre-line'  # This enables newline rendering
    })

    # Style the column headers
    styled = styled.set_table_styles([
        {'selector': 'th',
         'props': [('text-align', 'center'),
                   ('font-weight', 'bold'),
                   ('background-color', '#f0f0f0'),
                   ('border', '1px solid black'),
                   ('padding', '10px')]}
    ])

    # Hide index
    styled = styled.hide()

    return styled
