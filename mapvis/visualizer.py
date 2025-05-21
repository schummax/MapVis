import pandas as pd
import numpy as np # For NaN values if needed, though empty strings are probably better
from . import utils # Import the new utils module

# DEFAULT_COLORS_HEX_OPAQUE_50 is now removed, will use utils

def create_celltype_mapping_table(
    mapping1: dict,
    mapping2: dict,
    color_scheme: dict = None, # Expects base 6-digit hex colors, e.g., #RRGGBB
    caption: str = "Celltype Mapping Table",
    show_legend: bool = True,
    dataset1_name: str = "Dataset 1",
    dataset2_name: str = "Dataset 2"
):
    if color_scheme is None:
        color_scheme = {}

    # Invert mappings: consensus_label -> [original_label1, original_label2, ...]
    inverted_mapping1 = {}
    for orig_label, cons_label in mapping1.items():
        inverted_mapping1.setdefault(cons_label, []).append(orig_label)

    inverted_mapping2 = {}
    for orig_label, cons_label in mapping2.items():
        inverted_mapping2.setdefault(cons_label, []).append(orig_label)

    all_consensus_labels = sorted(
        list(set(inverted_mapping1.keys()) | set(inverted_mapping2.keys()))
    )

    table_data = []
    for cons_label in all_consensus_labels:
        orig_labels1 = inverted_mapping1.get(cons_label, [])
        orig_labels2 = inverted_mapping2.get(cons_label, [])
        orig_labels1.sort()
        orig_labels2.sort()
        max_len = max(len(orig_labels1), len(orig_labels2))
        if max_len == 0: continue
        for i in range(max_len):
            row = {
                dataset1_name: orig_labels1[i] if i < len(orig_labels1) else "",
                "Consensus Label": cons_label,
                dataset2_name: orig_labels2[i] if i < len(orig_labels2) else "",
            }
            table_data.append(row)

    df = pd.DataFrame(table_data)

    if df.empty:
        return "<table><caption>No data to display</caption></table>", None, df

    # --- Color assignment using utils ---
    unique_consensus_in_table = list(df["Consensus Label"].unique())
    
    # Initialize base color map with user-provided scheme (ensure they are valid base colors)
    base_color_map = {}
    for label, color_val in color_scheme.items():
        if isinstance(color_val, str) and color_val.startswith("#") and len(color_val) == 7:
             base_color_map[label] = color_val
        # else: user provided an invalid color, it will be ignored and default will be generated

    # Generate default colors for labels not in the validated color_scheme
    labels_needing_defaults = [lbl for lbl in unique_consensus_in_table if lbl not in base_color_map]
    if labels_needing_defaults:
        default_colors_for_new_labels = utils.generate_default_colors(labels_needing_defaults, existing_colors=base_color_map)
        base_color_map.update(default_colors_for_new_labels)
            
    # --- Styling ---
    def style_row_background(row):
        cons_label = row["Consensus Label"]
        base_color = base_color_map.get(cons_label, "#FFFFFF") # Default to white if somehow missing
        display_color = utils.format_color_with_opacity(base_color, 0.5)
        return [f'background-color: {display_color}' for _ in row]

    styled_df = df.style.apply(style_row_background, axis=1)\
                        .set_caption(caption)\
                        .hide(axis='index')\
                        .set_properties(**utils.get_default_table_properties())
    
    styled_table_html = styled_df.to_html()

    # --- Legend using utils ---
    legend_html = None
    if show_legend:
        # Pass the base_color_map; utils.get_legend_html handles opacity for swatches
        legend_html = utils.get_legend_html(base_color_map, title="Legend", swatch_opacity=1.0)
            
    return styled_table_html, legend_html, df


def create_feature_mapping_table(
    feature_df: pd.DataFrame,
    caption: str = "Feature Mapping Table",
    show_legend: bool = True,
    color_scheme: dict = None, # Expects base 6-digit hex colors
    protein_col: str = "Protein name",
    rna_col: str = "RNA name",
    protein_sep: str = "/",
    rna_sep: str = "/"
):
    if color_scheme is None:
        color_scheme = {}

    processed_rows = []
    # Data processing logic (same as before)
    for _, row in feature_df.iterrows():
        proteins_str = str(row.get(protein_col, ""))
        rnas_str = str(row.get(rna_col, ""))

        proteins = [p.strip() for p in proteins_str.split(protein_sep) if p.strip()] if proteins_str else []
        rnas = [r.strip() for r in rnas_str.split(rna_sep) if r.strip()] if rnas_str else []

        p_count = len(proteins)
        r_count = len(rnas)

        consensus_label = ""
        op1_val = ""
        op2_val = ""

        if p_count == 1 and r_count == 1: consensus_label = rnas[0]
        elif p_count == 1 and r_count > 1: consensus_label = proteins[0]; op2_val = "sum()"
        elif p_count > 1 and r_count == 1: consensus_label = rnas[0]; op1_val = "max()"
        elif p_count > 1 and r_count > 1: consensus_label = rnas[0] if rnas else (proteins[0] if proteins else "Undefined"); op1_val = "max()"; op2_val = "sum()"
        elif p_count == 0 and r_count > 0: consensus_label = rnas[0]
        elif p_count > 0 and r_count == 0: consensus_label = proteins[0]
        else: continue

        max_rows = max(p_count, r_count, 1)
        for i in range(max_rows):
            protein_name_val = proteins[i] if i < p_count else ""
            rna_name_val = rnas[i] if i < r_count else ""
            current_op1 = op1_val if i == 0 else ""
            current_op2 = op2_val if i == 0 else ""
            current_consensus = consensus_label if i == 0 else ""
            if p_count == 1 and r_count == 1: current_consensus = consensus_label
            if p_count > 1 and r_count == 1 and i > 0: rna_name_val = ""
            if p_count == 1 and r_count > 1 and i > 0: protein_name_val = ""
            
            processed_rows.append({
                "Protein name": protein_name_val, "Operation1": current_op1,
                "Consensus label": current_consensus, "Operation2": current_op2,
                "RNA name": rna_name_val, "_sort_key_consensus": consensus_label
            })

    if not processed_rows:
        df = pd.DataFrame(columns=["Protein name", "Operation", "Consensus label", "Operation", "RNA name"])
        return "<table><caption>No data to display</caption></table>", None, df

    df = pd.DataFrame(processed_rows)
    df.sort_values(by=["_sort_key_consensus", "Protein name", "RNA name"], inplace=True)
    df.drop(columns=["_sort_key_consensus"], inplace=True)

    # --- Color assignment using utils ---
    unique_consensus_in_table = list(df["Consensus label"].replace("", pd.NA).dropna().unique())
    
    base_color_map = {}
    for label, color_val in color_scheme.items():
        if isinstance(color_val, str) and color_val.startswith("#") and len(color_val) == 7:
             base_color_map[label] = color_val

    labels_needing_defaults = [lbl for lbl in unique_consensus_in_table if lbl not in base_color_map]
    if labels_needing_defaults:
        default_colors_for_new_labels = utils.generate_default_colors(labels_needing_defaults, existing_colors=base_color_map)
        base_color_map.update(default_colors_for_new_labels)

    # --- Styling ---
    style_df = df.copy()
    style_df["_style_consensus_label_filled"] = df["Consensus label"].replace("", pd.NA).ffill()
    
    def get_style_colors_for_group(row_in_style_df):
        cons_label = row_in_style_df["_style_consensus_label_filled"]
        base_color = base_color_map.get(cons_label, "#FFFFFF") # Default white
        display_color = utils.format_color_with_opacity(base_color, 0.5)
        # Ensure the number of style properties matches the number of columns in the *original* df
        return [f'background-color: {display_color}' for _ in df.columns]


    styled_pandas_df = style_df.style.apply(get_style_colors_for_group, axis=1)\
                            .set_caption(caption)\
                            .hide(axis='index')\
                            .set_properties(**utils.get_default_table_properties())\
                            .rename(columns={"Operation1": "Operation", "Operation2": "Operation"})
    
    if "_style_consensus_label_filled" in styled_pandas_df.columns:
         styled_pandas_df = styled_pandas_df.hide(axis="columns", subset=["_style_consensus_label_filled"])

    styled_table_html = styled_pandas_df.to_html()
    
    # --- Legend using utils ---
    legend_html = None
    if show_legend:
        # Create a map for the legend with only the labels present in the table
        legend_color_map = {k: v for k, v in base_color_map.items() if k in unique_consensus_in_table}
        legend_html = utils.get_legend_html(legend_color_map, title="Legend", swatch_opacity=1.0)

    final_df_columns = {"Operation1": "Operation", "Operation2": "Operation"}
    df_renamed = df.rename(columns=final_df_columns)
    return styled_table_html, legend_html, df_renamed


if __name__ == '__main__':
    # === Example for create_celltype_mapping_table ===
    codex_map = {
        'Mature B': 'B-cell', 'Pro B': 'B-cell', 'Plasma cells': 'B-cell', 'Early B': 'B-cell',
        'cd4+ t': 'CD4+ T-cell', 'cd8+ t': 'CD8+ T-cell', 'treg': 'Treg',
        'macrophage': 'Myeloid', 'monocyte': 'Myeloid', 'dc': 'Myeloid',
        'nk': 'NK cell', 'tumor': 'Tumor', 'fibroblast': 'Stroma', 'endothelial': 'Stroma', 'other_1': 'Other'
    }
    scrna_map = {
        'B cell': 'B-cell', 'Memory B': 'B-cell', 'Naive B': 'B-cell',
        't CD4': 'CD4+ T-cell', 't CD8': 'CD8+ T-cell', 'Treg': 'Treg', 'Naive T': 'CD4+ T-cell',
        'Macrophage': 'Myeloid', 'Monocyte': 'Myeloid', 'cDC': 'Myeloid',
        'NK cell': 'NK cell', 'Tumor cells': 'Tumor', 'Tumor cluster A': 'Tumor',
        'Fibroblasts': 'Stroma', 'Endothelial cells': 'Stroma', 'other_A': 'Other', 'Unknown': 'Other'
    }
    custom_colors_cell = { # Base 6-digit hex
        'B-cell': '#ADD8E6', 'CD4+ T-cell': '#90EE90', 'CD8+ T-cell': '#32CD32', 'Treg': '#008000',
        'Myeloid': '#FFD700', 'NK cell': '#FFA07A', 'Tumor': '#DC143C', 'Stroma': '#D2B48C', 'Other': '#D3D3D3'
    }
    html_table_cell, legend_cell, _ = create_celltype_mapping_table(
        codex_map, scrna_map, color_scheme=custom_colors_cell, caption="Cell Type Mapping: CODEX vs scRNA-seq (Refactored)",
        dataset1_name="CODEX Labels", dataset2_name="scRNA-seq Labels", show_legend=True
    )
    with open("mapping_table_celltype_example_refactored.html", "w") as f:
        f.write(f"<html><head><title>Cell Type Mapping</title></head><body><h1>Cell Type Mapping Comparison (Refactored)</h1>{html_table_cell}{legend_cell if legend_cell else ''}</body></html>")
    print("Generated mapping_table_celltype_example_refactored.html")

    # === Example for create_feature_mapping_table ===
    feature_data = {
        'Protein name': ['CD45RA', 'CD45RO', 'Cytokeratin', 'FOXP3', 'CD3E/CD3G', 'CD20', 'CD20', 'CD19', 'CD8A/CD8B', 'CD4', 'MKI67', 'ProteinA/ProteinB/ProteinC', 'SingleProteinOnly', 'SingleRNAOnly', 'NoColorProtein'],
        'RNA name': ['PTPRC', 'PTPRC', 'KRT1/KRT10/KRT5', 'FOXP3', 'CD3E/CD3G', 'MS4A1_Transcript1', 'MS4A1_Transcript2', 'CD19', 'CD8A/CD8B', 'CD4_RNA', '', 'GeneX/GeneY', '', 'SingleRNA', 'NoColorRNA'] 
    }
    feature_df_input = pd.DataFrame(feature_data)
    
    custom_colors_feature = { # Base 6-digit hex
        'PTPRC': '#FF0000', 'Cytokeratin': '#00FF00', 'FOXP3': '#0000FF', 'CD3E/CD3G': '#FFFF00',
        'MS4A1_Transcript1': '#FF00FF', 'MS4A1_Transcript2': '#FF00FF', 
        'CD19': '#00FFFF', 'CD8A/CD8B': '#800080', 'CD4_RNA': '#008000',
        'MKI67': '#D3D3D3', 'GeneX': '#FFA500',  'SingleRNA': '#A52A2A'
        # 'NoColorRNA' and 'NoColorProtein' will get default colors
    }

    html_table_feat, legend_feat, df_raw_feat = create_feature_mapping_table(
        feature_df_input,
        caption="Feature Mapping: Protein to RNA (Refactored)",
        color_scheme=custom_colors_feature,
        show_legend=True
    )

    html_output_feat = f"""
    <html>
    <head>
        <title>Feature Mapping (Refactored)</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #DDDDDD; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            caption {{ font-size: 1.2em; font-weight: bold; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <h1>Feature Mapping Details (Refactored)</h1>
        {html_table_feat}
        {legend_feat if legend_feat else ""}
        <h2>Raw DataFrame Output:</h2>
        {df_raw_feat.to_html()}
    </body>
    </html>
    """
    with open("mapping_table_feature_example_refactored.html", "w") as f:
        f.write(html_output_feat)
    print("Generated mapping_table_feature_example_refactored.html")

    # Test feature mapping with no custom colors
    feature_data_no_color = {
        'Protein name': ['CD45RA', 'CD45RO', 'Cytokeratin'],
        'RNA name': ['PTPRC', 'PTPRC', 'KRT1/KRT10'] 
    }
    feature_df_no_color = pd.DataFrame(feature_data_no_color)
    html_table_feat_no_color, legend_feat_no_color, _ = create_feature_mapping_table(
        feature_df_no_color, caption="Feature Mapping (No Custom Colors, Refactored)", show_legend=True
    )
    with open("mapping_table_feature_no_color_refactored.html", "w") as f:
        f.write(f"<html><body>{html_table_feat_no_color}{legend_feat_no_color}</body></html>")
    print("Generated mapping_table_feature_no_color_refactored.html")

```
