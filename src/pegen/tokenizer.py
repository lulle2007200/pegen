from typing import Generic
from pegen.py_tokenizer import PyTokenInfo
from pegen.py_tokenizer import PyTokenType
from pegen.base_tokenizer import TokenTypeCo
from typing import Protocol, Iterator, TextIO
import tokenize

from pegen.base_tokenizer import BaseTokenizer, TokenType, TokenInfo, Mark, TokenGenerator
from pegen.py_tokenizer import PyTokenizer, PyTokenGenerator
from pegen.py_tokenizer import PyTokenizer as Tokenizer

class TokenizerFactory(Protocol, Generic[TokenType]):
    def __call__(self, tokengen: Iterator[TokenInfo[TokenType]], *, verbose: bool) -> BaseTokenizer[TokenType]:
        ...

class TokengenFactory(Protocol, Generic[TokenTypeCo]):
    def __call__(self, file: TextIO) -> Iterator[TokenInfo[TokenTypeCo]]:
        ...

def py_tokengen_factory(file: TextIO) -> Iterator[TokenInfo[PyTokenType]]:
    return PyTokenGenerator(tokenize.generate_tokens(file.readline))
