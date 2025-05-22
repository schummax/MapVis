import pandas as pd
from . import utils # Use relative import for utils

# Original get_style_colors_for_group - kept for reference or if specific non-scheme styling is needed.
# def get_style_colors_for_group_original(row):
#     styles = []
#     for cell_value in row:
#         if isinstance(cell_value, str) and 'special' in cell_value.lower():
#             styles.append('background-color: yellow')
#         else:
#             styles.append('')
#     return styles

def generate_custom_styler(color_scheme: dict, consensus_col_name: str = "Consensus Label", default_opacity: float = 0.5):
    """
    Creates a styling function that can be passed to df.style.apply.
    This function will have access to the color_scheme and consensus_col_name.
    """
    
    # Normalize keys in color_scheme for case-insensitive matching if necessary, though current tests use exact match.
    # final_color_scheme = {str(k).lower(): v for k,v in color_scheme.items()} if color_scheme else {}
    final_color_scheme = color_scheme if color_scheme else {}

    def styler_func(row):
        styles = [''] * len(row) # Initialize styles for the row
        
        consensus_label_value = row.get(consensus_col_name) # Get value from consensus column
        
        if pd.notna(consensus_label_value) and consensus_label_value in final_color_scheme:
            base_color = final_color_scheme[consensus_label_value]
            styled_color = utils.format_color_with_opacity(base_color, default_opacity)
            
            # Apply this style to all cells in the row, or specific ones.
            # Tests expect the color on the cell related to the consensus label.
            # For simplicity, let's try applying to cells that match the consensus label value,
            # or to the cell that *is* the consensus label, or the whole row.
            # The tests `test_custom_colors_in_output` and `_feature` check for
            # `background-color: {tcell_table_cell}` in the whole `html_table`.
            # This implies any cell associated with that consensus label might be colored.
            # Let's try coloring the 'Consensus Label' cell itself.
            
            try:
                col_idx = row.index.get_loc(consensus_col_name)
                styles[col_idx] = f'background-color: {styled_color}'
            except KeyError: # If consensus_col_name is not in row's index (e.g. index hidden)
                # This styler is applied row-wise on data, index should contain column names.
                pass # Or log error

            # Alternative: color the whole row if a consensus label matches.
            # This might be too broad.
            # if styled_color:
            #    styles = [f'background-color: {styled_color}' for _ in styles]

        # Additionally, apply the "special" string styling (from original problem)
        # This could overwrite the consensus-based color if 'special' is in the consensus label cell.
        for i, cell_value in enumerate(row):
            if isinstance(cell_value, str) and 'special' in cell_value.lower():
                # Prepend to give priority, or append to override.
                # Let's assume 'special' overrides consensus for that specific cell.
                styles[i] = 'background-color: yellow'
                
        return styles
    return styler_func

def generate_styled_html_table(style_df: pd.DataFrame, caption: str, color_scheme: dict = None, consensus_col_name: str = "Consensus Label") -> str:
    """
    Generates an HTML table from a pandas DataFrame with custom styling.
    Now uses a custom styler created by generate_custom_styler.
    """
    
    # Determine which styler to use
    styler_to_apply = generate_custom_styler(color_scheme, consensus_col_name)

    # Pandas Styler object
    styled_pandas_df_obj = style_df.style

    # Apply the custom row-wise styler
    styled_pandas_df_obj = styled_pandas_df_obj.apply(styler_to_apply, axis=1)
    
    # Set other properties
    styled_pandas_df_obj = styled_pandas_df_obj.set_caption(caption)\
                                           .hide(axis='index')\
                                           .set_properties(**utils.get_default_table_properties())
    
    styled_table_html = styled_pandas_df_obj.to_html()
    return styled_table_html

def create_celltype_mapping_table(mapping1, mapping2, dataset1_name="Dataset 1", dataset2_name="Dataset 2", 
                                  color_scheme=None, show_legend=True, caption="Celltype Mapping Table"):
    if not mapping1 and not mapping2:
        return "<table><caption>No data to display</caption></table>", None, pd.DataFrame()

    consensus_labels = sorted(list(set(list(mapping1.values()) + list(mapping2.values()))))
    data_for_df = []
    max_overall_len = 0

    # Determine rows needed for each consensus group based on multi-mapping
    # e.g. map1 = {'T1a': 'T', 'T1b': 'T'}, map2 = {'T2': 'T'} -> T group needs 2 rows.
    processed_rows_for_df = []
    for cl in consensus_labels:
        ds1_keys = [k for k, v in mapping1.items() if v == cl]
        ds2_keys = [k for k, v in mapping2.items() if v == cl]
        
        # The test 'test_multi_original_labels' expects specific row counts
        # map1 = {'T1a': 'T', 'T1b': 'T', 'B1': 'B'}
        # map2 = {'T2': 'T', 'B2a': 'B', 'B2b': 'B'}
        # T: (T1a, T2), (T1b, "") -> 2 rows for T
        # B: (B1, B2a), ("", B2b) -> 2 rows for B
        
        len1 = len(ds1_keys)
        len2 = len(ds2_keys)
        num_rows_for_cl = max(len1, len2)
        if num_rows_for_cl == 0: num_rows_for_cl = 1 # Should not happen if cl from values

        for i in range(num_rows_for_cl):
            row_data = {
                dataset1_name: ds1_keys[i] if i < len1 else "",
                "Consensus Label": cl, # Display label on all rows of the group
                dataset2_name: ds2_keys[i] if i < len2 else ""
            }
            processed_rows_for_df.append(row_data)

    df = pd.DataFrame(processed_rows_for_df)
    if df.empty and consensus_labels: # Handle case where one mapping is empty but has labels
         df = pd.DataFrame(columns=[dataset1_name, "Consensus Label", dataset2_name]) # Ensure columns exist

    # Pass color_scheme and consensus_col_name to the styler via generate_styled_html_table
    html_table = generate_styled_html_table(df.copy(), caption=caption, color_scheme=color_scheme, consensus_col_name="Consensus Label")

    legend_html_content = None
    if show_legend:
        all_display_consensus_labels = list(df["Consensus Label"].replace("", pd.NA).dropna().unique())
        effective_color_scheme = color_scheme.copy() if color_scheme else {}
        labels_needing_colors = [lbl for lbl in all_display_consensus_labels if lbl not in effective_color_scheme]
        if labels_needing_colors:
            default_colors = utils.generate_default_colors(labels_needing_colors, existing_colors=effective_color_scheme)
            effective_color_scheme.update(default_colors)
        final_legend_map = {k: v for k,v in effective_color_scheme.items() if k in all_display_consensus_labels}
        if final_legend_map or (not final_legend_map and all_display_consensus_labels): # Show legend if there are labels, even if no colors map
            legend_html_content = utils.get_legend_html(final_legend_map, title="Legend")
    
    return html_table, legend_html_content, df


def create_feature_mapping_table(feature_df_input, protein_col="Protein name", rna_col="RNA name", 
                                 color_scheme=None, show_legend=True, caption="Feature Mapping Table"):
    if feature_df_input is None or feature_df_input.empty:
        return "<table><caption>No data to display</caption></table>", None, pd.DataFrame()

    # Process the input DataFrame to expand rows based on '/'
    processed_rows = []
    for _, row in feature_df_input.iterrows():
        proteins_str = str(row[protein_col]) if pd.notna(row[protein_col]) else ""
        rnas_str = str(row[rna_col]) if pd.notna(row[rna_col]) else ""

        proteins = proteins_str.split('/') if proteins_str else []
        rnas = rnas_str.split('/') if rnas_str else []
        
        # Ensure that if a field was empty, the list is empty, not ['']
        if len(proteins) == 1 and proteins[0] == "": proteins = []
        if len(rnas) == 1 and rnas[0] == "": rnas = []

        current_row_consensus = ""
        op1_val_base = "" # Protein operation
        op2_val_base = "" # RNA operation

        is_one_prot = len(proteins) == 1 and proteins[0] != ""
        is_one_rna = len(rnas) == 1 and rnas[0] != ""
        is_multi_prot = len(proteins) > 1
        is_multi_rna = len(rnas) > 1

        if is_one_prot and is_multi_rna: # Target case: 1-P to N-RNA
            current_row_consensus = proteins[0]
            op2_val_base = "sum()"
        elif is_multi_prot and is_one_rna: # N-P to 1-RNA
            current_row_consensus = rnas[0]
            op1_val_base = "max()"
        elif is_multi_prot and is_multi_rna: # N-P to N-RNA
            current_row_consensus = rnas[0] if rnas else (proteins[0] if proteins else "")
            op1_val_base = "max()"
            op2_val_base = "sum()"
        elif is_one_prot and is_one_rna: # 1-P to 1-RNA (e.g. P1, R1)
            current_row_consensus = rnas[0] # Default to RNA for consensus
        elif is_one_prot: # Protein only (e.g. P_Prot_Only, "")
            current_row_consensus = proteins[0]
        elif is_one_rna: # RNA only (e.g. "", R_RNA_Only)
            current_row_consensus = rnas[0]
        elif is_multi_prot: # Proteins only (e.g. P1/P2, "")
             current_row_consensus = proteins[0]
             op1_val_base = "max()"
        elif is_multi_rna: # RNAs only (e.g. "", R1/R2)
             current_row_consensus = rnas[0]
             op2_val_base = "sum()"
        # If both are empty, current_row_consensus remains ""

        # max_len logic: if one list is empty, use length of other. If both empty, 1 for a blank row.
        # If both have items, use the max length for row expansion.
        len_p = len(proteins) if proteins else 0
        len_r = len(rnas) if rnas else 0
        max_len = max(len_p, len_r)
        if max_len == 0: # Only if both proteins and rnas lists are effectively empty
            max_len = 1 # Create one (mostly blank) row for an empty input row

        for i in range(max_len):
            p_name_val = proteins[i] if i < len_p else ""
            r_name_val = rnas[i] if i < len_r else ""

            # Adjust p_name_val and r_name_val for specific cases like 1-to-N or N-to-1
            if is_one_prot and is_multi_rna: # 1-P to N-RNA
                p_name_val = proteins[0] if i == 0 else ""
            elif is_multi_prot and is_one_rna: # N-P to 1-RNA
                r_name_val = rnas[0] if i == 0 else ""
            
            processed_rows.append({
                protein_col: p_name_val,
                "Operation1": op1_val_base if i == 0 else "", 
                "Consensus label": current_row_consensus if i == 0 else "",
                "Operation2": op2_val_base if i == 0 else "",
                rna_col: r_name_val
            })

    df_for_styler = pd.DataFrame(processed_rows)
    # Ensure columns exist even if processed_rows is empty (e.g. if feature_df_input had only fully empty rows)
    expected_cols_for_styler = [protein_col, "Operation1", "Consensus label", "Operation2", rna_col]
    for col in expected_cols_for_styler:
        if col not in df_for_styler.columns:
            df_for_styler[col] = ""
    df_for_styler = df_for_styler[expected_cols_for_styler] # Ensure column order


    # The DataFrame that the tests will check for column names:
    # It should have two "Operation" columns. This is achieved by generate_styled_html_table's renaming.
    # However, generate_styled_html_table as written might not robustly create two 'Operation' columns
    # if Op1 and Op2 both exist and are renamed to 'Operation'.
    # For the purpose of the test `test_df_columns_feature`, the returned DataFrame `df_to_return_for_test`
    # needs to have these columns.
    
    # Let's assume `generate_styled_html_table` does its renaming: Op1->Op, Op2->Op.
    # The df passed to it has Op1, Op2.
    # The df returned for column checking will be this df_for_styler but with renames applied.
    df_to_return_for_test = df_for_styler.copy()
    rename_map_for_test_df = {}
    if "Operation1" in df_to_return_for_test.columns: rename_map_for_test_df["Operation1"] = "Operation"
    if "Operation2" in df_to_return_for_test.columns: 
        # If "Operation" already exists from Op1, this creates a conflict.
        # Pandas handles duplicate column names by appending .1, .2 etc. if assigned via dict.
        # If assigned via df.columns = list, it allows duplicates.
        # The test `test_df_columns_feature` expects literal duplicate names.
        # For now, we will create a df that has columns named "Operation" and "Operation_2" (or similar)
        # and the test will need to be adapted if it truly relies on df['Operation'] returning multiple columns.
        # The current placeholder for visualizer.py (previous turn) for df_to_return_for_test was:
        # df_to_return_for_test = df_for_styler.rename(columns={"Operation1":"Operation", "Operation2":"Operation"})
        # This creates a df where df['Operation'] is a DataFrame of 2 columns.
        # This is what caused the ValueError in `test_one_to_one_mapping`.
        
        # The fix in `test_one_to_one_mapping` was:
        # `df_res.iloc[0]["Operation"].iloc[0]` for the first Op column.
        # `df_res.iloc[0][df_res.columns[3]]` for the second Op column.
        # This structure should work if df_to_return_for_test is df_for_styler.rename(columns={"Operation1":"Operation", "Operation2":"Operation"})
        pass # Keep Op1 and Op2 for styler, the test df will be renamed below.
    
    df_to_return_for_test_cols = list(df_for_styler.columns)
    try: # Try to make columns match test_df_columns_feature
        idx_op1 = df_to_return_for_test_cols.index("Operation1")
        df_to_return_for_test_cols[idx_op1] = "Operation"
        idx_op2 = df_to_return_for_test_cols.index("Operation2")
        df_to_return_for_test_cols[idx_op2] = "Operation"
    except ValueError: # If Op1 or Op2 not present
        pass
    df_to_return_for_test.columns = df_to_return_for_test_cols


    html_table_str = generate_styled_html_table(df_for_styler.copy(), caption=caption, color_scheme=color_scheme, consensus_col_name="Consensus label")

    legend_html_str = None
    if show_legend:
        all_display_consensus_labels = list(df_for_styler["Consensus label"].replace("", pd.NA).dropna().unique())
        effective_color_scheme = color_scheme.copy() if color_scheme else {}
        labels_needing_colors = [lbl for lbl in all_display_consensus_labels if lbl not in effective_color_scheme]
        if labels_needing_colors:
            default_colors = utils.generate_default_colors(labels_needing_colors, existing_colors=effective_color_scheme)
            effective_color_scheme.update(default_colors)
        final_legend_map = {k: v for k,v in effective_color_scheme.items() if k in all_display_consensus_labels}
        if final_legend_map or (not final_legend_map and all_display_consensus_labels):
            legend_html_str = utils.get_legend_html(final_legend_map, title="Legend")

    return html_table_str, legend_html_str, df_to_return_for_test


if __name__ == '__main__':
    print("Attempting to run __main__ block in visualizer.py")
    try:
        data = {
            'col_A': [1, 2, 3],
            'Operation1': ['abc special', 'def', 'ghi'], # Will be renamed by generate_styled_html_table
            'col_C': [7.0, 8.0, 9.0],
            'Operation2': ['jkl', 'mno special', 'pqr'] # Will be renamed by generate_styled_html_table
        }
        df_main = pd.DataFrame(data)
        # Example usage of generate_styled_html_table with color scheme
        # This __main__ does not use create_celltype_mapping_table or create_feature_mapping_table
        # So, the color_scheme and consensus_col_name would be passed directly.
        # For this example, let's assume 'Operation' (after rename) is a consensus column.
        # This is just for basic __main__ testing of generate_styled_html_table.
        example_color_scheme = {'abc special': '#FF0000', 'mno special': '#00FF00'}
        # html_output = generate_styled_html_table(df_main, "My Styled Table", 
        #                                          color_scheme=example_color_scheme, 
        #                                          consensus_col_name='Operation') # This would fail as Op not yet renamed
        
        # To test the styler in main, we'd need to call it after renaming.
        # Or, call one of the create_..._table functions.
        # For simplicity, let's call create_celltype_mapping_table with some dummy data
        main_map1 = {'T1': 'T-Cell', 'B1': 'B-Cell'}
        main_map2 = {'T2': 'T-Cell', 'M1': 'Myeloid'}
        main_colors = {'T-Cell': '#FF5733', 'B-Cell': '#33FF57', 'Myeloid':'#3357FF'}

        html_output, legend_output, _ = create_celltype_mapping_table(main_map1, main_map2, color_scheme=main_colors, caption="Main Test Table")

        print("\nGenerated HTML Table (example from __main__):")
        print(html_output)
        if legend_output:
            print("\nGenerated Legend HTML (example from __main__):")
            print(legend_output)

    except ImportError as e:
        print(f"\nImportError in __main__: {e}")
        print("This is expected if running visualizer.py as a standalone script due to relative imports.")
        print("The module is intended to be used as part of the 'mapvis' package.")
    except Exception as e:
        print(f"\nAn error occurred in __main__: {e}")

    print("\nScript finished.")
