## Add your own custom Makefile targets here

## don't add anything to the Makefile, because that could be overwritten by the template

## unfortunately, the default? Makefile plugin for PyCharm
##   can't seem to launch *.makefile (non-Makefile) rules from the GUI

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

# ---

.PHONY: clean_targ all_sqlite l2s

all_sqlite_plus: clean_targ target/linkml_abuse_generated.yaml target/persons.yaml \
target/persons_by_schema_from_yaml.db target/persons_by_schema_from_tsv.db target/persons_by_module_from_yaml.db

problematic_sqlite: clean_targ target/persons_by_module_from_yaml.db

clean_targ:
	rm -rf target/*yaml
	rm -rf target/*db
	rm -rf target/*tsv

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
		--target-class Registry \
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

schemasheets/output/template.tsv:
	$(RUN) linkml2sheets \
		--schema $(SOURCE_SCHEMA_PATH) schemasheets/templates/*.tsv -d schemasheets/output/ --overwrite

target/schema_definition_slotvals.tsv:
	$(RUN) python utils/get_metaclass_slotvals.py --selected_element schema_definition

target/annotation_slotvals.tsv:
	$(RUN) python utils/get_metaclass_slotvals.py --selected_element annotation

target/annotations.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source $(SOURCE_SCHEMA_PATH) \
		--meta_element annotation \
		--tsv_output $@

target/annotations.yaml: target/annotations.tsv
	$(RUN) sheets2linkml \
		--output $@ $<

target/enums.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source $(SOURCE_SCHEMA_PATH) \
		--meta_element enum_definition \
		--tsv_output $@

target/enums.yaml: target/enums.tsv
	$(RUN) sheets2linkml \
		--output $@ $<

target/nmdc_annotations.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source "/home/mark/gitrepos/nmdc-schema/src/schema/nmdc.yaml" \
		--meta_element annotation \
		--tsv_output $@

target/nmdc_enums.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source "/home/mark/gitrepos/nmdc-schema/src/schema/nmdc.yaml" \
		--meta_element enum_definition \
		--tsv_output $@

target/mixs_annotations.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source "/home/mark/gitrepos/mixs/model/schema/mixs.yaml" \
		--meta_element annotation \
		--tsv_output $@

target/mixs_enums.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source "/home/mark/gitrepos/mixs/model/schema/mixs.yaml" \
		--meta_element enum_definition \
		--tsv_output $@


target/nmdc_types.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source "/home/mark/gitrepos/nmdc-schema/src/schema/nmdc.yaml" \
		--meta_element type_definition \
		--tsv_output $@

target/nmdc_types.yaml: target/nmdc_types.tsv
	# WARNING:root:Filling in missing prefix for: xsd => http://www.w3.org/2001/XMLSchema#
    # WARNING:root:Filling in missing prefix for: qud => http://example.org/qud/
	$(RUN) sheets2linkml \
		--output $@ $<

target/nmdc_prefixes.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source "/home/mark/gitrepos/nmdc-schema/src/schema/nmdc.yaml" \
		--meta_element prefix \
		--tsv_output $@

target/nmdc_prefixes.yaml: target/nmdc_prefixes.tsv
	$(RUN) sheets2linkml \
		--output $@ $<


target/nmdc_subsets.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source "/home/mark/gitrepos/nmdc-schema/src/schema/nmdc.yaml" \
		--meta_element subset_definition \
		--tsv_output $@

target/nmdc_subsets.yaml: target/nmdc_subsets.tsv
	$(RUN) sheets2linkml \
		--output $@ $<



target/nmdc_slots.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source "/home/mark/gitrepos/nmdc-schema/src/schema/nmdc.yaml" \
		--meta_element slot_definition \
		--tsv_output $@

target/nmdc_slots.yaml: target/nmdc_slots.tsv
	$(RUN) sheets2linkml \
		--output $@ $<


target/nmdc_schema_def.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source "/home/mark/gitrepos/nmdc-schema/src/schema/nmdc.yaml" \
		--meta_element schema_definition \
		--tsv_output $@


target/nmdc_schema_def.yaml: target/nmdc_schema_def.tsv
	$(RUN) sheets2linkml \
		--output $@ $<


# ---

roundtrip_input = "/home/mark/gitrepos/sheets_and_friends/artifacts/nmdc_dh.yaml"

target/roundtrip_annotations.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source $(roundtrip_input) \
		--meta_element annotation \
		--tsv_output $@

target/roundtrip_enums.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source $(roundtrip_input) \
		--meta_element enum_definition \
		--tsv_output $@

target/roundtrip_prefixes.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source $(roundtrip_input) \
		--meta_element prefix \
		--tsv_output $@

target/roundtrip_schema_definition.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source $(roundtrip_input) \
		--meta_element schema_definition \
		--tsv_output $@

target/roundtrip_slots.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source $(roundtrip_input) \
		--meta_element slot_definition \
		--tsv_output $@

target/roundtrip_subsets.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source $(roundtrip_input) \
		--meta_element subset_definition \
		--tsv_output $@

target/roundtrip_types.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source $(roundtrip_input) \
		--meta_element type_definition \
		--tsv_output $@

target/roundtrip_classes.tsv:
	$(RUN) python utils/l2s_supplement.py \
		--schema_source $(roundtrip_input) \
		--meta_element class_definition \
		--tsv_output $@

target/roundtrip.yaml: target/roundtrip_annotations.tsv target/roundtrip_enums.tsv target/roundtrip_prefixes.tsv \
target/roundtrip_schema_definition.tsv target/roundtrip_slots.tsv target/roundtrip_subsets.tsv \
target/roundtrip_classes.tsv target/roundtrip_types.tsv
	$(RUN) sheets2linkml \
		--output $@ $^

target/roundtrip_diff.yaml: target/roundtrip.yaml
	$(RUN) deep diff \
		--exclude-regex-paths from_schema \
		--ignore-order $(roundtrip_input) target/roundtrip.yaml > $@

