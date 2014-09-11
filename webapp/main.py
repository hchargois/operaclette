#!/usr/bin/env python3
from flask import Flask, render_template, jsonify
from flask.json import JSONEncoder
from werkzeug.local import LocalProxy
from pymongo import MongoClient
from datetime import datetime
import config

app = Flask(__name__)
db = MongoClient(config.MONGO_URL)[config.MONGO_DBNAME]

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.isoformat()
            else:
                iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)

app.json_encoder = CustomJSONEncoder


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/json/spectacles.json')
def spectacles_json():
    spectacles = db.spectacles.find()
    res = []
    for s in spectacles:
        del s['_id']
        res.append(s)
    return jsonify(spectacles=res)

@app.route('/json/details/<path:name_id>.json')
def details_json(name_id):
    s = db.spectacles.find_one({"name_id": name_id})
    rs = db.representations.find({"spectacle_id": s['_id']})
    r_res = []
    for r in rs:
        del r['_id']
        del r['spectacle_id']
        r['day_in_week'] = r['date'].isoweekday()
        r_res.append(r)
    del s['_id']
    result = {"details": {
        "spectacle": s,
        "representations": r_res,
    }}
    return jsonify(result)

if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0", port=8080)
