import ast


# Define a visitor class to traverse the AST and extract table names
class TableNameExtractor(ast.NodeVisitor):
    def __init__(self):
        self.table_names = []

    def visit_ClassDef(self, node):
        if table_name := next(
            (
                statement.value.s
                for statement in node.body
                if isinstance(statement, ast.Assign)
                and (
                    isinstance(statement.targets[0], ast.Name)
                    and statement.targets[0].id == "__tablename__"
                )
            ),
            None,
        ):
            self.table_names.append(table_name)
        self.generic_visit(node)

    def visit_Assign(self, node):
        if (
            hasattr(node, "value")
            and hasattr(node.value, "args")
            and hasattr(node.value, "func")
            and hasattr(node.value.func, "id")
        ):
            if table_name := next(
                (
                    arg.s
                    for arg in node.value.args
                    if isinstance(node.value, ast.Call)
                    and isinstance(node.value.args, ast.Constant)
                    and node.value.func.id == "Table"
                ),
                None,
            ):
                self.table_names.append(table_name)
        self.generic_visit(node)
