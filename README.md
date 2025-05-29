# MapVis

A Python module for visualizing celltype and feature (RNA/Protein) mappings between datasets.

## Installation

```bash
pip install mapvis

# For image export functionality
pip install mapvis[image]
```

## Quick Start

### Celltype Mapping

```python
from mapvis import MapVisualizer

# Define mappings
dataset1_mapping = {
    'B-CD22-CD40': 'B-CD22-CD40',
    'CD4 T': 'CD4+ T cell',
    'Plasma': 'plasma cell'
}

dataset2_mapping = {
    'CD4+ T cell': 'CD4+ T cell',
    'B-CD22-CD40': 'B-CD22-CD40',
    'plasma cell': 'plasma cell'
}

# Create visualization
vis = MapVisualizer()
styled_table = vis.visualize_celltype_mapping(
    dataset1_mapping,
    dataset2_mapping,
    dataset1_name="scRNA-seq",
    dataset2_name="CODEX"
)

# Display in Jupyter
styled_table
```

### Feature Mapping

```python
# Define feature mappings
rna_mapping = {
    'PTPRC': 'PTPRC',
    'HLA-DRB1': 'HLA-DR',
    'HLA-DRB5': 'HLA-DR',
    'HLA-DRA': 'HLA-DR'
}

protein_mapping = {
    'CD45': 'PTPRC',
    'CD45RA': 'PTPRC',
    'HLA-DR': 'HLA-DR'
}

# Create visualization
styled_table = vis.visualize_feature_mapping(
    rna_mapping,
    protein_mapping
)
```

### Custom Color Maps

```python
# Define custom colors for specific consensus labels
custom_colors = {
    'B-CD22-CD40': '#FF6B6B',
    'CD4+ T cell': '#4ECDC4',
    'plasma cell': '#45B7D1'
}

# Apply custom colors
styled_table = vis.visualize_celltype_mapping(
    dataset1_mapping,
    dataset2_mapping,
    color_map=custom_colors
)
```

### Export to Image

```python
# Export styled table to PNG
vis.export_to_image(styled_table, 'celltype_mapping.png')

# Use different backend if Chrome is not available (not working yet)
vis.export_to_image(styled_table, 'celltype_mapping.png',
                   table_conversion='matplotlib')
```

### Loading from TSV/CSV

```python
from mapvis import load_mapping_from_tsv, load_mapping_from_csv

# Load from TSV (recommended for data with commas)
mapping = load_mapping_from_tsv(
    'celltype_mapping.tsv',
    source_col='original_name',
    target_col='consensus_name'
)

# Load from CSV (if no commas in data)
mapping = load_mapping_from_csv(
    'mapping.csv',
    source_col='original_name',
    target_col='consensus_name'
)

# Or specify delimiter explicitly
mapping = load_mapping_from_csv(
    'mapping.txt',
    source_col='original_name',
    target_col='consensus_name',
    delimiter='\t'
)
```

## Testing

```bash
pip install -e ".[dev]"
pytest tests/
```
