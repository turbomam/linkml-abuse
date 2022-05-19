MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help
.DELETE_ON_ERROR:
.SUFFIXES:
.SECONDARY:

RUN = poetry run
# get values from about.yaml file
SCHEMA_NAME = $(shell sh ./utils/get-value.sh name)
SOURCE_SCHEMA_PATH = $(shell sh ./utils/get-value.sh source_schema_path)
SRC = src
DEST = project
PYMODEL = $(SRC)/$(SCHEMA_NAME)/datamodel
DOCDIR = docs

# basename of a YAML file in model/
.PHONY: all clean

help: status
	@echo ""
	@echo "make all -- makes site locally"
	@echo "make install -- install dependencies"
	@echo "make setup -- initial setup"
	@echo "make test -- runs tests"
	@echo "make testdoc -- builds docs and runs local test server"
	@echo "make deploy -- deploys site"
	@echo "make update -- updates linkml version"
	@echo "make help -- show this help"
	@echo ""

status: check-config
	@echo "Project: $(SCHEMA_NAME)"
	@echo "Source: $(SOURCE_SCHEMA_PATH)"

setup: install gen-project gendoc git-init-add

install:
	poetry install
.PHONY: install

all: gen-project gendoc
%.yaml: gen-project
deploy: all mkd-gh-deploy

# generates all project files
gen-project: $(PYMODEL)
	$(RUN) gen-project -d $(DEST) $(SOURCE_SCHEMA_PATH) && mv $(DEST)/*.py $(PYMODEL)

test:
	$(RUN) gen-project -d tmp $(SOURCE_SCHEMA_PATH) 

check-config:
	@(grep my-datamodel about.yaml > /dev/null && printf "\n**Project not configured**:\n\n  - Remember to edit 'about.yaml'\n\n" || exit 0)

convert-examples-to-%:
	$(patsubst %, $(RUN) linkml-convert  % -s $(SOURCE_SCHEMA_PATH) -C Person, $(shell find src/data/examples -name "*.yaml")) 

examples/%.yaml: src/data/examples/%.yaml
	$(RUN) linkml-convert -s $(SOURCE_SCHEMA_PATH) -C Person $< -o $@
examples/%.json: src/data/examples/%.yaml
	$(RUN) linkml-convert -s $(SOURCE_SCHEMA_PATH) -C Person $< -o $@
examples/%.ttl: src/data/examples/%.yaml
	$(RUN) linkml-convert -P EXAMPLE=http://example.org/ -s $(SOURCE_SCHEMA_PATH) -C Person $< -o $@

upgrade:
	poetry add -D linkml@latest

# Test documentation locally
serve: mkd-serve

# Python datamodel
$(PYMODEL):
	mkdir -p $@


$(DOCDIR):
	mkdir -p $@

gendoc: $(DOCDIR)
	cp $(SRC)/docs/*md $(DOCDIR) ; \
	$(RUN) gen-doc -d $(DOCDIR) $(SOURCE_SCHEMA_PATH)

testdoc: gendoc serve

MKDOCS = $(RUN) mkdocs
mkd-%:
	$(MKDOCS) $*

PROJECT_FOLDERS = sqlschema shex shacl protobuf prefixmap owl jsonschema jsonld graphql excel
git-init-add: git-init git-add git-commit git-status
git-init:
	git init
git-add:
	git add .gitignore .github Makefile LICENSE *.md examples utils about.yaml mkdocs.yml poetry.lock project.Makefile pyproject.toml src/linkml/*yaml src/*/datamodel/*py src/data
	git add $(patsubst %, project/%, $(PROJECT_FOLDERS))
git-commit:
	git commit -m 'Initial commit' -a
git-status:
	git status

clean:
	rm -rf $(DEST)
	rm -rf tmp

include project.Makefile

# todo how to trigger rules from included makefile?

.PHONY: clean_targ all_sqlite

all_sqlite_plus: clean_targ target/linkml_abuse_generated.yaml target/persons.yaml \
target/persons_by_schema_from_yaml.db target/persons_by_schema_from_tsv.db target/persons_by_module_from_yaml.db

problematic_sqlite: clean_targ target/persons_by_module_from_yaml.db

clean_targ:
	rm -rf target/*yaml
	rm -rf target/*db

target/linkml_abuse_generated.yaml: $(SOURCE_SCHEMA_PATH)
	# src/linkml/linkml_abuse.yaml
	$(RUN) gen-yaml  $< > $@

target/persons.yaml: src/data/examples/persons.tsv
	$(RUN) linkml-convert \
		--output $@ \
		--target-class Registry \
		--index-slot persons \
		--schema $(SOURCE_SCHEMA_PATH) $<

target/persons_by_module_from_yaml.db: target/persons.yaml
	# https://linkml.io/linkml/intro/tutorial09.html
	poetry run linkml-sqldb dump \
		--module src/linkml-abuse/datamodel/linkml_abuse.py \
		--db $@ $<
	# UnboundLocalError: local variable 'sv' referenced before assignment
	sqlite3 $@ ".tables" ""
	sqlite3 $@ ".headers on" "select * from Person" ""
	sqlite3 $@ ".headers on" "select * from Registry" ""

target/persons_by_schema_from_yaml.db: target/persons.yaml
	# https://linkml.io/linkml/intro/tutorial09.html
	poetry run linkml-sqldb dump \
		--schema $(SOURCE_SCHEMA_PATH) \
		--db $@ $<
	# WARNING:root:There is no established path to my_datamodel - compile_python may or may not work
	sqlite3 $@ ".tables" ""
	# ".mode tabs"
	sqlite3 $@ ".headers on" "select * from Person" ""
	sqlite3 $@ ".headers on" "select * from Registry" ""

target/persons_by_schema_from_tsv.db: src/data/examples/persons.tsv
	# https://linkml.io/linkml/intro/tutorial09.html
	poetry run linkml-sqldb dump \
		--schema $(SOURCE_SCHEMA_PATH) \
		--index-slot persons \
		--db $@ $<
	# WARNING:root:There is no established path to my_datamodel - compile_python may or may not work
	sqlite3 $@ ".tables" ""
	sqlite3 $@ ".headers on" "select * from Person" ""
	sqlite3 $@ ".headers on" "select * from Registry" ""
