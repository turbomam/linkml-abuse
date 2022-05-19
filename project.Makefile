## Add your own custom Makefile targets here

## some of this might be redundant with the ./Makefile

.PHONY: phoniest
phoniest:
	$(RUN) gen-yaml src/linkml/linkml_abuse.yaml
