import sys
from enum import IntEnum
from typing import cast, Self, Tuple, Dict, Iterator, List, TypeVar, Optional, Collection, Generic, NamedTuple, Protocol

Mark = int  # NewType('Mark', int)

TokenTypeCo = TypeVar("TokenTypeCo", bound=IntEnum, covariant=True, default=IntEnum)
TokenType = TypeVar("TokenType", bound=IntEnum, default=IntEnum)

Position = Tuple[int, int]

class TokenInfoWithoutExactType(Protocol, Generic[TokenTypeCo]):
    @property
    def type(self) -> TokenTypeCo:
        ...

    @property
    def line(self) -> str:
        ...

    @property
    def string(self) -> str:
        ...

    @property
    def start(self) -> Position:
        ...

    @property
    def end(self) -> Position:
        ...

class TokenInfo(TokenInfoWithoutExactType[TokenTypeCo], Protocol):
    @property
    def exact_type(self) -> Optional[TokenTypeCo]:
        ...

class TokenInfoAdapter(NamedTuple, Generic[TokenType]):
    type: TokenType
    line: str
    string: str
    start: Position
    end: Position
    exact_type: Optional[TokenType] 

class TokenGenerator(Iterator[TokenInfo[TokenType]]):
    def __init__(self, tokengen: Iterator[TokenInfo[TokenType]] | Iterator[TokenInfoWithoutExactType[TokenType]]) -> None:
        raise NotImplementedError()

    def __iter__(self) -> Iterator[TokenInfo[TokenType]]:
        raise NotImplementedError()

    def __next__(self) -> TokenInfo[TokenType]:
        raise NotImplementedError()

class TokenGeneratorAdapter(TokenGenerator[TokenType]):
    def __init__(self, tokengen: Iterator[TokenInfo[TokenType]] | Iterator[TokenInfoWithoutExactType[TokenType]]) -> None:
        self._token_gen = tokengen

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> TokenInfo[TokenType]:
        tok: TokenInfo[TokenType] | TokenInfoWithoutExactType[TokenType] = next(self._token_gen)

        res: TokenInfo[TokenType]
        if not hasattr(tok, "exact_type"):
            res = TokenInfoAdapter(tok.type, tok.line, 
                                   tok.string, 
                                   tok.start, tok.end, 
                                   None)
        else:
            res = cast(TokenInfo[TokenType], tok)
        
        return res

def shorttok(tok: TokenInfo) -> str:
    return "%-25.25s" % f"{tok.start[0]}.{tok.start[1]}: {tok.type.name}:{tok.string!r}"

class BaseTokenizer(Generic[TokenType]):
    """Caching wrapper for the tokenize module.

    This is pretty tied to Python's syntax.
    """

    _tokens: List[TokenInfo[TokenType]]

    def __init__(
        self, 
        tokengen: Iterator[TokenInfo[TokenType] | TokenInfoWithoutExactType[TokenType]] | TokenGenerator[TokenType],
        end_token: TokenType,
        *, 
        skip_tokens: Collection[TokenType] = (),
        collapse_tokens: Collection[TokenType] = (),
        non_syntactic_tokens: Collection[TokenType] = (),
        path: str = "", 
        verbose: bool = False
    ):
        self._collapse_tokens = collapse_tokens
        self._non_syntactic_tokens = non_syntactic_tokens
        self.end_token = end_token
        self._skip_tokens = skip_tokens
        self._tokengen: TokenGenerator[TokenType]
        if isinstance(tokengen, TokenGenerator):
            self._tokengen = tokengen
        else:
            self._tokengen = TokenGeneratorAdapter[TokenType](tokengen)
        self._tokens = []
        self._index = 0
        self._verbose = verbose
        self._lines: Dict[int, str] = {}
        self._path = path
        if verbose:
            self.report(False, False)

    def getnext(self) -> TokenInfo:
        """Return the next token and updates the index."""
        cached = not self._index == len(self._tokens)
        tok = self.peek()
        self._index += 1
        if self._verbose:
            self.report(cached, False)
        return tok

    def get_last_token(self) -> Optional[TokenInfo[TokenType]]:
        if self._tokens:
            return self._tokens[-1]

    def should_skip(self, tok: TokenInfo[TokenType]) -> bool:
        if tok.type in self._skip_tokens:
            return True
        elif tok.type in self._collapse_tokens:
            last_tok = self.get_last_token()
            if last_tok and last_tok.type == tok.type:
                return True
        return False

    def peek(self) -> TokenInfo:
        """Return the next token *without* updating the index."""
        while self._index == len(self._tokens):
            tok = next(self._tokengen)
            if self.should_skip(tok):
                continue
            self._tokens.append(tok)
            if not self._path and tok.start[0] not in self._lines:
                self._lines[tok.start[0]] = tok.line
        return self._tokens[self._index]

    def diagnose(self) -> TokenInfo:
        if not self._tokens:
            self.getnext()
        return self._tokens[-1]

    def get_last_syntactic_token(self) -> TokenInfo[TokenType]:
        # TODO: tok may be unbound if there are no tokens
        for tok in reversed(self._tokens[: self._index]):
            if tok.type != self.end_token and (
                tok.type not in self._non_syntactic_tokens
            ):
                break
        return tok

    def get_lines(self, line_numbers: List[int]) -> List[str]:
        """Retrieve source lines corresponding to line numbers."""
        if self._lines:
            lines = self._lines
        else:
            n = len(line_numbers)
            lines = {}
            count = 0
            seen = 0
            with open(self._path) as f:
                for line in f:
                    count += 1
                    if count in line_numbers:
                        seen += 1
                        lines[count] = line
                        if seen == n:
                            break

        return [lines[n] for n in line_numbers]

    def mark(self) -> Mark:
        return self._index

    def reset(self, index: Mark) -> None:
        if index == self._index:
            return
        assert 0 <= index <= len(self._tokens), (index, len(self._tokens))
        old_index = self._index
        self._index = index
        if self._verbose:
            self.report(True, index < old_index)

    def report(self, cached: bool, back: bool) -> None:
        if back:
            fill = "-" * self._index + "-"
        elif cached:
            fill = "-" * self._index + ">"
        else:
            fill = "-" * self._index + "*"
        if self._index == 0:
            print(f"{fill} (Bof)")
        else:
            tok = self._tokens[self._index - 1]
            print(f"{fill} {shorttok(tok)}")
