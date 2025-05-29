"""Tests for utility functions."""

import pytest
import tempfile
import csv
from pathlib import Path
from mapvis.utils import (load_mapping_from_csv, load_mapping_from_tsv,
                          get_consensus_mapping, get_feature_operations,
                          sort_mappings_by_presence)


class TestUtils:

    def test_load_mapping_from_csv(self):
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['source', 'target'])
            writer.writerow(['CD4 T', 'CD4+ T cell'])
            writer.writerow(['CD8 T', 'CD8+ T cell'])
            temp_path = f.name

        try:
            mapping = load_mapping_from_csv(temp_path)
            assert mapping['CD4 T'] == 'CD4+ T cell'
            assert mapping['CD8 T'] == 'CD8+ T cell'
        finally:
            Path(temp_path).unlink()

    def test_load_mapping_from_tsv(self):
        # Create temporary TSV file with celltype names containing commas
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['source', 'target'])
            writer.writerow(['B cells, activated', 'B cell'])
            writer.writerow(['T cells, CD4+', 'CD4+ T cell'])
            writer.writerow(['Macrophages, M1', 'Macrophage'])
            temp_path = f.name

        try:
            mapping = load_mapping_from_tsv(temp_path)
            assert mapping['B cells, activated'] == 'B cell'
            assert mapping['T cells, CD4+'] == 'CD4+ T cell'
            assert mapping['Macrophages, M1'] == 'Macrophage'
        finally:
            Path(temp_path).unlink()

    def test_load_mapping_with_custom_delimiter(self):
        # Test pipe-delimited file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('source|target\n')
            f.write('Cell A|Type A\n')
            f.write('Cell B|Type B\n')
            temp_path = f.name

        try:
            mapping = load_mapping_from_csv(temp_path, delimiter='|')
            assert mapping['Cell A'] == 'Type A'
            assert mapping['Cell B'] == 'Type B'
        finally:
            Path(temp_path).unlink()

    def test_load_mapping_invalid_file(self):
        with pytest.raises(FileNotFoundError):
            load_mapping_from_csv('nonexistent.csv')

    def test_get_consensus_mapping(self):
        map1 = {'A': 'consensus1', 'B': 'consensus1', 'C': 'consensus2'}
        map2 = {'X': 'consensus1', 'Y': 'consensus2'}

        result = get_consensus_mapping(map1, map2)

        assert result['consensus1'] == (['A', 'B'], ['X'])
        assert result['consensus2'] == (['C'], ['Y'])

    def test_get_feature_operations(self):
        map1 = {'Gene1': 'Complex1', 'Gene2': 'Complex1', 'Gene3': 'Gene3'}
        map2 = {'Prot1': 'Complex1', 'Prot2': 'Gene3', 'Prot3': 'Gene3'}

        result = get_feature_operations(map1, map2)

        # Multiple genes, one protein
        assert result['Complex1'] == ('sum()', '')
        # One gene, multiple proteins
        assert result['Gene3'] == ('', 'max()')

    def test_sort_mappings_by_presence(self):
        consensus_map = {
            'shared1': (['A'], ['X']),
            'only_d1': (['B'], []),
            'shared2': (['C'], ['Y']),
            'only_d2': ([], ['Z'])
        }

        result = sort_mappings_by_presence(consensus_map)

        # Shared mappings should come first
        assert result[:2] == ['shared1', 'shared2']
        # Single dataset mappings should come last
        assert set(result[2:]) == {'only_d1', 'only_d2'}
