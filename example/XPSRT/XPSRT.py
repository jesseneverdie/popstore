from textwrap import indent
from flask import Flask, render_template, Response, request, redirect, stream_with_context
from popstore.popstore import popstore
import json
import inspect
import time
from datetime import datetime, timedelta
from metapensiero.pj.api import translates

app = Flask(__name__)
Pops = popstore(ip='127.0.0.1')
blist = ["home"]

""" Real Time Report Pre-Set Data"""
foldertext = 'c:/popstore'
ipentry = '127.0.0.1'
wh = {}
rt_status = "ready"

def rt_Server_launcher(param):
    print("RT Server Running")
    return "RT Server Running"

def rt_launcher(func, func_args):
    print(Pops.set_whdata(func, func_args))
    pass 

def init_sys():
    global Pops
    Pops.set_addr(ipentry)
    info = Pops.get_info()
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
    global Pops
    global wh

    try:
        if Pops.scan_item.is_empty() is True:
            return None
        while True:
            if Pops.scan_item.is_empty() is not True:
                val = Pops.scan_item.deQueue()
                ret_obj = parse_val(val)
                if ret_obj is not None:
                    wh_name = wh_match(ret_obj['path'])
                    wh[wh_name]['Done'] = 1
                    wh_i = wh[wh_name]
                    date_str = datetime.strptime(ret_obj['time'], '%Y:%m:%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                    for idx in wh_i['line']:
                        wh_i['line'][idx][date_str] = ret_obj[idx]
                        for idx in wh_i['line']:
                            if len(wh_i['line'][idx]) > 180:
                                key = list(wh_i['line'][idx].keys())[0]
                                del wh_i['line'][idx][key]
                                # print(wh_name+":"+idx+":"+key)
                            # print(wh_name+":"+idx+":"+str(len(wh_i['line'][idx])))
            else:
                break
    except:
        print("Abnormally Thread stop.")


    return None

def rt_run():
    global Pops
    global wh
    dir = foldertext
    if Pops.rt_stat != "Running":
        if init_sys() is True:
            time.sleep(0.4)
            ret = Pops.rt_set(dir)
            if ret != "":
                print("RT Set Error")
            else:
                
                    Pops.scan_start_iter(rt_draw)
                    Pops.rt_stat = "Running"
                    rt_status == "Running"
        else:
            print("System INIT Error")
    else:
        Pops.scan_stop()
    return
rt_run()

@app.route('/chart-data')
def chart_data():
    def read_rt_data():
        session = {}
        session['id'] = datetime.now().timestamp()
        session['date_str'] = ""
        while True:
            item = {}
            del_flag = True
            for idx in wh:
                if session['date_str'] == "":
                    keys = list(wh[idx]['line']['MS'].keys())
                    if len(keys) == 0:
                        break
                    session['date_str'] = list(wh[idx]['line']['MS'].keys())[0]

                item[idx] = {}
                
                try:
                    item[idx]['MS'] = {'time':session['date_str'].split(" ")[1], 'value':wh[idx]['line']['MS'][session['date_str']]}
                    item[idx]['CPU'] = {'time':session['date_str'].split(" ")[1], 'value':wh[idx]['line']['CPU'][session['date_str']]}
                    item[idx]['rxS'] = {'time':session['date_str'].split(" ")[1], 'value':wh[idx]['line']['rxS'][session['date_str']]}
                    item[idx]['txS'] = {'time':session['date_str'].split(" ")[1], 'value':wh[idx]['line']['txS'][session['date_str']]}
                    
                except:
                    item = {}
                    del_flag = False
                    # print("Drop action")
                    break
            if del_flag == True and session['date_str'] != "":
                json_data = json.dumps(item)
                yield f"data:{json_data}\n\n"
                newtime = datetime.strptime(session['date_str'], '%Y-%m-%d %H:%M:%S')
                newtime = newtime + timedelta(seconds=1)
                newtime = newtime.strftime('%Y-%m-%d %H:%M:%S')
                # print(str(session['id'])+"::"+ newtime)
                session['date_str'] = newtime
                time.sleep(0.1)
            else:
                time.sleep(0.8)

    response = Response(stream_with_context(read_rt_data()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response

@app.route('/')
@app.route('/home')
def hello_world():
    wh_list = json.loads(Pops.get_info())['result']
    for idx in wh_list:
        ipport = idx['warehouse_id'].split(":")
        idx['ip'] = ipport[0]
        idx['port'] = ipport[1]
    bunch_list = json.loads(Pops.get_bunch_list())['result']
    wh_count = len(wh_list)
    return render_template(
				'home.html',
				title     = 'Popstore RT Monitor',
				wh_count  = wh_count,
				button_list = blist,
                bunch_list = bunch_list,
				wh_info = json.dumps(wh),
				wh_list = wh_list,
				wh_list_str = json.dumps(wh_list, indent=2)
			)
wh_ret_val = None
def get_wh_name():
    pass
def bunch_count(db_item, param):
    if wh_ret_val == None:
        wh_ret_val = {}
        wh_ret_val['wh_name'] = get_wh_name()
        wh_ret_val['count'] = 0
        wh_ret_val['data_size'] = 0
    wh_ret_val['count'] += 1
    return None

@app.route('/scan_bunch', methods = ['POST', 'GET'])
def scan_bunch():
    bunch_name = request.args.get('name')
    def get_data(bunch_name):
        
        iterator_text = inspect.getsource(bunch_count)
        ret = Pops.find_item_inline(bunch_name, bunch_count, "", translates(iterator_text)[0])
        try:
            json_data = json.loads(ret)['result']
            ret_item = []
            for idx in json_data:
                ret_item.append(idx['find_item'])
            json_data = json.dumps(ret_item)
        except:
            json_data = "Error."
        yield f"data:{json_data}\n\n"
    response = Response(get_data(bunch_name), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response
if __name__ == '__main__':
    app.run()