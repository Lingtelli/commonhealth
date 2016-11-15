# coding: utf-8
import pandas as pd
import numpy as np
import sys
import operator
import time
import json
import string
import jieba
import requests
import time
#from . import functions
import commonhealth_functions
from collections import Counter

import math
import multiprocessing

# 繁體文章類  文章不適合用LCS

def startClustering(origin_comments, comments):
    tags = commonhealth_functions.getClusterTfIdf(comments.to_string(), tag_num=500, return_weight=True)
    candidate_centers = [x[0] for x in tags[:20]]
    cluster_center = []
    for idx in range(0, len(candidate_centers)):
        if '...' == candidate_centers[idx]:
            continue
        try:
            float(candidate_centers[idx])
            continue
        except:
            cluster_center.append(candidate_centers[idx])
        if len(cluster_center) == 5:
            break
    tag_dict = dict(tags)
    comments_seg = comments.apply(commonhealth_functions.generateSegmentList)

    # 把一樣的斷詞找出來，包含出現次數 可用來列出所有的斷詞
    word_counted = Counter([word for comment in comments_seg for word in comment])

    # 刪除seg_word內不必要的東西
    seg_words = list(word_counted.keys())
    useless_words = ['你','我','他','的','了','啦','很','太','哦','/','r','n','嗎','呢','呀','哎','她','噢','麼','耶','還是','最','啊',']', '為', '在', '是', '也', '會', '有', '有', '人', '不', '都', '和', '或', '就', '後']
    clean_seg_words = [x for x in seg_words if x not in useless_words]

    # 找出所有clean_seg_words的tf-idf value，以dataframe的方式去取得tf-idf value因為比較快
    seg_word_df = pd.DataFrame()
    seg_word_df['word'] = clean_seg_words
    seg_word_df['tf_idf'] = seg_word_df['word'].apply(lambda x: tag_dict[x] if x in tag_dict else -10.0)

    # 把所有斷詞的 tf-idf dataframe 變成 dict, 方便未來查詢用
    tf_idf_dict = dict(zip(seg_word_df['word'], seg_word_df['tf_idf']))

    # 根據tf-idf值，找出每一句評論的關鍵詞(critical_words) （前10個有最高tf-idf分數的斷詞）
    comments_df = comments.to_frame('comment')
    comments_df['origin_comment'] = origin_comments
    comments_df['seg_comment'] = comments_seg
    comments_df['critical_words'] = comments_df['seg_comment'].apply(commonhealth_functions.getTopTfIdfWords, args=(tf_idf_dict, 10))

    # 從每一個評論的關連詞(comments_df['critical_words'])裡，找出哪個關連詞最先在sorted_tag_dict出現(有最高的tf-idf分數)（兩陣列中找到第一個共同元素）
    # http://stackoverflow.com/questions/16118621/first-common-element-from-two-lists
    # 此方法會有評論無法被分群，故需要以choosen來紀錄
    comments_df['choosen'] = False
    cluster = {}
    sorted_tag_dict = sorted(tag_dict.items(), key=operator.itemgetter(1), reverse=True)

    for comment_id, critical_words in enumerate(comments_df['critical_words']):
        set_y = set(critical_words)
        first_critical_word = next(( word for word in sorted_tag_dict if word[0] in set_y ), None )
        if first_critical_word == None:
            # 在這段落會被拋棄
            print('no critical word in', comments_df['comment'][comment_id])
            print('centers:', cluster_center, 'critical_words:', critical_words)
            continue
        first_critical_word_idx = sorted_tag_dict.index(first_critical_word)
        comments_df['choosen'][comment_id] = True
        try:
            cluster[first_critical_word_idx].append(comment_id)
        except:
            cluster[first_critical_word_idx] = [comment_id]
    
    '''
    # 上面方法仍有可能會有單獨一評論一群的狀況（因為此評論同時有熱門以及不熱門但數量大於1的關連詞）故需要另外把這種一評論一群的狀況刪除
    remove_list = []
    for key, value in cluster.items():
        if len(value) <= 1:
            remove_list.append(key)
    for ele in remove_list:
        cluster.pop(ele, None)
    '''

    result_df_list = []
    # 儲存沒有分到群的為一群
    no_group_comments = comments_df[comments_df['choosen']==False]['origin_comment'].tolist()
    if len(no_group_comments) > 0:
        no_group_df = pd.DataFrame(columns=['comment','cluster_center','keyword','member_size'], index=[0])
        comments_str = ',  '.join(no_group_comments)
        ################################################################
        no_group_df['cluster_center'] = 'NO_GROUP'
        no_group_df['keyword'] = int(round(time.time() * 1000))
        no_group_df['comment'] = comments_str
        no_group_df['member_size'] = len(no_group_comments)
        result_df_list.append(no_group_df)

    # 找出有評論的cluster
    # （好像可以和上上面合併？或是根本不需要）
    new_clusters_id = []
    for cluster_id, members in cluster.items():
        if len(members) > 0:
            new_clusters_id.append(cluster_id)

    for _id in new_clusters_id:
        # 把評論集中成一條list
        group_comments = comments_df.loc[cluster[_id], ['origin_comment']]['origin_comment'].tolist()
        group_comments_len = len(group_comments)
        group_comments_str = ',  '.join(group_comments)
        cluster_center_str = ','.join(cluster_center)

        group_df = pd.DataFrame(columns=['comment','cluster_center','keyword','member_size'], index=[0])
        group_df['cluster_center'] = cluster_center_str
        group_df['keyword'] = sorted_tag_dict[_id][0]
        group_df['comment'] = group_comments_str
        group_df['member_size'] = group_comments_len
        result_df_list.append(group_df)

    if len(result_df_list) > 0:
        result = pd.concat(result_df_list, ignore_index=True)
        return result
    else:
        print('nothing to concate for this cluster.', '\t origin cluster size:', len(origin_comments))
        return None


def parallelClustering(origin_comments_list, cleaned_comments_list):
    results = []
    for origin_comments, cleaned_comments in zip(origin_comments_list, cleaned_comments_list):
        results.append(startClustering(pd.Series(origin_comments), pd.Series(cleaned_comments), ))
    return results


def main(argv):
    data_path = '/Users/jlin/Lingtelli/kanjian/data/'
    #data_path = '/home/lingtelli/jlsche/kanjian/data/'

    filename = argv[0]
    df = pd.read_csv(data_path + filename + '.csv', names=['count', 'comments'])
    df['count'] = df['count'].apply(lambda x: int(x))
    df = df[df['count'] > 0].reset_index()
    df['comments_cleaned'] = df['comments'].apply(commonhealth_functions.removePunctuation)
    comments_cleaned_series = df['comments_cleaned'].apply(commonhealth_functions.strToSeries)
    comments_cleaned_series = comments_cleaned_series.apply(commonhealth_functions.chopTail2)
    comments_series = df['comments'].apply(commonhealth_functions.strToSeries)

    task_size = len(comments_series)
    print('Task Size:', task_size)

    NUM_OF_CORES = 12
    p = multiprocessing.Pool(NUM_OF_CORES)

    results = []
    job_each_core = []
    percentage_each_core = [0.001, 0.009, 0.01, 0.01, 0.01, 0.01, 0.05, 0.1, 0.1, 0.2, 0.2, 0.3]

    lower = 0
    for i in percentage_each_core:
        upper = lower + math.ceil(task_size * i)
        job_each_core.append((lower, upper))
        lower = upper

    origin_clusters = comments_series.tolist()
    cleaned_clusters = comments_cleaned_series.tolist()

    start_time = time.time()
    for arg in job_each_core:
        results.append(p.apply_async(parallelClustering, args=(origin_clusters[arg[0]: arg[1]], cleaned_clusters[arg[0]: arg[1]], )))

    results = [r.get() for r in results]
    results = [x for r in results for x in r if x is not None]

    output_df = pd.concat(results)
    output_df.to_csv(data_path + filename + '_multiprocessing_temp.csv', index=False, sep=',', encoding='utf8')
    end_time = time.time()
    print("%.2f seconds to finish the task %s" % ((end_time - start_time), filename))
    return 'OK'

if __name__ == "__main__":
    main(sys.argv[1:])
