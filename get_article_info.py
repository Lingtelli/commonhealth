import re
import json
import pandas as pd
import numpy as np

df_dataset = pd.read_csv('./pcluster_cluster_result.csv')
df_article_info = pd.read_csv('~/Downloads/kangjiantype/20160715-ch-article_data.csv')

def makeTitle(data):
    return data['WEB_TITLE'] if data['WEB_TITLE'] != 'NO_VALUE' else data['PAPER_TITLE']

def toDateForm(data):
    date_str = data['PUBLISH_DATE'] if data['PUBLISH_DATE'] != 'NO_VALUE' else data['CREATE_TIME']
    date = date_str.split(' ')[0]
    date_split = date.split('/')
    try:
        if len(date_split[1]) == 1:
            date_split[1] = '0' + date_split[1]
        if len(date_split[2]) == 1:
            date_split[2] = '0' + date_split[2]
        return '-'.join(date_split)
    except:
        print('cannot convert date format of', data['UUID'])
        return date_split[0]
    
        
# 有髒資料，直接忽略
df_article_info = df_article_info[pd.notnull(df_article_info['PUBLISH_DATE'])]
df_article_info['TITLE'] = df_article_info.apply(makeTitle, axis=1)
df_article_info['PUBLISH_DATE'] = df_article_info.apply(toDateForm, axis=1)


df_article_subtype = pd.read_csv('/Users/jlin/Downloads/kangjiantype/0727-article_type_ref.csv')
df_subtype_ref = pd.read_csv('/Users/jlin/Downloads/kangjiantype/0727-sub_type_code_utf8.csv')
df_type_ref = pd.read_csv('/Users/jlin/Downloads/kangjiantype/0727-type_code.csv', encoding='big5')

df_article_info_subtype = df_article_info.merge(df_article_subtype[['ARTICLE_DATA_UUID', 'SUB_TYPE']], left_on='UUID', right_on='ARTICLE_DATA_UUID', left_index=True, how='left')
df_article_info_subtype_name = df_article_info_subtype.merge(df_subtype_ref[['UUID', 'NAME', 'MAIN_TYPE']], left_on='SUB_TYPE', right_on='UUID', how='left')
df_article_info_all_type = df_article_info_subtype_name.merge(df_type_ref[['UUID', 'NAME']], left_on='MAIN_TYPE', right_on='UUID', how='left')

df_article_info_all_type = df_article_info_all_type[['UUID_x', 'TITLE', 'AUTHOR', 'PUBLISH_DATE', 'URL_ID', 'NAME_x', 'NAME_y']]
df_article_info_all_type.rename(columns={'UUID_x': 'article_id', 'TITLE': 'title', 'AUTHOR':'author', 'PUBLISH_DATE':'publish_date', 'URL_ID':'url', 'NAME_x':'article_tag', 'NAME_y':'source'}, inplace=True)
df_article_info_all_type.fillna('NO_DATA', inplace=True)
df_article_info_all_type.to_csv('article_info.csv', index=False)
print(df_article_info_all_type)


