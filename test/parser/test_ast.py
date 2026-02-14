"""Tests for src/parser/ast.py."""
from src.parser import AST, pretty_print
from src.lexer import Token


class TestAST:
    def test_leaf_node(self):
        node = AST("x")
        assert node.content == "x"
        assert node.children == []

    def test_node_with_children(self):
        child1 = AST("a")
        child2 = AST("b")
        parent = AST("root", [child1, child2])
        assert parent.content == "root"
        assert len(parent.children) == 2
        assert parent.children[0].content == "a"
        assert parent.children[1].content == "b"

    def test_default_children_is_empty(self):
        n1 = AST("x")
        n2 = AST("y")
        # Verify default children are independent (no shared mutable default)
        assert n1.children is not n2.children

    def test_token_content(self):
        tok = Token("NUM", "42")
        node = AST(tok)
        assert node.content is tok


class TestPrettyPrint:
    def test_single_node(self):
        node = AST("root")
        result = pretty_print(node, 0)
        assert result.strip() == "root"

    def test_nested_tree(self):
        leaf = AST("leaf")
        mid = AST("mid", [leaf])
        root = AST("root", [mid])
        result = pretty_print(root, 0)
        lines = result.strip().split("\n")
        assert lines[0] == "root"
        assert lines[1] == "  mid"
        assert lines[2] == "    leaf"

    def test_str_uses_pretty_print(self):
        leaf = AST("child")
        root = AST("parent", [leaf])
        s = str(root)
        assert "parent" in s
        assert "child" in s

    def test_multiple_children(self):
        c1 = AST("a")
        c2 = AST("b")
        c3 = AST("c")
        root = AST("root", [c1, c2, c3])
        result = pretty_print(root, 0)
        lines = result.strip().split("\n")
        assert len(lines) == 4
        assert lines[0] == "root"
        assert lines[1] == "  a"
        assert lines[2] == "  b"
        assert lines[3] == "  c"
