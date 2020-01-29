from codanim.data import Heap, Struct, Value

h = Heap()
p = h.new(Struct({"data": 1, "next": None}))
p = h.new(Struct({"data": 2, "next": p}))
p = h.new(Struct({"data": 3, "next": p}))
h.new(Value(p, value={"yshift": "-1cm"}))

with open("out.tikz", "w") as out :
    out.write(h.tex(tikzpicture={"scale": .7}))
