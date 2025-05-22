import unittest
from mapvis import utils  # Assuming mapvis is installed or in PYTHONPATH

class TestGenerateDefaultColors(unittest.TestCase):

    def test_empty_list(self):
        self.assertEqual(utils.generate_default_colors([]), {})

    def test_unique_items(self):
        items = ["a", "b", "c"]
        colors = utils.generate_default_colors(items)
        self.assertEqual(len(colors), len(items))
        self.assertEqual(len(set(colors.values())), len(items)) # Unique colors
        for item in items:
            self.assertIn(item, colors)

    def test_cycling(self):
        num_default_colors = len(utils.DEFAULT_HEX_COLORS)
        items = [f"item_{i}" for i in range(num_default_colors + 5)]
        colors = utils.generate_default_colors(items)
        self.assertEqual(len(colors), len(items))
        # Check if colors are cycling by looking at colors of items far apart
        self.assertEqual(colors["item_0"], colors[f"item_{num_default_colors}"])
        self.assertEqual(colors["item_1"], colors[f"item_{num_default_colors + 1}"])

    def test_with_existing_colors(self):
        existing = {"a": "#FF0000", "b": "#00FF00"}
        items_to_generate = ["c", "d"]
        all_items = ["a", "b", "c", "d"] # For checking final output

        # Test when items_to_generate does not overlap with existing_colors keys
        generated_colors = utils.generate_default_colors(items_to_generate, existing_colors=existing.copy())
        
        # Check that only new colors for "c" and "d" are in generated_colors
        self.assertEqual(len(generated_colors), 2)
        self.assertIn("c", generated_colors)
        self.assertIn("d", generated_colors)
        self.assertNotIn("#FF0000", generated_colors.values()) # Existing colors should not be re-generated here
        self.assertNotEqual(generated_colors["c"], generated_colors["d"])
        
        # If the function is to return a combined map, the test would be different.
        # Based on docstring: "Returns a dictionary mapping each new item to a unique hex color"
        # So, existing items are not in the direct output of generate_default_colors.
        # The calling code in visualizer.py does `base_color_map.update(default_colors_for_new_labels)`

        # Test when items list includes items already in existing_colors
        # generate_default_colors should only generate for items NOT in existing_colors.
        items_list_for_func = ["a", "c", "d"] # "a" is in existing
        generated_for_mixed_list = utils.generate_default_colors(items_list_for_func, existing_colors=existing.copy())
        self.assertEqual(len(generated_for_mixed_list), 2) # Only for "c", "d"
        self.assertIn("c", generated_for_mixed_list)
        self.assertIn("d", generated_for_mixed_list)
        self.assertNotIn("a", generated_for_mixed_list)


class TestFormatColorWithOpacity(unittest.TestCase):

    def test_valid_hex_opacities(self):
        self.assertEqual(utils.format_color_with_opacity("#123456", 1.0), "#123456ff")
        self.assertEqual(utils.format_color_with_opacity("#ABCDEF", 0.5), "#abcdef80") # Test case insensitivity
        self.assertEqual(utils.format_color_with_opacity("#1a2b3c", 0.0), "#1a2b3c00")
        self.assertEqual(utils.format_color_with_opacity("#FF0000", 0.5), "#ff000080")

    def test_valid_hex_no_hash_opacities(self):
        self.assertEqual(utils.format_color_with_opacity("123456", 0.5), "#12345680")

    def test_invalid_hex(self):
        # Expects default transparent color: #00000000
        self.assertEqual(utils.format_color_with_opacity("#123", 0.5), "#00000000")
        self.assertEqual(utils.format_color_with_opacity("INVALID", 0.5), "#00000000")
        self.assertEqual(utils.format_color_with_opacity(None, 0.5), "#00000000")
        self.assertEqual(utils.format_color_with_opacity("#12345G", 0.5), "#00000000") # Invalid char

    def test_opacity_out_of_bounds(self):
        # Alpha should be clamped to 00 or ff
        self.assertEqual(utils.format_color_with_opacity("#123456", 1.5), "#123456ff")
        self.assertEqual(utils.format_color_with_opacity("#123456", -0.5), "#12345600")

    def test_already_has_alpha(self):
        # If it already has alpha, it should be returned as is (ensuring # prefix)
        self.assertEqual(utils.format_color_with_opacity("#12345678", 0.5), "#12345678")
        self.assertEqual(utils.format_color_with_opacity("abcdef12", 0.5), "#abcdef12")


class TestGetDefaultTableProperties(unittest.TestCase):

    def test_returns_dict(self):
        props = utils.get_default_table_properties()
        self.assertIsInstance(props, dict)
        self.assertTrue(len(props) > 0)
        self.assertIn('border', props)
        self.assertIn('vertical-align', props)
        self.assertEqual(props['vertical-align'], 'middle')


class TestBuildFinalColorMap(unittest.TestCase):

    def test_no_user_scheme(self):
        labels = ["a", "b", "c"]
        color_map = utils.build_final_color_map(labels)
        self.assertEqual(len(color_map), len(labels))
        for label in labels:
            self.assertIn(label, color_map)
            self.assertTrue(color_map[label].startswith("#"))
            self.assertEqual(len(color_map[label]), 7) # 6 hex + #

    def test_user_scheme_covers_all(self):
        labels = ["a", "b"]
        user_scheme = {"a": "#FF0000", "b": "#00FF00"}
        color_map = utils.build_final_color_map(labels, user_scheme)
        self.assertEqual(color_map, user_scheme)

    def test_user_scheme_partial(self):
        labels = ["a", "b", "c"]
        user_scheme = {"a": "#FF0000"}
        color_map = utils.build_final_color_map(labels, user_scheme)
        self.assertEqual(len(color_map), len(labels))
        self.assertEqual(color_map["a"], "#FF0000")
        self.assertIn("b", color_map)
        self.assertIn("c", color_map)
        self.assertNotEqual(color_map["b"], "#FF0000")
        self.assertNotEqual(color_map["c"], "#FF0000")
        self.assertNotEqual(color_map["b"], color_map["c"])

    def test_user_scheme_invalid_colors(self):
        labels = ["a", "b", "c"]
        # "a" is valid, "b" is invalid short, "c" is invalid format
        user_scheme = {"a": "#123456", "b": "#123", "c": "notacolor"}
        color_map = utils.build_final_color_map(labels, user_scheme)
        
        self.assertEqual(len(color_map), len(labels))
        self.assertEqual(color_map["a"], "#123456") # Valid user color kept
        
        # "b" and "c" should get default colors
        self.assertIn("b", color_map)
        self.assertNotEqual(color_map["b"], "#123") 
        self.assertTrue(color_map["b"].startswith("#") and len(color_map["b"]) == 7)
        
        self.assertIn("c", color_map)
        self.assertNotEqual(color_map["c"], "notacolor")
        self.assertTrue(color_map["c"].startswith("#") and len(color_map["c"]) == 7)
        
        self.assertNotEqual(color_map["b"], color_map["a"])
        self.assertNotEqual(color_map["c"], color_map["a"])
        self.assertNotEqual(color_map["b"], color_map["c"])


    def test_empty_unique_labels(self):
        self.assertEqual(utils.build_final_color_map([]), {})
        self.assertEqual(utils.build_final_color_map([], user_color_scheme={"a": "#FF0000"}), {})

    def test_user_scheme_has_extra_labels_not_in_table(self):
        labels_in_table = ["a", "b"]
        user_scheme = {"a": "#FF0000", "b": "#00FF00", "extra": "#0000FF"}
        color_map = utils.build_final_color_map(labels_in_table, user_scheme)
        self.assertEqual(len(color_map), len(labels_in_table))
        self.assertNotIn("extra", color_map)
        self.assertEqual(color_map["a"], "#FF0000")
        self.assertEqual(color_map["b"], "#00FF00")


class TestGetDefaultLegendStyles(unittest.TestCase):

    def test_returns_dict_with_keys(self):
        styles = utils.get_default_legend_styles()
        self.assertIsInstance(styles, dict)
        self.assertIn('container', styles)
        self.assertIn('item', styles)
        self.assertIn('swatch_base', styles)
        self.assertTrue(all(isinstance(v, str) for v in styles.values()))


class TestGetLegendHtml(unittest.TestCase):

    def test_empty_color_map(self):
        self.assertIsNone(utils.get_legend_html({}))

    def test_simple_color_map(self):
        color_map = {'B-cell': '#ADD8E6', 'T-cell': '#90EE90'}
        legend_html = utils.get_legend_html(color_map, title="My Legend")
        
        self.assertIsNotNone(legend_html)
        self.assertIn('<h4 style="margin-top:0; margin-bottom:10px;">My Legend</h4>', legend_html)
        self.assertIn('<span>B-cell</span>', legend_html)
        self.assertIn('<span>T-cell</span>', legend_html)
        # Swatch with full opacity (default for swatch_opacity=1.0)
        self.assertIn('background-color: #add8e6ff;', legend_html.lower()) # Check formatted color
        self.assertIn('background-color: #90ee90ff;', legend_html.lower())

    def test_swatch_opacity(self):
        color_map = {'MyLabel': '#FF0000'}
        legend_html = utils.get_legend_html(color_map, swatch_opacity=0.5)
        self.assertIsNotNone(legend_html)
        self.assertIn('background-color: #ff000080;', legend_html.lower()) # Check color with 50% opacity

    def test_label_sorting(self):
        color_map = {'Z Label': '#FF0000', 'A Label': '#00FF00'}
        legend_html = utils.get_legend_html(color_map)
        self.assertIsNotNone(legend_html)
        # 'A Label' should appear before 'Z Label' in the HTML
        self.assertTrue(legend_html.find('A Label') < legend_html.find('Z Label'))

if __name__ == '__main__':
    unittest.main()
```
