from __future__ import unicode_literals

import inspect
from collections import OrderedDict

import mongoengine
from graphene import Node
from graphene.utils.trim_docstring import trim_docstring
from graphql.utils.ast_to_dict import ast_to_dict


def get_model_fields(model, excluding=None):
    excluding = excluding or []
    attributes = dict()
    for attr_name, attr in model._fields.items():
        if attr_name in excluding:
            continue
        attributes[attr_name] = attr
    return OrderedDict(sorted(attributes.items()))


def get_model_reference_fields(model, excluding=None):
    excluding = excluding or []
    attributes = dict()
    for attr_name, attr in model._fields.items():
        if attr_name in excluding or not isinstance(
                attr,
                (mongoengine.fields.ReferenceField, mongoengine.fields.LazyReferenceField),
        ):
            continue
        attributes[attr_name] = attr
    return attributes


def is_valid_mongoengine_model(model):
    return inspect.isclass(model) and (
            issubclass(model, mongoengine.Document)
            or issubclass(model, mongoengine.EmbeddedDocument)
    )


def import_single_dispatch():
    try:
        from functools import singledispatch
    except ImportError:
        singledispatch = None

    if not singledispatch:
        try:
            from singledispatch import singledispatch
        except ImportError:
            pass

    if not singledispatch:
        raise Exception(
            "It seems your python version does not include "
            "functools.singledispatch. Please install the 'singledispatch' "
            "package. More information here: "
            "https://pypi.python.org/pypi/singledispatch"
        )

    return singledispatch


# noqa
def get_type_for_document(schema, document):
    types = schema.types.values()
    for _type in types:
        type_document = hasattr(_type, "_meta") and getattr(
            _type._meta, "document", None
        )
        if document == type_document:
            return _type


def get_field_description(field, registry=None):
    """
    Common metadata includes verbose_name and help_text.

    http://docs.mongoengine.org/apireference.html#fields
    """
    parts = []
    if hasattr(field, "document_type"):
        doc = trim_docstring(field.document_type.__doc__)
        if doc:
            parts.append(doc)
    if hasattr(field, "verbose_name"):
        parts.append(field.verbose_name.title())
    if hasattr(field, "help_text"):
        parts.append(field.help_text)
    if field.db_field != field.name:
        name_format = "(%s)" if parts else "%s"
        parts.append(name_format % field.db_field)

    return "\n".join(parts)


def get_node_from_global_id(node, info, global_id):
    try:
        for interface in node._meta.interfaces:
            if issubclass(interface, Node):
                return interface.get_node_from_global_id(info, global_id)
    except AttributeError:
        return Node.get_node_from_global_id(info, global_id)


def collect_query_fields(node, fragments):
    """Recursively collects fields from the AST

    Args:
        node (dict): A node in the AST
        fragments (dict): Fragment definitions

    Returns:
        A dict mapping each field found, along with their sub fields.

        {'name': {},
         'image': {'id': {},
                                   'name': {},
                                   'description': {}},
         'slug': {}}
    """

    field = {}

    if node.get('selection_set'):
        for leaf in node['selection_set']['selections']:
            if leaf['kind'] == 'Field':
                field.update({
                    leaf['name']['value']: collect_query_fields(leaf, fragments)
                })
            elif leaf['kind'] == 'FragmentSpread':
                field.update(collect_query_fields(fragments[leaf['name']['value']],
                                                  fragments))

    return field


def get_query_fields(info):
    """A convenience function to call collect_query_fields with info

    Args:
        info (ResolveInfo)

    Returns:
        dict: Returned from collect_query_fields
    """

    fragments = {}
    node = ast_to_dict(info.field_asts[0])

    for name, value in info.fragments.items():
        fragments[name] = ast_to_dict(value)

    query = collect_query_fields(node, fragments)
    if "edges" in query:
        return query["edges"]["node"].keys()
    return query


def camel_to_snake(field):
    return ''.join(['_' + c.lower() if c.isupper() else c for c in field]).lstrip('_')
