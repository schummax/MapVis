import math
import re # For validating hex colors

DEFAULT_HEX_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
]

def generate_default_colors(labels, existing_colors=None):
    if existing_colors is None:
        existing_colors = {}
    new_colors = {}
    color_idx = 0
    for label in labels:
        if label not in existing_colors:
            new_colors[label] = DEFAULT_HEX_COLORS[color_idx % len(DEFAULT_HEX_COLORS)]
            color_idx += 1
    return new_colors

def format_color_with_opacity(color_hex: str, opacity: float) -> str:
    default_invalid_color = "#00000000" 

    if not isinstance(color_hex, str):
        return default_invalid_color

    if opacity < 0.0: opacity = 0.0
    elif opacity > 1.0: opacity = 1.0
    
    alpha_int = int(round(opacity * 255))
    alpha_hex = "{:02x}".format(alpha_int)

    color_hex_lower = color_hex.lower()
    if color_hex_lower.startswith('#'):
        color_hex_lower = color_hex_lower[1:]

    if len(color_hex_lower) == 8 and re.match(r'^[0-9a-f]{8}$', color_hex_lower):
        return f"#{color_hex_lower}"
    
    if len(color_hex_lower) == 6 and re.match(r'^[0-9a-f]{6}$', color_hex_lower):
        return f"#{color_hex_lower}{alpha_hex}"
    
    return default_invalid_color


def get_default_legend_styles() -> dict:
    return {
        'container': 'padding: 10px; border: 1px solid #ccc; margin-top: 10px;',
        'item': 'display: flex; align-items: center; margin-bottom: 5px;',
        'swatch_base': 'width: 12px; height: 12px; margin-right: 5px; border: 1px solid #000;',
        'title': 'margin-top:0; margin-bottom:10px;' 
    }

def get_legend_html(color_map: dict, title: str = "Legend", swatch_opacity: float = 1.0) -> str:
    if not color_map:
        return None

    styles = get_default_legend_styles()
    # Ensure the title style string uses double quotes for the style attribute value
    # as expected by the current test_utils.py
    # The style string itself does not contain double quotes, so f-string with double quotes is fine.
    html_parts = [f"<div style=\"{styles['container']}\">"] # Use escaped double quotes for outer HTML attribute
    if title:
        # For the h4 style, the test expects <h4 style="margin-top:0; margin-bottom:10px;">
        # The styles['title'] is 'margin-top:0; margin-bottom:10px;'
        html_parts.append(f"<h4 style=\"{styles['title']}\">{title}</h4>") 
    
    sorted_labels = sorted(color_map.keys())

    for label in sorted_labels:
        base_color = color_map[label]
        swatch_color_formatted = format_color_with_opacity(base_color, swatch_opacity)
        
        # Use escaped double quotes for outer HTML attributes
        item_html = (
            f"<div style=\"{styles['item']}\">"
            f"<span style=\"{styles['swatch_base']} background-color: {swatch_color_formatted};\"></span>"
            f"<span>{label}</span>"
            f"</div>"
        )
        html_parts.append(item_html)
    
    html_parts.append("</div>")
    return "\n".join(html_parts)

def get_default_table_properties() -> dict:
    return {'border': '1px solid black', 'width': '100%', 'border-collapse': 'collapse'}

if __name__ == '__main__':
    print("--- Testing format_color_with_opacity ---")
    # ... (rest of __main__ from agent_turn 22 utils.py, unchanged)
    tests_format_color = [
        (("#123456", 1.0), "#123456ff"), (("#ABCDEF", 0.5), "#abcdef80"),
        (("1a2b3c", 0.0), "#1a2b3c00"), (("#FF0000", 0.5), "#ff000080"),
        (("#123", 0.5), "#00000000"), (("INVALID", 0.5), "#00000000"),
        ((None, 0.5), "#00000000"), (("#12345G", 0.5), "#00000000"),
        (("#123456", 1.5), "#123456ff"), (("#123456", -0.5), "#12345600"),
        (("#12345678", 0.5), "#12345678"), (("abcdef12", 0.5), "#abcdef12"),
    ]
    for i, (inputs, expected) in enumerate(tests_format_color):
        actual = format_color_with_opacity(inputs[0], inputs[1])
        print(f"Test {i+1}: format_color_with_opacity{inputs} -> '{actual}' (Expected: '{expected}') - {'PASS' if actual == expected else 'FAIL'}")

    print("\n--- Testing get_legend_html ---")
    color_map_test = {'B-cell': '#ADD8E6', 'T-cell': '#90EE90', 'Z Label': '#FF0000', 'A Label': '#00FF00'}
    legend_html_output = get_legend_html(color_map_test, title="My Custom Legend", swatch_opacity=0.7)
    print(f"Legend HTML Output:\n{legend_html_output}")
    # Check for title, sorted labels (A Label before B-cell), and opacity in color
    # Adjusted expected h4 style to use double quotes around attribute value
    if legend_html_output and "<h4 style=\"margin-top:0; margin-bottom:10px;\">My Custom Legend</h4>" in legend_html_output and \
       legend_html_output.find('A Label') < legend_html_output.find('B-cell') and \
       "#add8e6b3" in legend_html_output: 
        print("PASS: Basic get_legend_html checks passed.")
    else:
        print("FAIL: Basic get_legend_html checks failed.")

    print("\n--- Testing generate_default_colors ---")
    items = ["a", "b", "c", "d", "e"]
    existing = {"a": "#FF0000", "f": "#0000FF"}
    generated = generate_default_colors(items, existing_colors=existing)
    print(f"Items: {items}, Existing: {existing}, Generated: {generated}")
    expected_gen_count = len([item for item in items if item not in existing])
    if len(generated) == expected_gen_count and "b" in generated and "a" not in generated:
        print(f"PASS: generate_default_colors generated {len(generated)} new colors as expected.")
    else:
        print(f"FAIL: generate_default_colors generated {len(generated)}, expected {expected_gen_count} or other logic error.")

    print("\nScript finished testing utils.")
