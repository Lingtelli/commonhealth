# -*- coding: utf-8 -*-
import json
import itertools
from operator import itemgetter
from datetime import datetime
from collections import Counter, defaultdict


# Filtering a list based on a list of booleans
def calculateScore(keywords, target, bonus):
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
            matched.append((cluster, score))
     
    sorted_matched = sorted(matched, key=itemgetter(1), reverse=True)
    sorted_matched = [x[0] for x in sorted_matched]
    return sorted_matched

def isQualified(member, center, author, date_start, date_end, categories):
    if ((center is not None) and (center not in member['_centers'])):
        return False
    if ((author is not None) and (author != member['author'])):
        return False
    if ((categories is not None and len(categories) > 0)  and (member['source'] not in categories)):
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
    
def searchQualified(clusters, center=None, author=None, date_start=None, date_end=None, categories=None):
    for cluster in clusters:
        cluster['member'][:] = [member for member in cluster['member'] if isQualified(member, center, author, date_start, date_end, categories)]
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

def getCenterSize2(cluster):
    centers = cluster['centers']
    _centers_lists = []
    for member in cluster['member']:
        _centers_lists.append(member['_centers'])

    total_count = Counter(i for i in list(itertools.chain.from_iterable(_centers_lists)))
    return total_count

def getExtraInfo(clusters):
    for cluster in clusters:
        # 群內各中心的數量
        cluster['each_center_count'] = getCenterSize2(cluster)
        
        # 群內不重複文章數量及文章標題
        title_in_cluster = [member['title'] for member in cluster['member']]
        cluster['article_count'] = Counter(title_in_cluster)
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
        else:
            for member in cluster['member']:
                del member['article_id']
                del member['parapraph_tags']
                del member['article_tag']
            
    return clusters

output_filename = './cluster_result0.json'
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

    data = open('test_big.json', encoding='utf-8')
    cluster_list = json.load(data)

    matched_clusters = filterClusters(cluster_list, query_words)
    print('after filterClusters, # of candidate cluster:', len(matched_clusters))
    
    matched_clusters = searchClusters(matched_clusters, query_dict['groups'])
    print('after searchClusters, # of candidate cluster:', len(matched_clusters))

    matched_clusters = searchQualified(matched_clusters, query_dict['center'], query_dict['author'], query_dict['date_start'], query_dict['date_end'], query_dict['categories'])
    print('after searchQualified, # of candidate cluster:', len(matched_clusters))

    # 計算每一個center的數量
    matched_clusters = getExtraInfo(matched_clusters)
    #matched_clusters = countCenterSize(matched_clusters)

    if query_dict['page_start'] != None:
        matched_clusters = trimClusters(matched_clusters, query_dict['page_start'])
    
    print('Done.')

    return json.dumps(matched_clusters, ensure_ascii=False)


def query():
    if request.json:                        # request from website
        print('\nGOT REQUEST FROM CURL')
        query_dict = request.json
        query_keys = query_dict.keys()

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
  
    df, keywords = allFieldsQuery(query_dict)
    clusters_json = convertJSON(df, keywords, query_dict)
    return json.dumps(clusters_json, ensure_ascii=False)
