import re
import copy
import json
import string
import operator
import jieba
import jieba.analyse
import requests
import multiprocessing

jieba.set_dictionary('/Users/jlin/.pyenv/versions/kanjian/lib/python3.5/site-packages/jieba/dict.txt.big')
#jieba.set_dictionary('/home/lingtelli/.pyenv/versions/Croton_Clustering/lib/python3.4/site-packages/jieba/dict.txt.big')
jieba.del_word('...')

def generateSegmentList(comment):
    words = jieba.cut(comment, cut_all=False)
    return list(words)

def strToSeries(string):
    return string.split(',  ')
    #return string.replace(' ', '').split(',')

def tras2sims(tra_words):
    if type(tra_words) != list:
        tra_words = [tra_words]
    sim_words = []
    for tra_word in tra_words:
        sim_words.append(requests.post('http://192.168.10.108:3001/tra2sim', params={'tra': tra_word}).json()['sim'][0])
    return sim_words

def getWordsWithAssoc(associations):
    words_with_assoc = {}
    for word in associations.json():
        words_sibling = []
        for word_sibling in word['sibling']:
            words_sibling.append(word_sibling['name'])
        words_with_assoc[word['name']] = word['parents'] + words_sibling + word['children']
    return words_with_assoc

def wordsWithAssocToSim_multiprocess(words_with_assoc):
    sim_words_with_assoc = {}
    #pool = multiprocessing.Pool(multiprocessing.cpu_count()-1)
    pool = multiprocessing.Pool(5)
    for word, assoc in words_with_assoc.items():
        sim_words_with_assoc[word] = {}
        sim_words_with_assoc[word] = pool.map(tra2sim, words_with_assoc[word])
    return sim_words_with_assoc

def wordsWithAssocToSim(words_with_assoc):
    sim_words_with_assoc = {}
    with requests.Session() as s:
        s.keep_alive = False
        for word, assoc in words_with_assoc.items():
            sim_words_with_assoc[word] = {}
            sim_words_assoc = []
            for tra_word in words_with_assoc[word]:
                resp = s.get('http://192.168.10.108:3001/tra2sim', params={'tra': tra_word})
                sim_words_assoc.append(resp.json()['sim'][0])
            sim_words_with_assoc[word] = sim_words_assoc
        return sim_words_with_assoc

def wordsWithAssocToSim_old(words_with_assoc):
    sim_words_with_assoc = {}
    for word, assoc in words_with_assoc.items():
        sim_words_with_assoc[word] = {}
        sim_words_assoc = []
        for tra_word in words_with_assoc[word]:
            print(requests.post('http://192.168.10.108:3001/tra2sim', params={'tra': tra_word}).json()['sim'][0])
            sim_word = requests.post('http://192.168.10.108:3001/tra2sim', params={'tra': tra_word}).json()['sim']
            sim_words_assoc.append(sim_word[0])
        sim_words_with_assoc[word] = sim_words_assoc
    return sim_words_with_assoc

def getAssoc(word, *args):
    if type(word) == list:
        word = word[0]
    words_sim_with_assoc = args[0]
    assoc = []
    try:
        assoc.extend(words_sim_with_assoc[word])
    except:
        print(word, 'not found')
    assoc.append(word)
    return assoc

def getCriticalWord(words, *args):
    seg_word_df = args[0]
    critical_word_tf_idf_value = -1000.0
    critical_word = None

    for word in words:
        try:
            word_tf_idf_value = seg_word_df[word]
            if word_tf_idf_value > critical_word_tf_idf_value:
                critical_word_tf_idf_value = word_tf_idf_value
                critical_word = word
        except:
            # word can't find is in remove_list (clean_seg_words)
            pass
    if critical_word == None:
        try:
            critical_word = words[0]
        except:
            critical_word = 'NO_CRITICAL_WORD'
    return critical_word

def getCenterCandidate_TfIdf(words, *args):
    tf_idf_dict = args[0]
    word_tfidf_dict = {}
    for word in words:
        try:
            word_tfidf_dict[word] = tf_idf_dict[word]
        except:
            word_tfidf_dict[word] = -10.0
    return sorted(word_tfidf_dict.items(), key=operator.itemgetter(1))[-1:][0][0]

def getCenterCandidate_MostCommon(words, *args):
    word_counted = args[0]
    useless_words = args[1]

    for word in word_counted.most_common(30):
        if (word[0] not in useless_words) and (word[0] in words):
            return word[0]
    return 'OOPS'

def getTopTfIdfWords(words, *args):
    tf_idf_dict = args[0]
    topN = args[1]
    word_tfidf_dict = {}
    for word in words:
        if word == ' ':
            continue
        try:
            word_tfidf_dict[word] = tf_idf_dict[word]
        except:
            word_tfidf_dict[word] = -10.0
    return [x[0] for x in sorted(word_tfidf_dict.items(), key=operator.itemgetter(1), reverse=True)[:topN]]

def getTfIdfValue(word, *args):
    tf_idf_df = args[0]
    word_tf_idf_value = -1000.0
    try:
        word_index = tf_idf_df[tf_idf_df['sim_word']==word].index[0]
        word_tf_idf_value = tf_idf_df['tf_idf'][word_index]

    except:
        # word not in tf-idf data.
        pass
    return word_tf_idf_value

def getTfIdfValueFromList(words, *args):
    tf_idf_df = args[0]
    critical_word_tf_idf_value = -100
    critical_word = None
    for word in words:
        try:
            word_index = tf_idf_df[tf_idf_df['sim_word']==word].index[0]
            word_tf_idf_value = tf_idf_df['tf_idf'][word_index]

            if word_tf_idf_value > critical_word_tf_idf_value:
                critical_word_tf_idf_value = word_tf_idf_value
                critical_word = word
        except:
            # word not in tf-idf data.
            pass
    return critical_word_tf_idf_value

# http://stackoverflow.com/questions/2892931/longest-common-substring-from-more-than-two-strings-python
def getLCS(comments):
    substr = []
    if len(comments) > 1 and len(comments[0]) > 0:
        for idx in range(len(comments[0])):
            for jdx in range(len(comments[0]) - idx + 1):
                if jdx > len(substr) and is_subseq_of_any(comments[0][idx: idx + jdx], comments):
                    substr = comments[0][idx: idx + jdx]
    return substr

def is_subseq_of_any(find, data):
    if len(data) < 1 and len(find) < 1:
        return False
    for i in range(len(data)):
        if not is_subseq(find, data[i]):
            return False
    return True

def is_subseq(possible_subseq, seq):
    if len(possible_subseq) > len(seq):
        return False
    def get_length_n_slices(n):
        for i in range(0, len(seq) + 1 - n):
            yield seq[i:i+n]
    for slyce in get_length_n_slices(len(possible_subseq)):
        if slyce == possible_subseq:
            return True
    return False

def removePunctuation(words):
    #'!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    #regex1 = re.compile('[%s]' % re.escape(string.punctuation))
    regex = re.compile('[，。”~〈《》〉（）「」『』\n\t；！？～⋯〃《》〃、●■：◎★☆＊※()><=▼【】*．／﹙﹚〔〕＝▓˙@\[\]]')#!\"#$%&\'()*+-./:;<=>?@[\\]^_`{|}~]')
    #return regex2.sub('', regex1.sub('', words))
    return regex.sub('', words)

def getClusterTfIdf(comments, tag_num=10, return_weight=False):
    return jieba.analyse.extract_tags(comments, topK=tag_num, withWeight=return_weight)

def findRole(seg_comment, *args):
    roles = args[0]
    first_role = next((word for word in seg_comment if word in roles.tolist()), None)
    return first_role if first_role is not None else False

def removeCenter2(df):
    #if df['center'] not in df['seg_comment']:
    #print(df['center'], ':', type(df['center']), '\t', df['seg_comment'], ':', type(df['seg_comment']), '\tis in?', df['center'] in df['seg_comment'])
    resp = [x for x in df['seg_comment'] if x != df['center']]
    #print(type(df['seg_comment']), type(df['center']), type(resp))
    return [resp]
    resp = [x for x in df if x != center]
    print(center, resp)
    return resp

def removeCenter(df, args):
    center = args[0]
    print(center, df)
    return None
    resp = [x for x in df if x != center]
    print(center, resp)
    return resp

def findFirstAssocWord(words, *args):
    sorted_word_count_top = args[0]
    set_y = set(words)
    first_assoc_word = next((element for element in sorted_word_count_top if element[0] in set_y), None)
    return first_assoc_word[0] if first_assoc_word is not None else 'NO_ASSOC_WORD'

def copyMore(df):
    count = df['count']
    comment = df['origin_comment']
    return ',  '.join([comment[:]] * count)

def calculateTfIdf(comments, word_size):
    return jieba.analyse.extract_tags(comments, topK=word_size, withWeight=True)

def chopTail(comment):
    searchObj = re.search( r'([a-z0-9]+-)+[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+(.*)', comment, re.M|re.I)
    if searchObj.span() is None:
        print(comment)
    return comment[:searchObj.start()]

def chopTail2(comments):
    resp = []
    for c in comments:
        searchObj = re.search( r'([a-z0-9]+-)+[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]+(.*)', c, re.M|re.I)
        if searchObj is None:
            print(c)
        else:
            resp.append(c[:searchObj.start()])
    return resp
