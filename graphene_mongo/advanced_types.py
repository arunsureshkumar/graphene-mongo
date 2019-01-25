import graphene

from mongoengine import Document
from mongoengine.fields import (
    IntField,
    StringField,
)

from .types import MongoengineObjectType

__all__ = [
    'PointFieldType',
    'MultiPolygonFieldType'
]


def _resolve_type_coordinates(self, info):
    return self['coordinates']

class FsFile(Document):

    meta = {'collection': 'fs.files'}
    content_type = StringField(name='contentType')
    chunk_size = IntField(name='chunkSize')
    length = IntField()
    md5 = StringField()


class FsFileType(MongoengineObjectType):

    class Meta:
        model = FsFile


class PointFieldType(graphene.ObjectType):

    type = graphene.String()
    coordinates = graphene.List(
        graphene.Float, resolver=_resolve_type_coordinates)

    def resolve_type(self, info):
        return self['type']


class MultiPolygonFieldType(graphene.ObjectType):

    type = graphene.String()
    coordinates = graphene.List(
                    graphene.List(
                        graphene.List(
                            graphene.List(graphene.Float))),
                    resolver=_resolve_type_coordinates)

    def resolve_type(self, info):
        return self['type']
