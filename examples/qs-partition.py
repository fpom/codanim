from codanim.data import Array, Struct, Value, Heap
from codanim.flow import FUNC, BLOCK, ENV, WS, DECL, WHILE, EXPR, DO, STMT, RETURN, IF

a = Array([3, 13, 5, 0, 7, 11, 4, 9, 14, 2, 10, 1, 12, 8, 6],
          index=["a", "b"])
t = Struct({"len": Value(15), "val": a.ptr()})

h = Heap()
h.new(a)
h.new(t)

partition = FUNC(BLOCK(ENV("t", t),
                       WS("  "),
                       DECL("pivot", EXPR("t.val[(t.len-1)//2]",
                                          src="t.val[(t.len-1)/2]"),
                            animate=True,
                            src="int {name} = {init};"),
                       WS("\n  "),
                       DECL("a", EXPR("-1"),
                            animate=True,
                            src="uint {name} = {init};"),
                       WS("\n  "),
                       DECL("b", EXPR("t.len"),
                            animate=True,
                            src="uint {name} = {init};"),
                       WS("\n  "),
                       WHILE(EXPR("1", src="1"),
                             BLOCK(WS("    "),
                                   DO(STMT("a+=1", src="a++;"),
                                      EXPR("t.val[a] < pivot"),
                                      src="do {{ {body} }} while ({cond});"),
                                   WS("\n    "),
                                   DO(STMT("b-=1", src="b--;"),
                                      EXPR("t.val[b] > pivot"),
                                      src="do {{ {body} }} while ({cond});"),
                                   WS("\n    "),
                                   IF(EXPR("a >= b"),
                                      RETURN(EXPR("b"),
                                             src="return {value};"),
                                      src="if ({cond}) {{ {then} }}"),
                                   WS("\n     "),
                                   STMT("_old = t.val[a], t.val[b]",
                                        "t.val[b], t.val[a] = _old",
                                        src="swap(t, a, b);"),
                                   WS("\n")),
                             src="while ({cond}) {{\n{body}  }}"),
                       WS("\n")),
                 src="uint partition (Tab t) {{\n{body}}}\n")

partition.IP += 1  # do not highlight first step
partition()        # simulate execution

# save code animation
with open("out.code", "w") as out :
    out.write(partition.tex())

# save data animation
with open("out.tikz", "w") as out :
    out.write(h.tex(tikzpicture={"scale": .6}))
