import matplotlib.colors

# Base colors (6-digit hex, no opacity)
_TABLEAU_COLORS_HEX = [
    matplotlib.colors.to_hex(c) for c in matplotlib.colors.TABLEAU_COLORS.values()
]
_KELLY_COLORS_HEX = [
    "#FFB300", "#803E75", "#FF6800", "#A6BDD7", "#C10020", "#CEA262", "#817066",
    "#007D34", "#F6768E", "#00538A", "#FF7A5C", "#53377A", "#FF8E00", "#B32851",
    "#F4C800", "#7F180D", "#93AA00", "#593315", "#F13A13", "#232C16",
]
DEFAULT_HEX_COLORS = _TABLEAU_COLORS_HEX + _KELLY_COLORS_HEX


def generate_default_colors(
    items: list[str], 
    existing_colors: dict[str, str] = None
) -> dict[str, str]:
    """
    Generates a dictionary mapping items to unique 6-digit hex color strings.
    Items already in existing_colors are skipped.

    Args:
        items: A list of unique items (e.g., consensus labels) that need colors.
        existing_colors: A dictionary of items that already have assigned colors.
                         Items in this dict will not be assigned new colors.

    Returns:
        A dictionary mapping each new item to a unique 6-digit hex color string 
        (e.g., {"New Label": "#FF0000"}).
    """
    if existing_colors is None:
        existing_colors = {}
    
    new_color_map = {}
    color_idx = 0
    # Try to maintain color consistency for items seen before, even if not in existing_colors for this run
    # This simple loop won't do that, but for now, it assigns based on order of *new* items.
    # A more robust approach might involve a predefined mapping for common labels if consistency across calls is critical.
    
    unique_items_needing_colors = []
    for item in items:
        if item not in existing_colors and item not in new_color_map: # Ensure we only process items that need colors
            unique_items_needing_colors.append(item)

    for item in unique_items_needing_colors:
        new_color_map[item] = DEFAULT_HEX_COLORS[color_idx % len(DEFAULT_HEX_COLORS)]
        color_idx += 1
    return new_color_map


def format_color_with_opacity(hex_color: str, opacity: float = 0.5) -> str:
    """
    Converts a 6-digit hex color to an 8-digit hex color with specified opacity.

    Args:
        hex_color: 6-digit hex color string (e.g., "#RRGGBB" or "RRGGBB").
                   If None or not a string, returns a default transparent color.
        opacity: Opacity value from 0.0 (transparent) to 1.0 (opaque).

    Returns:
        8-digit hex color string with alpha (e.g., "#RRGGBB80").
        Returns a default fully transparent color if input is invalid.
    """
    if not isinstance(hex_color, str):
        return "#00000000" # Default: fully transparent black

    clean_hex_color = hex_color.lstrip('#')
    
    if not (len(clean_hex_color) == 6 and all(c in '0123456789abcdefABCDEF' for c in clean_hex_color)):
        # If it's not a 6-digit hex, it might already have alpha, or be a named color.
        # For this function, we strictly expect 6-digit hex.
        # Return transparent black if invalid, or consider raising error.
        if len(clean_hex_color) == 8 and all(c in '0123456789abcdefABCDEF' for c in clean_hex_color): # Already has alpha
             return f"#{clean_hex_color}" # Assume it's fine
        return "#00000000" 

    alpha_val = max(0, min(255, int(opacity * 255))) # Clamp opacity to 0-255 range
    alpha_hex = f"{alpha_val:02x}"
    return f"#{clean_hex_color}{alpha_hex}"


def get_default_table_properties() -> dict:
    """
    Returns a dictionary of default CSS properties for table cells.
    """
    return {
        'color': 'black',
        'border': '1px solid #DDDDDD',
        'padding': '8px',
        'text-align': 'left',
        'min-width': '70px' # Consistent with visualizer.py
    }

def get_default_legend_styles() -> dict[str, str]:
    """
    Returns a dictionary of default CSS styles for legend elements.
    """
    return {
        "container": (
            "padding: 10px; border: 1px solid #DDDDDD; margin-top: 20px; "
            "display: inline-block; font-family: Arial, sans-serif;"
        ),
        "item": "display: flex; align-items: center; margin-bottom: 5px;",
        "swatch_base": (
            "width: 20px; height: 20px; margin-right: 10px; border: 1px solid #CCCCCC;"
        )
    }

def get_legend_html(
    base_color_map: dict[str, str], 
    title: str = "Legend",
    swatch_opacity: float = 1.0
) -> str | None:
    """
    Generates HTML for a legend given a map of labels to their base hex colors.

    Args:
        base_color_map: Dictionary mapping labels to their base 6-digit hex colors.
        title: Title for the legend.
        swatch_opacity: Opacity to apply to colors for the legend swatches (default 1.0 for full opacity).

    Returns:
        HTML string for the legend, or None if base_color_map is empty.
    """
    if not base_color_map:
        return None

    styles = get_default_legend_styles()
    legend_items_html = []
    
    sorted_legend_labels = sorted(base_color_map.keys())

    for label in sorted_legend_labels:
        base_color = base_color_map.get(label)
        if not base_color: # Should not happen if map is properly populated
            continue 
            
        # Color for the swatch, typically full opacity
        swatch_display_color = format_color_with_opacity(base_color, swatch_opacity)
        
        swatch_style = f"{styles['swatch_base']} background-color: {swatch_display_color};"
        item_html = (
            f'<div style="{styles["item"]}">'
            f'<div style="{swatch_style}"></div>'
            f'<span>{label}</span>'
            f'</div>'
        )
        legend_items_html.append(item_html)

    if not legend_items_html:
        return None

    return (
        f'<div class="legend" style="{styles["container"]}">'
        f'<h4 style="margin-top:0; margin-bottom:10px;">{title}</h4>'
        f'{"".join(legend_items_html)}</div>'
    )

```
