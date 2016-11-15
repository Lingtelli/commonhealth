import os
import sys
from functools import reduce
import pandas as pd
import numpy as np

data_path = '/Users/jlin/Lingtelli/kanjian/data/'

def merge_all_df(filename):
    df = pd.read_csv(data_path + filename + '_multiprocessing_temp.csv')

    def f(x):
        try:
            return pd.Series(dict( member_size = x['member_size'].sum(), comment = "%s" % ',  '.join(x['comment'])))
        except:
            return pd.Series(dict( member_size = x['member_size'].sum(), comment = "%s" % ',  '.join(str(x['comment']))))

    def twoSpace(comments):
        return comments.replace(', ', ',  ')

    grouped = df.groupby(['cluster_center','keyword']).apply(f).sort_values(by=['member_size'], ascending=[False])
    #grouped['comment'] = grouped['comment'].apply(twoSpace)
    #grouped = grouped[grouped['member_size']>=3]
    #grouped = grouped[['member_size', 'comment']]

    grouped = grouped.reset_index()
    grouped.to_csv(data_path +  str(filename) + '_final_result.csv', columns=['member_size', 'cluster_center', 'keyword', 'comment'], index=False, encoding='utf8')

    return 'OK'

if __name__ == '__main__':
    filename = sys.argv[1:][0]
    merge_all_df(filename)
