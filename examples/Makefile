all: heap.pdf qs-partition.pdf qs-main.pdf

%.pdf: %.py tpl.tex
	ln -sf ../codanim .
	rm -f out.*
	python $<
	pdflatex tpl
	pdflatex tpl
	cp tpl.pdf $@

clean:
	rm -f out.* $$(grep '^*' ../.gitignore)
