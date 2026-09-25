import io
import sys
from tokenize import NEWLINE, NUMBER, ENDMARKER, TokenInfo, generate_tokens

from pegen.tokenizer import PyTokenizer, PyTokenGenAdapter


def test_peek_getnext():
    source = io.StringIO("# test\n1")
    tokengen_adapter = PyTokenGenAdapter(generate_tokens(source.readline))
    t = PyTokenizer(tokengen_adapter)
    assert t.peek() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1")
    assert t.getnext() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1")
    assert t.peek() == TokenInfo(
        NEWLINE, "", (2, 1), (2, 2), "1" if sys.version_info >= (3, 12) else ""
    )
    assert t.getnext() == TokenInfo(
        NEWLINE, "", (2, 1), (2, 2), "1" if sys.version_info >= (3, 12) else ""
    )


def test_mark_reset():
    source = io.StringIO("\n1 2")
    tokengen_adapter = PyTokenGenAdapter(generate_tokens(source.readline))
    t = PyTokenizer(tokengen_adapter)
    index = t.mark()
    assert t.peek() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1 2")
    assert t.getnext() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1 2")
    t.reset(index)
    assert t.peek() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1 2")
    assert t.getnext() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1 2")


def test_last_non_whitespace():
    source = io.StringIO("\n1\n2")
    tokengen_adapter = PyTokenGenAdapter(generate_tokens(source.readline))
    t = PyTokenizer(tokengen_adapter)
    assert t.peek() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1\n")
    assert t.getnext() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1\n")
    assert t.getnext() == TokenInfo(NEWLINE, "\n", (2, 1), (2, 2), "1\n")
    assert t.get_last_syntactic_token() == TokenInfo(NUMBER, "1", (2, 0), (2, 1), "1\n")


def test_get_lines():
    source = io.StringIO("1\n2\n3")
    tokengen_adapter = PyTokenGenAdapter(generate_tokens(source.readline))
    t = PyTokenizer(tokengen_adapter)
    while True:
        if t.getnext().type == ENDMARKER:
            break
    assert t.get_lines([1, 2, 3]) == ["1\n", "2\n", "3"]
