# _*_ coding:utf-8 _*_
# FileName: data_html.py
# IDE: PyCharm

# pip install fastapi[all]
# pip install uvicorn[standard]
import os
import json
import time
from fastapi import FastAPI
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="html")


@app.get("/")
def show_index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.get('/friends//6')
def no_qq():
    return "请输入qq号！"


@app.get('/groups//6')
def no_qq():
    return "请输入qq号！"


@app.get('/friends/{qq:int}/{s:str}')
def show_friends(request: Request, qq, s):
    if os.path.isfile(f'{qq}.json'):
        friends = []
        information = json.loads(open(f'{qq}.json', 'r', encoding='utf-8').read())
        for g in information:
            for p in information[g]:
                try:
                    friends.append(p[:6] + [g, p[6] == '创号之日' and '创号时长' or p[6] == '好友状态异常' and '天数异常！' or f'{int((time.time() - int(time.mktime(time.strptime(p[6], "%Y-%m-%d")))) // 3600 // 24)}天'])
                except OverflowError:
                    friends.append(p[:6] + [g, '天数异常！'])
        if int(s[-1]) in [0, 1]:
            friends = sorted(friends, key=lambda _: _[int(s[-1])], reverse=not s.count(s[-1]) % 2 and True or False)
        elif s[-1] == '6':
            friends = sorted(friends, key=lambda _: not _[6] and '4' or _[6], reverse=not s.count(s[-1]) % 2 and True or False)  # 解决2717057684突然出现的空白分组
        elif s[-1] == '7':
            friends = sorted(friends, key=lambda _: _[7] != '天数异常！' and (_[7] == '创号时长' and 999999999 or int(_[7][:-1])) or 0, reverse=s.count(s[-1]) % 2 and True or False)
        else:
            friends = sorted(friends, key=lambda _: _[int(s[-1])] in ['否', '好友状态异常'] and '0' or _[int(s[-1])], reverse=s.count(s[-1]) % 2 and True or False)
        return templates.TemplateResponse('friends.html', dict(request=request, friends=friends, total=len(friends), begin='时间未知', day='时间未知'))
    return f'数据文件 {qq}.json 不存在！'


@app.get('/groups/{qq:int}/{s:str}')
def show_groups(request: Request, qq, s):
    if os.path.isfile(f'{qq}_group.json'):
        groups = []
        information = json.loads(open(f'{qq}_group.json', 'r', encoding='utf-8').read())
        for g in information:
            temp = [g, information[g]["群名"], information[g]["当前人数"], information[g]["最多人数"], list(information[g]["创建者"].keys())[0], list(information[g]["创建者"].values())[0]["入群时间"]]
            for r in ["创建者", "管理员", "群成员"]:
                if information[g][r].get(str(qq), None):
                    temp.append(r)
                    temp.append(information[g][r][str(qq)]["入群时间"])
                    break
            groups.append(temp)
        groups = sorted(groups, key=lambda _: _[int(s[-1])], reverse=not s.count(s[-1]) % 2 and True or False)
        return templates.TemplateResponse('groups.html', dict(request=request, groups=groups, total=len(groups), begin='时间未知', day='时间未知'))
    return f'数据文件 {qq}_group.json 不存在！'


if __name__ == '__main__':
    import uvicorn
    try:
        port = int(input('请输入端口号：'))
    except ValueError:
        port = 12345
    if not os.system('where chrome'):
        os.system(f'chrome http://127.0.0.1:{port}')
    uvicorn.run(app, host="127.0.0.1", port=port)
