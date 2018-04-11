from elasticsearch import Elasticsearch
from pymongo import MongoClient

MONGO_PORT = 27019
ES_PORT = 9400


def create_index(db_name, db_collection, index, id_field='mongo_id'):
    db_cli = MongoClient(port=MONGO_PORT)
    es_cli = Elasticsearch(port=ES_PORT)
    collection = db_cli[db_name][db_collection]

    # also look if it's possible to bulk-index the whole collection
    i = 0
    for document in collection.find({}):
        document[id_field] = str(document['_id'])
        del document['_id']
    indexed_fields = ['first_name', 'last_name', 'email', id_field]
    bod = {x: document[x] for x in indexed_fields}
    es_cli.index(index=index, doc_type=db_collection, id=i, body=document)
    i += 1
