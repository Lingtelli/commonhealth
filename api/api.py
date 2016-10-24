# -*- coding: utf-8 -*-
import sys, os, inspect
from flask import Flask, request, send_from_directory
from flask_restful import Resource, Api, reqparse
from flask_cors import CORS, cross_origin
import json
from operator import itemgetter

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

app = Flask(__name__, static_folder='/home/jlsche/Lingtelli/commonhealth/api/')
api = Api(app)
CORS(app)
parser = reqparse.RequestParser()
parser.add_argument('disease')

#'''
data = open('origin_new_output.json', encoding='utf-8')
json_list = json.load(data)
data.close()


def calculateScore(keywords, target, bonus):
    # Filtering a list based on a list of booleans
    mask = [word in target for word in keywords]
    matched = [k for (k, m) in zip(keywords, mask) if m]
    keywords = [x for x in keywords if x not in matched]
    score = len(matched) * bonus
    return score, keywords

def queryDisease(_keywords):
    matched = []
    for _json in json_list:
        keywords = _keywords[:]
        type_score, keywords = calculateScore(keywords, ''.join(_json['types']), 30)
        keyword_score, keywords = calculateScore(keywords, _json['keywords'], 100)
        score = type_score + keyword_score
        
        if len(keywords) > 0:
            content = ''
            for member in _json['member']:
                content += member['content']
            content_score, keywords = calculateScore(keywords, content, 2)
            score += content_score

        if len(keywords) == 0:
            matched.append((_json, score))
     
    sorted_matched = sorted(matched, key=itemgetter(1), reverse=True)
    sorted_matched = [j[0] for j in sorted_matched]
    return json.dumps(sorted_matched, ensure_ascii=False)
    

output_filename = './cluster_result0.json'
class Task(Resource):
    def post(self):
        args = parser.parse_args(strict=True)
        keywords = args['disease']
        print(keywords)
        print(type(keywords.split(' ')))
        return queryDisease(keywords.split(' '))
        #return send_from_directory(app.static_folder, output_filename)
api.add_resource(Task, '/')

if __name__ == '__main__':
    app.run(host='192.168.10.116', port=5011, debug=True)
