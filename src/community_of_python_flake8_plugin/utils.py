from __future__ import annotations
import ast


def find_parent_class_definition(syntax_tree: ast.AST, target_node: ast.AST) -> ast.ClassDef | None:
    for potential_parent in ast.walk(syntax_tree):
        if isinstance(potential_parent, ast.ClassDef):
            for child_node in ast.walk(potential_parent):  # noqa: COP007
                if child_node is target_node:
                    return potential_parent
    return None
