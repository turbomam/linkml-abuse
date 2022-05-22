## Add your own custom Makefile targets here

## don't add anything to the Makefile, because that could be overwritten by the template

## unfortunately, the default? Makefile plugin for PyCharm
##   can't seem to launch *.makefile (non-Makefile) rules from the GUI

.PHONY: clean_targ all_sqlite l2s

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

get_metaclass_slotvals:
	$(RUN) python utils/get_metaclass_slotvals.py --selected_element schema_definition
