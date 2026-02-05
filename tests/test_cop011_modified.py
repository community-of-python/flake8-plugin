import ast
import textwrap

from community_of_python_flake8_plugin.checks.temp_var import TempVarCheck


def test_cop011_applies_to_single_line_immediate_usage():
    """Test that COP011 applies to single-line variables used in next line."""
    code = textwrap.dedent("""
        def func():
            a = 1
            b = a + 1
    """)
    
    tree = ast.parse(code)
    checker = TempVarCheck(tree)
    checker.visit(tree)
    
    assert len(checker.violations) == 1
    assert checker.violations[0].violation_code.code == "COP011"


def test_cop011_not_applied_with_intervening_lines():
    """Test that COP011 does not apply when there are intervening lines."""
    code = textwrap.dedent("""
        def func():
            a = 1
            # some things here
            b = a + 1
    """)
    
    tree = ast.parse(code)
    checker = TempVarCheck(tree)
    checker.visit(tree)
    
    assert len(checker.violations) == 0


def test_cop011_not_applied_to_multi_line_assignment():
    """Test that COP011 does not apply to multi-line assignments."""
    code = textwrap.dedent("""
        def func():
            a = (
                one_item for one_item
                in lst
            )
            b = a[0]
    """)
    
    tree = ast.parse(code)
    checker = TempVarCheck(tree)
    checker.visit(tree)
    
    assert len(checker.violations) == 0


def test_cop011_not_applied_to_tuple_unpacking():
    """Test that COP011 does not apply to tuple unpacking."""
    code = textwrap.dedent("""
        def func():
            a, b = (1, 2)
            c = a + b
    """)
    
    tree = ast.parse(code)
    checker = TempVarCheck(tree)
    checker.visit(tree)
    
    assert len(checker.violations) == 0