class AST:
    """
    A class to represent a node in an Abstract Syntax Tree (AST).
    Attributes:
        content: The value or label of the node (e.g., a token or non-terminal).
        children (list): A list of child nodes.
    """

    def __init__(self, root, children=None):
        """
        Initializes an ASTNode with a root value and its children.
        Args:
            root: The value or label of the node.
            children (list, optional): A list of child nodes. Defaults to an empty list if not provided.
        """
        if children is None:
            children = []
        self.content: any = root
        self.children: list[AST] = children

    def __str__(self):
        return pretty_print(self, 0)

def pretty_print(node, depth: int) -> str:
    indent = "  " * depth  # Indentation for the current depth
    result = f"{indent}{node.content}\n"
    for child in node.children:
        result += pretty_print(child, depth + 1)  # Recurse for children
    return result
