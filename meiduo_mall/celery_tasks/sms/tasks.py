from celery_tasks.main import app
from meiduo_mall.libs.yuntongxun.sms import CCP

@app.task(bind=True,name="send_msg_code")
def send_msg_code(self,mobile,sms_code):
    #1,发送短信
    try:
        ccp = CCP()
        result = ccp.send_template_sms(mobile, [sms_code, 5], 1)
    except Exception as e:
        result = -1

    #2,判断短信是否发送成功
    if result == -1:
        #exc: 发送失败之后的异常,  countdown:间隔的时间  max_retries:重试的次数
        self.retry(exc=Exception("短信发送失败啦!"),countdown=5,max_retries=3)
