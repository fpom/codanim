all: heap.pdf qs-partition.pdf qs-main.pdf stack-push.pdf
gif: qs-partition.gif qs-main.gif stack-push.gif
mp4: qs-partition.mp4 qs-main.mp4 stack-push.mp4

%.pdf: %.py tpl.tex
	ln -sf ../codanim .
	rm -f out.*
	python3 $<
	pdflatex tpl
	pdflatex tpl
	cp tpl.pdf $@

%.gif: %.pdf
	rm -rf _gif
	mkdir _gif
	gs -dSAFER -DBATCH -dNOPAUSE -sDEVICE=png16m -r400 -sOutputFile=_gif/%03d.png $<
	mogrify -resize 800x600 -format gif _gif/*.png
	gifsicle -k64 -d80 -l0 _gif/*.gif -O2 -o $@
	rm -rf _gif

%.mp4: %.pdf
	rm -rf _mp4
	mkdir _mp4
	gs -dSAFER -DBATCH -dNOPAUSE -sDEVICE=png16m -r400 -sOutputFile=_mp4/%03d.png $<
	ffmpeg -r 1 -s 1024x768 -i _mp4/%03d.png -vcodec libx264 -crf 25 -pix_fmt yuv420p $@
	rm -rf _mp4

clean:
	rm -f out.* $$(grep '^*' ../.gitignore)
	rm -rf _gif
	rm -rf _mp4
