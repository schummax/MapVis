# MapVis: Cell Type and Feature Mapping Visualization

MapVis is a Python package designed to generate clear and informative HTML tables for visualizing mappings between cell types or features (like proteins and RNAs) from different datasets or annotation versions.

## Key Features

-   **`create_celltype_mapping_table`**: Generates a 3-column HTML table to compare cell type mappings from two sources to a consensus annotation.
-   **`create_feature_mapping_table`**: Generates a 5-column HTML table to visualize mappings between features (e.g., proteins to RNAs), highlighting relationships like 1:1, 1:n (protein complexes), n:1 (alternative splicing), and n:m.
-   Customizable captions and dataset names.
-   Optional, configurable color schemes for consensus labels.
-   Automatic default color generation if no custom scheme is provided.
-   Styled HTML output with alternating row colors (50% opacity) and clear legend.
-   Returns raw pandas DataFrames along with HTML for further analysis.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url> 
    # Replace <repository_url> with the actual URL of the MapVis repository
    cd mapvis 
    ```

2.  **Install the package:**
    For regular use:
    ```bash
    pip install .
    ```
    For development (editable install):
    ```bash
    pip install -e .
    ```
    Dependencies (`pandas` and `matplotlib`) are listed in `setup.py` and will be handled automatically by pip.

## Usage Examples

First, import the `mapvis` package and `pandas` if you're creating DataFrames:

```python
import mapvis
import pandas as pd
from IPython.display import HTML, display # For Jupyter environments
```

### 1. `create_celltype_mapping_table`

This function helps visualize how original cell type labels from two different datasets map to a set of consensus cell type labels.

```python
# Sample input data
mapping1 = {
    'Mature B': 'B-cell', 'Pro B': 'B-cell',
    'cd4+ t': 'CD4+ T-cell', 'cd8+ t': 'CD8+ T-cell',
    'macrophage': 'Myeloid'
}
mapping2 = {
    'B cell': 'B-cell', 'Memory B': 'B-cell',
    't CD4': 'CD4+ T-cell', 'Treg': 'Treg', # Treg is unique to mapping2 for CD4+ T-cell consensus
    'Monocyte': 'Myeloid', 'cDC': 'Myeloid'
}

# Optional: Define custom colors for consensus labels (use 6-digit hex)
custom_colors = {
    'B-cell': '#ADD8E6',
    'CD4+ T-cell': '#90EE90',
    'CD8+ T-cell': '#32CD32',
    'Myeloid': '#FFD700',
    'Treg': '#008000' # Treg will also get its color
}

# Generate the table
table_html, legend_html, df = mapvis.create_celltype_mapping_table(
    mapping1,
    mapping2,
    color_scheme=custom_colors,
    caption="Cell Type Mapping: Dataset A vs Dataset B",
    show_legend=True,
    dataset1_name="Dataset A Labels",
    dataset2_name="Dataset B Labels"
)

# Display in a Jupyter Notebook
display(HTML(table_html))
if legend_html:
    display(HTML(legend_html))

# Or save to an HTML file
with open("celltype_mapping_visualization.html", "w", encoding="utf-8") as f:
    f.write("<html><head><title>Celltype Mapping</title>")
    # Basic styles for table readability if not embedded in a styled page
    f.write("<style>body{font-family: Arial, sans-serif;} table{border-collapse: collapse; margin-bottom: 20px;} th,td{border:1px solid #ddd; padding:8px; text-align:left;} caption{font-size:1.2em; font-weight:bold; margin-bottom:10px;}</style>")
    f.write("</head><body>")
    f.write(table_html)
    if legend_html:
        f.write(legend_html)
    f.write("</body></html>")

print("Celltype mapping table saved to celltype_mapping_visualization.html")
print("Underlying DataFrame for celltype mapping:")
print(df.head())
```

### 2. `create_feature_mapping_table`

This function visualizes relationships between two sets of features, such as proteins and their corresponding RNAs, indicating operations like sum (for protein complexes) or max (for alternative splicing).

```python
# Sample input DataFrame
feature_data = {
    'Protein name': ['CD45RA', 'CD45RO', 'Cytokeratin', 'FOXP3', 'CD3E/CD3G', 'CD20', 'CD20', 'CD19', 'P_ComplexA/P_ComplexB'],
    'RNA name': ['PTPRC', 'PTPRC', 'KRT1/KRT10/KRT5', 'FOXP3', 'CD3E/CD3G', 'MS4A1_Transcript1', 'MS4A1_Transcript2', 'CD19', 'GeneX/GeneY/GeneZ']
}
feature_df = pd.DataFrame(feature_data)

# Optional: Custom colors for consensus labels
custom_feature_colors = {
    'PTPRC': '#FF0000',             # For CD45RA, CD45RO -> PTPRC (n:1, RNA is consensus)
    'Cytokeratin': '#00FF00',       # For Cytokeratin -> KRT1/KRT10/KRT5 (1:n, Protein is consensus)
    'FOXP3': '#0000FF',             # For FOXP3 -> FOXP3 (1:1, RNA is consensus)
    'CD3E/CD3G': '#FFFF00',         # For CD3E/CD3G -> CD3E/CD3G (n:m, first RNA is consensus)
    'MS4A1_Transcript1': '#FF00FF', # For CD20 -> MS4A1_Transcript1 (1:1, RNA is consensus)
    'MS4A1_Transcript2': '#FF00FF', # For CD20 -> MS4A1_Transcript2 (1:1, RNA is consensus)
    'CD19': '#00FFFF',              # For CD19 -> CD19 (1:1, RNA is consensus)
    'GeneX': '#800080'              # For P_ComplexA/P_ComplexB -> GeneX/GeneY/GeneZ (n:m, first RNA is consensus)
}

# Generate the table
table_html_feat, legend_html_feat, df_feat = mapvis.create_feature_mapping_table(
    feature_df,
    color_scheme=custom_feature_colors,
    caption="Feature Mapping: Protein to RNA",
    show_legend=True,
    protein_col="Protein name", # Default, can be changed
    rna_col="RNA name"          # Default, can be changed
)

# Display in a Jupyter Notebook
display(HTML(table_html_feat))
if legend_html_feat:
    display(HTML(legend_html_feat))

# Or save to an HTML file
with open("feature_mapping_visualization.html", "w", encoding="utf-8") as f:
    f.write("<html><head><title>Feature Mapping</title>")
    f.write("<style>body{font-family: Arial, sans-serif;} table{border-collapse: collapse; margin-bottom: 20px;} th,td{border:1px solid #ddd; padding:8px; text-align:left;} caption{font-size:1.2em; font-weight:bold; margin-bottom:10px;}</style>")
    f.write("</head><body>")
    f.write(table_html_feat)
    if legend_html_feat:
        f.write(legend_html_feat)
    f.write("</body></html>")

print("Feature mapping table saved to feature_mapping_visualization.html")
print("Underlying DataFrame for feature mapping:")
print(df_feat.head())
```

## Output Description

Both functions generate:
1.  `table_html (str)`: An HTML string representing the styled table.
2.  `legend_html (str or None)`: An HTML string for the legend, or `None` if `show_legend=False` or no legend items are generated.
3.  `df (pd.DataFrame)`: The underlying pandas DataFrame used to construct the HTML table, allowing for further programmatic access to the data.

**HTML Table Features:**
-   **Styling:** Table cells are colored based on their consensus label, with a 50% opacity on the background. Text color is black for readability.
-   **Sorting:** Rows are grouped by consensus labels.
-   **`create_celltype_mapping_table`:** Displays original labels from two datasets alongside their shared consensus annotation.
-   **`create_feature_mapping_table`:**
    -   Displays protein and RNA names in the first and last columns.
    -   Includes two "Operation" columns and a central "Consensus label" column.
    -   "Operation" columns indicate relationships:
        -   `max()`: Typically shown on the protein side for n:1 mappings (e.g., multiple proteins from one gene due to alternative splicing).
        -   `sum()`: Typically shown on the RNA side for 1:n mappings (e.g., one protein complex composed of products from multiple genes).
        -   Both `max()` and `sum()` can appear for n:m mappings.
        -   Blank for 1:1 mappings.
    -   The "Consensus label" is determined based on the mapping type (e.g., RNA name for 1:1 or n:1, protein name for 1:n).
    -   Items involved in n:1, 1:n, or n:m relationships are stacked vertically for clarity.

*(Example output screenshots will be added here. For now, you can generate example HTML files by running `python mapvis/visualizer.py` if you have cloned the repository, which will create `mapping_table_celltype_example_refactored.html` and `mapping_table_feature_example_refactored.html`.)*

## Development and Testing

To run the unit tests for this package:

1.  Ensure you have `unittest` (standard library) available.
2.  Navigate to the root directory of the `mapvis` package.
3.  Run the tests using the following command:

    ```bash
    python -m unittest discover -s tests
    ```

## License
This project is licensed under the MIT License. See the `LICENSE` file for details (though a `LICENSE` file was not explicitly created in this exercise, it's standard to mention).
```
