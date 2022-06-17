import ast
import builtins
from typing import Any

ATTRIBUTES_BLACKLIST = ["token", "base_url", "request", "private_key"]

BUILTINS_BLACKLIST = [
    "exec",
    "eval",
    "compile",
    "globals",
    "locals",
    "vars",
    "builtins",
    "dir",
    "open",
    "input",
    "breakpoint",
    "getattr",
    "delattr",
    "__dict__",
    "__base__",
    "__loader__",
]

BUILTINS_WHITELIST = {
    "str": builtins.str,
    "abs": builtins.abs,
    "len": builtins.len,
    "bool": builtins.bool,
    "dict": builtins.dict,
    "filter": builtins.filter,
    "float": builtins.float,
    "int": builtins.int,
    "list": builtins.list,
    "map": builtins.map,
    "max": builtins.max,
    "min": builtins.min,
    "pow": builtins.pow,
    "range": builtins.range,
    "round": builtins.round,
    "set": builtins.set,
    "sum": builtins.sum,
    "__import__": builtins.__import__,
}

MODULES_WHITELIST = [
    "math",
    "types",
    "time",
    "datetime",
    "random",
    "re",
    "telegram",
    "requests",
    "PIL",
    "textwrap",
    "gtts",
    "json",
]


class UnsafeCodeError(Exception):
    pass


class SecureNodeVisitor(ast.NodeVisitor):
    def visit_Attribute(self, node: ast.Attribute) -> Any:
        if "__" in node.attr:
            raise UnsafeCodeError("Attempting to access private attribute")
        elif node.attr in ATTRIBUTES_BLACKLIST:
            raise UnsafeCodeError("Operation with these attributes is disallowed")

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            if alias.name not in MODULES_WHITELIST:
                raise UnsafeCodeError(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        if node.module not in MODULES_WHITELIST:
            raise UnsafeCodeError(node.module)


def secure_compile(source, filename="<unknown>", mode="exec"):
    code_node = ast.parse(source, filename, mode)
    SecureNodeVisitor().visit(ast.parse(source, filename, mode))
    return compile(code_node, filename, mode)
