"""Test package marker so pytest computes a unique module name.

Without this file, tests/t1_five/test_ops.py and tests/t3_round2/test_ops.py
share the basename "test_ops" and pytest aborts collection with
"import file mismatch" (import-file-mismatch on identical basenames when
no __init__.py chain exists).
"""
