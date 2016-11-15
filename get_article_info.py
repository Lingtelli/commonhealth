import re
import sys
import json
import pandas as pd
import numpy as np


def makeTitle(data):
    try:
        if np.isnan(data['WEB_TITLE']):
            return data['PAPER_TITLE']
    except:
        return data['WEB_TITLE']

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
    
def main():
    # 刪除PUBLISH_DATE欄位是nan的row
    # 看起來只有刪除一個row
    df_article_info = pd.read_csv('~/Downloads/kangjiantype/20160715-ch-article_data.csv')
    #df_article_info = df_article_info[pd.isnull(df_article_info['PUBLISH_DATE'])]
    df_article_info = df_article_info[pd.notnull(df_article_info['PUBLISH_DATE'])]

    df_article_info['TITLE'] = df_article_info.apply(makeTitle, axis=1)

    df_article_info['PUBLISH_DATE'] = df_article_info.apply(toDateForm, axis=1)

    df_article_subtype = pd.read_csv('/Users/jlin/Downloads/kangjiantype/0727-article_type_ref.csv')        # article_data_uuid, sub_type_id
    df_subtype_ref = pd.read_csv('/Users/jlin/Downloads/kangjiantype/0727-sub_type_code_utf8_clean.csv')          # 文章的子分類, 該子分類所屬的main_type
    df_type_ref = pd.read_csv('/Users/jlin/Downloads/kangjiantype/0727-type_code.csv', encoding='big5')     # 文章的分類

    # 抓到文章的子分類id
    df_article_info_subtype = df_article_info.merge(df_article_subtype[['ARTICLE_DATA_UUID', 'SUB_TYPE']], left_on='UUID', right_on='ARTICLE_DATA_UUID', left_index=True, how='left')
    print('所整理的資料共有', len(df_article_info_subtype['SUB_TYPE'].unique()), '種子項目')
    print('全部共有', len(df_subtype_ref['IUUID'].unique()), '個子項目')
    print('沒有資料不在全部子項目裡？', set(df_subtype_ref['IUUID'].unique()) > set(df_article_info_subtype['SUB_TYPE']), ', 整理的資料多了', list(set(df_article_info_subtype['SUB_TYPE']) - set(df_subtype_ref['IUUID'].unique())))

    # 抓到子分類的命名以及分類的id
    df_article_info_subtype_name = df_article_info_subtype.merge(df_subtype_ref[['IUUID', 'NAME', 'MAIN_TYPE']], left_on='SUB_TYPE', right_on='IUUID', how='left')

    # 抓到分類的命名
    df_article_info_all_type = df_article_info_subtype_name.merge(df_type_ref[['UUID', 'NAME']], left_on='MAIN_TYPE', right_on='UUID', how='left')

    # UUID_y: 文章分類項目的id, SUB_TYPE: 文章分類子項目的id
    df_article_info_all_type = df_article_info_all_type[['UUID_x', 'TITLE', 'AUTHOR', 'PUBLISH_DATE', 'URL_ID', 'NAME_x', 'NAME_y']]
    df_article_info_all_type.rename(
            columns={'UUID_x': 'article_id', 'TITLE': 'title', 'AUTHOR':'author', 'PUBLISH_DATE':'publish_date', 'URL_ID':'url', 'NAME_x':'category', 'NAME_y':'type'},
            inplace=True) #category: subtype

    print('--------------------------------------------------------------------------------------------------------------')
    print('fields contain nan:')
    print(df_article_info_all_type.isnull().any())
     
    print('--------------------------------------------------------------------------------------------------------------')
    #print('有subtype_id但沒辦法對應到其名稱:')
    #print(df_article_info_all_type[pd.isnull(df_article_info_all_type['subtype'])]['_sid'].unique())
    #print('有type_id但沒辦法對應到其名稱:')
    #print(df_article_info_all_type[pd.isnull(df_article_info_all_type['type'])]['_id'].unique())
    print('沒辦法找到文章分類(subtype, type)：')
    print(df_article_info_all_type[pd.isnull(df_article_info_all_type['category'])]['article_id'].unique())

    ############
    ######### 那文章出處到底在哪裡？
    ###########

    df_article_info_all_type.fillna('NO_DATA', inplace=True)
    df_article_info_all_type.to_csv('article_info.csv', index=False)
    #print(df_article_info_all_type)

if __name__ == '__main__': 
    main()
