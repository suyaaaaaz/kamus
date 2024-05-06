import os
from os.path import join, dirname
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, jsonify, request
from pymongo import MongoClient
from datetime import datetime
import requests
from bson import ObjectId

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)

db = client[DB_NAME]

app = Flask(__name__)


@app.route('/')
def index():
    words_result = db.kamus.find({}, {'_id': False})
    words = []
    # print(words)
    for word in words_result:
        definitions = word.get('definitions', [])
        # print(definitions)
        if definitions:
            first_definition = definitions[0].get('shortdef', [])
            if isinstance(first_definition, str) and first_definition.strip():
                definition_text = first_definition.strip()
            else:
                definition_text = 'No shortdef found'
        else:
            definition_text = 'No definition found'
        words.append({
            'word': word['word'],
            'definition': definition_text
        })
    msg = request.args.get('msg')
    return render_template('index.html', words=words, msg=msg)

@app.route('/error')
def error():
    return render_template('error.html',)

@app.route('/detail/<keyword>')
def detail(keyword):
    # print(keyword)
    api_key = '8d86122f-e55c-4654-9f5f-d13ef35631d9'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response =  requests.get(url)
    definitions = response.json()
    # print(definitions)
    
    if not definitions:
        return render_template(
            'errors.html',
            kata=keyword
        )
    if type(definitions[0]) == str:
        suggestions = definitions
        # print(suggestions)
        return render_template(
            'error.html',
            msg=suggestions, kata=keyword
        )
    
    status = request.args.get('status_give', 'new')
    return render_template('detail.html', word=keyword, definitions=definitions, status=status)

@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')

    

    doc = {
        'word' : word,
        'definitions' : definitions,
        'date': datetime.now().strftime('%y%m%d')
    }

    db.kamus.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'the word, {word}, was saved!!!',
    })

@app.route('/api/delete_word',methods=['POST'])
def delete_word():
    word = request.form.get('word_give')
    db.kamus.delete_one({'word': word})
    db.contoh.delete_many({'word':word})
    return jsonify({
        'result': 'success',
        'msg': f'the word {word} was deleted'
    })
    
@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word')
    example_data = db.contoh.find({'word': word})
    examples = []
    for example in example_data:
        examples.append({
            'example' : example.get('example'),
            'id' : str(example.get('_id')),
        })
    return jsonify({
        'result': 'success',
        'example' : examples,
        })

@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    word = request.form.get('word')
    example = request.form.get('example')
    doc = {
        'word' : word,
        'example' : example,
    }
    db.contoh.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg' : f'your example, {example}, was saved!'
        })


@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    db.contoh.delete_one({'_id': ObjectId(id)})
    return jsonify({
        'result': 'success',
        'msg' : f'the word, {word}, was deleted'
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
 