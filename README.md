# Flask Prometheus client

## 依赖包
- python3.x
  - flask
  - flask_apscheduler
  - flask_redis
  - prometheus_client
- redis-server

## web端接口
1. POST /netping_data，被动接收传入丢包（office_netping_loss）、出口IP地址（office_outside_ip）和延迟（office_netping_sec）写入redis。
2. GET /metrics，prometheus服务器拉取。
3. 10秒定时任务，调用ping.sh脚本，收集本地网络延迟和丢包信息写入redis


## 客户端
1、10秒定时任务，调用ping.sh脚本，收集网络延迟和丢包信息POST到web端