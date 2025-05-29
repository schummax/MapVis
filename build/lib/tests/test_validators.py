"""Tests for validation functions."""

import pytest
from mapvis.validators import (validate_mapping_dict, validate_celltype_mappings,
                               validate_feature_mappings)


class TestValidators:

    def test_validate_mapping_dict_valid(self):
        valid_mapping = {'A': 'B', 'C': 'D'}
        validate_mapping_dict(
            valid_mapping, "test_mapping")  # Should not raise

    def test_validate_mapping_dict_not_dict(self):
        with pytest.raises(TypeError):
            validate_mapping_dict(["not", "a", "dict"], "test_mapping")

    def test_validate_mapping_dict_empty(self):
        with pytest.raises(ValueError):
            validate_mapping_dict({}, "test_mapping")

    def test_validate_mapping_dict_invalid_types(self):
        with pytest.raises(TypeError):
            validate_mapping_dict({1: 'A'}, "test_mapping")

    def test_validate_mapping_dict_empty_values(self):
        with pytest.raises(ValueError):
            validate_mapping_dict({'A': ''}, "test_mapping")

    def test_validate_celltype_mappings_no_overlap(self):
        map1 = {'A': 'consensus1'}
        map2 = {'B': 'consensus2'}

        with pytest.raises(ValueError, match="No common consensus labels"):
            validate_celltype_mappings(map1, map2)

    def test_validate_celltype_mappings_valid(self):
        map1 = {'A': 'consensus1', 'B': 'consensus2'}
        map2 = {'X': 'consensus1', 'Y': 'consensus3'}

        # Should not raise - they share consensus1
        validate_celltype_mappings(map1, map2)

    def test_validate_feature_mappings_valid(self):
        map1 = {'Gene1': 'Protein1', 'Gene2': 'Protein2'}
        map2 = {'Prot1': 'Protein1', 'Prot2': 'Protein2'}

        # Should not raise
        validate_feature_mappings(map1, map2)
