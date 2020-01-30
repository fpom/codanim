from codanim.data import Array, Box
from codanim.flow import FUNC, BLOCK, ENV, WS, XDECL, DECL, PY, EXPR, STMT, WHILE, IF

##
## quicksort partitioning
##

array = Array([3, 13, 5, 0, 7, 11, 4, 9, 14, 2, 10, 1, 12, 8, 6],
              index=["a", "b", "p"])
first = Array(15,
              aggregate={"grow": "north",
                         "ticks": "west",
                         "index": None})
last = Array(15,
             index=["top"],
             aggregate={"grow": "north",
                        "ticks": None,
                        "index": "east"})

def part (tab, first, last) :
    t = [tab[i] for i in range(first, last+1)]
    a, b, pivot = -1, len(t), t[(len(t)-1)//2]
    while True :
        while True :
            a += 1
            if t[a] >= pivot :
                break
        while True :
            b -= 1
            if t[b] <= pivot :
                break
        if a >= b :
            for i, v in enumerate(t) :
                tab[i+first] = v
            return b
        t[a], t[b] = t[b], t[a]

sort = FUNC(BLOCK(ENV("t", array),
                  ENV("part", part),
                  ENV("top", None),
                  ENV("_first", first),
                  ENV("_last", last),
                  WS("\n  "),
                  XDECL("p", "a", "b",
                        src="uint p, a, b;"),
                  WS("\n  "),
                  DECL("first", EXPR("_first", src="stackNew(t.len)"),
                       src="Stack {name} = {init};"),
                  PY("top = 0"),
                  WS("\n  "),
                  DECL("last", EXPR("_last", src="stackNew(t.len)"),
                       src="Stack {name} = {init};"),
                  WS("\n  "),
                  STMT("first[top] = 0",
                       src="stackPush(&first, 0);"),
                  WS("\n  "),
                  STMT("last[top] = (len(t)-1); top += 1",
                       src="stackPush(&last, t.len-1);"),
                  WS("\n  "),
                  WHILE(EXPR("top > 0", src="!stackEmpty(first)"),
                        BLOCK(WS("    "),
                              STMT("a, first[top-1] = first[top-1], None",
                                   src="a = stackPop(&first);"),
                              WS("\n    "),
                              STMT("b, last[top-1] = last[top-1], None; top -= 1",
                                   src="b = stackPop(&last);"),
                              WS("\n    "),
                              IF(EXPR("a < b"),
                                 BLOCK(WS("      "),
                                       STMT("p = a + part(t, a, b)",
                                            src="p = a + partition(slice(t, a, b));"),
                                       WS("\n      "),
                                       STMT("first[top] = a",
                                            src="stackPush(&first, a);"),
                                       WS("\n      "),
                                       STMT("last[top] = p; top += 1",
                                            src="stackPush(&last, p);"),
                                       WS("\n      "),
                                       STMT("first[top] = p+1",
                                            src="stackPush(&first, p+1);"),
                                       WS("\n      "),
                                       STMT("last[top] = b; top += 1",
                                            src="stackPush(&last, b);"),
                                       WS("\n")),
                                 src="if ({cond}) {{\n{then}    }}"),
                              WS("\n")),
                        src="while ({cond}) {{\n{body}  }}\n")),
            src="void sort (Tab t) {{{body}}}")

# run code and save its animation
sort.IP += 1
sort()
with open("out.code", "w") as out :
    out.write(sort.tex())

# save data animation
b = Box(Box(array), Box(first, last, distance="0pt"))
with open("out.tikz", "w") as out :
    out.write(b.tex(tikzpicture={"scale": .55},
                    tail=r"\node at (-2,1) {};"))
