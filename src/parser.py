import ast
from pathlib import Path
from models import ImportEdge, ModuleInfo, ModuleMetrics
from scanner import module_name_from_path, package_name_from_module


class ModuleParser:
    def __init__(self, root: Path, known_modules: set[str]):
        self.root = root.resolve()
        self.known_modules = known_modules
        self.known_roots = {name.split(".")[0] for name in known_modules}

    def parse(self, path: Path) -> ModuleInfo:
        module_name = module_name_from_path(self.root, path)
        info = ModuleInfo(
            name=module_name, path=path, package=package_name_from_module(module_name)
        )
        text = path.read_text(encoding="utf-8")
        info.metrics.lines = len(text.splitlines())
        info.metrics.code_lines = self._count_code_lines(text)
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            info.syntax_error = f"{exc.msg} at line {exc.lineno}"
            return info
        visitor = _AstVisitor(module_name, self.known_modules, self.known_roots)
        visitor.visit(tree)
        info.imports = visitor.imports
        info.classes = visitor.classes
        info.functions = visitor.functions
        info.methods = visitor.methods
        info.call_names = visitor.call_names
        info.metrics.import_count = len(info.imports)
        info.metrics.class_count = len(info.classes)
        info.metrics.function_count = len(info.functions)
        info.metrics.method_count = sum(len(items) for items in info.methods.values())
        info.metrics.async_function_count = visitor.async_function_count
        info.metrics.branch_count = visitor.branch_count
        info.metrics.max_nesting = visitor.max_nesting
        info.metrics.complexity_score = self._complexity(info.metrics)
        return info

    def _count_code_lines(self, text: str) -> int:
        total = 0
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                total += 1
        return total

    def _complexity(self, metrics: ModuleMetrics) -> int:
        return (
            metrics.code_lines
            + metrics.import_count * 2
            + metrics.class_count * 4
            + metrics.function_count * 3
            + metrics.method_count * 2
            + metrics.async_function_count * 3
            + metrics.branch_count * 5
            + metrics.max_nesting * 4
        )


class _AstVisitor(ast.NodeVisitor):
    def __init__(
        self, module_name: str, known_modules: set[str], known_roots: set[str]
    ):
        self.module_name = module_name
        self.known_modules = known_modules
        self.known_roots = known_roots
        self.imports: list[ImportEdge] = []
        self.classes: list[str] = []
        self.functions: list[str] = []
        self.methods: dict[str, list[str]] = {}
        self.call_names: list[str] = []
        self.async_function_count = 0
        self.branch_count = 0
        self.max_nesting = 0
        self._class_stack: list[str] = []
        self._nesting = 0

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            target = alias.name
            self.imports.append(
                ImportEdge(
                    self.module_name,
                    target,
                    alias.asname or alias.name,
                    node.lineno,
                    self._is_external(target),
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        base = self._resolve_from_import(node)
        for alias in node.names:
            target = base
            if base and f"{base}.{alias.name}" in self.known_modules:
                target = f"{base}.{alias.name}"
            self.imports.append(
                ImportEdge(
                    self.module_name,
                    target,
                    alias.asname or alias.name,
                    node.lineno,
                    self._is_external(target),
                )
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.append(node.name)
        self.methods.setdefault(node.name, [])
        self._class_stack.append(node.name)
        self._visit_nested(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if self._class_stack:
            self.methods.setdefault(self._class_stack[-1], []).append(node.name)
        else:
            self.functions.append(node.name)
        self._visit_nested(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.async_function_count += 1
        self.visit_FunctionDef(node)

    def visit_If(self, node: ast.If) -> None:
        self.branch_count += 1
        self._visit_nested(node)

    def visit_For(self, node: ast.For) -> None:
        self.branch_count += 1
        self._visit_nested(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.branch_count += 1
        self._visit_nested(node)

    def visit_While(self, node: ast.While) -> None:
        self.branch_count += 1
        self._visit_nested(node)

    def visit_Try(self, node: ast.Try) -> None:
        self.branch_count += len(node.handlers) + 1
        self._visit_nested(node)

    def visit_Match(self, node: ast.Match) -> None:
        self.branch_count += len(node.cases)
        self._visit_nested(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.branch_count += max(0, len(node.values) - 1)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = self._call_name(node.func)
        if name:
            self.call_names.append(name)
        self.generic_visit(node)

    def _visit_nested(self, node: ast.AST) -> None:
        self._nesting += 1
        self.max_nesting = max(self.max_nesting, self._nesting)
        self.generic_visit(node)
        self._nesting -= 1

    def _call_name(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = self._call_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return None

    def _resolve_from_import(self, node: ast.ImportFrom) -> str:
        module = node.module or ""
        if node.level == 0:
            return module
        current_parts = self.module_name.split(".")[:-1]
        prefix_length = max(0, len(current_parts) - node.level + 1)
        prefix = current_parts[:prefix_length]
        if module:
            prefix.extend(module.split("."))
        return ".".join(part for part in prefix if part)

    def _is_external(self, target: str) -> bool:
        if not target:
            return False
        root = target.split(".")[0]
        return root not in self.known_roots
