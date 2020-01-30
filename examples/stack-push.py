from codanim.data import Heap, Struct, Value
from codanim.flow import FUNC, BLOCK, ENV, WS, DECL, EXPR, STMT

heap = Heap()

stack = heap.new(Struct({"val": Value(1), "next": None}))
stack = heap.new(Struct({"val": Value(2), "next": stack}))
s = Value(stack, nodeid="s")
t = Value(None, nodeid="t", value={"xshift": "-25mm"})

v = Heap(heap={"grow": "above",
               "separation": "0pt"})
h = Heap(heap={"grow": "right"},
         )
h.new(t)
h.new(s)
v.new(heap)
v.new(h)

push = FUNC(BLOCK(ENV("s", s),
                  ENV("u", Value(3)),
                  ENV("top", t),
                  ENV("new", heap.new),
                  ENV("Struct", Struct),
                  ENV("Value", Value),
                  WS("\n  "),
                  DECL("top", EXPR("new(Struct({'val': None, 'next': None}))",
                                   src="malloc(sizeof(StackCell))"),
                       src="Stack {name} = {init};"),
                  WS("\n  "),
                  STMT("top.val = u", src="top->val = u;"),
                  WS("\n  "),
                  STMT("top.next = s", src="top->next = *s;"),
                  WS("\n  "),
                  STMT("s = top", src="*s = top;"),
                  WS("\n")),
            src="void stackPush (Stack* s, uint u) {{{body}}}\n")

# run code and save its animation
push.IP += 1
push()
with open("out.code", "w") as out :
    out.write(push.tex())

# save data and animation
with open("out.tikz", "w") as out :
    out.write(v.tex(tail=r"""
    \node[above] at (s.north) {\texttt{s}};
    \node[above] at (t.north) {\texttt{top}};
    """))
