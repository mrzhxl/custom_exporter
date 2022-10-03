from flask import Flask, Response, request
from prometheus_client import Gauge, CollectorRegistry, generate_latest
import subprocess
from flask_redis import FlaskRedis
from flask_apscheduler import APScheduler


"""
1、定时任务，部署服务器每20秒ping 114.114.114.114,丢包（server_netping_loss）和延迟（server_netping_sec）写入redis。
2、POST /netping_data，被动接收传入丢包（office_netping_loss）和延迟（office_netping_sec）写入redis。
3、GET /metrics，prometheus服务器拉取。
"""


class Config(object):  # 创建配置，用类
    # 任务列表
    JOBS = [
        {  # 任务1，每隔20S执行一次
            'id': 'job1',
            'func': 'web:server_ping_start',  # 方法名
            'args': ('114.114.114.114',),  # 入参
            'trigger': 'interval',  # interval表示循环任务
            'seconds': 10,
        }
    ]
    # SCHEDULER_API_ENABLED = True


app = Flask(__name__)
app.config.from_object(Config())  # 为实例化的flask引入配置

app.config["REDIS_URL"] = "redis://:password@127.0.0.1:6379/0"
redis_client = FlaskRedis(app)


# 服务器ping loss
def server_ping_start(ipaddress):
    res = subprocess.check_output(["bash", "ping.sh", ipaddress])
    res_list = res.decode('utf-8').split(',')
    redis_client.set('server_netping_loss', res_list[0], ex=60)
    redis_client.set('server_netping_sec', res_list[1], ex=60)
    return 'server ping info set redis'


@app.route('/')
def get_key():
    if redis_client.exists('name'):
        a = redis_client.get('name')
    else:
        a = "Request error, please request '/metrics"
    return a


@app.post('/netping_data')
def post_key():
    data = request.get_json()
    office_netping_loss = data.get('office_netping_loss', '-1')
    office_netping_sec = data.get('office_netping_sec', '-1')
    office_outside_ip = data.get('office_outside_ip', '-1')
    redis_client.set('office_netping_loss', office_netping_loss, ex=60)
    redis_client.set('office_netping_sec', office_netping_sec, ex=60)
    redis_client.set('office_outside_ip', office_outside_ip, ex=60)
    return 'set redis success'


@app.route("/metrics")
def custom_key():
    # 实例化CollectorRegistry
    registry = CollectorRegistry()

    # 创建服务器ping指标
    server_ping_time = Gauge(
        'server_ping_time', 'server ping time info', registry=registry)
    server_ping_loss = Gauge(
        'server_ping_loss', 'server ping loss info', ['hostname'], registry=registry)
    # 创建办公室ping指标
    office_ping_time = Gauge(
        'office_ping_time', 'office ping time info', registry=registry)
    office_ping_loss = Gauge(
        'office_ping_loss', 'office ping loss info', ['hostname'], registry=registry)

    # office outside ip
    office_out_ip = Gauge("office_ip_info", "office outside IP", [
                          'hostname', 'office_outside_ip'], registry=registry)

    # 服务器网络丢包
    if redis_client.exists('server_netping_loss'):
        server_net_loss = redis_client.get('server_netping_loss')
    else:
        server_net_loss = 100

    # 服务器网络延迟
    if redis_client.exists('server_netping_sec'):
        server_net_sec = redis_client.get('server_netping_sec')
    else:
        server_net_sec = -1

    # 办公室网络丢包
    if redis_client.exists('office_netping_loss'):
        office_net_loss = redis_client.get('office_netping_loss')
    else:
        office_net_loss = 100

    # 办公室网络延迟
    if redis_client.exists('office_netping_sec'):
        office_net_sec = redis_client.get('office_netping_sec')
    else:
        office_net_sec = -1

    # 办公室出口地址
    if redis_client.exists('office_outside_ip'):
        office_outside_ip_value = 1
        office_outside_ip = (redis_client.get(
            'office_outside_ip')).decode('utf-8')
        # 判断出口ip是否变化
        if office_outside_ip != "127.0.0.1":
            office_outside_ip_value = 2
        print(office_outside_ip)
    else:
        office_outside_ip = "0.0.0.0"
        office_outside_ip_value = 0
        print('office_outside_ip does not exist')

    server_ping_time.set(server_net_sec)
    server_ping_loss.labels('ServerNetwork').set(server_net_loss)
    office_ping_time.set(office_net_sec)
    office_ping_loss.labels('OfficeNetwork').set(office_net_loss)
    office_out_ip.labels("OfficeNetwork", office_outside_ip).set(
        office_outside_ip_value)
    return Response(generate_latest(registry), mimetype='text/plain')


scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9120)
