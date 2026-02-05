from __future__ import annotations
import ast


def find_parent_class_definition(syntax_tree: ast.AST, target_node: ast.AST) -> ast.ClassDef | None:
    for potential_parent in ast.walk(syntax_tree):
        if isinstance(potential_parent, ast.ClassDef):
            for child_node in ast.walk(potential_parent):
                if child_node is target_node:
                    return potential_parent
    return None


def find_parent_function_definition(syntax_tree: ast.AST, target_node: ast.AST) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for potential_parent in ast.walk(syntax_tree):
        if isinstance(potential_parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child_node in ast.walk(potential_parent):
                if child_node is target_node:
                    return potential_parent
    return None


def check_inherits_from_bases(class_definition: ast.ClassDef, base_classes: set[str]) -> bool:
    for base_class in class_definition.bases:
        if isinstance(base_class, ast.Name) and base_class.id in base_classes:
            return True
        if isinstance(base_class, ast.Attribute) and base_class.attr in base_classes:
            return True
        # Handle generic types like ModelFactory[SomeType]
        if isinstance(base_class, ast.Subscript):
            if isinstance(base_class.value, ast.Name) and base_class.value.id in base_classes:
                return True
            if isinstance(base_class.value, ast.Attribute) and base_class.value.attr in base_classes:
                return True
    return False


def find_parent_node(syntax_tree: ast.AST, target_node: ast.AST, node_types: tuple[type, ...]) -> ast.AST | None:
    for potential_parent in ast.walk(syntax_tree):
        if isinstance(potential_parent, node_types):
            for child_node in ast.walk(potential_parent):
                if child_node is target_node:
                    return potential_parent
    return None
