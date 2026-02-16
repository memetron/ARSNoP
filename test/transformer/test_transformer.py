"""Tests for src/transformer/transformer.py."""
from arsnop.transformer import Transformer
from arsnop.parser import AST
from arsnop.lexer import Token


class TestTransformer:
    def test_token_leaf_returns_lexeme(self):
        tok = Token("NUM", "42")
        tree = AST("start", [AST(tok)])

        class T(Transformer):
            def start(self, children):
                return children

        result = T().transform(tree)
        assert result == ["42"]

    def test_custom_visitor(self):
        tok1 = Token("NUM", "3")
        tok2 = Token("NUM", "4")
        tree = AST("add", [AST(tok1), AST(tok2)])

        class Adder(Transformer):
            def add(self, children):
                return int(children[0]) + int(children[1])

        assert Adder().transform(tree) == 7

    def test_nested_transform(self):
        inner_tok = Token("NUM", "5")
        inner = AST("double", [AST(inner_tok)])
        outer = AST("negate", [inner])

        class Math(Transformer):
            def double(self, children):
                return int(children[0]) * 2

            def negate(self, children):
                return -children[0]

        assert Math().transform(outer) == -10

    def test_dfs_order(self):
        """Children are transformed before their parent."""
        order = []
        tok = Token("X", "x")
        tree = AST("root", [AST("child", [AST(tok)])])

        class Recorder(Transformer):
            def child(self, children):
                order.append("child")
                return children[0]

            def root(self, children):
                order.append("root")
                return children[0]

        Recorder().transform(tree)
        assert order == ["child", "root"]

    def test_multiple_children(self):
        t1 = Token("A", "a")
        t2 = Token("B", "b")
        t3 = Token("C", "c")
        tree = AST("collect", [AST(t1), AST(t2), AST(t3)])

        class Collector(Transformer):
            def collect(self, children):
                return "".join(children)

        assert Collector().transform(tree) == "abc"
