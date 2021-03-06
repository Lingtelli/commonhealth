import re
import json
import operator
import jieba
import pandas as pd
import numpy as np
from itertools import count
from collections import Counter, defaultdict
from gensim.models import word2vec

def extractInfo(c):
    searchObj = re.search( r'[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}(.*)$', c['comment_no_punc'], re.M|re.I)
    if searchObj == None:
        print('NO PATTERN MATCHED IN COMMENT %s' % c['comment_no_punc'])
        c['article_id'] = 'NO_DATA'
        c['tags'] = 'NO_DATA'
        c['comment_pure'] = c['comment_no_punc']
    else:
        c['article_id'] = c['comment_no_punc'][searchObj.start(): searchObj.end()].split(' ', 1)[0]
        c['tags'] = c['comment_no_punc'][searchObj.start(): searchObj.end()].split(' ', 1)[1]
        c['comment_pure'] = c['comment_no_punc'][: searchObj.start()]

    search_content = re.search( r'[a-z0-9]{8}-+[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}(.*)$', c['comment'], re.M|re.I)
    if search_content is not None:
        c['content'] = c['comment'][: search_content.start()]
    else:
        c['content'] = c['comment']
    return c

# erase [nan], NaN in df_comment_tag['keywords']
def cleanKeywords(keywords):
    if (type(keywords) == float) or (len(keywords) > 0 and type(keywords[0]) is float):
        return []
    keywords = [x for x in keywords if str(x) != 'nan']
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
        try:
            most_similar = w2v_model.most_similar(w, topn=10)
            concepts[w] = [m[0] for m in most_similar if m[1] >= threshold] + [w]
        except:
            continue
        #print(concepts[w])
    return concepts


def allFieldsQuery(q_dict):
    df_dataset = pd.read_msgpack('df_dataset.msg')
    df_dataset['keywords_str'] = df_dataset['keywords'].apply(lambda x: ' '.join(x))
    df_dataset['comment_no_punc'] = df_dataset['content'].apply(removePunctuation)

    tdf = df_dataset
    for word in q_dict['query']:
        tdf = tdf[(tdf.comment_no_punc.str.contains(word, na=False)) | (tdf.keywords_str.str.contains(word, na=False))]

    query = '|'.join(q_dict['query'])
    #tdf = df_dataset[(df_dataset.comment_no_punc.str.contains(query, na=False)) | (df_dataset.keywords_str.str.contains(query, na=False))]
        
    # 在目前的tdf的各篇段落裡的所有關鍵字，不包含query
    keyword_contain_query = [k for kws in tdf.keywords.str for k in kws if (type(k) is not float) and (k not in query)]

    query_fields = q_dict.keys()

    top_candidate_words = Counter(keyword_contain_query).most_common()
    return_cluster_size = len(top_candidate_words) if 'return_cluster_size' not in query_fields else q_dict['return_cluster_size']
    top_keywords = [w[0] for w in top_candidate_words[: return_cluster_size]]

    if 'return_cluster_size' not in query_fields:
        print('query for all clusters. (', return_cluster_size, ')')
    else:
        print('query for', return_cluster_size, 'clusters.')

    if 'author' in query_fields:
        tdf = tdf[(tdf.author.str.contains(q_dict['author'], na=False))]
        
    if 'categories' in query_fields:
        query = '|'.join(q_dict['categories'])
        tdf = tdf[(tdf.category.str.contains(query, na=False))]
            
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
        concepts = getConceptWords(top_keywords)
                
    for concept, words in concepts.items():
        #print(concept, 'size:', end='')
        _query = '|'.join(words)
        temp_df = tdf[tdf.keywords_str.str.contains(_query, na=False)]
        #print(len(temp_df))
        if len(temp_df) > 0:
            clusters.append(temp_df)
            keywords.append(concept)
    
    return clusters, keywords

def rankClusters(clusters, keywords, query_words):
    score_dict = dict()
    query = '|'.join(query_words)

    # 如果是words出現在同一文章應該要最高
    for idx, c in enumerate(clusters):
        # 可能需要先只留下同樣的文章？
        num_rows_keywords_contain_words = c.keywords_str.str.contains(query, na=False).sum()
        num_rows_content_contain_words = c.comment_no_punc.str.contains(query, na=False).sum()
         
        score = num_rows_keywords_contain_words * 100 + 2 * num_rows_content_contain_words
        score_dict[idx] = score
        c.sort_values(by='article_id', inplace=True)
        c.drop_duplicates(inplace=True)
        #print(keywords[idx], '->', score)
    
    ranking = sorted(score_dict.items(), key=operator.itemgetter(1), reverse=True)
    ranking = [x[0] for x in ranking]
    
    sorted_keywords = [keywords[idx] for idx in ranking]
    sorted_clusters = [clusters[idx] for idx in ranking]
    
    return sorted_clusters, sorted_keywords


# batch_size 表示要完整顯示的群組，若沒有給，表示是由Curl request，應回傳所有群組的完整資料
def convertJSON(df_list, keywords, q_dict):
    clusters = []
    
    idx_from = 0
    idx_to = len(df_list)
    
    if 'cluster_idx' in q_dict.keys():
        idx_from = int(q_dict['cluster_idx'])
    if 'batch_size' in q_dict.keys():
        idx_to = idx_from + q_dict['batch_size']
        print('detail data from cluster', idx_from, 'to', idx_to)
    else:
        print('ALL DATA ARE IN DETAIL')

    # 踢掉除了關鍵字不一樣，其他內容完全一樣的群
    #########################################################################
    remove_list = []
    for idx, df in enumerate(df_list):
        if idx + 1 != len(keywords):
            if df[['content']].equals(df_list[idx+1][['content']]):
                remove_list.append(idx+1)
    df_list = [df for idx, df in enumerate(df_list) if idx not in remove_list]
    keywords = [k for idx, k in enumerate(keywords) if idx not in remove_list]
    #########################################################################

    for idx, df, kw in zip(count(), df_list, keywords):
        cluster_obj = dict()
        cluster_obj['keyword'] = kw
        cluster_obj['size'] = len(df)
        if idx >= idx_from and idx < idx_to:
            temp_df = df[['content', 'article_id', 'title', 'author', 'publish_date', 'url', 'category', 'keywords']]
            temp_df['publish_date'] = temp_df['publish_date'].apply(lambda x: str(x)[:4] + '-' + str(x)[4:6] + '-' + str(x)[6:])
        else:
            temp_df = df[['title', 'category']]
        
        num_each_article = Counter(df['title'].tolist())
        cluster_obj['member'] = temp_df.to_dict(orient='records')
        cluster_obj['article_count'] = num_each_article
        clusters.append(cluster_obj)
                                        
    return clusters



