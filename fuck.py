# coding=utf-8
import os

import requests
import copy
import random
import json
import re
import urllib

import myproperties

HEADER = {'Host': 'jktb.haedu.gov.cn',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
          'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/605.1.15 (KHTML, like Gecko) '
                        'Version/13.1 Safari/605.1.15',
          'Accept-Encoding': 'gzip, deflate',
          'Accept-Language': 'en-us',
          }
# 学校的开始URL 若是其他学校 可以识别学校的二维码 获得链接
start_url = 'http://jktb.haedu.gov.cn/?ext=eHt3MD8wPiwzeXV4Mik%3D&rn=1569842325'
# 测试中 http://jktb.haedu.gov.cn/?ext=eHt3MD 这个链接一样指向河南科技学院 不知道为什么

login_url = 'http://jktb.haedu.gov.cn/?act=login'
verify_url = 'http://jktb.haedu.gov.cn/?act=verify'
init_url = 'http://jktb.haedu.gov.cn/?act=health'


def fk(phone, id_last, school=None, isDebug=False):
    if isDebug:
        return json.loads('{"code": 0, "msg": "未曾修改", "data": []}')

    if school is None:
        pass
    else:
        global start_url
        start_url = school

    # 所有Header核心就 type 和 school 这两个 其他都是自动添加的
    Header = copy.copy(HEADER)
    # 使用全局session 保存cookie
    sess = requests.session()
    # 发起学校首页请求 主要是为了获取Cookie
    response = sess.get(start_url, headers=Header)

    # 跳转到填报页面 也是核验Cookie相关信息
    Header['Referer'] = login_url
    sess.cookies.set('type', '1')
    response = sess.get(verify_url, headers=Header)

    # 将Cookie获得 反手再以表单的形式传到服务器上 实现登陆操作
    str_ = response.cookies.get('uvauth')
    rn = str(random.random())
    data = {
        'do': 'check',
        'str': str_,
        'mobile': phone,
        'idCard': id_last,
        'rn': rn,
    }
    response = sess.post(verify_url, data, headers=Header)

    # 跳转到修改页面 以获得原始数据 然后反手再传回服务器
    response = sess.post(init_url, {'do': 'init'}, headers=Header)

    js = json.loads(response.content, encoding='utf-8')
    data = js['data']
    data['touchWhere'] = 0
    data['do'] = 'ajax'

    # 签到操作
    response = sess.post(init_url, data=data, headers=Header)
    print(response.text)
    js = json.loads(response.content, encoding='utf-8')
    msg = js['msg']
    print('msg:' + msg)

    print(sess.cookies.values())
    print(response.headers)
    print(js)
    return js


# 通过smtp服务器 发送邮件 可以发送附件
def send2EmailSimple(receiver, subject, content, *attachName):
    import smtplib
    from email.mime.text import MIMEText
    from email.header import Header
    from email.utils import formataddr
    from email.mime.multipart import MIMEMultipart

    sender = myproperties.email
    my_pass = myproperties.email_password

    message = MIMEMultipart()
    message['From'] = formataddr(['Service Notice', sender])
    message['To'] = formataddr(['email', receiver])

    message['Subject'] = Header(subject, 'utf-8')

    message.attach(MIMEText(content, 'html', 'utf-8'))

    # 添加附件📎
    for i in attachName:
        path = os.path.join('./', i)
        att = MIMEText(open(path, 'rb').read(), 'base64', 'utf-8')
        att['Content-Type'] = 'application/octet-stream'
        # att['Content-Disposition'] = 'attachment; filename="'+i.replace(' ','')+'"'
        att.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', i))
        message.attach(att)

    try:
        server = smtplib.SMTP(myproperties.host, myproperties.host_port)
        server.starttls()
        server.login(sender, my_pass)
        server.sendmail(sender, [receiver], message.as_string())
        server.quit
    except smtplib.SMTPException as err:
        sendMsg2Wechat('email 发送失败', msg='发送邮件异常被触发,strerror:' + str(err))


# 使用方糖的微信消息推送 细节清关注公众号或访问官网https://sc.ftqq.com
def sendMsg2Wechat(title, msg='None', ):
    Murl = 'https://sc.ftqq.com/' + myproperties.wechat_code + '.send'
    Mdatas = {'text': title, 'desp': msg}
    Mdata = urllib.parse.urlencode(Mdatas)

    Mnewurl = Murl + '?' + Mdata

    Mreq = urllib.request.urlopen(Mnewurl)
    Mda = Mreq.read().decode('utf-8')
    if (Mda.find('success')):
        print('消息已推送至微信！')
    else:
        print('返回的参数中缺少success关键字，消息可能没有发送成功')


def checkSchoolIndex(url, isDebug=True):
    """
    传入学校首页链接 返回链接是否正确 若正确返回学校的名称
    :param url:
    :return:(True/False,SchoolName)
    """
    if isDebug:
        return True, 'School_' + str(random.randint(1, 100))
    Header = copy.copy(HEADER)
    # 使用全局session 保存cookie
    sess = requests.session()
    # 发起学校首页请求 主要是为了获取Cookie
    response = sess.get(start_url, headers=Header)
    if 'schoolName' in response.cookies.keys():
        schoolName = urllib.parse.unquote(response.cookies.get('schoolName'))
        return True, schoolName
    else:
        return False, None


if __name__ == '__main__':
    #
    # fk(手机号, 身份证后四位)
    # fk('')
    # start_url = 'http://jktb.haedu.gov.cn/?ext=eHt3M'
    # isOk,url = checkSchoolIndex(start_url)
    # print(isOk,url)
    result = fk(myproperties.phone, myproperties.card)
    print(result)
    if result['code'] == 0:
        sendMsg2Wechat("签到成功"+str(result))
    else:
        sendMsg2Wechat("签到失败"+str(result))
    pass
