PYTHON ?= python3
EPUB := yuwen-suyang-gaoji-duben.epub
MD := manuscript.md

.PHONY: all epub check clean

all: epub

epub: $(EPUB)

$(EPUB): $(MD) build_epub.py cover.jpg
	$(PYTHON) build_epub.py

check: $(EPUB)
	unzip -t $(EPUB) > /dev/null && echo "zip ok"
	$(PYTHON) -c "\
import re, glob, zipfile; \
z = zipfile.ZipFile('$(EPUB)'); \
refs = asides = 0; \
[None for n in z.namelist() if n.endswith('.xhtml') for s in [z.read(n).decode('utf-8')] for _ in [0]]; \
import sys; \
refs = sum(len(re.findall(r'id=\"fnref-', z.read(n).decode('utf-8'))) for n in z.namelist() if n.endswith('.xhtml')); \
asides = sum(len(re.findall(r'id=\"fn-', z.read(n).decode('utf-8'))) for n in z.namelist() if n.endswith('.xhtml')); \
print('fnref:', refs, 'aside:', asides); \
sys.exit(0 if refs == asides else 1)"

clean:
	rm -rf build $(EPUB)
