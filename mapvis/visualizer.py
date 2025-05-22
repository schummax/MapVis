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

    # Determine sorting order for consensus labels
    consensus_map1_values = set(mapping1.values())
    consensus_map2_values = set(mapping2.values())

    consensus_in_both = sorted(list(consensus_map1_values & consensus_map2_values))
    consensus_in_map1_only = sorted(list(consensus_map1_values - consensus_map2_values))
    consensus_in_map2_only = sorted(list(consensus_map2_values - consensus_map1_values))
    
    ordered_consensus_labels = consensus_in_both + consensus_in_map1_only + consensus_in_map2_only
    
    single_dataset_consensus_labels = set(consensus_in_map1_only) | set(consensus_in_map2_only)

    table_data = []
    for cons_label in ordered_consensus_labels:
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
    base_color_map = utils.build_final_color_map(unique_consensus_in_table, color_scheme)
            
    # --- Styling ---
    # Redefine style_row_celltype to explicitly use original label for logic, display label for merge check
    # This local redefinition is to ensure it uses the `df` from the outer scope correctly for original label lookup.
    def style_row_celltype_revised(row_from_df_display, df_original_lookup, single_dataset_labels_set_lookup, base_color_map_lookup_param):
        original_cons_label = df_original_lookup.loc[row_from_df_display.name, "Consensus Label"]
        
        base_color = base_color_map_lookup_param.get(original_cons_label, "#FFFFFF")
        display_color = utils.format_color_with_opacity(base_color, 0.5)
        
        font_style_css = ""
        if cons_label in single_dataset_labels_set:
            font_style_css = "font-style: italic;"
            # The problem description mentioned "lighter background color" for single-dataset types
            # but the current implementation uses the same 50% opacity for all.
            # If "lighter" means modifying the base_color or opacity further, that logic would go here.
            # For now, sticking to 50% opacity for all background colors as per previous implementation
            # and only adding italics.
        
        # Basic style for all cells in the row
        styles = [f'background-color: {display_color}; {font_style_css}' for _ in row.index]
        
        # Check for cell merging for "Consensus Label"
        # Need to know if this row is a continuation of a merged cell
        # This requires passing the original df to check previous row, or a pre-calculated mask.
        # Let's assume `df` is accessible here or relevant info is on `row` itself if df is modified for display.
        # If `row['Consensus Label HTML'] == ''` (meaning it's a subsequent row in a merge group for display)
        # then we apply `border-top-style: none;` to the 'Consensus Label' cell.
        
        # This logic will be applied after preparing a display version of the DataFrame.
        # The style_row_celltype will receive a row from the *display* DataFrame.
        # The original "Consensus Label" (for coloring/italics) must be accessed via `df.loc[row.name, 'Consensus Label']`
        # or be part of the row if we add it as a hidden column.

        # Simplified: The function will receive the row from the df_display.
        # We need to apply border style based on whether the display label is empty.
        consensus_label_col_idx = row.index.get_loc("Consensus Label") # Get by name
        
        # If the displayed text for "Consensus Label" is empty, it's a merged cell.
        if row["Consensus Label"] == "": # This checks the display version of "Consensus Label"
            styles[consensus_label_col_idx] += " border-top-style: none;"
            
        return styles

    # Prepare DataFrame for display (blanking out merged labels)
    df_display = df.copy()
    # Mark rows where 'Consensus Label' is the same as the previous row.
    # These will have their 'Consensus Label' text blanked out and top border removed by styler.
    is_subsequent_in_group = (df_display['Consensus Label'] == df_display['Consensus Label'].shift(1))
    df_display.loc[is_subsequent_in_group, 'Consensus Label'] = ''
    
    # The styling function now needs the original 'Consensus Label' for logic if it's different from display version
    # We can pass df for lookup or add original values to df_display as temp columns.
    # Let's ensure style_row_celltype uses original values for coloring/italics by looking up in original `df`.
    
    def get_original_consensus_label_for_row(row_from_df_display):
        return df.loc[row_from_df_display.name, "Consensus Label"]

    styled_styler_obj = df_display.style.apply(
        style_row_celltype, 
        axis=1, 
        single_dataset_labels_set=single_dataset_consensus_labels,
        base_color_map_lookup=base_color_map # This map uses original consensus labels
        # The style_row_celltype needs to use original consensus label for color/italics
        # This is implicitly handled as `cons_label` in style_row_celltype comes from the (potentially modified) row,
        # but color map and single_dataset_labels_set use original labels.
        display_color_val = utils.format_color_with_opacity(base_color, 0.5)
        
        font_style_val = ""
        if original_cons_label in single_dataset_labels_set_lookup:
            font_style_val = "font-style: italic;"
            
        styles_list = [f'background-color: {display_color_val}; {font_style_val}' for _ in row_from_df_display.index]
        
        consensus_label_col_idx_val = row_from_df_display.index.get_loc("Consensus Label")
        if row_from_df_display["Consensus Label"] == "": # Check display version for border
            styles_list[consensus_label_col_idx_val] += " border-top-style: none;"
            
        return styles_list

    styled_styler_obj = df_display.style.apply(
        style_row_celltype_revised, # Now this is the only style_row_celltype function
        axis=1,
        df_original_lookup=df, 
        single_dataset_labels_set_lookup=single_dataset_consensus_labels,
        base_color_map_lookup_param=base_color_map
    ).set_caption(caption).hide(axis='index')\
                        .set_properties(**utils.get_default_table_properties())
    
    styled_table_html = styled_styler_obj.to_html()

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
    base_color_map = utils.build_final_color_map(unique_consensus_in_table, color_scheme)

    # --- Styling ---
    style_df = df.copy()
    style_df["_style_consensus_label_filled"] = df["Consensus label"].replace("", pd.NA).ffill()

    # Define column renaming mapping
    final_df_columns_rename_map = {"Operation1": "Operation", "Operation2": "Operation"}

    # Rename columns on the DataFrame that will be styled
    # The get_style_colors_for_group function depends on the number of columns of the *original* df (before this rename)
    # So, we must ensure it uses the correct column reference.
    # The `df.columns` in `get_style_colors_for_group` refers to the columns of the DataFrame `df` (which has Op1, Op2)
    # So, we should rename `style_df` *after* `get_style_colors_for_group` definition or adjust `get_style_colors_for_group`.
    # Let's adjust get_style_colors_for_group to expect renamed columns if we rename style_df first.
    
    # Alternative: Rename df first, then style_df is a copy of the renamed df.
    # df = df.rename(columns=final_df_columns_rename_map)
    # style_df = df.copy() # style_df now has renamed columns
    # style_df["_style_consensus_label_filled"] = df["Consensus label"].replace("", pd.NA).ffill() # This needs to use original column names for ffill if df is not renamed yet.

    # Safest approach: rename the `style_df` just before styling, and ensure styling function uses correct column count.
    # The `get_style_colors_for_group` returns styles for columns of `df` (original names).
    # If `style_df` is renamed before .style, the Styler will see renamed columns.
    # The number of columns doesn't change, so `len(df.columns)` is fine.
    
    style_df_renamed_for_styling = style_df.rename(columns=final_df_columns_rename_map) # Has "Operation" columns
    
    # Prepare for cell merging in "Consensus label" column
    # Blank out text for subsequent identical consensus labels
    df_for_html_display = style_df_renamed_for_styling.copy()
    # Use _style_consensus_label_filled to define groups for merging actual displayed text
    # We only blank out if the *visible* text in "Consensus label" is same as previous row's visible text
    mask_blank_consensus = (df_for_html_display['Consensus label'] == df_for_html_display['Consensus label'].shift(1)) & \
                           (df_for_html_display['Consensus label'] != '')
    df_for_html_display.loc[mask_blank_consensus, 'Consensus label'] = ''


    def get_style_for_feature_row(row_from_df_for_html, base_color_map_lookup, filled_consensus_series_lookup):
        # `row_from_df_for_html` has "Consensus label" potentially blanked for display.
        # `filled_consensus_series_lookup` contains the logical consensus label for coloring.
        # `base_color_map_lookup` uses these logical labels.
        
        logical_cons_label = filled_consensus_series_lookup.loc[row_from_df_for_html.name]
        base_color = base_color_map_lookup.get(logical_cons_label, "#FFFFFF") # Default white
        display_color_val = utils.format_color_with_opacity(base_color, 0.5)
        
        # Base style for all cells
        num_cols_to_style = len(row_from_df_for_html.index) -1 # Exclude _style_consensus_label_filled if present as column
        if '_style_consensus_label_filled' not in row_from_df_for_html.index: # Should always be there from style_df
             num_cols_to_style = len(row_from_df_for_html.index)


        styles_list = [f'background-color: {display_color_val}' for _ in range(num_cols_to_style)]
        
        # Cell merging for "Consensus label" column
        consensus_col_name = "Consensus label" # After rename
        consensus_label_col_idx_val = row_from_df_for_html.index.get_loc(consensus_col_name)
        
        # If the display text for "Consensus label" is empty AND it was not originally empty
        # (meaning it was blanked for merging, not because it's a subsequent row of a feature group like 1:n)
        original_consensus_text_in_style_df = style_df_renamed_for_styling.loc[row_from_df_for_html.name, consensus_col_name]

        if row_from_df_for_html[consensus_col_name] == "" and original_consensus_text_in_style_df != "":
            styles_list[consensus_label_col_idx_val] += " border-top-style: none;"
            
        return pd.Series(styles_list, index=row_from_df_for_html.index.drop("_style_consensus_label_filled", errors='ignore'))


    styled_pandas_df = df_for_html_display.style.apply(
        get_style_for_feature_row,
        axis=1,
        base_color_map_lookup=base_color_map,
        filled_consensus_series_lookup=df_for_html_display["_style_consensus_label_filled"] # from df_for_html_display
    ).set_caption(caption).hide(axis='index')\
     .set_properties(**utils.get_default_table_properties())
    
    # The Styler object `styled_pandas_df` now refers to a DataFrame with renamed columns.
    # The temporary column `_style_consensus_label_filled` should still be hidden from the final HTML.
    if "_style_consensus_label_filled" in styled_pandas_df.columns: 
         styled_pandas_df = styled_pandas_df.hide(axis="columns", subset=["_style_consensus_label_filled"])

    styled_table_html = styled_pandas_df.to_html()
    
    # --- Legend using utils ---
    legend_html = None
    if show_legend:
        # Create a map for the legend with only the labels present in the table
        legend_color_map = {k: v for k, v in base_color_map.items() if k in unique_consensus_in_table}
        legend_html = utils.get_legend_html(legend_color_map, title="Legend", swatch_opacity=1.0)

    # The original df (before copy to style_df) still has "Operation1", "Operation2"
    # The df_renamed that is returned should have the final column names.
    df_renamed = df.rename(columns=final_df_columns_rename_map)
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
