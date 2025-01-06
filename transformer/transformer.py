from lexer.token import Token
from parser.ast import AST


class Transformer:
    """
    A parent class for transforming an abstract syntax tree (AST) by applying custom transformation rules.
    Should be overridden by language-specific transformers containing methods of how to transform non-terminal nodes
    of the AST.
    Methods:
        transform(root: AST):
            Transforms the AST starting from the root node.
    """
    def transform(self, root: AST) -> any:
        """
        Transforms an AST starting from its root node.
        Args:
            root (AST): The root of the AST to transform.
        Returns:
            Any: The transformed result of the AST.
        """
        return self._transform_dfs(root)

    def _transform_dfs(self, node):
        new_children = []
        for child in node.children:
            new_children.append(self._transform_dfs(child))
        return self._visit(node.content, new_children)

    def _visit(self, root, children):
        if isinstance(root, Token):
            return root.lexeme
        else:
            visit_func = getattr(self, root)
            if visit_func:
                return visit_func(children)
            else:
                return children