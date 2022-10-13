#-*- coding: utf-8 -*-
# Copyright 2022 Jesse Kim <jesse@nextwith.com>
# "xPopcornStore Database Simple Driver for python"
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION
# OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import socket
import struct
import threading
import json
from time import localtime, strftime
import inspect
from metapensiero.pj.api import translates
import os, sys
import time
import dill

class CircularQueue:
    def __init__(self, k):
        self.q = [None] * k
        self.len = k
        self.front = 0
        self.rear = 0
    def enQueue(self, value):
        if self.q[self.rear] is None:
            self.q[self.rear] = value 
            self.rear = (self.rear + 1) % self.len 
            return True
        else:
            return False

    def deQueue(self):
        if self.q[self.front] is not None:
            result = self.q[self.front]
            self.q[self.front] = None
            self.front = (self.front + 1) % self.len
            return result
        else:
            return False

    def pr_front(self):
        return False if self.q[self.front] is None else self.q[self.front]

    def pr_rear(self):
        return False if self.q[self.rear] is None else self.q[self.rear]

    def is_empty(self):
        return self.q[self.front] == None and self.q[self.rear] == None

    def is_full(self):
        return None not in self.q

class popstore:
    """xPopcornStore Driver"""

    addr = ''
    port = 28734
    split_size = 32768
    client_socket = None
    timer = None
    scan_interval = 0.3
    function_point = None
    enabled_wh_count = 0
    wh_conn = []
    rt_stat = "Stop"
    scan_item = CircularQueue(100)
    base_str = """
            storekeeper_api = function() {
                ;
            }

            storekeeper_api.prototype = {
                __set_result : function(param)
                {
                    var ss_result = {};
                    ss_result["result"] = param;
                    var ret = JSON.stringify(ss_result);
                    pst_query_result(ret);
                },"""
    def __init__(self, ip = "127.0.0.1", port = 28734, split_size = 32768, scan=False):
        self.addr = ip
        self.port = port
        self.split_size = split_size
    def set_addr(self, ip = "127.0.0.1", port = 28734):
        self.addr = ip
        self.port = port
        pass
    def run(self, js_str):
        try:
            server_address = (self.addr, self.port)
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(server_address)
            self.client_socket.settimeout(100)

            recv_data = b""
            # make network packet
            contents = bytes(js_str,'UTF-8')          
            types = struct.pack('I', 1234)
            length = struct.pack('I', len(contents)+1)

            send_data = types
            send_data += length
            send_data += contents
            send_data += bytes('\0','UTF-8')

            # send data ( split chunk size )
            for i in range(0, len(send_data), self.split_size):
                self.client_socket.sendall(send_data[i:self.split_size+i])

            # receive data
            recv_data = b""

            while True:
                chunk = self.client_socket.recv(self.split_size)
                if chunk:
                    recv_data += chunk
                else:
                    break
        except:
            self.client_socket.close()
            return None
        finally:
            self.client_socket.close()
        return recv_data.decode('utf-8')
    
    def scan_run(self):
        start_time = time.time()
        for sock in self.wh_conn:
            message = "a"
            sock.send(message.encode())
            
            data = sock.recv(1024).decode()

            data = data.split("\n")
            if self.scan_item.is_full() == True:
                self.scan_item.deQueue()
            for item in data:
                if item != '':
                    self.scan_item.enQueue(item)
        end_time = time.time()
        # print("socket time = %f seconds..." % (end_time - start_time)) 
    def scan_stop(self):
        if self.timer != None:
            self.timer.cancel()
        self.function_point = None
        return True
    def set_scan_inverval(self, interval = 0.3):
        self.scan_interval = interval
        return True
    def scan_start_iter(self, f):
        self.function_point = f
        self.scan_start()
    def scan_start(self):
        self.timer = threading.Timer(self.scan_interval, self.scan_start)
        self.scan_run()
        if self.function_point != None:
            self.function_point()
        self.timer.start()
        return True
    def get_info(self):
        jsstr = self.base_str + """
            get_warehouse_infomation : function() 
                {
                    var wh_info = pst_warehouse_info();
                    this.__set_result(wh_info);
                }
            }
            var p = new storekeeper_api();
            p.get_warehouse_infomation();
            """
        ret = self.run(jsstr)
        return ret
    def add_item(self, bunch, item):
        if type(item) is not str:
            item = json.dumps(item)
        jsstr = self.base_str + """
            add_item : function(bunch_name, item) 
                {
                var add_keys = pst_add_item(bunch_name, item);
                //pst_log(add_keys);
                this.__set_result(add_keys);
                }
            }
            var p = new storekeeper_api();
            p.add_item('"""+bunch+"""','"""+item+"""');
            """
        ret = self.run(jsstr)
        return ret
    def get_bunch_list(self):
        jsstr = self.base_str + """
                bunch_list : function(bunch_name, item) 
                {
                    var bunch_list = pst_list_bunch();
                    for (bunch_idx in bunch_list)
                    {
                        pst_log(bunch_list[bunch_idx]);
                    }
                    this.__set_result(bunch_list)
                }
            }
            var p = new storekeeper_api();
            p.bunch_list();
            """
        ret = self.run(jsstr)
        return ret
    def edit_item(self, bunch, item, hash_key):
        if type(item) is not str:
            item = json.dumps(item)
        jsstr = self.base_str + """
                edit_item : function(bunch_name, item, hash_key)
                {
                    var ret_val = pst_edit_item(bunch_name, hash_key, item);
                    
                    this.__set_result(ret_val.toString());
                }
            }
            var p = new storekeeper_api();
            p.edit_item('"""+bunch+"""','"""+item+"""','"""+hash_key+"""');
            """
        ret = self.run(jsstr)
        return ret
    def delete_item(self, bunch, hash_key):
        jsstr = self.base_str + """
                delete_item : function(bunch_name, hash_key)
                {
                    var ret_val = pst_delete_item(bunch_name, hash_key);
                    
                    this.__set_result(ret_val.toString());
                }
            }
            var p = new storekeeper_api();
            p.delete_item('"""+bunch+"""','"""+hash_key+"""');
            """
        ret = self.run(jsstr)
        return ret
    def create_bunch(self, bunch_name):
        jsstr = self.base_str + """
                create_bunch : function(bunch_name)
                {
                    var ret_val = pst_create_bunch(bunch_name);
                    
                    this.__set_result(ret_val.toString());
                }
            }
            var p = new storekeeper_api();
            p.create_bunch('"""+bunch_name+"""');
            """
        ret = self.run(jsstr)
        return ret
    def delete_bunch(self, bunch_name):
        jsstr = self.base_str + """
                delete_bunch : function(bunch_name)
                {
                    var ret_val =  pst_delete_bunch(bunch_name);
                    
                    this.__set_result(ret_val.toString());
                }
            }
            var p = new storekeeper_api();
            p.delete_bunch('"""+bunch_name+"""');
            """
        ret = self.run(jsstr)
        return ret

    def get_func_str(self, func):
        func_name = func.__name__
        source=dill.source.getsource(func)
        file_name = inspect.getfile(func)
        print("file_name:"+file_name)
        try:
            codes = inspect.getsource(func)
            # print("codes:"+codes)
            path = sys._MEIPASS
            # print("_MEIPASS:"+path)
            js_func = translates(codes)[0]    #Using pyinstaller Any_source.py include

        except:
            # print("except:")

            codes = inspect.getsource(func)
            # print("codes:"+codes)
            js_func = translates(codes)[0]    #Using pyinstaller Any_source.py include      

        return js_func

    def find_item(self, bunch_name, func, func_args):
        func_name = func.__name__

        
        js_func = self.get_func_str(func)    #Using pyinstaller Any_source.py include
        # codes = inspect.getsource(func)
        # js_func = translates(codes)[0]    #Using pyinstaller Any_source.py include
        js_func = self.js_replace(js_func)
        if func_args is None:
            func_args = ""
        jsstr = self.base_str + """
            find_item : function(bunch_name, func_name, func_code, func_args) 
                {
                    var find_items = pst_find_item(bunch_name, func_name, func_code, func_args);

                    for( var f_idx in find_items)
                    {
                        //pst_log("hash_key : " + find_items[f_idx].hash_key);
                        //pst_log("find_item : " + find_items[f_idx].find_item);
                    }
                    this.__set_result(find_items);
                }
            }
            """
        jsstr = jsstr+js_func+"""
            var p = new storekeeper_api();
            p.find_item('"""+bunch_name+"', '"+func_name+"', "+func_name+".toString(), '"+func_args+"""');
            """
        ret = self.run(jsstr)
        return ret

    def find_item_inline(self, bunch_name, func, func_args, func_code):
        func_name = func.__name__
        js_func = func_code
        js_func = self.js_replace(js_func)
        if func_args is None:
            func_args = ""
        jsstr = self.base_str + """
            find_item : function(bunch_name, func_name, func_code, func_args) 
                {
                    var find_items = pst_find_item(bunch_name, func_name, func_code, func_args);

                    for( var f_idx in find_items)
                    {
                        //pst_log("hash_key : " + find_items[f_idx].hash_key);
                        //pst_log("find_item : " + find_items[f_idx].find_item);
                    }
                    this.__set_result(find_items);
                }
            }
            """
        jsstr = jsstr+js_func+"""
            var p = new storekeeper_api();
            p.find_item('"""+bunch_name+"', '"+func_name+"', "+func_name+".toString(), '"+func_args+"""');
            """
        ret = self.run(jsstr)
        return ret

    def set_whdata(self, func, func_args):
        func_name = func.__name__
        js_func = self.get_func_str(func)    #Using pyinstaller Any_source.py include
        # js_func = translates(inspect.getsource(func))[0]    #Using pyinstaller Any_source.py include
        js_func = self.js_replace(js_func)
        if func_args is None:
            func_args = ""
        jsstr = self.base_str + """
            set_whdata : function(func_name, func_code, func_args) 
                {
                   var ret_val = pst_set_whdata(func_name, func_code, func_args);

		            this.__set_result(ret_val);
                }
            }
            """
        jsstr = jsstr+js_func+"""
            var p = new storekeeper_api();
            p.set_whdata('"""+func_name+"', "+func_name+".toString(), '"+func_args+"""');
            """
        ret = self.run(jsstr)
        return ret
    def js_replace(self, func_str):
        func_str_list = func_str.split(";")
        func_str = ""
        for i in func_str_list:
            if i.find("var ") > -1:
                i = i.replace("storekeeper_global_object","xyz131")
                i = i.replace("wh_global_object","xyz132")
                i = i.replace("wh_ret_val","xyz133")
                i = i.replace("wh_hash_val","xyz134")
            func_str += i + ";"
        func_str = func_str.replace("console.log(","popstore_log(")
        func_str = func_str.replace("datetime(","new Date(")
        func_str = func_str.replace("json.dumps(","JSON.stringify(")
        func_str = func_str.replace("json.loads(","JSON.parse(")
        func_str = func_str.replace("index(","indexOf(")
        func_str = func_str.replace("append(","push(")  #.. check LOD
        func_str = func_str.replace("//r","\\r")
        func_str = func_str.replace("//n","\\n")
        func_str = func_str.replace("//t","\\t")
        func_str = func_str.replace("===","==")
        func_str = func_str.replace("!==","!=")

        
        
        func_arr = func_str.split("\n")
        func_str = ""
        for i in range(0, len(func_arr)):
            if i != 1:
                func_str += func_arr[i] + "\n"
            else:
                if func_arr[i].find("var ") == -1:
                    func_str += func_arr[i] + "\n"
        return func_str
    def set_whdata_py(self, func, func_args):
        func_name = func.__name__
        js_func = self.get_func_str(func)    #Using pyinstaller Any_source.py include
        # js_func = translates(inspect.getsource(func))[0]    #Using pyinstaller Any_source.py include
        js_func = self.js_replace(js_func)
        if func_args is None:
            func_args = ""
        jsstr = self.base_str + """
            set_whdata : function(func_name, func_code, func_args) 
                {
                   var ret_val = pst_set_whdata(func_name, func_code, func_args);

		            this.__set_result(ret_val);
                }
            }
            """
        jsstr = jsstr+js_func+"""
            var p = new storekeeper_api();
            p.set_whdata('"""+func_name+"', "+func_name+".toString(), '"+func_args+"""');
            """
        ret = self.run(jsstr)
        return ret
    
    def set_whdata_inline(self, func, func_args, func_code):
        func_name = func.__name__
        js_func = func_code
        js_func = self.js_replace(js_func)
        if func_args is None:
            func_args = ""
        jsstr = self.base_str + """
            set_whdata : function(func_name, func_code, func_args) 
                {
                   var ret_val = pst_set_whdata(func_name, func_code, func_args);

		            this.__set_result(ret_val);
                }
            }
            """
        jsstr = jsstr+js_func+"""
            var p = new storekeeper_api();
            p.set_whdata('"""+func_name+"', "+func_name+".toString(), '"+func_args+"""');
            """
        ret = self.run(jsstr)
        return ret

    def wh_connect(self, host, port):
        client_socket = None
        try:
            client_socket = socket.socket()  # instantiate
            client_socket.connect((host, port))  # connect to the server
        except:
            client_socket.close()
            return None

        return client_socket

    def rt_set(self, jsstr):
        ret = ""
        self.wh_conn = []
        last_char = jsstr[-1]
        if last_char != "/":
            jsstr += "/"
        f = open(jsstr+"storekeeper.cfg", 'r')
        ip = ""
        port = ""
        self.enabled_wh_count = 0
        while True:
            line = f.readline()
            if not line: break
            first_char = line[0]
            if first_char != ";":
                if line.find("IP") > -1 or line.find("PORT") > -1:
                    cmd = line.split('=')
                    if len(cmd) > 1:
                        key = cmd[0].strip()
                        val = cmd[1].strip()
                        if key == "IP":
                            ip = val
                        if key == "PORT":
                            port = val
                            wh_socket = self.wh_connect(ip, int(port)+1000)
                            if wh_socket is not None:
                                self.wh_conn.append(wh_socket)
                                self.enabled_wh_count += 1
                                print("IP:"+ip+", PORT:"+port)
                            else:
                                ret = "Error IP:"+ip+", PORT:"+port
                                print("Error IP:"+ip+", PORT:"+port)
                                break
                            
        f.close()
        return ret
    def rt_release(self):
        for sock in self.wh_conn:
            sock.close()
        self.wh_conn = []
        self.enabled_wh_count = 0
        return None

