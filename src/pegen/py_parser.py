from typing import Optional

from pegen.py_tokenizer import PyTokenType
from pegen.tokenizer import TokenInfo
from pegen.base_parser import BaseParser, memoize

class PyParser(BaseParser[PyTokenType]):
    # NOTE: Grammars may not have/use a SOFT_KEYWORD token.
    #       If non-python grammars want to use it, they need to define a handler for it.
    @memoize
    def soft_keyword(self) -> Optional[TokenInfo[PyTokenType]]:
        tok = self._tokenizer.peek()
        if tok.type == PyTokenType.NAME and tok.string in self.SOFT_KEYWORDS:
            return self._tokenizer.getnext()
        return None

    @memoize
    def name(self) -> Optional[TokenInfo[PyTokenType]]:
        tok = self._tokenizer.peek()
        if tok.type == PyTokenType.NAME and tok.string not in self.KEYWORDS:
            return self._tokenizer.getnext()
        return None

    @memoize
    def number(self) -> Optional[TokenInfo[PyTokenType]]:
        tok = self._tokenizer.peek()
        if tok.type == PyTokenType.NUMBER:
            return self._tokenizer.getnext()
        return None

    @memoize
    def string(self) -> Optional[TokenInfo[PyTokenType]]:
        tok = self._tokenizer.peek()
        if tok.type == PyTokenType.STRING:
            return self._tokenizer.getnext()
        return None

    @memoize
    def fstring_start(self) -> Optional[TokenInfo[PyTokenType]]:
        tok = self._tokenizer.peek()
        if tok.type == PyTokenType.FSTRING_START:
            return self._tokenizer.getnext()
        return None

    @memoize
    def fstring_middle(self) -> Optional[TokenInfo[PyTokenType]]:
        tok = self._tokenizer.peek()
        if tok.type == PyTokenType.FSTRING_MIDDLE:
            return self._tokenizer.getnext()
        return None

    @memoize
    def fstring_end(self) -> Optional[TokenInfo[PyTokenType]]:
        tok = self._tokenizer.peek()
        if tok.type == PyTokenType.FSTRING_END:
            return self._tokenizer.getnext()
        return None

    @memoize
    def op(self) -> Optional[TokenInfo[PyTokenType]]:
        tok = self._tokenizer.peek()
        if tok.type == PyTokenType.OP:
            return self._tokenizer.getnext()
        return None

    @memoize
    def type_comment(self) -> Optional[TokenInfo[PyTokenType]]:
        tok = self._tokenizer.peek()
        if tok.type == PyTokenType.TYPE_COMMENT:
            return self._tokenizer.getnext()
        return None
