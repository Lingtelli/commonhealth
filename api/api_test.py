# -*- coding: utf-8 -*-
import sys, os, inspect
from flask import Flask, request, send_from_directory
from flask_restful import Resource, Api
from flask_cors import CORS, cross_origin
import json
from operator import itemgetter
from datetime import datetime
from collections import Counter, defaultdict
import itertools

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

app = Flask(__name__, static_folder='/home/jlsche/Lingtelli/commonhealth/api/')
api = Api(app)
CORS(app)

VALID_PARAMS = ['query', 'clusterid', 'center', 'author', 'date_start', 'date_end', 'source', 'groups', 'page_start']

def calculateScore(keywords, target, bonus):
    # Filtering a list based on a list of booleans
    mask = [word in target for word in keywords]
    matched = [k for (k, m) in zip(keywords, mask) if m]
    keywords = [x for x in keywords if x not in matched]
    score = len(matched) * bonus
    return score, keywords

def filterClusters(cluster_list, query_words):
    matched = []
    if ' ' in query_words:
        return cluster_list

    for cluster in cluster_list:
        keywords = query_words[:]
        keyword_score, keywords = calculateScore(keywords, cluster['keyword'], 100)
        center_score, keywords = calculateScore(keywords, ''.join(cluster['centers']), 30)
        score = center_score + keyword_score
        
        if len(keywords) > 0:
            content = ''
            for member in cluster['member']:
                content += member['content']
            content_score, keywords = calculateScore(keywords, content, 2)
            score += content_score
        
        if len(keywords) == 0:
            #print('append cluster', cluster['clusterid'])
            matched.append((cluster, score))
     
    sorted_matched = sorted(matched, key=itemgetter(1), reverse=True)
    sorted_matched = [x[0] for x in sorted_matched]
    return sorted_matched

def isQualified(member, center, author, date_start, date_end, source):
    if ((center is not None) and (center not in member['_centers'])):
        return False
    if ((author is not None) and (author != member['author'])):
        return False
    if ((source is not None) and (source != member['source'])):
        return False
     
    date = ''.join(member['publish_date'].split('-'))
    if date_start is not None:
        date_start = ''.join(date_start.split('-'))
        if datetime.strptime(date, "%Y%m%d").date() < datetime.strptime(date_start, "%Y%m%d").date():
            return False 
    if date_end is not None:
        date_end = ''.join(date_end.split('-'))
        if datetime.strptime(date, "%Y%m%d").date() > datetime.strptime(date_end, "%Y%m%d").date():
            return False
    return True
    
def searchQualified(clusters, center=None, author=None, date_start=None, date_end=None, source=None):
    for cluster in clusters:
        cluster['member'][:] = [member for member in cluster['member'] if isQualified(member, center, author, date_start, date_end, source)]
    clusters[:] = [cluster for cluster in clusters if (len(cluster['member']) > 0)]
    return clusters

def matchQueryPair(queried_centers, member):
    #if len(set(queried_centers).intersection(member['_centers'])) > 0:     # perform OR calculation
    if set(queried_centers).issubset(set(member['_centers'])):              # perform AND calculation
        return True
    else:
        return False

def searchClusters(clusters, center_id_list=None):
    if len(center_id_list) > 0:
        match_dict = defaultdict(list)
        match_pair = [(x.split('_')[0], x.split('_')[1]) for x in center_id_list]
        for x in match_pair:
            match_dict[x[0]].append(x[1])
        #clusters[:] = [cluster for cluster in clusters if (((id_cluster_list is not None) and (cluster['clusterid'] in cluster_ids)) or (id_cluster_list is None))]
        clusters[:] = [cluster for cluster in clusters if cluster['keyword'] in match_dict.keys()]
        for cluster in clusters:
            cluster_keyword = cluster['keyword']
            queried_centers = match_dict[cluster_keyword]
            if queried_centers[0] == '':
                continue
            cluster['member'][:] = [member for member in cluster['member'] if matchQueryPair(queried_centers, member)]
        return clusters
    else:
        return clusters

def lookupByClusterid(clusters, _id):
    clusters[:] = [cluster for cluster in clusters if (cluster['clusterid'] == _id)]
    return clusters[0]


def countCenterSize(clusters):
    for cluster in clusters:
        centers = cluster['centers']
        _centers_lists = []
        for member in cluster['member']:
            _centers_lists.append(member['_centers'])
        total_count = Counter(i for i in list(itertools.chain.from_iterable(_centers_lists)))
        cluster['each_center_count'] = total_count
    return clusters

def trimClusters(clusters, page_start):
    mask_start  = (int(page_start) - 1) * 10
    mask_end = int(page_start) * 10
    
    for idx, cluster in enumerate(clusters):
        if idx < mask_start or idx >= mask_end: 
            for member in cluster['member']:
                del member['author']
                del member['content']
                del member['source']
                del member['parapraph_tags']
                del member['article_id']
                del member['article_tag']
                del member['url']
                del member['_centers']
                '''
                member['author'] = None
                member['content'] = None
                member['source'] = None
                member['parapraph_tags'] = None
                member['article_id'] = None
                member['article_tag'] = None
                member['url'] = None
                member['_centers'] = None
                member['title'] = None
                '''
        else:
            for member in cluster['member']:
                del member['article_id']
                del member['parapraph_tags']
                del member['article_tag']
                '''
                member['article_id'] = None
                member['parapraph_tags'] = None
                member['article_tag'] = None
                '''
            
    return clusters

output_filename = './cluster_result0.json'
@app.route('/commonhealth_api/', methods=['POST'])
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
    #'''
    matched_clusters = filterClusters(cluster_list, query_words)
    print('after filterClusters, # of candidate cluster:', len(matched_clusters))
    
    matched_clusters = searchClusters(matched_clusters, query_dict['groups'])
    print('after searchClusters, # of candidate cluster:', len(matched_clusters))

    matched_clusters = searchQualified(matched_clusters, query_dict['center'], query_dict['author'], query_dict['date_start'], query_dict['date_end'], query_dict['source'])
    print('after searchQualified, # of candidate cluster:', len(matched_clusters))
    #'''
    # 計算每一個center的數量
    matched_clusters = countCenterSize(matched_clusters)

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

if __name__ == '__main__':
    app.run(host='192.168.10.116', port=5012, debug=True)
