import datetime

from flask import Flask, Response, request, render_template
from pybadges import badge
from hashlib import md5
import requests
from os import environ
from dotenv import find_dotenv,load_dotenv
from PIL import Image
import os

load_dotenv(find_dotenv())

app = Flask(__name__)

# raw=[]
# for i in range(10):
#     raw.append(Image.open('pictures/' + str(i) + '.png'))
    
def invalid_count_resp(err_msg) -> Response:
    """
    Return a svg badge with error info when cannot process repo_id param from request
    :return: A response with invalid request badge
    """
    svg = badge(left_text="Error", right_text=err_msg,
                whole_link="https://github.com/jwenjian/visitor-badge")
    expiry_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)

    headers = {'Cache-Control': 'no-cache,max-age=0', 'Expires': expiry_time.strftime("%a, %d %b %Y %H:%M:%S GMT")}

    return Response(response=svg, content_type="image/svg+xml", headers=headers)


def update_counter(key):
    url = 'https://api.countapi.xyz/hit/visitor-badge/{0}'.format(key)
    try:
        resp = requests.get(url)
        if resp and resp.status_code == 200:
            return resp.json()['value']
        else:
            return None
    except Exception as e:
        return None


@app.route("/badge")
def visitor_svg() -> Response:
    """
    Return a svg badge with latest visitor count of 'Referer' header value

    :return: A svg badge with latest visitor count
    """

    req_source = identity_request_source()

    if not req_source:
        return invalid_count_resp('Missing required param: page_id')

    latest_count = update_counter(req_source)

    if not latest_count:
        return invalid_count_resp("Count API Failed")


    raw=[]
    for i in range(10):
        raw.append(Image.open('pictures/' + str(i) + '.png'))

    ll = len(str(latest_count))

    merge_Png = Image.new('RGB', (200*ll, 200))  # 创建一个新图
    # 横向拼接（因为是横向裁剪的，文件的顺序须保持一致）。x,y用来控制换行
    y = 0
    x = ll*200-200  # w = 480

    for i in range(ll):
        merge_Png.paste(raw[latest_count%10], (x, y))
        latest_count = int(latest_count/10)
        x -= 200
    merge_Png.save('merge.png')


    # svg = badge(left_text="visitors", right_text=str(latest_count))

    expiry_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)

    headers = {'Cache-Control': 'no-cache,max-age=0,no-store,s-maxage=0,proxy-revalidate',
               'Expires': expiry_time.strftime("%a, %d %b %Y %H:%M:%S GMT")}

    return Response(response=open('merge.png','rb'), content_type="image/png", headers=headers)


@app.route("/index.html")
@app.route("/index")
@app.route("/")
def index() -> Response:
    return render_template('index.html')


def identity_request_source() -> str:
    page_id = request.args.get('page_id')
    if page_id is not None and len(page_id):
        m = md5(page_id.encode('utf-8'))
        m.update(environ.get('md5_key').encode('utf-8'))
        return m.hexdigest()
    return None


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
