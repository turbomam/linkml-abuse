import pprint

from linkml_runtime import SchemaView
import pandas as pd

import logging

import click
import click_log
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.linkml_model import TypeDefinition

import get_metaclass_slotvals as gms

logger = logging.getLogger(__name__)
click_log.basic_config(logger)

pd.set_option("display.max_columns", None)

cowardly_skip = [
    "all_of",
    "alt_descriptions",
    "annotations",
    "any_of",
    "classes",
    "default_curi_maps",
    "enum_range",
    "enums",
    "exactly_one_of",
    "extensions",
    "from_schema",
    "implicit_prefix",
    "imports",
    "local_names",
    "name",
    "none_of",
    "prefixes",
    "slot_definitions",
    "structured_aliases",
    "subsets",
    "type_uri",
]


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
    elif meta_element == "enum_definition":
        get_enums(schema_view, meta_view, tsv_output)
    elif meta_element == "prefix":
        get_prefixes(schema_view, meta_view, tsv_output)
    elif meta_element == "schema_definition":
        get_schema(schema_view, meta_view, tsv_output)
    elif meta_element == "slot_definition":
        get_slots(schema_view, meta_view, tsv_output)
    elif meta_element == "subset_definition":
        get_subsets(schema_view, meta_view, tsv_output)
    elif meta_element == "type_definition":
        get_types(schema_view, meta_view, tsv_output)


def get_schema(schema_view: SchemaView, meta_view: SchemaView, tsv_output: str):
    # must omit:
    # "default_curi_maps" (0..* String)
    #   ERROR:root:Cannot fetch: https://raw.githubusercontent.com/prefixcommons/biocontext/master/registry/obo_context|idot_context.jsonld
    # "imports" (SchemaDefinition → 0..* Uriorcurie)
    #   WARNING:rdflib.term:https://w3id.org/linkml/types|mixs|core|prov|workflow_execution_activity|annotation|external_identifiers does not look like a valid URI, trying to serialize this will break.
    # "subsets" (SchemaDefinition → 0..* SubsetDefinition)
    #   TypeError: unsupported operand type(s) for +: 'dict' and 'list'
    schema_schema = schema_view.schema
    sis_dict, sis_names = gms.element_to_is_dict(meta_view, "schema_definition")
    cowardly_names = [i for i in sis_dict if i not in cowardly_skip]
    current_dict = {"schema": schema_schema.name}
    for i in cowardly_names:
        # print(f"{sis_dict[i].multivalued} {sis_dict[i].range} {i}")
        current_dict[i] = gms.flatten_some_lists(
            possible_list=schema_schema[i], slot_def=sis_dict[i]
        )
    df = pd.DataFrame(current_dict, index=[0])
    df = prioritize_columns(df, ["schema"])
    df = add_gt_row(df)
    df.to_csv(tsv_output, sep="\t", index=False)


def get_subsets(schema_view: SchemaView, meta_view: SchemaView, tsv_output: str):
    # todo subsets aren't getting merged
    #   other files with subsets:
    #   core.yaml: subsets:
    #   nmdc.yaml: subsets:
    #   workflow_execution_activity.yaml: subsets:

    schema_view.merge_imports()
    schema_subsets = schema_view.all_subsets(imports=True)
    sis_dict, sis_names = gms.element_to_is_dict(meta_view, "subset_definition")
    cowardly_names = [i for i in sis_dict if i not in cowardly_skip]
    lod = []
    for k, v in schema_subsets.items():
        current_dict = {"subset": k}
        for i in cowardly_names:
            current_dict[i] = gms.flatten_some_lists(
                possible_list=v[i], slot_def=sis_dict[i]
            )
        lod.append(current_dict)
    df = pd.DataFrame(lod)
    df = add_gt_row(df)
    df = prioritize_columns(df, ["subset"])
    df.to_csv(tsv_output, sep="\t", index=False)


def get_prefixes(schema_view: SchemaView, meta_view: SchemaView, tsv_output: str):
    # todo are prefixes getting merged from imports?
    schema_view.merge_imports()
    schema_prefixes = schema_view.schema.prefixes
    lod = []
    for k, v in schema_prefixes.items():
        lod.append({"prefix": v.prefix_prefix, "prefix_reference": v.prefix_reference})
    df = pd.DataFrame(lod)
    df = add_gt_row(df)
    df = prioritize_columns(df, ["prefix"])
    df.to_csv(tsv_output, sep="\t", index=False)


def get_slots(schema_view: SchemaView, meta_view: SchemaView, tsv_output: str):
    sis_dict, sis_names = gms.element_to_is_dict(meta_view, "slot_definition")
    cowardly_names = [i for i in sis_names if i not in cowardly_skip]
    schema_slots = schema_view.all_slots()
    schema_slot_dicts = []
    for k, v in schema_slots.items():
        current_dict = {"slot": k}
        for i in cowardly_names:
            current_dict[i] = gms.flatten_some_lists(
                possible_list=v[i], slot_def=sis_dict[i]
            )
        # # why not type_uri?
        # current_dict["uri"] = v.uri
        schema_slot_dicts.append(current_dict)
    df = pd.DataFrame(schema_slot_dicts)
    # final_frame = prioritize_columns(df, ["type", "uri"])
    final_frame = add_gt_row(df)
    final_frame.to_csv(tsv_output, sep="\t", index=False)


def get_types(schema_view: SchemaView, meta_view: SchemaView, tsv_output: str):
    tis_dict, tis_names = gms.element_to_is_dict(meta_view, "type_definition")
    cowardly_names = [i for i in tis_names if i not in cowardly_skip]
    schema_types = schema_view.all_types(imports=True)
    schema_type_dicts = []
    for k, v in schema_types.items():
        # try this!
        # for i in v.__iter__():
        #     print(i)
        if str(v.from_schema) != "https://w3id.org/linkml/types":
            current_dict = {"type": k}
            for i in cowardly_names:
                current_dict[i] = gms.flatten_some_lists(
                    possible_list=v[i], slot_def=tis_dict[i]
                )
            # todo why not type_uri?
            current_dict["uri"] = v.uri
            schema_type_dicts.append(current_dict)
    df = pd.DataFrame(schema_type_dicts)
    if len(df.columns) > 0:
        final_frame = prioritize_columns(df, ["type", "uri"])
        final_frame = add_gt_row(final_frame)
        # final_frame = final_frame.replace(dict(), None, regex=False)
    else:
        final_frame = pd.DataFrame([{"type": "> type"}])
    final_frame.to_csv(tsv_output, sep="\t", index=False)


def add_gt_row(df: pd.DataFrame) -> pd.DataFrame:
    r1 = list(df.columns)
    r1[0] = f"> {r1[0]}"
    extra_row_dict = dict(zip(df.columns, r1))
    extra_row = pd.DataFrame(extra_row_dict, index=[0])
    final_frame = pd.concat([extra_row, df]).reset_index(drop=True)
    return final_frame


def get_enums(schema_view: SchemaView, meta_view: SchemaView, tsv_output: str):
    initial_columns = ["enum", "permissible_value"]
    sis_dict, sis_names = gms.element_to_is_dict(meta_view, "enum_definition")
    pv_is_dict, pv_is_names = gms.element_to_is_dict(meta_view, "permissible_value")
    # todo could a PV's usage of a slot
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
                            and current_pv_slot_name not in cowardly_skip
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
                if j not in cowardly_skip:
                    final = gms.flatten_some_lists(
                        possible_list=schema_enum_dict[i][j],
                        slot_def=sis_dict[j],
                    )
                    current_row[j] = final
        lod.append(current_row)
    df = pd.DataFrame(lod)
    pv_df = pd.DataFrame(pv_lod)
    final_frame = pd.concat([df, pv_df])

    final_frame = prioritize_columns(final_frame, initial_columns)

    # # this doesn't work for removing empty dict serializations
    # temp = final_frame.replace("{}", "", regex=False)
    # print(temp)

    final_frame = add_gt_row(final_frame)

    final_frame.to_csv(tsv_output, sep="\t", index=False)


def prioritize_columns(df: pd.DataFrame, initial_columns) -> pd.DataFrame:
    all_columns = list(df.columns)
    for i in initial_columns:
        all_columns.remove(i)
    all_columns.sort()
    final_columns = initial_columns + all_columns
    df = df[final_columns]
    df.sort_values(by=initial_columns, inplace=True)
    return df


def get_annotations(schema_view: SchemaView, meta_view: SchemaView, tsv_output: str):
    # todo this creates a standalone table.
    #  Will schemasheets honor it in combination with other sheets that specify the same terms?
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
