from linkml_runtime import SchemaView
import pandas as pd

import logging

import click
import click_log
from linkml_runtime.dumpers import yaml_dumper

import get_metaclass_slotvals as gms

logger = logging.getLogger(__name__)
click_log.basic_config(logger)

pd.set_option("display.max_columns", None)


# todo
#  enums/pvs:
#  alt_descriptions, extensions, local_names, and structured_aliases are dicts
#  examples	is a list of Examples
#  see otherwise_handled list below


# todo add click help and better docstrings
#  turn the requests params into click options (with defaults)
@click.command()
@click_log.simple_verbosity_option(logger)
@click.option("--schema_source", required=True)
@click.option("--meta_element", required=True)
@click.option("--tsv_output", required=True)
def cli(schema_source: str, meta_element: str, tsv_output: str):
    """
    :param schema_source:
    :param meta_element:
    :param tsv_output:
    :return:
    """

    meta_source = "https://w3id.org/linkml/meta.yaml"

    meta_view = SchemaView(meta_source)

    schema_view = SchemaView(schema_source)

    if meta_element == "annotation":
        get_annotations(schema_view, meta_view, tsv_output)

    if meta_element == "enum_definition":
        get_enums(schema_view, meta_view, tsv_output)


def get_enums(schema_view: SchemaView, meta_view: SchemaView, tsv_output: str):
    # see https://github.com/linkml/schemasheets/blob/main/examples/input/enums.tsv
    # > enum	permissible_value
    otherwise_handled = ["name", "annotations"]
    cowardly_skip = [
        "alt_descriptions",
        "examples",
        "extensions",
        "local_names",
        "structured_aliases",
    ]
    #  alt_descriptions, extensions, local_names, and structured_aliases are dicts
    #  examples	is a list of Examples
    #  id_prefixes list of ncnmaes?
    otherwise_handled = otherwise_handled + cowardly_skip
    initial_columns = ["enum", "permissible_value"]
    # todo parameterize otherwise_handled etc
    sis_dict, sis_names = gms.element_to_is_dict(meta_view, "enum_definition")
    pv_is_dict, pv_is_names = gms.element_to_is_dict(meta_view, "permissible_value")
    # todo combine?
    #  could a PV's usage of a slot
    #   be different from an enum's?
    sis_dict.update(pv_is_dict)
    schema_enum_dict = schema_view.all_enums()
    schema_enum_names = list(schema_enum_dict)
    schema_enum_names.sort()
    enum_slots = meta_view.class_induced_slots("enum_definition")
    enum_slot_names = [i.alias for i in enum_slots]
    enum_slot_names.sort()
    pv_slots = meta_view.class_induced_slots("permissible_value")
    pv_slot_names = [i.alias for i in pv_slots]
    pv_slot_names.sort()
    lod = []
    pv_lod = []
    for i in schema_enum_names:
        current_row = {"enum": i}
        for j in enum_slot_names:
            if j == "permissible_values":
                all_pvs = schema_enum_dict[i][j]
                pv_names = list(all_pvs.keys())
                pv_names.sort()
                for current_pv_name in pv_names:
                    current_pv_row = {"enum": i, "permissible_value": current_pv_name}
                    for current_pv_slot_name in pv_slot_names:
                        if (
                                current_pv_slot_name in all_pvs[current_pv_name]
                                and current_pv_slot_name not in otherwise_handled
                        ):
                            # todo add handling for dicts and lists of objs
                            current_value = all_pvs[current_pv_name][
                                current_pv_slot_name
                            ]
                            final = gms.flatten_some_lists(
                                possible_list=current_value,
                                slot_def=sis_dict[current_pv_slot_name],
                            )
                            current_pv_row[current_pv_slot_name] = final
                    pv_lod.append(current_pv_row)
            else:
                if j not in otherwise_handled:
                    final = gms.flatten_some_lists(
                        possible_list=schema_enum_dict[i][j],
                        slot_def=sis_dict[j],
                    )
                    current_row[j] = final
        lod.append(current_row)
    df = pd.DataFrame(lod)
    pv_df = pd.DataFrame(pv_lod)
    final_frame = pd.concat([df, pv_df])
    all_columns = list(final_frame.columns)
    for i in initial_columns:
        all_columns.remove(i)
    final_columns = initial_columns + all_columns
    final_frame = final_frame[final_columns]
    final_frame.sort_values(by=initial_columns, inplace=True)
    # # this doesn't work for removing empty dict serializations
    # temp = final_frame.replace("{}", "", regex=False)
    # print(temp)
    r1 = list(final_frame.columns)
    r1[0] = f"> {r1[0]}"
    extra_row_dict = dict(zip(final_frame.columns, r1))
    extra_row = pd.DataFrame(extra_row_dict, index=[0])
    final_frame = pd.concat([extra_row, final_frame]).reset_index(drop=True)
    final_frame.to_csv(tsv_output, sep="\t", index=False)


def get_annotations(schema_view: SchemaView, meta_view: SchemaView, tsv_output: str):
    type_to_col = {"class_definition": "class", "slot_definition": "slot"}
    lod = []
    tag_set = set()
    all_type_list = []
    annotated_type_list = []
    schema_elements = schema_view.all_elements()
    annotation_slots = meta_view.class_induced_slots("annotation")
    annotation_slot_names = [i.alias for i in annotation_slots]
    annotation_slot_names.sort()
    element_names = list(schema_elements.keys())
    element_names.sort()
    for i in element_names:
        current_element = schema_elements[i]
        element_type = type(current_element).class_name
        all_type_list.append(element_type)
        if "annotations" in current_element:
            if current_element.annotations:
                annotated_type_list.append(element_type)
                for k, v in current_element.annotations.items():
                    current_dict = {
                        "schema": schema_view.schema.name,
                        "element": i,
                        "element_type": element_type,
                    }
                    for j in annotation_slot_names:
                        current_dict[j] = v[j]
                        if j == "tag":
                            tag_set.add(v[j])
                    lod.append(current_dict)

    # df = pd.DataFrame(lod)
    # # todo reshape to match schemasheets' input expectations
    # # logger.info(pd.Series(all_type_list).value_counts())
    # # logger.info(pd.Series(annotated_type_list).value_counts())
    # # logger.info(f"annotation tags {tag_set}")
    # # logger.info(df)
    #
    # # todo need initial > and additional header rows
    # #   f"inner_key: {i['tag']}"

    schema_sheets_lod = []
    for i in lod:
        raw_type = i["element_type"]
        col_name = type_to_col[raw_type]
        current_row = {col_name: i["element"], i["tag"]: i["value"]}
        schema_sheets_lod.append(current_row)
    schema_sheets_df = pd.DataFrame(schema_sheets_lod)

    initial_cols = set(schema_sheets_df.columns)
    element_cols = set(type_to_col.values())
    used_element_cols = list(element_cols.intersection(initial_cols))
    used_element_cols.sort()
    tag_cols = list(tag_set)
    tag_cols.sort()
    r1 = used_element_cols + tag_cols
    schema_sheets_df = schema_sheets_df[r1]
    annotations_placeholder = ["annotations"] * len(tag_cols)
    r2 = used_element_cols + annotations_placeholder
    r2[0] = f"> {r2[0]}"
    r3_rhs = [f"inner_key: {i}" for i in tag_cols]
    r3 = ([""] * len(used_element_cols)) + r3_rhs
    r3[0] = ">"
    headers_frame = pd.DataFrame([r2, r3], columns=schema_sheets_df.columns)
    final_frame = pd.concat([headers_frame, schema_sheets_df])

    final_frame.to_csv(tsv_output, sep="\t", index=False)


if __name__ == "__main__":
    cli()
