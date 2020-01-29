all: heap.pdf qs-partition.pdf

%.pdf: %.py tpl.tex
	ln -sf ../codanim .
	rm -f out.*
	python $<
	latexmk -pdf tpl
	cp tpl.pdf $@
	latexmk -C tpl

clean:
	rm -f $$(grep '^*' ../.gitignore)
