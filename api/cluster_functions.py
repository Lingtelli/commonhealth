import re
import json
import jieba
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from gensim.models import word2vec

def extractInfo(c):
    searchObj = re.search( r'([a-z0-9]+-)+[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]+(.*)$', c['comment_no_punc'], re.M|re.I)
    if searchObj == None:
        print('NO PATTERN MATCHED IN COMMENT %s' % c['comment_no_punc'])
        c['article_id'] = 'NO_DATA'
        c['tags'] = 'NO_DATA'
        c['comment_pure'] = c['comment_no_punc']
    else:
        c['article_id'] = c['comment_no_punc'][searchObj.start(): searchObj.end()].split(' ', 1)[0]
        c['tags'] = c['comment_no_punc'][searchObj.start(): searchObj.end()].split(' ', 1)[1]
        c['comment_pure'] = c['comment_no_punc'][: searchObj.start()]

    searchObj2 = re.search( r'([a-z0-9]+-)+[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]+(.*)$', c['comment'], re.M|re.I)
    if searchObj2 is not None:
        c['content'] = c['comment'][: searchObj.start()]
    else:
        c['content'] = c['comment']
    return c

# erase [nan], NaN in df_comment_tag['keywords']
def cleanKeywords(keywords):
    if (type(keywords) == float) or (len(keywords) > 0 and type(keywords[0]) is float):
        return []
    return keywords

def makeTitle(data):
    try:
        if np.isnan(data['WEB_TITLE']):
            return data['PAPER_TITLE']
    except:
        return data['WEB_TITLE']

def toDateForm(data):
    date_str = data['PUBLISH_DATE']# if data['PUBLISH_DATE'] != 'NO_VALUE' else data['CREATE_TIME']
    date = date_str.split(' ')[0]
    date_split = date.split('/')
    
    try:
        if len(date_split[1]) == 1:
            date_split[1] = '0' + date_split[1]
        if len(date_split[2]) == 1:
            date_split[2] = '0' + date_split[2]
        return ''.join(date_split)
    except:
        print('cannot convert date format of', data['UUID'])
        return date_split[0]

def removePunctuation(words):
    regex = re.compile('[，。”~〈《》〉（）「」『』\n\t；！？～⋯〃《》〃、●■：◎★☆＊※()><=▼【】*．／﹙﹚〔〕＝▓˙@\[\]]')
    return regex.sub('', words)

# 利用word2vec查出與_query_list內所有query相近的詞與為一群
def getConceptWords(words, threshold=0.65):
    w2v_model = word2vec.Word2Vec.load('w2v_model.mdl')
    concepts = defaultdict(list)
    for w in words:
        #print('\n\n', w, '->', end=' ')
        most_similar = w2v_model.most_similar(w, topn=9)
        concepts[w] = [m[0] for m in most_similar if m[1] >= threshold] + [w]
        #print(concepts[w])
    return concepts


def allFieldsQuery(q_dict):
    df_dataset = pd.read_msgpack('df_dataset.msg')
    df_dataset['keywords_str'] = df_dataset['keywords'].apply(lambda x: ' '.join(x))
    df_dataset['comment_no_punc'] = df_dataset['content'].apply(removePunctuation)

    query = '|'.join(q_dict['query'])
    tdf = df_dataset[(df_dataset.comment_no_punc.str.contains(query, na=False)) | (df_dataset.keywords_str.str.contains(query, na=False))]
        
    keyword_contain_query = [k for kws in tdf.keywords.str for k in kws if (type(k) is not float) and (k not in query)]

    query_fields = q_dict.keys()

    most_common_size = 10 if 'most_common_size' not in query_fields else q_dict['most_common_size']
    top_keywords = [w[0] for w in Counter(keyword_contain_query).most_common(most_common_size)]

    if 'author' in query_fields:
        tdf = tdf[(tdf.author.str.contains(q_dict['author'], na=False))]
        
    if 'categories' in query_fields:
        query = '|'.join(q_dict['categories'])
        tdf = tdf[(tdf.subtype.str.contains(query, na=False))]
            
    if 'publish_date' in query_fields:
        start = ''.join(q_dict['publish_date'][0].split('-'))
        end = ''.join(q_dict['publish_date'][1].split('-'))
        mask = (tdf['publish_date'] >= start) & (tdf['publish_date'] <= end)
        tdf = tdf.loc[mask]
            
    clusters = []
    keywords = []
    if 'keywords' in query_fields:
        concepts = getConceptWords(q_dict['keywords'])
    else:
        concepts = getConceptWords(top_keywords[:10])
                
    for concept, words in concepts.items():
        print(concept, 'size:', end='')
        _query = '|'.join(words)
        temp_df = tdf[tdf.keywords_str.str.contains(_query, na=False)]
        print(len(temp_df))
        if len(temp_df) > 0:
            clusters.append(temp_df)
            keywords.append(concept)
    
    cluster_idx = 0
    batch_size = 5
    if 'cluster_idx' in query_fields:
        cluster_idx = q_dict['cluster_idx']
    if 'batch_size' in query_fields:
        batch_size = q_dict['batch_size']

    return clusters[cluster_idx: cluster_idx + batch_size], keywords[cluster_idx: cluster_idx + batch_size]


def convertJSON(df_list, keywords):
    clusters = []
    
    for df, kw in zip(df_list, keywords):
        cluster_obj = dict()
        cluster_obj['keyword'] = kw
        cluster_obj['size'] = len(df)
        temp_df = df[['content', 'article_id', 'title', 'author', 'publish_date', 'url', 'subtype', 'keywords']]
        cluster_obj['member'] = temp_df.to_dict(orient='records')
        clusters.append(cluster_obj)
                                        
    return clusters



