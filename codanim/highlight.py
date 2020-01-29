from pygments import highlight as _pygmentize
import pygments.lexers, pygments.formatters

##
## code pretty-printing
##

_lexer = pygments.lexers.get_lexer_by_name("C")
_formatter = pygments.formatters.get_formatter_by_name("latex")

def pygmentize (src) :
    return "\n".join("\n".join(_pygmentize(line, _lexer, _formatter).splitlines()[1:-1])
                     for line in src.split("\n"))
