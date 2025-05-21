# MapVis
Cell type and feature mapping visualization

## Vision for the final program
### Cell type mapping 
#### Input
- two dictionaries of label mappings from the original cell type label, to the consensus label. E.g.: {"Mature B": "B-cell", "cd4+ t": "CD4+ T-cell", "CD8 cell": "CD8+ T-cell", ...}
- optional a third dictionary that assigns specific colors to cell types {"B-cell": "#0000FF", "CD4+ T-cell": "#CD5C5C", "CD8+ T-cell": "#FFB3B3", ...}
- optional a table caption
- boolean if a legend should be shown
- the names of the two datasets the mappings belong to (e.g. scRNAseq and codex)
#### Output
A styled tabel with three columns. The first and the last columns hold the original labels from the to mappings (the keys of the dictionaries) and the middle column holds the assigned consensus label. The mappings are sorted to group the consensus labels. The table cells have a background color with 50% opaccity. Text is always black. The table hides the index column (with .hide()). 

### Feature mapping
#### Input
- a DataFrame that assigns protein names to rna names. E.g.:
  Protein name	RNA name
0	CD19	CD19
1	CD45	PTPRC/PTPRCAP
2	CD45RA	PTPRC/PTPRCAP
3	HLA-DR	HLA-DRA/HLA-DRB1/HLA-DRB3/HLA-DRB4/HLA-DRB5
4	CD71	TFRC

- optional a table caption
- boolean if a legend should be shown
- optional dictionary that assigns specific colors to consensus labels. e.g.: {"HLA-DR": "#0000FF", "PTPRC": "#CD5C5C", "CD19": "#FFB3B3", ...}
#### Output
A styled tabel with five columns. 
The headers are:
- Protein name
- Operation
- Consensus label
- Operation (this header is repeated)
- RNA name
E.g. description of the structure:
Row 1 (Orange Highlight):
- Protein name: "CD45RA" and "CD45RO" are listed, stacked vertically, suggesting they are grouped.
- Operation (1st): "max()" is written, seemingly applying to the CD45RA/RO group.
- Consensus label: "PTPRC"
- Operation (2nd): Appears blank.
- RNA name: "PTPRC"
Row 2 (Blue Highlight):
- Protein name: "Cytokeratin"
- Operation (1st): Appears blank.
- Consensus label: "Cytokeratin"
- Operation (2nd): "sum()" is written.
- RNA name: "KRT 1" and "KRT10" are listed, stacked vertically, suggesting the "sum()" operation might apply to these.
Row 3 (Pink Highlight):
- Protein name: "FOXP3"
- Operation (1st): Appears blank.
- Consensus label: "FOXP3"
- Operation (2nd): Appears blank.
- RNA name: "FOXP3"

- Multiple genes that code for one proteinkomplex (1:n) are are split by "/" in the dataframe and are get the operation sum(). (for proteincomlexes, the protein name is the consenus label)
- If multiple proteins are belong to the same gene(s) (alternative splicing) (n:1), the max() operation gets assigned. (for alternative splicings, the gene name is the consenus label)
- In case of a 1:1 mapping, no operation gets assigned. (for 1:1 mappings the gene name is the consensus label)
- If the proteinkomplex and alternative splicing case happen both simultaneously, the first listed gene gets used as consensus label.

The mappings are sorted by consensus label. The table cells have a background color with 50% opaccity. Text is always black. The table hides the index column (with .hide()). 
 
---

current code...
Note that this code produces not the correct output at the moment. The requested output table format was changed, as described above.
The code below only serves as inspiration.

## __init__.py
from .visualizer import create_celltype_mapping_table, save_celltype_mapping_html

## visualizer.py
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from IPython.display import display, HTML
import os

def create_celltype_mapping_table(
    codex_mapping, 
    scrna_mapping, 
    caption='Celltype annotation mapping (fine)', 
    color_scheme=None
):
    # Extract unique manual annotations and sort them alphabetically
    all_manual_annotations = sorted(set(list(codex_mapping.values()) + list(scrna_mapping.values())))
    
    # Determine which annotations are in both datasets or unique to one
    annotation_in_scrna = {ann: ann in scrna_mapping.values() for ann in all_manual_annotations}
    annotation_in_codex = {ann: ann in codex_mapping.values() for ann in all_manual_annotations}
    
    # Create lists to store in-both, only-scrna, and only-codex annotations
    in_both = [ann for ann in all_manual_annotations if annotation_in_scrna[ann] and annotation_in_codex[ann]]
    only_scrna = [ann for ann in all_manual_annotations if annotation_in_scrna[ann] and not annotation_in_codex[ann]]
    only_codex = [ann for ann in all_manual_annotations if not annotation_in_scrna[ann] and annotation_in_codex[ann]]
    
    # Sort harmonized annotations - first those in both datasets, then the rest
    sorted_annotations = in_both + only_scrna + only_codex
    
    # Create reverse mappings from harmonized to original annotations
    scrna_to_original = {}
    for original, harmonized in scrna_mapping.items():
        if harmonized not in scrna_to_original:
            scrna_to_original[harmonized] = []
        scrna_to_original[harmonized].append(original)
    
    codex_to_original = {}
    for original, harmonized in codex_mapping.items():
        if harmonized not in codex_to_original:
            codex_to_original[harmonized] = []
        codex_to_original[harmonized].append(original)
    
    # Sort original annotations within each harmonized group
    for key in scrna_to_original:
        scrna_to_original[key] = sorted(scrna_to_original[key])
    for key in codex_to_original:
        codex_to_original[key] = sorted(codex_to_original[key])
    
    # Create the DataFrame structure
    data = []
    for harmonized in sorted_annotations:
        row = {}
        if harmonized in scrna_to_original:
            scrna_originals = scrna_to_original[harmonized]
            row[('scRNA-seq', 'Original')] = ",</br>".join(scrna_originals)
            row[('scRNA-seq', 'Harmonized')] = harmonized if harmonized in annotation_in_scrna else ""
        else:
            row[('scRNA-seq', 'Original')] = ""
            row[('scRNA-seq', 'Harmonized')] = ""
            
        if harmonized in codex_to_original:
            codex_originals = codex_to_original[harmonized]
            row[('CODEX', 'Original')] = ",</br>".join(codex_originals)
            row[('CODEX', 'Harmonized')] = harmonized if harmonized in annotation_in_codex else ""
        else:
            row[('CODEX', 'Original')] = ""
            row[('CODEX', 'Harmonized')] = ""
        data.append(row)
    
    columns = pd.MultiIndex.from_product([['scRNA-seq', 'CODEX'], ['Original', 'Harmonized']], 
                                         names=['Dataset', 'Annotation Type'])
    df = pd.DataFrame(data, index=sorted_annotations, columns=columns)
    df.index.name = 'Harmonized Cell Type'
    
    # Generate or use provided color map
    colors = {}
    if color_scheme:
        colors = color_scheme.copy()  # Use a copy to avoid modifying the input dict
    
    # Ensure all annotations have a color, generate if not in scheme or if no scheme provided
    num_annotations_to_color = len(all_manual_annotations)
    
    # Default colors generation if not all are covered by scheme
    generated_colors_list = []
    if len(colors) < num_annotations_to_color:
        # Add colors from tab20
        generated_colors_list.extend([mcolors.rgb2hex(c[:3]) for c in plt.colormaps['tab20'].colors])
        # Add colors from tab20b if needed
        if num_annotations_to_color > len(generated_colors_list):
            generated_colors_list.extend([mcolors.rgb2hex(c[:3]) for c in plt.colormaps['tab20b'].colors])
        # Add colors from tab20c if needed
        if num_annotations_to_color > len(generated_colors_list):
            generated_colors_list.extend([mcolors.rgb2hex(c[:3]) for c in plt.colormaps['tab20c'].colors])
        
        # Fallback for even more colors (cycle through generated list)
        if not generated_colors_list:  # Should not happen with tab20/b/c unless matplotlib changes
            generated_colors_list = ['#D3D3D3']  # Default fallback grey

    color_idx = 0
    for annotation in all_manual_annotations:
        if annotation not in colors:
            colors[annotation] = generated_colors_list[color_idx % len(generated_colors_list)]
            color_idx += 1
            
    # Apply styling
    styled_df = df.style.apply(lambda row: [style_rows(row, colors, annotation_in_scrna, annotation_in_codex) for _ in row.index], axis=1)
    
    # Set properties for a nicer display
    styled_df = styled_df.set_properties(**{
        'border': '1px solid silver',
        'padding': '5px',
        'text-align': 'left'
    })
    
    # Add a caption
    styled_df = styled_df.set_caption(caption)  # .hide() removed here, can be called by user if needed

    # Add a legend for cell types
    legend_html = "<div style='padding: 10px; border: 1px solid silver; margin-top: 10px;'>"
    legend_html += "<h4>Legend:</h4>"
    legend_html += "<ul style='list-style-type: none; padding: 0;'>"
    
    # First show annotations in both datasets
    if in_both:
        legend_html += "<h5>Cell Types in Both Datasets:</h5>"
        for annotation in sorted(in_both):
            color = colors.get(annotation, '#D3D3D3')  # Default to light gray if somehow missing
            r_val, g_val, b_val = mcolors.hex2color(color)
            brightness = 0.299 * r_val + 0.587 * g_val + 0.114 * b_val
            text_color = 'black' if brightness > 0.65 else 'white'
            legend_html += f"<li style='background-color: {color}; color: {text_color}; padding: 3px; margin: 2px; font-weight: bold;'>{annotation}</li>"
    
    # Then show annotations only in scRNA-seq
    if only_scrna:
        legend_html += "<h5>Cell Types Only in scRNA-seq:</h5>"
        for annotation in sorted(only_scrna):
            base_color = colors.get(annotation, '#D3D3D3')
            r_val, g_val, b_val = mcolors.hex2color(base_color)
            # Use lighter color for display in legend
            light_color_hex = mcolors.rgb2hex((r_val * 0.5 + 0.5, g_val * 0.5 + 0.5, b_val * 0.5 + 0.5))
            # Calculate brightness for the lightened color
            lr, lg, lb = mcolors.hex2color(light_color_hex)
            brightness = 0.299 * lr + 0.587 * lg + 0.114 * lb
            text_color = 'black' if brightness > 0.65 else 'white'
            legend_html += f"<li style='background-color: {light_color_hex}; color: {text_color}; padding: 3px; margin: 2px; font-style: italic; text-decoration: line-through;'>{annotation}</li>"
    
    # Finally show annotations only in CODEX
    if only_codex:
        legend_html += "<h5>Cell Types Only in CODEX:</h5>"
        for annotation in sorted(only_codex):
            base_color = colors.get(annotation, '#D3D3D3')
            r_val, g_val, b_val = mcolors.hex2color(base_color)
            # Use lighter color for display in legend
            light_color_hex = mcolors.rgb2hex((r_val * 0.5 + 0.5, g_val * 0.5 + 0.5, b_val * 0.5 + 0.5))
            # Calculate brightness for the lightened color
            lr, lg, lb = mcolors.hex2color(light_color_hex)
            brightness = 0.299 * lr + 0.587 * lg + 0.114 * lb
            text_color = 'black' if brightness > 0.65 else 'white'
            legend_html += f"<li style='background-color: {light_color_hex}; color: {text_color}; padding: 3px; margin: 2px; font-style: italic; text-decoration: line-through;'>{annotation}</li>"
    
    legend_html += "</ul>"
    legend_html += "<p><strong>Bold</strong>: Cell types present in both datasets</p>"
    legend_html += "<p><i style='text-decoration: line-through;'>Strikethrough & Italic</i>: Cell types in only one dataset (will not be used in analysis)</p>"
    legend_html += "</div>"
    
    return styled_df, legend_html, df

# Create a styling function based on the harmonized annotation (row index)
def style_rows(row, colors, annotation_in_scrna, annotation_in_codex, props=''):
    harmonized = row.name
    
    # Get color for this harmonized annotation
    bg_color = colors.get(harmonized, '#D3D3D3')  # Default to light gray if not in scheme
    
    # Adjust style based on presence in both datasets
    in_both_datasets = annotation_in_scrna[harmonized] and annotation_in_codex[harmonized]
    if not in_both_datasets:
        # Lighter color for annotations in only one dataset
        r, g, b = mcolors.hex2color(bg_color)
        bg_color = mcolors.rgb2hex((r * 0.5 + 0.5, g * 0.5 + 0.5, b * 0.5 + 0.5))
        text_style = 'font-style: italic; text-decoration: line-through;'
    else:
        text_style = 'font-weight: bold;'
    
    # Set text color for readability
    r, g, b = mcolors.hex2color(bg_color)
    brightness = 0.299 * r + 0.587 * g + 0.114 * b
    text_color = 'black' if brightness > 0.65 else 'white'
    
    return f'background-color: {bg_color}; color: {text_color}; {text_style}'

# Save the styled cell type mapping visualization as a standalone HTML file
def save_celltype_mapping_html(
    styled_df, 
    legend_html, 
    output_path, 
    title="Cell Type Annotation Mapping", 
    include_legend=True, 
    include_footer=True,
    dataset_name="Dataset", 
    generation_info=f"Generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}"
):
    """Save a complete HTML file with the styled cell type mapping table and legend."""
    
    footer_style_block = ""
    if include_footer:
        footer_style_block = """
            .footer {
                margin-top: 30px;
                border-top: 1px solid #ddd;
                padding-top: 10px;
                font-size: 0.9em;
                color: #666;
            }"""

    # Create a complete HTML document
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 20px;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1, h2, h3 {{
                color: #333;
            }}
            .container {{
                display: flex;
                flex-direction: column;
                gap: 20px;
            }}
            .table-container {{
                overflow-x: auto;
            }}
            .legend-container {{
                margin-top: 20px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            th, td {{
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            {footer_style_block}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{title}</h1>
            <p>This table shows the mapping between original cell type annotations and their harmonized annotations.</p>
            
            <div class="table-container">
                {styled_df.to_html() if styled_df else ""}
            </div>
            
            {f'<div class="legend-container">{legend_html}</div>' if include_legend and legend_html else ""}
            
            {f'<div class="footer"><p>{generation_info}</p><p>{dataset_name}</p></div>' if include_footer else ""}
        </div>
    </body>
    </html>
    """
    
    # Create the directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir: 
        os.makedirs(output_dir, exist_ok=True)
    
    # Write HTML content to file
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"Saved standalone HTML visualization to {output_path}")
