import pandas as pd
import json
import re


def centersInContent(content, centers):
    filters = [c in content for c in centers]
    return [center for (center, value) in zip(centers, filters) if value]



df_clusters = pd.read_csv('./pcluster_cluster_result.csv')
df_article_info = pd.read_csv('./article_info.csv')
all_clusters = []
ncols = df_clusters.values.shape[1]
for idx, cluster in enumerate(df_clusters.values):
    comments = cluster[2].split(',  ')
    cluster_obj = dict()
    cluster_obj['clusterid'] = str(idx+1) 
    cluster_obj['size'] = cluster[3]
    cluster_obj['centers'] = cluster[0].split(',')
    cluster_obj['keyword'] = cluster[1]

    members = []
    for c in comments:
        paragraph = dict()
        searchObj = re.search( r'([a-z0-9]+-)+[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+(.*)', c, re.M|re.I)
        filtered = c[searchObj.start():searchObj.end()]
        first_space_idx = filtered.find(' ')
        article_id = filtered[: first_space_idx]
        paragraph_tags = filtered[first_space_idx+1:].split(' ')
        paragraph['content'] = c[:searchObj.start()]
        paragraph['article_id'] = article_id
        paragraph['parapraph_tags'] = paragraph_tags
    
        paragraph['_centers'] = centersInContent(paragraph['content'], cluster_obj['centers'])
        paragraph_pos = df_article_info[df_article_info['article_id']==article_id]
        paragraph["title"] = paragraph_pos['title'].iloc[0]
        paragraph["author"] = paragraph_pos['author'].iloc[0]
        paragraph['url'] = paragraph_pos['url'].iloc[0]
        paragraph['source'] = paragraph_pos['source'].iloc[0]
        paragraph['publish_date'] = paragraph_pos['publish_date'].iloc[0]
        paragraph['article_tag'] = paragraph_pos['article_tag'].iloc[0]

        members.append(paragraph)

    cluster_obj['member'] = members
    all_clusters.append(cluster_obj)
    
json.dump(all_clusters, open('test.json', 'w'), ensure_ascii=False)






#json_obj = df_clusters.to_json(force_ascii=False, orient='records')
