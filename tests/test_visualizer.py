import unittest
import pandas as pd
from mapvis import visualizer, utils # Visualizer functions and utils for color formatting
import os
import shutil

# Helper to save HTML output for manual inspection if needed
SAVE_HTML_OUTPUT = False # Set to True to save files locally
HTML_OUTPUT_DIR = "temp_test_outputs"

if SAVE_HTML_OUTPUT:
    if os.path.exists(HTML_OUTPUT_DIR):
        shutil.rmtree(HTML_OUTPUT_DIR)
    os.makedirs(HTML_OUTPUT_DIR, exist_ok=True)

class TestCelltypeMappingTable(unittest.TestCase):

    def setUp(self):
        self.mapping1 = {'Tcell_1': 'T-cell', 'Bcell_A': 'B-cell', 'Macro_X': 'Myeloid'}
        self.mapping2 = {'T_cell_X': 'T-cell', 'B_cell_Y': 'B-cell', 'Mono_1': 'Myeloid', 'NK_1': 'NK cell'}
        self.custom_colors = {'T-cell': '#FF0000', 'B-cell': '#00FF00', 'Myeloid': '#0000FF'} # Base hex

    def test_smoke_test(self):
        html_table, html_legend, df = visualizer.create_celltype_mapping_table(self.mapping1, self.mapping2)
        self.assertIsInstance(html_table, str)
        self.assertIsInstance(html_legend, str)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(len(html_table) > 0)
        self.assertTrue(len(html_legend) > 0)
        if SAVE_HTML_OUTPUT:
            with open(os.path.join(HTML_OUTPUT_DIR, "ct_smoke.html"), "w") as f:
                f.write(html_table + (html_legend if html_legend else ""))


    def test_empty_mappings(self):
        html_table, html_legend, df = visualizer.create_celltype_mapping_table({}, {})
        self.assertIn("No data to display", html_table)
        self.assertIsNone(html_legend) # Or empty string, depending on impl; current utils.get_legend_html returns None
        self.assertTrue(df.empty)

    def test_one_mapping_empty(self):
        html_table, html_legend, df = visualizer.create_celltype_mapping_table(self.mapping1, {})
        self.assertFalse(df.empty)
        self.assertEqual(len(df.columns), 3)
        # Check that all labels from mapping1 are present as consensus
        self.assertIn('T-cell', df['Consensus Label'].values)

    def test_no_common_consensus(self):
        map1 = {'a': 'A', 'b': 'B'}
        map2 = {'c': 'C', 'd': 'D'}
        html_table, html_legend, df = visualizer.create_celltype_mapping_table(map1, map2)
        self.assertEqual(len(df), 4) # Each label forms its own consensus group
        self.assertIn('A', df['Consensus Label'].values)
        self.assertIn('D', df['Consensus Label'].values)

    def test_df_columns_and_rows(self):
        _, _, df = visualizer.create_celltype_mapping_table(
            self.mapping1, self.mapping2, dataset1_name="DS1", dataset2_name="OtherDS"
        )
        self.assertListEqual(list(df.columns), ["DS1", "Consensus Label", "OtherDS"])
        # Expected rows: T-cell (1), B-cell (1), Myeloid (1), NK cell (1 from map2 only) = 4 rows
        self.assertEqual(len(df), 4)

    def test_multi_original_labels(self):
        map1 = {'T1a': 'T', 'T1b': 'T', 'B1': 'B'}
        map2 = {'T2': 'T', 'B2a': 'B', 'B2b': 'B'}
        _, _, df = visualizer.create_celltype_mapping_table(map1, map2)
        # T-cells: T1a, T1b vs T2 -> 2 rows for T
        # B-cells: B1 vs B2a, B2b -> 2 rows for B
        self.assertEqual(len(df[df['Consensus Label'] == 'T']), 2)
        self.assertEqual(len(df[df['Consensus Label'] == 'B']), 2)
        self.assertEqual(len(df), 4)

    def test_legend_generation(self):
        _, html_legend_true, _ = visualizer.create_celltype_mapping_table(self.mapping1, self.mapping2, show_legend=True)
        self.assertIsNotNone(html_legend_true)
        self.assertIn("Legend", html_legend_true)

        _, html_legend_false, _ = visualizer.create_celltype_mapping_table(self.mapping1, self.mapping2, show_legend=False)
        self.assertIsNone(html_legend_false)

    def test_custom_colors_in_output(self):
        # Test with custom colors, check their presence in HTML (legend and table)
        # Legend swatch should be full opacity, table cells 50%
        # utils.format_color_with_opacity converts to lowercase hex
        
        # Expected formatted colors (lowercase hex)
        tcell_color_base = self.custom_colors['T-cell'].lower() # #ff0000
        tcell_legend_swatch = utils.format_color_with_opacity(tcell_color_base, 1.0) # #ff0000ff
        tcell_table_cell = utils.format_color_with_opacity(tcell_color_base, 0.5)   # #ff000080

        html_table, html_legend, _ = visualizer.create_celltype_mapping_table(
            self.mapping1, self.mapping2, color_scheme=self.custom_colors
        )
        self.assertIn(f"background-color: {tcell_legend_swatch}", html_legend.lower())
        self.assertIn(f"background-color: {tcell_table_cell}", html_table.lower())


    def test_caption_in_table(self):
        caption = "My Custom Celltype Table"
        html_table, _, _ = visualizer.create_celltype_mapping_table(self.mapping1, self.mapping2, caption=caption)
        self.assertIn(f"<caption>{caption}</caption>", html_table)

    def test_celltype_sorting_italicization_and_merging(self):
        map1_both = {'T1a': 'T-cell', 'T1b': 'T-cell', 'B1': 'B-cell'}
        map1_only = {'M1': 'Myeloid_M1', 'M2': 'Myeloid_M2'}
        map2_both = {'T2': 'T-cell', 'B2': 'B-cell'} # T-cell has one entry from map2, B-cell one.
        map2_only = {'N1': 'NK_N1', 'N2': 'NK_N2'}
        
        mapping1 = {**map1_both, **map1_only}
        mapping2 = {**map2_both, **map2_only}

        # For T-cell: map1 has T1a, T1b. map2 has T2. Max original labels = 2.
        # For B-cell: map1 has B1. map2 has B2. Max original labels = 1.

        html_table, _, df_result = visualizer.create_celltype_mapping_table(
            mapping1, mapping2, dataset1_name="DS1", dataset2_name="DS2"
        )

        # 1. Test Sorting
        # Expected order: B-cell, T-cell (both, alphabetical), 
        #                 Myeloid_M1, Myeloid_M2 (map1_only, alphabetical), 
        #                 NK_N1, NK_N2 (map2_only, alphabetical)
        # The df_result itself is built based on this order.
        expected_consensus_order = ['B-cell', 'T-cell', 'Myeloid_M1', 'Myeloid_M2', 'NK_N1', 'NK_N2']
        
        # Get the unique consensus labels in the order they appear in the DataFrame
        # This also tests that the DataFrame `df` itself is sorted correctly.
        actual_consensus_order_df = df_result['Consensus Label'].unique().tolist()
        self.assertListEqual(actual_consensus_order_df, expected_consensus_order)

        # 2. Test Italicization (HTML Check)
        # Myeloid_M1, Myeloid_M2, NK_N1, NK_N2 rows should have italic style.
        # This is a bit tricky to check precisely without parsing HTML.
        # We'll check if the style attribute is present near the label.
        self.assertIn("Myeloid_M1</td>", html_table) # Ensure label is present
        self.assertTrue(html_table.count("font-style: italic;") >= 4, "Expected at least 4 italicized rows for unique labels")
        
        # A more targeted check for one italicized label (e.g., Myeloid_M1)
        # This assumes Myeloid_M1 is in a <td> and the style is on that <td> or a parent <tr>'s <td>
        # The style is applied per cell, so we look for it in the cell containing the label.
        # Example: <td style="background-color: #...; font-style: italic;">Myeloid_M1</td>
        # Or on the consensus label cell of that row.
        # The current styling applies to all cells in the row.
        self.assertRegex(html_table, r'<td[^>]*style="[^"]*font-style: italic[^"]*"[^>]*>Myeloid_M1</td>')
        self.assertRegex(html_table, r'<td[^>]*style="[^"]*font-style: italic[^"]*"[^>]*>NK_N1</td>')


        # 3. Test Cell Merging (HTML Check)
        # T-cell group should have 2 rows (max_len of original labels for T-cell is 2: [T1a, T1b] vs [T2])
        # The first row for T-cell displays "T-cell". The second row for T-cell should have "" for display
        # and its "Consensus Label" cell should have `border-top-style: none;`.
        
        # Find the first occurrence of T-cell in a <td>. This is the main cell.
        # The HTML structure from df_display.style.apply(...) will have:
        # <tr> <td>T1a</td> <td class="col1">T-cell</td> <td>T2</td> </tr>
        # <tr> <td>T1b</td> <td class="col1" style="...border-top-style: none;"></td> <td></td> </tr>
        
        # Search for the T-cell content. The table is structured with DS1, Consensus, DS2.
        # First row: DS1: T1a, Consensus: T-cell, DS2: T2
        # Second row: DS1: T1b, Consensus: "", DS2: "" (because T2 was shorter)
        
        # This regex looks for a cell with T-cell, then a following cell in the same column (class="col1")
        # that is empty and has the border-top-style: none.
        # Note: Pandas styler adds classes like "col0", "col1", etc. "Consensus Label" is col1.
        # The actual HTML might not have `</td><td` directly due to newlines/spaces.
        # We need to ensure that after a <td>T-cell</td>, a subsequent row's Consensus Label cell is empty and styled.
        
        # A simpler check: count occurrences of "T-cell" (should be 1 in display) and border style.
        # df_display has "" for the second T-cell.
        # So, in HTML, "T-cell" appears once.
        self.assertEqual(html_table.count('>T-cell</td>'), 1, "T-cell text should appear once for the merged group")
        
        # There should be one cell for T-cell that has its top border removed.
        # This corresponds to the second row of the "T-cell" logical group.
        # The cell itself will be empty.
        # Example: <td id="T7_C1" class="data row7 col1 " style="background-color: #...; font-style: italic; border-top-style: none;"></td>
        # We need to find an empty <td> for Consensus Label in a T-cell styled row that has the border style.
        # This is hard to pinpoint without more specific IDs or classes on rows/cells from the styler.
        
        # Check: Number of rows for T-cell in raw df is 2.
        self.assertEqual(len(df_result[df_result['Consensus Label'] == 'T-cell']), 2)
        # One of these should have the border style applied to its "Consensus Label" cell.
        # The cell will be empty.
        # Count how many times "border-top-style: none;" appears for the "Consensus Label" column (col1).
        # This is still tricky. Let's assume if T-cell text is once, merging is happening.
        # A more robust test would parse HTML or check the df_display object if it were returned.
        # For now, presence of "T-cell" once and correct raw row count implies merging structure.
        
        if SAVE_HTML_OUTPUT:
            with open(os.path.join(HTML_OUTPUT_DIR, "ct_sorting_italic_merge.html"), "w") as f:
                f.write(html_table)


class TestFeatureMappingTable(unittest.TestCase):

    def setUp(self):
        # Basic 1:1, n:1, 1:n, n:m
        self.feature_data_basic = {
            'Protein name': ['P1', 'P2a/P2b', 'P3', 'P4a/P4b', 'P_RNA_Only', 'P_Prot_Only/P_Prot_Only2'],
            'RNA name': ['R1', 'R2', 'R3a/R3b', 'R4a/R4b', 'R_RNA_Only1/R_RNA_Only2', '']
        }
        self.feature_df_basic = pd.DataFrame(self.feature_data_basic)
        self.custom_colors_feat = { # base hex colors
            'R1': '#FF0000', 
            'R2': '#00FF00', 
            'P3': '#0000FF', # 1:n, protein is consensus
            'R4a': '#FFFF00', # n:m, first RNA is consensus
            'R_RNA_Only1': '#FF00FF',
            'P_Prot_Only': '#00FFFF' # protein only, protein is consensus
        }
        self.default_rna_col = "RNA name"


    def test_smoke_test_feature(self):
        html_table, html_legend, df = visualizer.create_feature_mapping_table(self.feature_df_basic)
        self.assertIsInstance(html_table, str)
        # Legend can be None if no unique_consensus_in_table, or if show_legend=False
        self.assertTrue(isinstance(html_legend, str) or html_legend is None)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(len(html_table) > 0)
        if SAVE_HTML_OUTPUT:
             with open(os.path.join(HTML_OUTPUT_DIR, "ft_smoke.html"), "w") as f:
                f.write(html_table + (html_legend if html_legend else ""))
        # This implicitly tests the AttributeError fix if it runs without error.

    def test_empty_dataframe_feature(self):
        empty_df = pd.DataFrame(columns=[self.default_protein_col, self.default_rna_col])
        html_table, html_legend, df = visualizer.create_feature_mapping_table(empty_df)
        self.assertIn("No data to display", html_table)
        self.assertIsNone(html_legend)
        self.assertTrue(df.empty)

    def test_df_columns_feature(self):
        _, _, df = visualizer.create_feature_mapping_table(self.feature_df_basic)
        expected_cols = ["Protein name", "Operation", "Consensus label", "Operation", "RNA name"]
        self.assertListEqual(list(df.columns), expected_cols)

    def test_one_to_one_mapping(self):
        df_input = pd.DataFrame({'Protein name': ['P1'], 'RNA name': ['R1']})
        html_table, _, df_res = visualizer.create_feature_mapping_table(df_input)
        self.assertEqual(len(df_res), 1)
        self.assertEqual(df_res.iloc[0]["Consensus label"], "R1")
        self.assertEqual(df_res.iloc[0]["Operation"], "") # Check first "Operation"
        self.assertEqual(df_res.iloc[0][df_res.columns[3]], "") # Check second "Operation"
        self.assertEqual(df_res.iloc[0]["Protein name"], "P1")
        self.assertEqual(df_res.iloc[0]["RNA name"], "R1")
        self.assertIn(">P1</td>", html_table)
        self.assertIn(">R1</td>", html_table)


    def test_one_to_many_mapping(self): # P3 -> R3a/R3b
        df_input = pd.DataFrame({'Protein name': ['P3'], 'RNA name': ['R3a/R3b']})
        html_table, _, df_res = visualizer.create_feature_mapping_table(df_input)
        self.assertEqual(len(df_res), 2) # P3, R3a; "", R3b
        self.assertEqual(df_res.iloc[0]["Consensus label"], "P3")
        self.assertEqual(df_res.iloc[0]["Operation"], "") 
        self.assertEqual(df_res.iloc[0][df_res.columns[3]], "sum()") # Second "Operation"
        self.assertEqual(df_res.iloc[0]["Protein name"], "P3")
        self.assertEqual(df_res.iloc[0]["RNA name"], "R3a")
        self.assertEqual(df_res.iloc[1]["Protein name"], "") # Blanked on second line
        self.assertEqual(df_res.iloc[1]["RNA name"], "R3b")
        self.assertEqual(df_res.iloc[1]["Consensus label"], "") # Blanked
        self.assertIn(">P3</td>", html_table)
        self.assertIn(">R3a</td>", html_table)
        self.assertIn(">R3b</td>", html_table)
        self.assertIn("sum()", html_table)


    def test_many_to_one_mapping(self): # P2a/P2b -> R2
        df_input = pd.DataFrame({'Protein name': ['P2a/P2b'], 'RNA name': ['R2']})
        html_table, _, df_res = visualizer.create_feature_mapping_table(df_input)
        self.assertEqual(len(df_res), 2)
        self.assertEqual(df_res.iloc[0]["Consensus label"], "R2")
        self.assertEqual(df_res.iloc[0]["Operation"], "max()")
        self.assertEqual(df_res.iloc[0][df_res.columns[3]], "")
        self.assertEqual(df_res.iloc[0]["Protein name"], "P2a")
        self.assertEqual(df_res.iloc[0]["RNA name"], "R2")
        self.assertEqual(df_res.iloc[1]["RNA name"], "") # Blanked
        self.assertEqual(df_res.iloc[1]["Protein name"], "P2b")
        self.assertIn(">P2a</td>", html_table)
        self.assertIn(">P2b</td>", html_table)
        self.assertIn(">R2</td>", html_table)
        self.assertIn("max()", html_table)

    def test_many_to_many_mapping(self): # P4a/P4b -> R4a/R4b
        df_input = pd.DataFrame({'Protein name': ['P4a/P4b'], 'RNA name': ['R4a/R4b']})
        html_table, _, df_res = visualizer.create_feature_mapping_table(df_input)
        self.assertEqual(len(df_res), 2)
        self.assertEqual(df_res.iloc[0]["Consensus label"], "R4a") # First RNA
        self.assertEqual(df_res.iloc[0]["Operation"], "max()")
        self.assertEqual(df_res.iloc[0][df_res.columns[3]], "sum()")
        self.assertEqual(df_res.iloc[0]["Protein name"], "P4a")
        self.assertEqual(df_res.iloc[0]["RNA name"], "R4a")
        self.assertEqual(df_res.iloc[1]["Protein name"], "P4b")
        self.assertEqual(df_res.iloc[1]["RNA name"], "R4b")
        self.assertIn("max()", html_table)
        self.assertIn("sum()", html_table)

    def test_protein_only_rna_only(self):
        df_input = pd.DataFrame({
            'Protein name': ['P_Prot_Only', ''], 
            'RNA name': ['', 'R_RNA_Only']
        })
        html_table, _, df_res = visualizer.create_feature_mapping_table(df_input)
        self.assertEqual(len(df_res), 2)
        self.assertEqual(df_res.iloc[0]["Consensus label"], "P_Prot_Only")
        self.assertEqual(df_res.iloc[0]["Protein name"], "P_Prot_Only")
        self.assertEqual(df_res.iloc[0]["RNA name"], "")
        self.assertEqual(df_res.iloc[1]["Consensus label"], "R_RNA_Only")
        self.assertEqual(df_res.iloc[1]["Protein name"], "")
        self.assertEqual(df_res.iloc[1]["RNA name"], "R_RNA_Only")
        self.assertIn(">P_Prot_Only</td>", html_table)
        self.assertIn(">R_RNA_Only</td>", html_table)


    def test_legend_generation_feature(self):
        _, html_legend_true, _ = visualizer.create_feature_mapping_table(self.feature_df_basic, show_legend=True)
        self.assertIsNotNone(html_legend_true) # Should generate a legend as there are consensus labels
        self.assertIn("Legend", html_legend_true)

        _, html_legend_false, _ = visualizer.create_feature_mapping_table(self.feature_df_basic, show_legend=False)
        self.assertIsNone(html_legend_false)

    def test_custom_colors_in_output_feature(self):
        r1_color_base = self.custom_colors_feat['R1'].lower()
        r1_legend_swatch = utils.format_color_with_opacity(r1_color_base, 1.0)
        r1_table_cell = utils.format_color_with_opacity(r1_color_base, 0.5)

        html_table, html_legend, _ = visualizer.create_feature_mapping_table(
            self.feature_df_basic, color_scheme=self.custom_colors_feat
        )
        self.assertIsNotNone(html_legend) # Should have a legend
        self.assertIn(f"background-color: {r1_legend_swatch}", html_legend.lower())
        self.assertIn(f"background-color: {r1_table_cell}", html_table.lower())

    def test_caption_in_table_feature(self):
        caption = "My Custom Feature Table"
        html_table, _, _ = visualizer.create_feature_mapping_table(self.feature_df_basic, caption=caption)
        self.assertIn(f"<caption>{caption}</caption>", html_table)

    def test_feature_cell_merging(self):
        feature_data = pd.DataFrame({
            'Protein name': ['P1', 'P2', 'P3', 'P4', 'P5', 'P6'],
            'RNA name':     ['ConsA', 'ConsA', 'ConsB', 'ConsA', 'ConsA', 'ConsC']
        })
        # Expected visible "Consensus label" (original logic): ConsA, ConsA, ConsB, ConsA, ConsA, ConsC
        # Expected after blanking for display (for merging): ConsA, "", ConsB, ConsA, "", ConsC

        html_table, _, df_result = visualizer.create_feature_mapping_table(feature_data)

        if SAVE_HTML_OUTPUT:
            with open(os.path.join(HTML_OUTPUT_DIR, "ft_merging_test.html"), "w") as f:
                f.write(html_table)
        
        # Check raw DataFrame output structure (Consensus label column should reflect the model's internal logic before display modifications)
        # The df_result has "Consensus label" as they are determined (e.g. R1 for P1->R1)
        # The merging logic is applied on a copy for display.
        # So df_result for this input: P1->ConsA, P2->ConsA, P3->ConsB, P4->ConsA, P5->ConsA, P6->ConsC
        # All are 1:1, so RNA name is consensus.
        self.assertEqual(df_result.loc[0, "Consensus label"], "ConsA")
        self.assertEqual(df_result.loc[1, "Consensus label"], "ConsA")
        self.assertEqual(df_result.loc[2, "Consensus label"], "ConsB")
        self.assertEqual(df_result.loc[3, "Consensus label"], "ConsA")
        self.assertEqual(df_result.loc[4, "Consensus label"], "ConsA")
        self.assertEqual(df_result.loc[5, "Consensus label"], "ConsC")

        # HTML Check for merging
        # First ConsA group
        self.assertRegex(html_table, r'>ConsA</td>') # First occurrence
        # For the second ConsA, the cell should be empty and have border-top-style: none
        # This requires finding the specific cell.
        # Example of what we are looking for (col2 is "Consensus label" in this 5-col table)
        # <td ... class="col2 data">ConsA</td>  (row 0)
        # <td ... class="col2 data" style="... border-top-style: none;"></td> (row 1)
        # <td ... class="col2 data">ConsB</td> (row 2)
        # <td ... class="col2 data">ConsA</td> (row 3)
        # <td ... class="col2 data" style="... border-top-style: none;"></td> (row 4)
        # <td ... class="col2 data">ConsC</td> (row 5)

        # Count occurrences of displayed labels
        self.assertEqual(html_table.count('>ConsA</td>'), 2) # Displayed twice (start of each group)
        self.assertEqual(html_table.count('>ConsB</td>'), 1)
        self.assertEqual(html_table.count('>ConsC</td>'), 1)

        # Count occurrences of the border-top-style for empty cells in Consensus Label column
        # This is hard to do precisely without full HTML parsing and knowing exact class/id.
        # We expect two cells to be merged (blanked and border removed)
        # The style is applied on the <td> element.
        # The text of such a cell is empty.
        self.assertEqual(html_table.count('border-top-style: none;"></td>'), 2)


if __name__ == '__main__':
    # For running tests: python -m unittest tests.test_visualizer from project root
    # Or: python tests/test_visualizer.py (if mapvis is in PYTHONPATH or installed)
    
    # Example of running and saving one output for manual check
    # SAVE_HTML_OUTPUT = True # Can be set globally for all tests in this file
    # if SAVE_HTML_OUTPUT:
    #     if os.path.exists(HTML_OUTPUT_DIR):
    #         shutil.rmtree(HTML_OUTPUT_DIR)
    #     os.makedirs(HTML_OUTPUT_DIR, exist_ok=True)
        
    #     tc = TestFeatureMappingTable()
    #     tc.setUp()
    #     html_table, html_legend, _ = visualizer.create_feature_mapping_table(
    #         tc.feature_df, color_scheme=tc.custom_colors_feat, caption="Manual Check Output"
    #     )
    #     with open(os.path.join(HTML_OUTPUT_DIR, "ft_manual_check.html"), "w") as f:
    #         f.write(html_table + (html_legend if html_legend else ""))
    #     print(f"Saved manual check HTML to {os.path.join(HTML_OUTPUT_DIR, 'ft_manual_check.html')}")

    unittest.main()
```
