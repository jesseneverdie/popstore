from textwrap import indent
from flask import Flask, render_template, request, redirect
from popstore.popstore import popstore
import json
import inspect
from metapensiero.pj.api import translates

app = Flask(__name__)
popstore = popstore(ip='127.0.0.1')
@app.route('/')
@app.route('/home')
def hello_world():
    wh_list = json.loads(popstore.get_info())['result']
    bunch_list = json.loads(popstore.get_bunch_list())['result']
    wh_count = len(wh_list)
    return render_template(
				'index.html',
				title     = 'popstore FLASK Hello',
				wh_count  = wh_count,
				button_list = ["home", "create_bunch", "delete_bunch", "add", "edit", "delete", "find"],
                bunch_list = bunch_list,
				wh_list = json.dumps(wh_list, indent=2)
			)

@app.route('/edit')
@app.route('/delete')
def notice_page():
    return render_template(
				'notice_page.html',
				title     = 'popstore Notice Page',
				button_list = ["home", "create_bunch", "delete_bunch", "add", "find"],
                comments = 'This function supported by "Find" function.'
			)
@app.route('/create_bunch', methods = ['POST', 'GET'])
def create_bunch():
    if request.method == 'POST':
        bn = request.form['bunch_name']
        ret = popstore.create_bunch(bn)
        if json.loads(ret)['result'] == '1':
            ret = 'Created <"'+bn+'">'
        else:
            ret = 'Error create bunch <"'+bn+'">'

        bunch_list = json.loads(popstore.get_bunch_list())['result']
        return render_template(
                    'create_bunch.html',
                    title     = 'Create Bunch',
                    button_list = ["home", "create_bunch", "delete_bunch", "add", "edit", "delete", "find"],
                    comments     = ret,
                    bunch_list = bunch_list
        )
    else:
        bunch_list = json.loads(popstore.get_bunch_list())['result']
        return render_template(
                    'create_bunch.html',
                    title     = 'Create Bunch',
                    button_list = ["home", "create_bunch", "delete_bunch", "add", "edit", "delete", "find"],
                    comments     = '',
                    bunch_list = bunch_list
        )
@app.route('/delete_bunch', methods = ['POST', 'GET'])
def delete_bunch():
    if request.method == 'POST':
        bn = request.form['del_bunch_name']
        ret = popstore.delete_bunch(bn)
        if json.loads(ret)['result'] == '1':
            ret = 'Deleted <"'+bn+'">'
        else:
            ret = 'Error delete bunch <"'+bn+'">'

        bunch_list = json.loads(popstore.get_bunch_list())['result']
        return render_template(
                    'delete_bunch.html',
                    title     = 'Delete Bunch',
                    button_list = ["home", "create_bunch", "delete_bunch", "add", "edit", "delete", "find"],
                    comments     = ret,
                    bunch_list = bunch_list
        )
    else:
        bunch_list = json.loads(popstore.get_bunch_list())['result']
        return render_template(
                    'delete_bunch.html',
                    title     = 'Delete Bunch',
                    button_list = ["home", "create_bunch", "delete_bunch", "add", "edit", "delete", "find"],
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
                ret = popstore.add_item(bn, item_obj)
                hash = json.loads(ret)['result']
                if len(hash) == 64:
                    ret = 'Add Item <"'+hash+'"> : '+json.dumps(item_obj,  indent=2)[:30]
                    format_str = json.dumps(item_obj, indent=2)
                else:
                    ret = 'Error Add Item <"'+json.dumps(item_obj,  indent=2)[:30]+'">'
            except Exception as e:
                format_str = item_txt
                ret = 'Error : '+ str(e)
        
        bunch_list = json.loads(popstore.get_bunch_list())['result']
        return render_template(
                    'add_item.html',
                    title     = 'Add Item',
                    button_list = ["home", "create_bunch", "delete_bunch", "add", "edit", "delete", "find"],
                    comments     = ret,
                    format_str  = format_str,
                    bunch_list = bunch_list
        )
    else:
        bunch_list = json.loads(popstore.get_bunch_list())['result']
        item = {}
        item['key'] = "value"
        return render_template(
                    'add_item.html',
                    title     = 'Add Item',
                    button_list = ["home", "create_bunch", "delete_bunch", "add", "edit", "delete", "find"],
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
                
                # ret = json.loads(popstore.delete_item(bunch=bn,hash_key=hash))['result']
                # if ret == "1":
                #     ret = "<"+hash+"> deleted."
                # else:
                #     ret = "<"+hash+"> delete fail."
        bunch_list = json.loads(popstore.get_bunch_list())['result']
        format_str = inspect.getsource(find_func)
        ret_list = []
        if bn == '':
            format_str = iterator_text
            ret = 'Error bunch name missed.'
        else:
            try:
                js_func_str = translates(iterator_text)
                ret_find = popstore.find_item_inline(bn, find_func, Parameter, js_func_str[0])
                ret_list = json.loads(ret_find)['result']
                format_str = iterator_text
                ret = ret
            except Exception as e:
                ret = 'Error : '+ str(e)
        return render_template(
                    'find_item.html',
                    title     = 'Find Item',
                    button_list = ["home", "create_bunch", "delete_bunch", "add", "edit", "delete", "find"],
                    comments     = ret,
                    format_str = format_str,
                    ret_list = ret_list,
                    bn = bn,
                    bunch_list = bunch_list
        )
    else:
        bunch_list = json.loads(popstore.get_bunch_list())['result']
        format_str = inspect.getsource(find_func)
        return render_template(
                    'find_item.html',
                    title     = 'Find Item',
                    button_list = ["home", "create_bunch", "delete_bunch", "add", "edit", "delete", "find"],
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
                ret = json.loads(popstore.edit_item(bunch=bn,hash_key=hash, item=object_item))['result']
            else:
                ret = json.loads(popstore.edit_item(bunch=bn,hash_key=hash, item=item))['result']
            if ret != "1":
                comments = "Fail : "+comments
        else:
            ret = json.loads(popstore.delete_item(bunch=bn,hash_key=hash))['result']
            if ret != "1":
                comments = "Fail : "+comments


    return render_template(
                    'edit_del.html',
                    title     = mode+' Item',
                    button_list = ["home", "create_bunch", "delete_bunch", "add", "edit", "delete", "find"],
                    bn = bn,
                    comments     = comments,
                    hash = hash,
                    item = json.dumps(json.loads(item), indent=2)
        )
if __name__ == '__main__':
    app.run()