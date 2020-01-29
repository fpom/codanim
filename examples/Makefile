all: heap.pdf

%.pdf: %.py tpl.tex
	ln -sf ../codanim .
	python $< > out.tikz
	latexmk -pdf tpl
	cp tpl.pdf $@
	latexmk -C tpl

clean:
	rm -f $$(grep '^*' ../.gitignore)
