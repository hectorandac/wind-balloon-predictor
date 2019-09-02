from flask import Flask, escape, request, send_from_directory
import subprocess
import demjson
import requests
import tempfile
import json

app = Flask(__name__)

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
    file_name = 'PROGRESS_{0}_{1}_{2}'.format(
                request.form['launch-site:timestamp'],
                request.form['launch-site:latitude'],
                request.form['launch-site:longitude']
            )

    subprocess.Popen(
        (['python', './predict.py', '--cd=./', '--fork', '--alarm', '-v', '-p1', '-f5', '--latdelta=2', '--londelta=2',
            '-t {0}'.format(request.form['launch-site:timestamp']),
            '--lat={0}'.format(request.form['launch-site:latitude']),
            '--lon={0}'.format(request.form['launch-site:longitude']),
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
    ini = form_to_ini({
        'launch-site:latitude': request.form['launch-site:latitude'],
        'launch-site:longitude': request.form['launch-site:longitude'],
        'launch-site:altitude': request.form['launch-site:altitude'],
        'launch-site:timestamp': request.form['launch-site:timestamp'],
        'atmosphere:wind-error': request.form['atmosphere:wind-error'],
        'altitude-model:ascent-rate': request.form['altitude-model:ascent-rate'],
        'altitude-model:descent-rate': request.form['altitude-model:descent-rate'],
        'altitude-model:burst-altitude': request.form['altitude-model:burst-altitude']
    })

    pred_process = subprocess.Popen(
        (['./pred_src/pred', '-v', '-i', './gfs/']),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    (output, log) = pred_process.communicate(bytes(ini, 'utf-8'))

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
    app.run()