import os.path
from flask import Flask, escape, request, send_from_directory
from flask_autoindex import AutoIndex
from environs import Env
import subprocess
import demjson
import requests
import tempfile
import json
from flask_cors import CORS
env = Env()
env.read_env()

app = Flask(__name__)
CORS(app)
AutoIndex(app, browse_root=os.path.curdir)


def form_to_ini(form):
    """Take the form submitted and convert it to an INI file."""
    ini_dict = {}

    for k in form.keys():
        v = form[k]
        sec_key = k.split(':')
        if len(sec_key) != 2:
            continue
        if not sec_key[0] in ini_dict:
            ini_dict[sec_key[0]] = {sec_key[1]: v}
        else:
            ini_dict[sec_key[0]][sec_key[1]] = v

    ini = ''
    for (k, v) in ini_dict.items():
        ini = ini + '[%s]\n' % k
        for (k2, v2) in v.items():
            ini = ini + '%s = %s\n' % (k2, v2)

    return ini


def dict_to_binary(the_dict):
    str = json.dumps(the_dict)
    binary = ' '.join(format(ord(letter), 'b') for letter in str)
    return binary


@app.route('/status/<string:target>')
def show_target(target):
    return send_from_directory(target, 'progress.json')


@app.route('/winddata/pull', methods=['POST'])
def import_wind_data():
    requestJson = request.get_json(force=True)
    file_name = 'PROGRESS_{0}_{1}_{2}'.format(
                requestJson['launch-site:timestamp'],
                requestJson['launch-site:latitude'],
                requestJson['launch-site:longitude']
    )

    subprocess.Popen(
        (['python2', './predict.py', '--cd=./', '--fork', '--alarm', '-v', '-p1', '-f5', '--latdelta=2', '--londelta=2',
            '-t {0}'.format(requestJson['launch-site:timestamp']),
            '--lat={0}'.format(requestJson['launch-site:latitude']),
            '--lon={0}'.format(requestJson['launch-site:longitude']),
            file_name
          ]),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE
    )

    output_dict = {
        'log': 'Request sent',
        'output': file_name
    }
    output_json = demjson.encode(output_dict)
    return output_json


@app.route('/predict', methods=['POST'])
def get_prediction():
    requestJson = request.get_json(force=True)
    ini = form_to_ini({
        'launch-site:latitude': requestJson['launch-site:latitude'],
        'launch-site:longitude': requestJson['launch-site:longitude'],
        'launch-site:altitude': requestJson['launch-site:altitude'],
        'launch-site:timestamp': requestJson['launch-site:timestamp'],
        'atmosphere:wind-error': requestJson['atmosphere:wind-error'],
        'altitude-model:ascent-rate': requestJson['altitude-model:ascent-rate'],
        'altitude-model:descent-rate': requestJson['altitude-model:descent-rate'],
        'altitude-model:burst-altitude': requestJson['altitude-model:burst-altitude']
    })

    pred_process = subprocess.Popen(
        (['./pred_src/pred', '-v', '-i', './gfs/']),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    (output, log) = pred_process.communicate(bytes(ini))

    parsed_output = []
    for output_line in output.decode('utf-8').split('\n'):
        if len(output_line) == 0:
            continue

        output_fields = output_line.rstrip().split(',')
        if len(output_fields) < 2:
            continue

        parsed_output.append(output_fields)

    output_dict = {
        'log': filter(lambda x: x.rstrip(), log.decode('utf-8').split('\n')),
        'output': parsed_output
    }
    output_json = demjson.encode(output_dict)

    return output_json


if __name__ == "__main__":
    app.run(debug=False, port=env("PORT", 5000), host='0.0.0.0')
