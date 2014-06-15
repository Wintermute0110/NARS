# Makefile for XBMCbuntu emulation guide

# Conversion parameters
XSLTPROC=/usr/bin/xsltproc
FOP=/usr/bin/fop
XSL-XHTML=XRU-manual-xhtml-onechunk.xsl
SS-PDF=/usr/share/xml/docbook/stylesheet/nwalsh/fo/docbook.xsl

.PHONY: all

# all: XRU-manual.html XRU-manual.pdf
all: XRU-manual.html

clean:
	rm -f XRU-manual.html 
	rm -f XRU-manual.pdf

# How to create (x)html from xml
%.html: %.xml $(XSL-XHTML)
	$(XSLTPROC) $(XSL-XHTML) $<

# How to create fo from xml
%.fo: %.xml
	$(XSLTPROC) --output $@ --stringparam paper.type a4 --stringparam fop1.extensions 1 --stringparam admon.graphics 1 --stringparam admon.graphics.extension .svg $(SS-PDF) $<

# How to create pdf from fo
%.pdf: %.fo
	$(FOP) -q -fo $< -pdf $@  >/dev/null
