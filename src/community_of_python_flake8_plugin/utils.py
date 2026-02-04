from __future__ import annotations
import ast


def check_module_has_all_declaration(module_node: ast.Module) -> bool:
    for statement in module_node.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__" for target in statement.targets
        ):
            return True
        if (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.target.id == "__all__"
        ):
            return True
    return False


def find_parent_class_definition(syntax_tree: ast.AST, target_node: ast.AST) -> ast.ClassDef | None:
    for potential_parent in ast.walk(syntax_tree):
        if isinstance(potential_parent, ast.ClassDef):
            for child_node in ast.walk(potential_parent):  # noqa: COP007
                if child_node is target_node:
                    return potential_parent
    return None


def find_parent_function(syntax_tree: ast.AST, target_node: ast.AST) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for potential_parent in ast.walk(syntax_tree):
        if isinstance(potential_parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child_node in ast.walk(potential_parent):  # noqa: COP007
                if child_node is target_node:
                    return potential_parent
    return None
