"""Tests for core MapVis functionality."""

import pytest
import pandas as pd
from mapvis import MapVisualizer


class TestMapVisualizer:

    def setup_method(self):
        self.visualizer = MapVisualizer()

        # Sample celltype mappings
        self.celltype_map1 = {
            'B-CD22-CD40': 'B-CD22-CD40',
            'CD4 T': 'CD4+ T cell',
            'B-Ki67': 'B-Ki67'
        }

        self.celltype_map2 = {
            'CD4+ T cell': 'CD4+ T cell',
            'B-CD22-CD40': 'B-CD22-CD40',
            'B-Ki67': 'B-Ki67'
        }

        # Sample feature mappings
        self.feature_map1 = {
            'PTPRC': 'PTPRC',
            'CD4': 'CD4',
            'HLA-DRB1': 'HLA-DR',
            'HLA-DRB5': 'HLA-DR',
            'HLA-DRA': 'HLA-DR'
        }

        self.feature_map2 = {
            'CD45': 'PTPRC',
            'CD45RA': 'PTPRC',
            'CD4': 'CD4',
            'HLA-DR': 'HLA-DR'
        }

    def test_celltype_visualization(self):
        result = self.visualizer.visualize_celltype_mapping(
            self.celltype_map1,
            self.celltype_map2
        )
        # Check it returns a Styler object
        assert hasattr(result, 'data')
        assert isinstance(result.data, pd.DataFrame)
        assert result.data.shape[0] == 3  # 3 consensus labels
        assert set(result.data.columns) == {
            "Dataset 1", "Consensus", "Dataset 2"}

    def test_feature_visualization(self):
        result = self.visualizer.visualize_feature_mapping(
            self.feature_map1,
            self.feature_map2
        )
        assert hasattr(result, 'data')
        assert isinstance(result.data, pd.DataFrame)
        assert "RNA Operation" in result.data.columns
        assert "Protein Operation" in result.data.columns

    def test_invalid_input(self):
        with pytest.raises(TypeError):
            self.visualizer.visualize_celltype_mapping(
                "not a dict", self.celltype_map2)

    def test_empty_mapping(self):
        with pytest.raises(ValueError):
            self.visualizer.visualize_celltype_mapping({}, self.celltype_map2)

    def test_custom_color_map(self):
        custom_colors = {
            'B-CD22-CD40': '#FF0000',
            'CD4+ T cell': '#00FF00',
            'B-Ki67': '#0000FF'
        }

        result = self.visualizer.visualize_celltype_mapping(
            self.celltype_map1,
            self.celltype_map2,
            color_map=custom_colors
        )

        assert hasattr(result, 'data')
        # The custom colors should be applied in the styling

    def test_export_to_image(self, tmp_path):
        """Test image export functionality (if dataframe-image is installed)."""
        try:
            import dataframe_image

            result = self.visualizer.visualize_celltype_mapping(
                self.celltype_map1,
                self.celltype_map2
            )

            # Test export to temporary file
            output_file = tmp_path / "test_table.png"
            self.visualizer.export_to_image(result, str(output_file))

            assert output_file.exists()
            assert output_file.stat().st_size > 0
        except ImportError:
            pytest.skip("dataframe-image not installed")

    def test_sorting(self):
        """Test that single-dataset mappings are sorted to the end."""
        # Add mapping that only exists in dataset1
        self.celltype_map1['Unique1'] = 'Unique1'
        # Add mapping that only exists in dataset2
        self.celltype_map2['Unique2'] = 'Unique2'

        result = self.visualizer.visualize_celltype_mapping(
            self.celltype_map1,
            self.celltype_map2
        )

        # Check that unique mappings appear at the end
        consensus_order = result.data['Consensus'].tolist()
        # Shared mappings should come first
        assert 'B-CD22-CD40' in consensus_order[:3]
        # Unique mappings should come last
        assert 'Unique1' in consensus_order[-2:]
        assert 'Unique2' in consensus_order[-2:]
