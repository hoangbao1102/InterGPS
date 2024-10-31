#!/usr/bin/env python3

import os
import base64
import requests
import json
import datetime
from random import Random
import hashlib

#
# Common module for calling Mathpix OCR service from Python.
#
# N.B.: Set your credentials in environment variables APP_ID and APP_KEY,
# either once via setenv or on the command line as in
# APP_ID=my-id APP_KEY=my-key python3 simple.py 
#

env = os.environ
SIMPLETEX_APP_ID = "........................................."
SIMPLETEX_APP_SECRET = "........................................."

def random_str(randomlength=16):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str += chars[random.randint(0, length)]
    return str


def get_req_data(req_data, appid, secret):
    header = {}
    header["timestamp"] = str(int(datetime.datetime.now().timestamp()))
    header["random-str"] = random_str(16)
    header["app-id"] = appid
    pre_sign_string = ""
    sorted_keys = list(req_data.keys()) + list(header)
    sorted_keys.sort()
    for key in sorted_keys:
        if pre_sign_string:
            pre_sign_string += "&"
        if key in header:
            pre_sign_string += key + "=" + str(header[key])
        else:
            pre_sign_string += key + "=" + str(req_data[key])

    pre_sign_string += "&secret=" + secret
    header["sign"] = hashlib.md5(pre_sign_string.encode()).hexdigest()
    return header, req_data
data = {
    'max_time':10,
}
default_headers, data = get_req_data(data, SIMPLETEX_APP_ID, SIMPLETEX_APP_SECRET)
service = 'https://server.simpletex.cn/api/latex_ocr_turbo/v2'
#
# Return the base64 encoding of an image with the given filename.
#
def latex(img_path, headers=default_headers):
    img_file = {"file": open(img_path, 'rb')}
    r = requests.post(service,files=img_file,data=data, headers=headers)
    return json.loads(r.text)
