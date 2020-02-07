# codanim: Animated code & data structures with LaTeX/beamer 

    (C) 2020 Franck Pommereau <franck.pommereau@univ-evry.fr>
        This is free software, see file LICENCE

codanim allows to generate LaTeX/TikZ code to animate source code and
data structures for beamer presentations. So far, it is oriented to
simulate C code, but there is no conceptual limitation for the
simulation of other languages.

codanim is currently highly experimental and neither well documented
nor well tested. You've been warned.

## INSTALL

There is so far no installation procedure. Just copy directory
`codanim` somewhere in your `PYTHONPATH`.

File `examples/pygments.sty` will be needed to compile the final LaTeX
files. File `examples/tpl.tex` shows how the generated LaTeX code may
be included in a beamer presentation.

## CONCEPTS

codanim defines Python classes to simulate the data and control-flow
structures of an imperative language. Data structures are defined in
`codanim.data` and include:

 * `Pointer(data)` a pointer to another data `data`
 * `Value(value)` an arbitrary value, initialised to `value`. If
   `value` is `None` (the default), the value is considered
   uninitialised
 * `Array(init, index=[])` an array of values, that is zero-indexed,
   and initialised as follows:
    * if `init` is an `int`, then it is the length of the array whose
      values are all uninitialised
    * if `init` is a `list` then is holds the initial values of the
      array
   `index` is a list of variables identifiers that may be used to
   access the array cells (see below)
 * `Struct(init)` a structure whose fields and initial values are
   defined by `init` that must be a `dict`
 * `Heap()` a container for dynamically allocated data that provides
   methods `new` and `free` to do so

Control-flow structures are used to simulate within Python code that
may potentially be written in any imperative language. Doing so, all
the changes that are made to the data structures defined above are
recorded so that they may be latter animated, consistently with the
animation of the code itself. The idea is that source code in the
simulated language is split into corresponding control-flow
structures, and actual computation is done using equivalent Python
code instead of executing the code in the source language.
Control-flow structures are defined in `codanim.flow` and include:

 * `RAW(src='...')` raw code from the simulated language, its
   simulation is no-op, but it is rendered highlighted in the final
   animation
 * `WS(src='...')` just like `RAW` but should be only white spaces (so
   that it won't be highlighted)
 * `BLOCK(*body)` a group of other structures that are simulated (and
   rendered) sequentially
 * `STMT(*steps, src='...')` an arbitrary statement that is simulated
   by running its`steps` sequentially, each of which being an
   arbitrary Python statement that is `exec`ed
 * `EXPR(expr, src='...')` an arbitrary Python expression `expr` that
   simulate an expression in the simulated language
 * `PY(code)` an arbitrary Python statement that need to be executed
   but is not rendered in the final animation, just like every
   structure that expects no `src='...'` argument
 * `ENV(name, value)` a data structure that need to be defined in
   order to do the simulation (typically: global or external
   variables), and which is stored into variable `name` that can be
   used from the Python code of statements and expression
 * `DECL(name, init=None, animate=False, src'...')` an actual variable
   declaration in the simulated language, that will be executed and
   rendered. The execution consists of evaluating `init` that should
   be an `EXPR` (or `None`) and assigning its value to `name`. If
   `animate` is `True` then the value of the variable will displayed
   within a comment just next to the declaration in the final
   animation
 * `XDECL(*names, src='...')` several uninitialised declarations
 * `BREAK` a `break` instruction for loops and switches
 * `RETURN(value, src='...')` a return instruction from a function
 * `IF(cond, then, otherwise=None, src='...')` simulates an `if` block
   with an optional `else` part (called `otherwise` since `else` is a
   Python keyword. Argument `cond` should be an `EXPR` instance
 * `WHILE(cond, body, src='...')` simulates a `while` loop
 * `DO(body, cond, src='...')` simulates a `do/while` loop
 * `FOR(init, cont, step, body)` simulates a C-like `for` loop
 * `FUNC(body, src='...')` simulates a function
   **TODO:** functions calls is not implemented yet, so basically, a
   function is so far only a `BLOCK` with source code
 * `SWITCH(cond, *cases, src='...')` simulates a C-like switch,
   `cases` may be:
   * `CASE(value, body)` to simulate a `case` statement
   * `DEFAULT()` to simulate a `default` statement

So, all what you need is to defined some data structures, some
control-flow structures with appropriate `src` arguments (so that code
is rendered in the simulated language), and with appropriate Python
code to simulate the original statements and expressions.

Writing the control-flow structures may be tedious, so codanim may be
called from the command line to parse actual code to be simulated and
generate the appropriate control-flow structures (in which the Python
code remains to be written). Run `python -m codanim` for help.

## EXAMPLES

File `examples/Makefile` can be used to build the PDF for all the
examples. For instance use `make heap.pdf` to build the first example
described below.

### `examples/heap.py`

It defines a `Heap` instance and add chained `Struct`s to it. The
final picture is rendered as TikZ code. There is no animation, this is
just the picture of a chained list.

### `examples/stack-push.py`

It uses the same kind of linked lists as above, seen as stacks, to
animate a push onto a stack. First the data is defined, then the
control-flow structure. The latter is then simulated and finally, both
code and data structures are rendered for LaTeX/beamer inclusion.

Note the use of class `Box` that can be used to layout several data
structures.

### `examples/qs-partition.py` and `examples/qs-main.py`

The partitioning and main algorithm of a quick-sort. This shows how to
use `Array`, in particular the `index` argument. `qs-main` also shows
how to define custom layout of arrays, as well as auxiliary Python
functions to simulate full C-functions calls in one step.
