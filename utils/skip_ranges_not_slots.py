# import os
import pprint

import yaml
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper

# import pandas as pd

# todo apply to arbitrary meta elements

# todo document lost information, like example descriptions

# todo break unimplementeds out by meta element

schema_source = "https://raw.githubusercontent.com/microbiomedata/nmdc-schema/main/src/schema/nmdc.yaml"
# schema_source = "https://w3id.org/linkml/meta.yaml"

# are there any authorities on what slots exist other than this YAML file? What about some python data classes?
meta_source = "https://w3id.org/linkml/meta.yaml"


# what are the imports?
# what actually gets imported?

# # imports:
# #   - linkml:types
# #   - linkml:mappings
# #   - linkml:extensions
# #   - linkml:annotations
# #   - linkml:validation
# #   - units


class Sheet:
    def __init__(self):
        self.unimplementeds = set()
        self.results_dict = {}
        self.arb_yamls = set()
        self.meta_view: SchemaView = None
        self.schema_view: SchemaView = None

    def set_meta(self, meta_path):
        print(f"loading meta schema from {meta_path}")
        self.meta_view = SchemaView(meta_path)

    def set_schema(self, schema_path):
        print(f"loading schema from {schema_path}")
        self.schema_view = SchemaView(schema_path)

    def one_insertion(
            self, current_meta_term, current_schema_term, current_attribute, current_value
    ):
        # print(f"starting an insertion {current_meta_term} {current_schema_term} {current_attribute} {current_value}")
        if current_meta_term not in self.results_dict:
            self.results_dict[current_meta_term] = {}
        if current_schema_term not in self.results_dict[current_meta_term]:
            self.results_dict[current_meta_term][current_schema_term] = {}
        if (
                current_attribute
                not in self.results_dict[current_meta_term][current_schema_term]
        ):
            self.results_dict[current_meta_term][current_schema_term][
                current_attribute
            ] = {}
        self.results_dict[current_meta_term][current_schema_term][
            current_attribute
        ] = current_value

    def process_classes(self):
        current_meta_term = "class_definition"
        schema_classes = self.schema_view.all_classes()
        meta_slots = self.meta_view.class_induced_slots("class_definition")
        ms_names = [str(ms.name) for ms in meta_slots]
        ms_names.sort()

        sc_names = [str(v.name) for k, v in schema_classes.items()]
        sc_names.sort()
        for current_schema_term in sc_names:
            for current_attribute in ms_names:
                try:
                    i_s = self.meta_view.induced_slot(current_attribute)
                    ia = i_s.alias
                    if ia != current_attribute:
                        current_value = self.schema_view.induced_class(
                            current_schema_term
                        )[ia]
                    else:
                        current_value = self.schema_view.induced_class(
                            current_schema_term
                        )[current_attribute]
                    # print(f"{current_meta_term} {current_schema_term} {current_attribute} {current_value}")
                    current_range = i_s.range
                    current_multi = i_s.multivalued
                    self.one_serialization(
                        current_schema_term,
                        current_meta_term,
                        current_attribute,
                        current_range,
                        current_multi,
                        current_value,
                    )
                except KeyError:
                    self.unimplementeds.add(current_attribute)

    def process_enums(self):
        current_meta_term = "enum_definition"
        schema_enums = self.schema_view.all_enums()
        meta_slots = self.meta_view.class_induced_slots("enum_definition")
        ms_names = [str(ms.name) for ms in meta_slots]
        ms_names.sort()

        se_names = [str(v.name) for k, v in schema_enums.items()]
        se_names.sort()
        for current_schema_term in se_names:
            for current_attribute in ms_names:
                try:
                    i_s = self.meta_view.induced_slot(current_attribute)
                    ia = i_s.alias
                    if ia != current_attribute:
                        current_value = self.schema_view.induced_enum(
                            current_schema_term
                        )[ia]
                    else:
                        current_value = self.schema_view.induced_enum(
                            current_schema_term
                        )[current_attribute]

                    current_range = i_s.range
                    current_multi = i_s.multivalued
                    self.one_serialization(
                        current_schema_term,
                        current_meta_term,
                        current_attribute,
                        current_range,
                        current_multi,
                        current_value,
                    )
                    if current_attribute == "permissible_values":
                        self.process_pvs(
                            schema_term=current_schema_term, pv_obj=current_value
                        )
                except KeyError:
                    self.unimplementeds.add(current_attribute)

    def process_pvs(self, schema_term, pv_obj):
        current_meta_term = "permissible_value"
        pv_slots = self.meta_view.class_induced_slots("permissible_value")
        pv_slot_names = [
            str(current_pv_slot_name.name) for current_pv_slot_name in pv_slots
        ]
        for k, v in pv_obj.items():
            for current_pv_slot_name in pv_slot_names:
                current_range = self.meta_view.induced_slot(current_pv_slot_name).range
                current_multi = self.meta_view.induced_slot(
                    current_pv_slot_name
                ).multivalued
                self.one_serialization(
                    current_schema_term=str(v.text),
                    current_meta_term=current_meta_term,
                    current_attribute=str(current_pv_slot_name),
                    current_range=str(current_range),
                    current_multi=current_multi,
                    current_value=v[current_pv_slot_name],
                    enum_name=schema_term,
                )

    def process_slots(self):
        current_meta_term = "slot_definition"
        schema_slots = self.schema_view.all_slots()
        meta_slots = self.meta_view.class_induced_slots("slot_definition")
        ms_names = [str(ms.name) for ms in meta_slots]
        ms_names.sort()
        ss_names = [str(v.name) for k, v in schema_slots.items()]
        ss_names.sort()
        for current_schema_term in ss_names:
            for current_attribute in ms_names:
                try:
                    i_s = self.meta_view.induced_slot(current_attribute)
                    ia = i_s.alias
                    if ia != current_attribute:
                        current_value = self.schema_view.induced_slot(
                            current_schema_term
                        )[ia]
                    else:
                        current_value = self.schema_view.induced_slot(
                            current_schema_term
                        )[current_attribute]

                    current_range = i_s.range
                    current_multi = i_s.multivalued
                    self.one_serialization(
                        current_schema_term,
                        current_meta_term,
                        current_attribute,
                        current_range,
                        current_multi,
                        current_value,
                    )
                except KeyError:
                    self.unimplementeds.add(current_attribute)

    def one_serialization(
            self,
            current_schema_term,
            current_meta_term,
            current_attribute,
            current_range,
            current_multi,
            current_value,
            enum_name=None,
    ):
        simplified = ""
        if current_range in [
            "alt_description",
            "annotation",
            "anonymous_class_expression",
            "anonymous_slot_expression",
            "class_rule",
            "expression",
            "extension",
            "local_name",
            "path_expression",
            "pattern_expression",
            "pv_formula_options",
            "range_expression",
            "relational_role_enum",
            "structured_alias",
            "type_definition",
            "unique_key",
        ]:
            if current_value:
                simplified = yaml_dumper.dumps(current_value)
                self.arb_yamls.add(current_attribute)
            else:
                simplified = ""

        elif current_range in ["boolean", "datetime"]:
            # todo could there ever be a multivalued boolean?
            simplified = current_value

        elif current_range in [
            "class_definition",
            "slot_definition",
            "subset_definition",
        ]:
            if current_multi and current_value:
                temp = []
                for current_single in current_value:
                    temp.append(str(current_single))
                cd_name_paste = "|".join(temp)
                simplified = cd_name_paste
            elif current_value:
                simplified = str(current_value)
            else:
                simplified = ""

        elif current_range == "definition" and current_attribute == "owner":
            # todo coerce to string?
            simplified = str(current_value)
        elif current_range == "definition" and current_attribute != "owner":
            # todo some definitions don't have names, like enum_definitions?
            #  Subclasses of Definition: ClassDefinition, SlotDefinition, EnumDefinition, SubsetDefinition, TypeDefinition
            pass
            # print(f"skipping non-owner definition {current_attribute}.")

        elif current_range == "element" and current_attribute == "range":
            # todo coerce to string?
            #  .name and .alias don't work
            simplified = str(current_value)
        elif current_range == "element" and current_attribute != "range":
            pass
            # print(f"skipping non-range element {current_attribute}.")

        elif current_range == "example":
            ex_vals = [ex["value"] for ex in current_value]
            ex_vals = "|".join(ex_vals)
            simplified = ex_vals

        elif current_range == "integer":
            # todo are there ever any multivalued integers?
            try:
                simplified = int(current_value)
            except TypeError:
                pass
                # print(f"bad integer type for {current_attribute}")

        elif current_range in ["uri", "uriorcurie", "ncname", "string"]:
            if current_value and current_multi:
                temp = []
                for current_single in current_value:
                    temp.append(str(current_single))
                simplified = "|".join(temp)
            elif current_value:
                simplified = str(current_value)
            else:
                simplified = ""

        elif current_range == "permissible_value":
            if current_value and current_multi:
                simplified = "|".join([v.text for k, v in current_value.items()])
            # todo elses?

        elif not current_range:
            print(
                f"skipping {current_attribute} with no range and value {current_value}."
            )

        else:
            print(f"punting on {current_range} {current_attribute}")

        if enum_name:
            pass
        else:
            self.one_insertion(current_meta_term, current_schema_term, current_attribute, simplified)

        # print(
        #     f"{current_meta_term} {current_schema_term}'s {current_attribute}: range={current_range} multi={current_multi} simplified_value:{simplified}"
        # )

        #         current_value,
        #         enum_name=None,


current_sheet = Sheet()
current_sheet.set_meta(meta_path=meta_source)
current_sheet.set_schema(schema_path=schema_source)

# current_sheet.one_serialization(
#     current_meta_term="slot_definition",
#     current_schema_term="pH",
#     current_attribute="description",
#     current_range="string",
#     current_multi=False,
#     current_value="words words words",
# )
#
# pprint.pprint(current_sheet.results_dict)

print("processing classes")
current_sheet.process_classes()

print("processing enums")
current_sheet.process_enums()

print("processing slots")
current_sheet.process_slots()

# pprint.pprint(current_sheet.results_dict)

print("writing flattened values as YAML")
with open("../target/flattened.yaml", "w") as outfile:
    yaml.dump(current_sheet.results_dict, outfile, default_flow_style=False)

pprint.pprint(f"current_sheet.unimplementeds: {current_sheet.unimplementeds}")

pprint.pprint(f"current_sheet.arb_yamls: {current_sheet.arb_yamls}")
