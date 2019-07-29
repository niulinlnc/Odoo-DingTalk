# Odoo平台集成钉钉应用
**最新说明**
- **基于dingtalk-sdk**
>本分支基于dingtalk-sdk，安装：pip3 install dingtalk-sdk
- **odoo.conf添加参数**
>请在odoo.conf配置文件里添加下面四个参数：
>
>din_agentid = xxxxxxx
>
>din_corpid = dingxxxxx
>
>din_appkey = dingxxxxxxx
>
>din_appsecret = xxxx
- **redis**
>access_token缓存在redis里，请在服务器里安装并配置好redis服务器。
>
>redis默认设置
>
>redis_host = localhost
>
>redis_port = 6379
>
>dingtalk_redis_db = 1

- **关于免登与扫码登入**
>
>免登与扫码基于auth_oauth 模块，安装登录模块会自动安装该模块。

