import requests
import subprocess
from flask import Flask, Response, request
from flask_apscheduler import APScheduler



class Config(object):  # 创建配置，用类
    # 任务列表
    JOBS = [
        {  # 任务1，每隔20S执行一次
            'id': 'job1',
            'func': 'client:server_ping_start',  # 方法名
            'args': ('114.114.114.114',),  # 入参
            'trigger': 'interval',  # interval表示循环任务
            'seconds': 10,
        }
    ]

def server_ping_start(ipaddress):
    res = subprocess.check_output(["bash", "ping.sh", ipaddress])
    res_list = res.decode('utf-8').split(',')
    DATA = {
        "office_netping_loss": res_list[0],
        "office_netping_sec": res_list[1],
        "office_outside_ip": res_list[2].replace('\n','')
    }
    headers = {
        'Content-Type': "application/json",
    }
    # 服务器接口地址
    url = "http://127.0.0.1:9120/netping_data"
    response = requests.request("POST", url, json=DATA, headers=headers)
    print('exec job1')


custom_exporter_client = Flask(__name__)
custom_exporter_client.config.from_object(Config())  # 为实例化的flask引入配置
scheduler = APScheduler()
scheduler.init_app(custom_exporter_client)
scheduler.start()


if __name__ == '__main__':
    custom_exporter_client.run(host='0.0.0.0', port=9121)
