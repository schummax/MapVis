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


class TestFeatureMappingTable(unittest.TestCase):

    def setUp(self):
        # Basic 1:1, n:1, 1:n, n:m
        self.feature_data = {
            'Protein name': ['P1', 'P2a/P2b', 'P3', 'P4a/P4b', 'P_RNA_Only', 'P_Prot_Only/P_Prot_Only2'],
            'RNA name': ['R1', 'R2', 'R3a/R3b', 'R4a/R4b', 'R_RNA_Only1/R_RNA_Only2', '']
        }
        self.feature_df = pd.DataFrame(self.feature_data)
        self.custom_colors_feat = { # base hex colors
            'R1': '#FF0000', 
            'R2': '#00FF00', 
            'P3': '#0000FF', # 1:n, protein is consensus
            'R4a': '#FFFF00', # n:m, first RNA is consensus
            'R_RNA_Only1': '#FF00FF',
            'P_Prot_Only': '#00FFFF'
        }
        self.default_protein_col = "Protein name"
        self.default_rna_col = "RNA name"


    def test_smoke_test_feature(self):
        html_table, html_legend, df = visualizer.create_feature_mapping_table(self.feature_df)
        self.assertIsInstance(html_table, str)
        self.assertIsInstance(html_legend, str) # Can be None if no valid consensus labels for legend
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(len(html_table) > 0)
        # self.assertTrue(len(html_legend) > 0 if html_legend else True) # Legend might be empty if no clear consensus
        if SAVE_HTML_OUTPUT:
             with open(os.path.join(HTML_OUTPUT_DIR, "ft_smoke.html"), "w") as f:
                f.write(html_table + (html_legend if html_legend else ""))


    def test_empty_dataframe_feature(self):
        empty_df = pd.DataFrame(columns=[self.default_protein_col, self.default_rna_col])
        html_table, html_legend, df = visualizer.create_feature_mapping_table(empty_df)
        self.assertIn("No data to display", html_table)
        self.assertIsNone(html_legend)
        self.assertTrue(df.empty)

    def test_df_columns_feature(self):
        _, _, df = visualizer.create_feature_mapping_table(self.feature_df)
        # After rename in visualizer.py, Operation1/2 become Operation
        expected_cols = ["Protein name", "Operation", "Consensus label", "Operation", "RNA name"]
        self.assertListEqual(list(df.columns), expected_cols)

    def test_one_to_one_mapping(self):
        df_input = pd.DataFrame({'Protein name': ['P1'], 'RNA name': ['R1']})
        _, _, df_res = visualizer.create_feature_mapping_table(df_input)
        self.assertEqual(len(df_res), 1)
        self.assertEqual(df_res.iloc[0]["Consensus label"], "R1")
        self.assertEqual(df_res.iloc[0]["Operation"], "") # Check first "Operation"
        self.assertEqual(df_res.iloc[0][df_res.columns[3]], "") # Check second "Operation"
        self.assertEqual(df_res.iloc[0]["Protein name"], "P1")
        self.assertEqual(df_res.iloc[0]["RNA name"], "R1")

    def test_one_to_many_mapping(self): # P3 -> R3a/R3b
        df_input = pd.DataFrame({'Protein name': ['P3'], 'RNA name': ['R3a/R3b']})
        _, _, df_res = visualizer.create_feature_mapping_table(df_input)
        self.assertEqual(len(df_res), 2) # P3, R3a; "", R3b
        self.assertEqual(df_res.iloc[0]["Consensus label"], "P3")
        self.assertEqual(df_res.iloc[0]["Operation"], "") 
        self.assertEqual(df_res.iloc[0][df_res.columns[3]], "sum()") # Second "Operation"
        self.assertEqual(df_res.iloc[0]["Protein name"], "P3")
        self.assertEqual(df_res.iloc[0]["RNA name"], "R3a")
        self.assertEqual(df_res.iloc[1]["Protein name"], "") # Blanked on second line
        self.assertEqual(df_res.iloc[1]["RNA name"], "R3b")
        self.assertEqual(df_res.iloc[1]["Consensus label"], "") # Blanked

    def test_many_to_one_mapping(self): # P2a/P2b -> R2
        df_input = pd.DataFrame({'Protein name': ['P2a/P2b'], 'RNA name': ['R2']})
        _, _, df_res = visualizer.create_feature_mapping_table(df_input)
        self.assertEqual(len(df_res), 2)
        self.assertEqual(df_res.iloc[0]["Consensus label"], "R2")
        self.assertEqual(df_res.iloc[0]["Operation"], "max()")
        self.assertEqual(df_res.iloc[0][df_res.columns[3]], "")
        self.assertEqual(df_res.iloc[0]["Protein name"], "P2a")
        self.assertEqual(df_res.iloc[0]["RNA name"], "R2")
        self.assertEqual(df_res.iloc[1]["RNA name"], "") # Blanked
        self.assertEqual(df_res.iloc[1]["Protein name"], "P2b")

    def test_many_to_many_mapping(self): # P4a/P4b -> R4a/R4b
        df_input = pd.DataFrame({'Protein name': ['P4a/P4b'], 'RNA name': ['R4a/R4b']})
        _, _, df_res = visualizer.create_feature_mapping_table(df_input)
        self.assertEqual(len(df_res), 2)
        self.assertEqual(df_res.iloc[0]["Consensus label"], "R4a") # First RNA
        self.assertEqual(df_res.iloc[0]["Operation"], "max()")
        self.assertEqual(df_res.iloc[0][df_res.columns[3]], "sum()")
        self.assertEqual(df_res.iloc[0]["Protein name"], "P4a")
        self.assertEqual(df_res.iloc[0]["RNA name"], "R4a")
        self.assertEqual(df_res.iloc[1]["Protein name"], "P4b")
        self.assertEqual(df_res.iloc[1]["RNA name"], "R4b")

    def test_protein_only_rna_only(self):
        df_input = pd.DataFrame({
            'Protein name': ['P_Prot_Only', ''], 
            'RNA name': ['', 'R_RNA_Only']
        })
        _, _, df_res = visualizer.create_feature_mapping_table(df_input)
        self.assertEqual(len(df_res), 2)
        self.assertEqual(df_res.iloc[0]["Consensus label"], "P_Prot_Only")
        self.assertEqual(df_res.iloc[0]["Protein name"], "P_Prot_Only")
        self.assertEqual(df_res.iloc[0]["RNA name"], "")
        self.assertEqual(df_res.iloc[1]["Consensus label"], "R_RNA_Only")
        self.assertEqual(df_res.iloc[1]["Protein name"], "")
        self.assertEqual(df_res.iloc[1]["RNA name"], "R_RNA_Only")

    def test_legend_generation_feature(self):
        _, html_legend_true, _ = visualizer.create_feature_mapping_table(self.feature_df, show_legend=True)
        self.assertIsNotNone(html_legend_true)
        self.assertIn("Legend", html_legend_true)

        _, html_legend_false, _ = visualizer.create_feature_mapping_table(self.feature_df, show_legend=False)
        self.assertIsNone(html_legend_false)

    def test_custom_colors_in_output_feature(self):
        # R1: '#FF0000' -> #ff0000
        r1_color_base = self.custom_colors_feat['R1'].lower()
        r1_legend_swatch = utils.format_color_with_opacity(r1_color_base, 1.0) # #ff0000ff
        r1_table_cell = utils.format_color_with_opacity(r1_color_base, 0.5)   # #ff000080

        html_table, html_legend, _ = visualizer.create_feature_mapping_table(
            self.feature_df, color_scheme=self.custom_colors_feat
        )
        self.assertIn(f"background-color: {r1_legend_swatch}", html_legend.lower())
        self.assertIn(f"background-color: {r1_table_cell}", html_table.lower())

    def test_caption_in_table_feature(self):
        caption = "My Custom Feature Table"
        html_table, _, _ = visualizer.create_feature_mapping_table(self.feature_df, caption=caption)
        self.assertIn(f"<caption>{caption}</caption>", html_table)


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
