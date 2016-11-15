import pandas as pd
import json
import sys
import re


# return words in centers that also appear in content
def centersInContent(content, centers):
    filters = [c in content for c in centers]
    return [center for (center, value) in zip(centers, filters) if value]


def main(filename):
    # _final_result.csv 分群法最後分出來的結果
    df_clusters = pd.read_csv('/Users/jlin/Lingtelli/kanjian/data/' + filename + '_final_result.csv')
    columns = df_clusters.columns.values.tolist()
    field_pos_dict = {'size': columns.index('member_size'), 'centers': columns.index('cluster_center'), 'keyword': columns.index('keyword'), 'comments': columns.index('comment')}
    print('columns:', columns)

    df_article_info = pd.read_csv('./article_info.csv')
    all_clusters = []
    ncols = df_clusters.values.shape[1]

    for idx, cluster in enumerate(df_clusters.values):
        comments = cluster[field_pos_dict['comments']].split(',  ')
        cluster_obj = dict()
        cluster_obj['clusterid'] = str(idx+1) 
        cluster_obj['size'] = cluster[field_pos_dict['size']]
        cluster_obj['centers'] = cluster[field_pos_dict['centers']].split(',')
        cluster_obj['keyword'] = cluster[field_pos_dict['keyword']]

        members = []
        for c in comments:
            paragraph = dict()
            searchObj = re.search( r'[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}(.*)', c, re.M|re.I)
            if searchObj is None:
                continue
            filtered = c[searchObj.start():searchObj.end()]
            first_space_idx = filtered.find(' ')
            article_id = filtered[: first_space_idx]
            paragraph_tags = filtered[first_space_idx+1:].split(' ')
            paragraph['content'] = c[:searchObj.start()]
            paragraph['article_id'] = article_id
            paragraph['parapraph_tags'] = paragraph_tags
        
            paragraph['_centers'] = centersInContent(paragraph['content'], cluster_obj['centers'])
            paragraph_pos = df_article_info[df_article_info['article_id']==article_id]
            try:
                paragraph["title"] = paragraph_pos['title'].iloc[0]
                paragraph["author"] = paragraph_pos['author'].iloc[0]
                paragraph['url'] = paragraph_pos['url'].iloc[0]
                paragraph['category'] = paragraph_pos['category'].iloc[0]
                paragraph['publish_date'] = paragraph_pos['publish_date'].iloc[0]
            except:
                print('NOT DATA FOR ARTICLE ID:', article_id)
                paragraph["title"] = 'NO_DATA'
                paragraph["author"] = 'NO_DATA'
                paragraph['url'] = 'NO_DATA'
                paragraph['category'] = 'NO_DATA'
                paragraph['publish_date'] = 'NO_DATA'
                #paragraph['article_tag'] = paragraph_pos['article_tag'].iloc[0]

            members.append(paragraph)

        cluster_obj['member'] = members
        all_clusters.append(cluster_obj)
        
    json.dump(all_clusters, open('query_data_for_v1.json', 'w'), ensure_ascii=False)


if __name__ == '__main__':
    main(sys.argv[1])




#json_obj = df_clusters.to_json(force_ascii=False, orient='records')
