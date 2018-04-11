import os

from elasticsearch import Elasticsearch
from flask_restful import Resource, abort, reqparse

ES_PORT = os.environ.get('ES_PORT')
ES_HOST = os.environ.get('ES_HOST')


class Search(Resource):
    def __init__(self):
        super().__init__()

        self._parser = reqparse.RequestParser()
        self._parser.add_argument('query', required='True')

        self._indices = {
            'clients': {
                'index': 'clients',
                'fields': ['first_name', 'last_name']
            },
            'products': {
                'index': 'products',
                'fields': ['name']
            }
        }

    def get(self, resource):
        args = self._parser.parse_args()
        query = args['query']

        es_cli = Elasticsearch(port=ES_PORT, host=ES_HOST)
        index = self._route_resource(resource)

        es_query = {
            'query': {
                'match_phrase_prefix': {'_all': query}
            }
        }
        resp = es_cli.search(index=index, body=es_query,
                             filter_path=self._get_fields_filter(resource))

        if resp['hits']['total'] > 0:
            return resp['hits']['hits'], 200
        else:
            return {}, 200

    def _route_resource(self, resource):
        try:
            return self._indices[resource]['index']
        except KeyError:
            abort(400, message='Unknown resource')

    def _get_fields_filter(self, resource):
        try:
            base_path = 'hits.hits._source'
            base_fields = ['hits.total', '{}.mongo_client_id'.format(base_path)]
            index_fields = ['{}.{}'.format(base_path, field)
                            for field in self._indices[resource]['fields']]
            return base_fields + index_fields
        except KeyError:
            abort(400, message='Unknown resource')
