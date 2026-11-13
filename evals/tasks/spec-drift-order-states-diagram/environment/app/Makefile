DOT_SOURCES := $(wildcard docs/diagrams/*.dot)

.PHONY: diagrams
diagrams: $(DOT_SOURCES:.dot=.svg)

docs/diagrams/%.svg: docs/diagrams/%.dot
	dot -Tsvg $< -o $@
