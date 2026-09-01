from __future__ import annotations

import gzip

from scripts.t3_s1d_exact_activity_evidence import (
    STUDIES,
    _effect,
    _gene_values,
    load_platform_symbols,
    load_series_matrix,
)


def test_effect_scale_is_explicit_and_deterministic() -> None:
    assert _effect([10.0, 10.0], [5.0, 5.0], "linear_expression_log2_ratio") == -1.0
    assert _effect([10.0, 12.0], [13.0, 15.0], "RMA_log2_difference") == 3.0
    assert _gene_values({"p1": [10.0, 20.0], "p2": [30.0, 40.0]}, ["p1", "p2"]) == [20.0, 30.0]


def test_platform_mapping_and_matrix_parser_keep_sample_identity(tmp_path) -> None:
    platform = tmp_path / "platform.annot.gz"
    with gzip.open(platform, "wt", encoding="utf-8", newline="") as handle:
        handle.write("^Annotation\n!platform_table_begin\n")
        handle.write("ID\tGene title\tGene symbol\tGene ID\n")
        handle.write("p1\tTarget\tGata4///Alias\t1\n")
        handle.write("p2\tResponse\tNkx2-5\t2\n")
        handle.write("!platform_table_end\n")
    mapping = load_platform_symbols(platform, {"Gata4", "Nkx2-5"})
    assert mapping == {"Gata4": ["p1"], "Nkx2-5": ["p2"]}

    matrix = tmp_path / "series_matrix.txt.gz"
    with gzip.open(matrix, "wt", encoding="utf-8", newline="") as handle:
        handle.write('!Sample_geo_accession\t"s1"\t"s2"\n')
        handle.write('!Sample_title\t"control"\t"ko"\n')
        handle.write("!series_matrix_table_begin\n")
        handle.write('"ID_REF"\t"s1"\t"s2"\n')
        handle.write('"p1"\t10\t5\n')
        handle.write('"p2"\t20\t25\n')
        handle.write("!series_matrix_table_end\n")
    parsed = load_series_matrix(matrix, {"p1", "p2"})
    assert parsed["accessions"] == ["s1", "s2"]
    assert parsed["values"] == {"p1": [10.0, 5.0], "p2": [20.0, 25.0]}
    assert parsed["n_rows"] == 2


def test_study_group_configuration_is_disjoint_and_explicit() -> None:
    assert {study["accession"] for study in STUDIES} == {"GSE5298", "GSE9652", "GSE78125"}
    for study in STUDIES:
        control = set(study["control_accessions"])
        perturbation = set(study["perturbation_accessions"])
        excluded = set(study["excluded_accessions"])
        assert control.isdisjoint(perturbation)
        assert control.isdisjoint(excluded)
        assert perturbation.isdisjoint(excluded)
        assert len(control) >= 2
        assert len(perturbation) >= 2
