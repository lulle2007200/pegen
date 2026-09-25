from pegen.py_tokenizer import PyTokenType
from enum import IntEnum
from typing import Protocol, Any, Generic
import time
import sys
import traceback
import ast
import argparse

from pegen.base_parser import BaseParser, logger, memoize, memoize_left_rec
from pegen.py_parser import PyParser
from pegen.py_parser import PyParser as Parser
from pegen.base_tokenizer import BaseTokenizer
from pegen.tokenizer import TokenType, Tokenizer, TokenizerFactory, PyTokenizer, TokengenFactory, py_tokengen_factory

class ParserFactory(Protocol, Generic[TokenType]):
    def __call__(self, tokenizer: BaseTokenizer[TokenType], *, verbose: bool) -> BaseParser[TokenType]:
        ...

class DumpFunc(Protocol):
    def __call__(self, tree: Any, filename: str) -> None:
        ...

class RunFunc(Protocol):
    def __call__(self, tree: Any, filename: str) -> None:
        ...

def simple_parser_main(parser_factory: ParserFactory[Any] = PyParser, 
                       tokenizer_factory: TokenizerFactory[Any] = PyTokenizer,
                       tokengen_factory: TokengenFactory[Any] = py_tokengen_factory,
                       dump: DumpFunc = lambda tree, filename: print(ast.dump(tree)),
                       run: RunFunc = lambda tree, filename: exec(compile(tree, filename=filename, mode="exec"))):
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Print timing stats; repeat for more debug output",
    )
    argparser.add_argument(
        "-q", "--quiet", action="store_true", help="Don't print the parsed program"
    )
    argparser.add_argument("-r", "--run", action="store_true", help="Run the parsed program")
    argparser.add_argument("filename", help="Input file ('-' to use stdin)")

    args = argparser.parse_args()
    verbose = args.verbose
    verbose_tokenizer = verbose >= 3
    verbose_parser = verbose == 2 or verbose >= 4

    t0 = time.time()

    filename = args.filename
    if filename == "" or filename == "-":
        filename = "<stdin>"
        file = sys.stdin
    else:
        file = open(args.filename)
    try:
        tokengen = tokengen_factory(file)
        tokenizer = tokenizer_factory(tokengen, verbose=verbose_tokenizer)
        parser = parser_factory(tokenizer, verbose=verbose_parser)
        tree = parser.start()
        try:
            if file.isatty():
                endpos = 0
            else:
                endpos = file.tell()
        except IOError:
            endpos = 0
    finally:
        if file is not sys.stdin:
            file.close()

    t1 = time.time()

    if not tree:
        err = parser.make_syntax_error(filename)
        traceback.print_exception(err.__class__, err, None)
        sys.exit(1)

    if not args.quiet:
        dump(tree, filename)
    if args.run:
        run(tree, filename)

    if verbose:
        dt = t1 - t0
        diag = tokenizer.diagnose()
        nlines = diag.end[0]
        if diag.type == tokenizer.end_token:
            nlines -= 1
        print(f"Total time: {dt:.3f} sec; {nlines} lines", end="")
        if endpos:
            print(f" ({endpos} bytes)", end="")
        if dt:
            print(f"; {nlines / dt:.0f} lines/sec")
        else:
            print()
        print("Caches sizes:")
        print(f"  token array : {len(tokenizer._tokens):10}")
        print(f"        cache : {len(parser._cache):10}")
        ## print_memstats()