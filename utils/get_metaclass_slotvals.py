# import prefixcommons as pc
from linkml_runtime import SchemaView
import pandas as pd

import logging

import click
import click_log

# todo how to remember the yaml_dumper import
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.linkml_model import Example

logger = logging.getLogger(__name__)
click_log.basic_config(logger)

pd.set_option("display.max_columns", None)


# todo add click help and better docstrings
#  turn the requests params into click options (with defaults)
@click.command()
@click_log.simple_verbosity_option(logger)
@click.option("--selected_element", required=True)
def cli(selected_element: str):
    """
    :param selected_element:
    :return:
    """

    # todo add indicator of whether the range for each row is a class or a type

    memorable = "linkml:meta.yaml"
    # todo how to remember what case to use?
    # selected_element = "schema_definition"
    # # selected_element = "prefix"

    expanded = "https://w3id.org/linkml/meta.yaml"

    # todo or add a column with the selected_element value?
    first_col = f"{selected_element}_slot"

    meta_view = SchemaView(expanded)

    # todo: how to immediately parse the two items out (from a tuple?)
    sis_dict, sis_names = element_to_is_dict(meta_view, "slot_definition")
    eis_dict, eis_names = element_to_is_dict(meta_view, selected_element)

    lod = []
    type_dict = {}
    type_tally = {}
    for en in eis_names:
        ev = eis_dict[en]
        current_dict = {first_col: en}
        for sn in sis_names:
            if sn in ev:
                if ev[sn]:
                    if sn in type_dict:
                        type_tally[sn] = type_tally[sn] + 1
                    else:
                        type_dict[sn] = sis_dict[sn].range
                        type_tally[sn] = 1
                    final = ""
                    # todo might want special handling for examples
                    # somehow the X_definitions have their names cast to strings
                    # todo: sis_dict doesn't consider the fact
                    #  that a slot might have different usage in some meta classes?
                    if sis_dict[sn].multivalued and sis_dict[sn].range in [
                        "string",
                        "class_definition",
                        "slot_definition",
                        "subset_definition",
                        "uri",
                        "uriorcurie",
                    ]:
                        final = "|".join(ev[sn])
                    else:
                        final = ev[sn]
                    current_dict[sn] = final
                    if sn == "range":
                        current_range_name = ev[sn]
                        cr_obj = meta_view.get_element(current_range_name)
                        cr_obj_type = type(cr_obj).class_name
                        current_dict["UNOFFICIAL_range_type"] = cr_obj_type
        lod.append(current_dict)
    df = pd.DataFrame(lod)

    col_names = list(df.columns)
    col_names.remove(first_col)
    col_names.sort()
    col_names = [first_col] + col_names
    df = df[col_names]

    type_frame = pd.DataFrame(list(type_dict.items()), columns=["slot", "range"])
    tally_frame = pd.DataFrame(list(type_tally.items()), columns=["slot", "count"])

    df.to_csv(f"target/{selected_element}_slotvals.tsv", sep="\t", index=False)
    type_frame.to_csv(
        f"target/{selected_element}_slotranges.tsv", sep="\t", index=False
    )
    tally_frame.to_csv(
        f"target/{selected_element}_range_tally.tsv", sep="\t", index=False
    )

    # todo attempt to get URL for meta.yaml from "linkml:meta.yaml" alone
    # Slot: default_curi_maps
    # ordered list of prefixcommon biocontexts to be fetched to resolve id prefixes and inline prefix variables
    # meta_url = pc.expand_uri(memorable)
    # print(meta_url)

    # prefix = "linkml"
    # prefix_expansion = "https://w3id.org/linkml/"
    # w3id_expansion = "https://linkml.github.io/linkml-model/linkml/meta.yaml"

    # todo: why are some of these file NOT imported into meta.yaml?
    # https://github.com/linkml/linkml-model/tree/main/linkml_model/model/schema
    # datasets.yaml
    # meta.yaml
    # validation.yaml

    # https://linkml.github.io/linkml-model/linkml/meta.yaml
    # imports:
    #   - linkml:types
    #   - linkml:mappings
    #   - linkml:extensions
    #   - linkml:annotations

    # annotations.yaml
    # extensions.yaml
    # mappings.yaml
    # types.yaml


def element_to_is_dict(view: SchemaView, element):
    eis = view.class_induced_slots(element)
    # todo why is replacing whitespace with an underscore necessary? for broad mappings etc
    #  or use alias instead?
    eis_names = [i.name.replace(" ", "_") for i in eis]
    eis_dict = dict(zip(eis_names, eis))
    eis_names.sort()
    return eis_dict, eis_names


def flatten_some_lists(possible_list, slot_def):
    # todo add super flexible typing?
    flatten_eligible = [
        "class_definition",
        "ncname",
        "slot_definition",
        "string",
        "subset_definition",
        "uri",
        "uriorcurie",
    ]
    if slot_def.multivalued and slot_def.range in flatten_eligible:
        final = "|".join(possible_list)
    elif slot_def.multivalued and slot_def.range == "example":
        temp = []
        for i in possible_list:
            temp.append(i.value)
        final = "|".join(temp)
    else:
        final = possible_list
    return final


if __name__ == "__main__":
    cli()

# x = Example()
# x.