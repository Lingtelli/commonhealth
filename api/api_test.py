# -*- coding: utf-8 -*-
import json
import sys, os, inspect
from cluster_functions import *
from api_functions import * 
from flask import Flask, request, send_from_directory, g
from flask_restful import Resource, Api
from flask_cors import CORS, cross_origin

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

app = Flask(__name__, static_folder='/home/jlsche/Lingtelli/commonhealth/api/')
api = Api(app)
CORS(app)

VALID_PARAMS = ['query', 'clusterid', 'center', 'author', 'date_start', 'date_end', 'categories', 'groups', 'page_start']
VALID_PARAMS_NEW = ['query', 'keywords', 'author', 'publish_date', 'categories', 'batch_size', 'cluster_idx', 'most_common_size']


output_filename = './cluster_result0.json'
@app.route('/commonhealth_api/', methods=['POST', 'GET'])
def commonhealth_api():
    if request.json:                        # request from website
        print('\nGOT REQUEST FROM CURL')
        query_dict = request.json
        query_keys = query_dict.keys()
        query_words = query_dict['query']

    else:                                   # request from curl
        print('\nGOT REQUEST FROM WEBSITE')
        query_dict = request.args.to_dict()
        query_keys = query_dict.keys()
        query_words = request.args.getlist('query')
        query_dict['groups'] = request.args.getlist('groups')
        query_dict['categories'] = request.args.getlist('categories')

    for key in query_keys:
        if key not in VALID_PARAMS:
            return str(key + ' is not a valid parameter.\n')

    for key in VALID_PARAMS:
        if key not in query_keys:
            query_dict[key] = None

    print('QUERY DICT:', query_dict)
    print(query_words)
    data = open('test_big.json', encoding='utf-8')
    #data = open('cluster_result0.json', encoding='utf-8') 
    cluster_list = json.load(data)

    '''
    matched_clusters = searchQualified(cluster_list, query_dict['center'], query_dict['author'], query_dict['date_start'], query_dict['date_end'], query_dict['source'])
    print('after searchQualified, # of candidate cluster:', len(matched_clusters))
    matched_clusters = filterClusters(matched_clusters, query_words)
    print('after filterClusters, # of candidate cluster:', len(matched_clusters))
    matched_clusters = searchQualified(matched_clusters, query_dict['center'], query_dict['author'], query_dict['date_start'], query_dict['date_end'], query_dict['source'])
    print('after searchClusters, # of candidate cluster:', len(matched_clusters))
    '''
    
    matched_clusters = filterClusters(cluster_list, query_words)
    print('after filterClusters, # of candidate cluster:', len(matched_clusters))
    
    matched_clusters = searchClusters(matched_clusters, query_dict['groups'])
    print('after searchClusters, # of candidate cluster:', len(matched_clusters))

    matched_clusters = searchQualified(matched_clusters, query_dict['center'], query_dict['author'], query_dict['date_start'], query_dict['date_end'], query_dict['categories'])
    print('after searchQualified, # of candidate cluster:', len(matched_clusters))
    

    matched_clusters = getExtraInfo(matched_clusters)

    if query_dict['page_start'] != None:
        matched_clusters = trimClusters(matched_clusters, query_dict['page_start'])
    
    print('Done.')

    return json.dumps(matched_clusters, ensure_ascii=False)


@app.route('/getDetail/', methods=['POST'])
def getDetail():
    query_dict = request.args.to_dict()
    _id = query_dict['clusterid']
    data = open('test_big.json', encoding='utf-8')
    cluster_list = json.load(data)
    matched_cluster = lookupByClusterid(cluster_list, _id)
    resp = list()
    for member in matched_cluster['member']:
        resp_dict = dict()
        resp_dict['author'] = member['author']
        resp_dict['_centers'] = member['_centers']
        resp_dict['source'] = member['source']
        resp_dict['content'] = member['content']
        resp.append(resp_dict)
        
    return json.dumps(resp, ensure_ascii=False)


@app.route('/query/', methods=['POST','GET'])
def query():
    if request.json:                        # request from website
        print('\nGOT REQUEST FROM CURL')
        query_dict = request.json
        query_keys = query_dict.keys()
        query_words = query_dict['query']

    else:                                   # request from curl
        print('\nGOT REQUEST FROM WEBSITE')
        query_dict = request.args.to_dict()
        query_keys = query_dict.keys()
        if 'query' in request.args:
            query_dict['query'] = request.args.getlist('query')
        if 'keywords' in request.args:
            query_dict['keywords'] = request.args.getlist('keywords')
        if 'categories' in request.args:
            query_dict['categories'] = request.args.getlist('categories')
        if 'publish_date' in request.args:
            query_dict['publish_date'] = request.args.getlist('publish_date')

    
    for key in query_keys:
        if key not in VALID_PARAMS_NEW:
            return str(key + ' is not a valid parameter.\n')

    print('QUERY DICT:', query_dict)
  
    clusters, keywords = allFieldsQuery(query_dict)
    sorted_clusters, sorted_keywords = rankClusters(clusters, keywords, query_dict['query'])
    clusters_json = convertJSON(sorted_clusters, sorted_keywords, query_dict)
    return json.dumps(clusters_json, ensure_ascii=False)

if __name__ == '__main__':
    app.run(host='192.168.10.116', port=5012, debug=True)
