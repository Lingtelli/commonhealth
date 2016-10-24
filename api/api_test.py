# -*- coding: utf-8 -*-
import sys, os, inspect
from flask import Flask, request, send_from_directory
from flask_restful import Resource, Api
from flask_cors import CORS, cross_origin
import json
from operator import itemgetter
from datetime import datetime
from collections import Counter
import itertools

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

app = Flask(__name__, static_folder='/home/jlsche/Lingtelli/commonhealth/api/')
api = Api(app)
CORS(app)

VALID_PARAMS = ['query', 'clusterid', 'center', 'author', 'start', 'end', 'source']

def calculateScore(keywords, target, bonus):
    # Filtering a list based on a list of booleans
    mask = [word in target for word in keywords]
    matched = [k for (k, m) in zip(keywords, mask) if m]
    keywords = [x for x in keywords if x not in matched]
    score = len(matched) * bonus
    return score, keywords

def filterClusters(cluster_list, query_words):
    matched = []
    for cluster in cluster_list:
        keywords = query_words[:]
        center_score, keywords = calculateScore(keywords, ''.join(cluster['centers']), 30)
        keyword_score, keywords = calculateScore(keywords, cluster['keyword'], 100)
        score = center_score + keyword_score
        
        if len(keywords) > 0:
            content = ''
            for member in cluster['member']:
                content += member['content']
            content_score, keywords = calculateScore(keywords, content, 2)
            score += content_score

        if len(keywords) == 0:
            print('append cluster', cluster['clusterid'])
            matched.append((cluster, score))
     
    sorted_matched = sorted(matched, key=itemgetter(1), reverse=True)
    sorted_matched = [j[0] for j in sorted_matched]
    return sorted_matched
    #return json.dumps(sorted_matched, ensure_ascii=False)

def isQualified(member, center, author, start, end, source):
    if ((center is not None) and (center not in member['_centers'])):
        return False
    if ((author is not None) and (author != member['author'])):
        return False
    if ((source is not None) and (source != member['source'])):
        return False
    if ((start is not None) and (end is not None)):
        date = ''.join(member['date'].split('-'))
        start = ''.join(start.split('-'))
        end = ''.join(end.split('-'))
        if ((datetime.strptime(date, "%Y%m%d").date() < datetime.strptime(start, "%Y%m%d").date()) or 
                (datetime.strptime(date, "%Y%m%d").date() > datetime.strptime(end, "%Y%m%d").date())):
            return False
    return True
    
def searchQualified(clusters, center=None, author=None, start=None, end=None, source=None):
    for cluster in clusters:
        cluster['member'][:] = [member for member in cluster['member'] if isQualified(member, center, author, start, end, source)]
    clusters[:] = [cluster for cluster in clusters if (len(cluster['member']) > 0)]
    return clusters

def searchClusters(clusters, clusterid=None):
    clusters[:] = [cluster for cluster in clusters if (((clusterid is not None) and (cluster['clusterid']==clusterid)) or (clusterid is None))]
    return clusters

def countCenterSize(clusters):
    for cluster in clusters:
        centers = cluster['centers']
        _centers_lists = []
        for member in cluster['member']:
            _centers_lists.append(member['_centers'])
        total_count = Counter(i for i in list(itertools.chain.from_iterable(_centers_lists)))
        cluster['each_center_count'] = total_count
    return clusters

output_filename = './cluster_result0.json'
@app.route('/commonhealth_api/', methods=['POST'])
def commonhealth_api():
    if request.json:
        query_dict = request.json
        query_keys = query_dict.keys()
        query_words = query_dict['query']
    else:
        query_dict = request.args.to_dict()
        query_keys = query_dict.keys()
        query_words = request.args.getlist('query')

    for key in query_keys:
        if key not in VALID_PARAMS:
            return str(key + ' is not a valid parameter.\n')

    for key in VALID_PARAMS:
        if key not in query_keys:
            query_dict[key] = None
    
    #print(query_dict)
    data = open('test_big.json', encoding='utf-8')
    #data = open('cluster_result0.json', encoding='utf-8') 
    cluster_list = json.load(data)

    matched_clusters = filterClusters(cluster_list, query_words)
    print('after filterClusters, # of candidate cluster:', len(matched_clusters))

    matched_clusters = searchClusters(matched_clusters, query_dict['clusterid'])
    print('after searchClusters, # of candidate cluster:', len(matched_clusters))

    matched_clusters = searchQualified(matched_clusters, query_dict['center'], query_dict['author'], query_dict['start'], query_dict['end'])
    print('after searchQualified, # of candidate cluster:', len(matched_clusters))

    # 計算每一個center的數量
    matched_clusters = countCenterSize(matched_clusters)

    return json.dumps(matched_clusters, ensure_ascii=False)

# not working if put it here
#data = open('cluster_result0.json', encoding='utf-8') 
#cluster_list = json.load(data)


if __name__ == '__main__':
    app.run(host='192.168.10.116', port=5012, debug=True)
