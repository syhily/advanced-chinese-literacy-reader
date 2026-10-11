PANDOC ?= pandoc
PYTHON ?= python3
EPUB := advanced-chinese-literacy-reader.epub
SRC_FILES := $(sort $(wildcard manuscript/*.md))

.PHONY: all epub check clean

all: epub

epub: $(EPUB)

$(EPUB): $(SRC_FILES) filter.lua epub.css metadata.yaml cover.jpg
	$(PANDOC) --from=markdown-tex_math_dollars \
		--to=epub3 --lua-filter=filter.lua \
		--toc-depth=4 --split-level=3 \
		--css=epub.css --metadata-file=metadata.yaml \
		--epub-cover-image=cover.jpg \
		--output=$@ $(SRC_FILES)

check: $(EPUB)
	unzip -t $(EPUB) > /dev/null && echo "zip ok"
	$(PYTHON) -c "\
import re, sys, zipfile; \
z = zipfile.ZipFile('$(EPUB)'); \
xhtml = [z.read(n).decode('utf-8') for n in z.namelist() if n.endswith(('.xhtml', '.html'))]; \
refs = sum(s.count('doc-noteref') for s in xhtml); \
notes = sum(s.count('doc-footnote') for s in xhtml); \
print('noteref:', refs, 'footnote:', notes); \
sys.exit(0 if refs == notes else 1)"

clean:
	rm -rf build $(EPUB)
