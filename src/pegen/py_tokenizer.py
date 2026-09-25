from enum import IntEnum
import tokenize
import token

from typing import Iterator, Self, NamedTuple, Optional, cast, TYPE_CHECKING
from pegen.base_tokenizer import TokenType, BaseTokenizer, TokenInfo, Position, TokenGenerator, TokenInfoWithoutExactType

exact_token_types = token.EXACT_TOKEN_TYPES

if TYPE_CHECKING:
    class PyTokenType(IntEnum):
        ...
else:
    PyTokenType =IntEnum("PyTokenType", {name: value for value, name in token.tok_name.items()})

class PyTokenInfo(NamedTuple):
    type: PyTokenType
    line: str
    string: str
    start: Position
    end: Position

    @property
    def exact_type(self) -> Optional[PyTokenType]:
        if self.type.value in exact_token_types.values():
            return PyTokenType(exact_token_types[self.string])
        return None
    
class PyTokenGenerator(TokenGenerator[PyTokenType]):
    def __init__(self, tokengen: Iterator[TokenInfo[PyTokenType]] | Iterator[TokenInfoWithoutExactType[PyTokenType]] | Iterator[tokenize.TokenInfo]):
        self._token_gen = tokengen

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> TokenInfo[PyTokenType]:
        tok: TokenInfo[PyTokenType] | TokenInfoWithoutExactType[PyTokenType] | tokenize.TokenInfo = next(self._token_gen)

        res: TokenInfo[PyTokenType]
        if type(tok) is tokenize.TokenInfo:
            res = PyTokenInfo(PyTokenType(tok.type), tok.line, tok.string, tok.start, tok.end)
        elif not hasattr(tok, "exact_type"):
            tok = cast(TokenInfo[PyTokenType], tok)
            res = PyTokenInfo(tok.type, tok.line, tok.string, tok.start, tok.end)
        else:
            res = cast(TokenInfo[PyTokenType], tok)

        return res

class PyTokenizer(BaseTokenizer[PyTokenType]):
    def __init__(self,
                 tokengen: Iterator[tokenize.TokenInfo] | Iterator[TokenInfo[PyTokenType] | TokenInfoWithoutExactType[PyTokenType]] | PyTokenGenerator,
                 *,
                 path: str = "",
                 verbose: bool = False):
        if not isinstance(tokengen, PyTokenGenerator):
            tokengen = PyTokenGenerator(tokengen)
        super().__init__(tokengen,
                         PyTokenType.ENDMARKER,
                         skip_tokens=(PyTokenType.COMMENT, PyTokenType.NL),
                         collapse_tokens=(PyTokenType.NEWLINE,),
                         non_syntactic_tokens=(PyTokenType.NEWLINE, PyTokenType.INDENT, PyTokenType.DEDENT),
                         path=path,
                         verbose=verbose)

    def should_skip(self, tok: TokenInfo[PyTokenType]) -> bool:
        if super().should_skip(tok):
            return True
        elif (tok.type == PyTokenType.ERRORTOKEN and tok.string == " "):
            return True
        else:
            return False                
