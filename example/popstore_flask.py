from textwrap import indent
from flask import Flask, render_template, Response, request, redirect, stream_with_context
from popstore.popstore import popstore
import json
import inspect
import time
from datetime import datetime
from metapensiero.pj.api import translates
import random

app = Flask(__name__)
Popstore = popstore(ip='127.0.0.1')
blist = ["home", "create_bunch", "delete_bunch", "add", "edit", "delete", "find", "wh_worker", "RTViewer"]

""" Real Time Report Pre-Set Data"""
foldertext = 'c:/popstore'
ipentry = '127.0.0.1'
wh = {}
rt_status = "ready"

def rt_Server_launcher(param):
    print("RT Server Running")
    return "RT Server Running"

def rt_launcher(func, func_args):
    print(Popstore.set_whdata(func, func_args))
    pass 

def init_sys():
    global Popstore
    Popstore.set_addr(ipentry)
    info = Popstore.get_info()
    if info is None:
        return False
    wh_obj = json.loads(info)
    for wh_i in wh_obj['result']:
        wh[wh_i['wi_name']] = {}
        wh[wh_i['wi_name']]['warehouse_id'] = wh_i['warehouse_id']
        wh[wh_i['wi_name']]['line'] = {}
        wh[wh_i['wi_name']]['line']['MS'] = {}
        
        wh[wh_i['wi_name']]['line']['rxS'] = {}
        wh[wh_i['wi_name']]['line']['txS'] = {}
        wh[wh_i['wi_name']]['line']['CPU'] = {}
        wh[wh_i['wi_name']]['Done'] = 0
        wh[wh_i['wi_name']]['val'] = {}

    wi_count = str(len(wh_obj['result']))+"[EA] Nodes"
    print(wh_obj)
    
    print(rt_launcher(rt_Server_launcher, "run_rt"))
    return True

def parse_val(val):
    if val == 'Queue is empty':
        return None
    else:
        val = val[1:-2]
        val = val.replace("'", "")
        val = val.replace("c:", "")
        obj = val.split(",")
        ret = {}
        for item in obj:
            item = item.strip()
            item = item.split(":")
            if item[0] == 'time':
                item[1] = ":".join(item[1:])
            ret[item[0]] = item[1]
        return ret
        # print("done")
    pass
def wh_match(str):
    global wh
    for wh_name in wh:
        if str.find(wh_name) > -1:
            return wh_name
    return
def rt_draw():
    global Popstore
    global wh
    try:
        if Popstore.scan_item.is_empty() is True:
            return None
        while True:
            if Popstore.scan_item.is_empty() is not True:
                val = Popstore.scan_item.deQueue()
                ret_obj = parse_val(val)
                if ret_obj is not None:
                    wh_name = wh_match(ret_obj['path'])
                    wh[wh_name]['Done'] = 1
                    wh_i = wh[wh_name]
                    date_str = datetime.strptime(ret_obj['time'], '%Y:%m:%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                    for idx in wh_i['line']:
                        wh_i['line'][idx][date_str] = ret_obj[idx]
                        pass
            else:
                break
    except:
        print("Abnormally Thread stop.")
    pass

def rt_run():
    global Popstore
    global wh
    dir = foldertext
    if Popstore.rt_stat != "Running":
        if init_sys() is True:
            time.sleep(0.5)
            ret = Popstore.rt_set(dir)
            if ret != "":
                print("RT Set Error")
            else:
                
                    Popstore.scan_start_iter(rt_draw)
                    Popstore.rt_stat = "Running"
                    rt_status == "Running"
        else:
            print("System INIT Error")
    else:
        Popstore.scan_stop()
    return
rt_run()

@app.route('/')
@app.route('/home')
def hello_world():
    wh_list = json.loads(Popstore.get_info())['result']
    bunch_list = json.loads(Popstore.get_bunch_list())['result']
    wh_count = len(wh_list)
    return render_template(
				'index.html',
				title     = 'Popstore FLASK Hello',
				wh_count  = wh_count,
				button_list = blist,
                bunch_list = bunch_list,
				wh_list = json.dumps(wh_list, indent=2)
			)

@app.route('/edit')
@app.route('/delete')
def notice_page():
    return render_template(
				'notice_page.html',
				title     = 'Popstore Notice Page',
				button_list = blist,
                comments = 'This function supported by "Find" function.'
			)
@app.route('/create_bunch', methods = ['POST', 'GET'])
def create_bunch():
    if request.method == 'POST':
        bn = request.form['bunch_name']
        ret = Popstore.create_bunch(bn)
        if json.loads(ret)['result'] == '1':
            ret = 'Created <"'+bn+'">'
        else:
            ret = 'Error create bunch <"'+bn+'">'

        bunch_list = json.loads(Popstore.get_bunch_list())['result']
        return render_template(
                    'create_bunch.html',
                    title     = 'Create Bunch',
                    button_list = blist,
                    comments     = ret,
                    bunch_list = bunch_list
        )
    else:
        bunch_list = json.loads(Popstore.get_bunch_list())['result']
        return render_template(
                    'create_bunch.html',
                    title     = 'Create Bunch',
                    button_list = blist,
                    comments     = '',
                    bunch_list = bunch_list
        )
@app.route('/delete_bunch', methods = ['POST', 'GET'])
def delete_bunch():
    if request.method == 'POST':
        bn = request.form['del_bunch_name']
        ret = Popstore.delete_bunch(bn)
        if json.loads(ret)['result'] == '1':
            ret = 'Deleted <"'+bn+'">'
        else:
            ret = 'Error delete bunch <"'+bn+'">'

        bunch_list = json.loads(Popstore.get_bunch_list())['result']
        return render_template(
                    'delete_bunch.html',
                    title     = 'Delete Bunch',
                    button_list = blist,
                    comments     = ret,
                    bunch_list = bunch_list
        )
    else:
        bunch_list = json.loads(Popstore.get_bunch_list())['result']
        return render_template(
                    'delete_bunch.html',
                    title     = 'Delete Bunch',
                    button_list = blist,
                    comments     = '',
                    bunch_list = bunch_list
        )
@app.route('/add', methods = ['POST', 'GET'])
def add_item():
    if request.method == 'POST':
        bn = request.form['add_bunch_name']
        item_txt = request.form['item_text']
        item = {}
        item['key'] = "value"
        format_str = json.dumps(item, indent=2)
        if bn == '':
            format_str = item_txt
            ret = 'Error bunch name missed.'
        else:
            try:
                item_obj = json.loads(item_txt)
                ret = Popstore.add_item(bn, item_obj)
                hash = json.loads(ret)['result']
                if len(hash) == 64:
                    ret = 'Add Item <"'+hash+'"> : '+json.dumps(item_obj,  indent=2)[:30]
                    format_str = json.dumps(item_obj, indent=2)
                else:
                    ret = 'Error Add Item <"'+json.dumps(item_obj,  indent=2)[:30]+'">'
            except Exception as e:
                format_str = item_txt
                ret = 'Error : '+ str(e)
        
        bunch_list = json.loads(Popstore.get_bunch_list())['result']
        return render_template(
                    'add_item.html',
                    title     = 'Add Item',
                    button_list = blist,
                    comments     = ret,
                    format_str  = format_str,
                    bunch_list = bunch_list
        )
    else:
        bunch_list = json.loads(Popstore.get_bunch_list())['result']
        item = {}
        item['key'] = "value"
        return render_template(
                    'add_item.html',
                    title     = 'Add Item',
                    button_list = blist,
                    comments     = '',
                    format_str  = json.dumps(item, indent=2),
                    bunch_list = bunch_list
        )

def find_func(db_item, param):
    return None

@app.route('/find', methods = ['POST', 'GET'])
def find_item():
    if request.method == 'POST':
        bn = request.form['find_bunch_name']
        iterator_text = request.form['iterator_text']
        Parameter = request.form['Parameter']
        selected_item = request.form['selected_item']
        ret = ''
        if selected_item != "":
            mode, hash, item = selected_item.split("::")
            return redirect("/edit_del", code=307)
            edit_del(hash=hash, mode=mode, item=item)
            # if mode == "del":
                
                # ret = json.loads(Popstore.delete_item(bunch=bn,hash_key=hash))['result']
                # if ret == "1":
                #     ret = "<"+hash+"> deleted."
                # else:
                #     ret = "<"+hash+"> delete fail."
        bunch_list = json.loads(Popstore.get_bunch_list())['result']
        format_str = inspect.getsource(find_func)
        ret_list = []
        if bn == '':
            format_str = iterator_text
            ret = 'Error bunch name missed.'
        else:
            try:
                js_func_str = translates(iterator_text)
                ret_find = Popstore.find_item_inline(bn, find_func, Parameter, js_func_str[0])
                ret_list = json.loads(ret_find)['result']
                format_str = iterator_text
                ret = ret
            except Exception as e:
                ret = 'Error : '+ str(e)
        return render_template(
                    'find_item.html',
                    title     = 'Find Item',
                    button_list = blist,
                    comments     = ret,
                    format_str = format_str,
                    ret_list = ret_list,
                    bn = bn,
                    bunch_list = bunch_list
        )
    else:
        bunch_list = json.loads(Popstore.get_bunch_list())['result']
        format_str = inspect.getsource(find_func)
        return render_template(
                    'find_item.html',
                    title     = 'Find Item',
                    button_list = blist,
                    comments     = '',
                    format_str = format_str,
                    ret_list = [],
                    bn = "",
                    bunch_list = bunch_list
        )
@app.route('/edit_del', methods = ['POST', 'GET'])
def edit_del():
    try:
        bn = request.form['find_bunch_name']
        Parameter = request.form['Parameter']
        iterator_text = request.form['iterator_text']
        selected_item = request.form['selected_item']
        mode, hash, item = selected_item.split("::")
        comments     = ''
    except:
        bn = request.form['edit_del_bunch_name']
        mode = request.form['mode_post']
        item = request.form['item_post']
        hash = request.form['hash_post']
        comments     = mode+" - ["+hash+"]"
        if mode == "Edit Item":
            item = request.form['item_text']
            if type(item) is str:
                object_item = json.loads(item)
                ret = json.loads(Popstore.edit_item(bunch=bn,hash_key=hash, item=object_item))['result']
            else:
                ret = json.loads(Popstore.edit_item(bunch=bn,hash_key=hash, item=item))['result']
            if ret != "1":
                comments = "Fail : "+comments
        else:
            ret = json.loads(Popstore.delete_item(bunch=bn,hash_key=hash))['result']
            if ret != "1":
                comments = "Fail : "+comments


    return render_template(
                    'edit_del.html',
                    title     = mode+' Item',
                    button_list = blist,
                    bn = bn,
                    comments     = comments,
                    hash = hash,
                    item = json.dumps(json.loads(item), indent=2)
        )
@app.route('/wh_worker', methods = ['POST', 'GET'])
def wh_worker():
    wh_list = json.loads(Popstore.get_info())['result']
    bunch_list = json.loads(Popstore.get_bunch_list())['result']
    wh_count = len(wh_list)
    return render_template(
				'index.html',
				title     = 'Popstore FLASK Hello',
				wh_count  = wh_count,
				button_list = blist,
                bunch_list = bunch_list,
				wh_list = json.dumps(wh_list, indent=2)
			)


@app.route('/chart-data')
def chart_data():
    def generate_random_data():
        while True:
            item = {}
            # item['MS'] = {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': random.random() * 100}
            # item['CPU'] = {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': random.random() * 100}
            # item['rxS'] = {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': random.random() * 100}
            # item['txS'] = {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': random.random() * 100}
            pos = 0
            date_str = ""
            for idx in wh:
                if date_str == "":
                    keys = list(wh[idx]['line']['MS'].keys())
                    if len(keys) == 0:
                        break
                    date_str = list(wh[idx]['line']['MS'].keys())[0]
                item[idx] = {}
                item[idx]['MS'] = {'time':date_str, 'value':wh[idx]['line']['MS'][date_str]}
                item[idx]['CPU'] = {'time':date_str, 'value':wh[idx]['line']['CPU'][date_str]}
                item[idx]['rxS'] = {'time':date_str, 'value':wh[idx]['line']['rxS'][date_str]}
                item[idx]['txS'] = {'time':date_str, 'value':wh[idx]['line']['txS'][date_str]}
                del wh[idx]['line']['MS'][date_str]
                pos += 1
            json_data = json.dumps(item)
            yield f"data:{json_data}\n\n"
            time.sleep(1)

    response = Response(stream_with_context(generate_random_data()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response

@app.route('/RTViewer', methods = ['POST', 'GET'])
def RTViewer():
    # if rt_status == "ready":
    
    return render_template(
				'RTViewer.html',
				title     = 'Popstore Realtime Report',
                wh_info = json.dumps(wh),
				button_list = blist
			)
if __name__ == '__main__':
    app.run()