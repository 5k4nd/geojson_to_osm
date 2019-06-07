# coding: utf-8

import dateutil.parser
import glob
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, send_file
from os import mkdir, remove, system
from uuid import uuid1


app = Flask(__name__)
DEBUG = True
app.config.from_object(__name__)
app.config['SECRET_KEY'] = ''

try:
    mkdir('tmp')
except FileExistsError:
    pass


def convert(geojson):
    uid = str(uuid1())[:8]
    dt_now = datetime.now().replace(microsecond=0).isoformat()
    geojson_path = 'tmp/{}_{}.geojson'.format(uid, dt_now)
    osm_path = 'tmp/{}_{}.osm'.format(uid, dt_now)
    with open(geojson_path, 'w') as f:
        f.write(geojson)
    system('ogr2osm/ogr2osm.py {} -o {}'.format(geojson_path, osm_path))
    with open(osm_path) as f:
        osm_xml = f.read()
    return uid, osm_path, osm_xml

def clean_tmp():
    """ Clean old tmp files at the beginning of each call as we can't do this at the end of a call. """
    one_hour_ago = datetime.now() - timedelta(hours=1)
    files = glob.glob('tmp/*')
    for f in files:
        f_raw_dt = f.split('_')[1].split('.')[0]
        f_dt = dateutil.parser.parse(f_raw_dt)
        if f_dt < one_hour_ago:
            remove(f)


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        clean_tmp()
        try:
            geojson_entry = request.form.get('geojson_entry')
            json.loads(geojson_entry)
            uid, osm_path, osm_xml = convert(geojson_entry)
            return send_file(osm_path, 
                mimetype='application/XML',
                as_attachment=True,
                attachment_filename='{}.osm'.format(uid)
            )
        except ValueError:
            return 'Invalid GeoJSON file. Please <a href="">try again</a>.'
        except Exception as e:
            print(e)
            return 'An error occured while converting your file. Please <a href="/">try again</a> or contact me at baptiste[dot]abel[arob]baptabl[dot]fr'
    return render_template('index.html')

