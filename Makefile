PANDOC ?= pandoc
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
	@refs=$$(unzip -p $(EPUB) 'EPUB/text/*.xhtml' | grep -o 'doc-noteref' | wc -l | tr -d ' '); \
	notes=$$(unzip -p $(EPUB) 'EPUB/text/*.xhtml' | grep -o 'doc-footnote' | wc -l | tr -d ' '); \
	echo "noteref: $$refs footnote: $$notes"; \
	[ "$$refs" = "$$notes" ]
	$(PANDOC) --from=epub --to=plain $(EPUB) > /dev/null && echo "pandoc parse ok"

clean:
	rm -rf build $(EPUB)
