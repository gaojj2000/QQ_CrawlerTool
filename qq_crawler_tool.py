# _*_ coding:utf-8 _*_
# FileName: qq_crawler_tool.py
# IDE: PyCharm

import os
import re
import bs4
import tkinter
import json as js
from math import ceil
from random import uniform
from threading import Thread
from string import whitespace
from tkinter import scrolledtext
from requests import get, post, exceptions
from time import sleep, time, strftime, localtime


class DownloaderThread:
    def __init__(self, function: object = None, count: int = os.cpu_count() * 2 + 2):
        self.function = function
        self.count = count
        self.threadPool = []

    def download(self, *args, **kwargs):
        self.wait_max()
        t = Thread(target=self.function, args=args, kwargs=kwargs)
        t.start()
        self.threadPool.append(t)

    def wait_max(self):
        while len(self.threadPool) >= self.count:
            for thread in self.threadPool:
                if not thread.is_alive():
                    self.threadPool.remove(thread)

    def wait_clean(self):
        while self.threadPool:
            for thread in self.threadPool:
                if not thread.is_alive():
                    self.threadPool.remove(thread)


class Crawler(tkinter.Tk):
    WIDTH = 576
    HEIGHT = 408
    HEADERS = {
        "accept": "text/html,application/xhtml+xml,application/xml,;q=0.9,image/webp,image/apng,*/*;q=0.8;",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "referer": "https://user.qzone.qq.com",  # 获取日志需要 referer 字段，否则返回 403。
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36"
    }

    def __init__(self):
        super().__init__()
        self.title('QQ空间保存程序')
        self.start_time = time()
        self.settings = {
            '主页': self.get_main_page,
            '日志': self.get_blog,
            '相册': self.get_photo,
            '留言': self.get_message,
            '说说': self.get_talk
        }
        self.top = tkinter.BooleanVar(value=True)
        self.blog = tkinter.BooleanVar(value=False)
        self.photo = tkinter.BooleanVar(value=False)
        self.message = tkinter.BooleanVar(value=False)
        self.talk = tkinter.BooleanVar(value=False)
        self.friends = tkinter.BooleanVar(value=False)
        self.groups = tkinter.BooleanVar(value=False)
        self.setting = tkinter.LabelFrame(self, text='设置参数区域')
        self.setting.grid(column=0, row=0, sticky='WENS')
        self.logging = tkinter.LabelFrame(self, text='日志输出区域')
        self.logging.grid(column=0, row=1, sticky='WENS')
        self.qq_tip = tkinter.Label(self.setting, text='目标QQ账号')
        self.qq_tip.grid(column=0, row=0, sticky='WE')
        self.qq = tkinter.Entry(self.setting)
        self.qq.grid(column=1, row=0, sticky='WE', columnspan=7)
        self.zone_cookie_tip = tkinter.Label(self.setting, text='QQ空间cookie')
        self.zone_cookie_tip.grid(column=0, row=1, sticky='WE')
        self.zone_cookie_entry = tkinter.Entry(self.setting)
        self.zone_cookie_entry.grid(column=1, row=1, sticky='WE', columnspan=7)
        self.qun_cookie_tip = tkinter.Label(self.setting, text='QQ群cookie')
        self.qun_cookie_tip.grid(column=0, row=2, sticky='WE')
        self.qun_cookie_entry = tkinter.Entry(self.setting)
        self.qun_cookie_entry.grid(column=1, row=2, sticky='WE', columnspan=7)
        tkinter.Checkbutton(self.setting, text='窗口置顶', offvalue=False, onvalue=True, variable=self.top, command=lambda: self.attributes('-topmost', self.top.get())).grid(column=0, row=3)
        tkinter.Checkbutton(self.setting, text='日志', offvalue=False, onvalue=True, variable=self.blog).grid(column=1, row=3)
        tkinter.Checkbutton(self.setting, text='相册', offvalue=False, onvalue=True, variable=self.photo).grid(column=2, row=3)
        tkinter.Checkbutton(self.setting, text='留言', offvalue=False, onvalue=True, variable=self.message).grid(column=3, row=3)
        tkinter.Checkbutton(self.setting, text='说说', offvalue=False, onvalue=True, variable=self.talk).grid(column=4, row=3)
        tkinter.Checkbutton(self.setting, text='好友', offvalue=False, onvalue=True, variable=self.friends).grid(column=5, row=3)
        tkinter.Checkbutton(self.setting, text='群聊', offvalue=False, onvalue=True, variable=self.groups).grid(column=6, row=3)
        self.start = tkinter.Button(self.setting, text='开始爬取', command=lambda: Thread(target=self.reptile, daemon=True).start())
        self.start.grid(column=7, row=3)
        self.scrolled_text = scrolledtext.ScrolledText(self.logging)
        self.scrolled_text.grid(column=0, row=1, sticky='WENS')
        self.scrolled_text.configure(state='disabled')
        self.minsize(self.WIDTH, self.HEIGHT)
        self.resizable(True, True)
        self.attributes('-topmost', self.top.get())
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.setting.columnconfigure([1, 2, 3, 4, 5, 6, 7], weight=1)
        self.logging.rowconfigure(1, weight=1)
        self.logging.columnconfigure(0, weight=1)
        self.geometry(f'{self.WIDTH}x{self.HEIGHT}+{int((self.winfo_screenwidth()-self.WIDTH-16)/2)}+{int((self.winfo_screenheight()-self.HEIGHT-32)/2)}')

    @staticmethod
    def str_time(time_number=None, ymd=True, hms=False):
        if ymd and hms:
            return strftime("%Y-%m-%d %H:%M:%S", localtime(time_number))
        if ymd:
            return strftime("%Y-%m-%d", localtime(time_number))
        if hms:
            return strftime("%H:%M:%S", localtime(time_number))
        return ''

    @staticmethod
    def parse_blog(blog):
        return '\n'.join([(lambda _: _[1] and _[1] or _[2])(_).replace('<br/>', '\n').replace('\n ', '\n').strip(' ').strip('\n').strip(' ') for _ in re.findall('(?=(</div>(.*?)<div.*?>|<div.*?>(.*?)</div>))', blog) if (_[1] and 'div' not in _[1]) or (_[2] and 'div' not in _[2])]).replace('\n\n', '\n').strip('\n')

    @staticmethod
    def parse_cookies(cookies):
        cookies_dict = {}
        for c in cookies.replace(' ', '').split(';'):
            try:
                cookies_dict[c.split('=')[0]] = c.split('=')[1]
            except IndexError:
                cookies_dict[c.split('=')[0]] = ''
        if "" in cookies_dict:
            del cookies_dict[""]
        return cookies_dict

    @staticmethod
    def parse_parameters(string: str):
        parameters = {}
        string = string.strip().replace(' ', '')
        if ':' not in string and '&' in string:
            for _ in string.split('&'):
                try:
                    parameters[_.split('=')[0]] = _.split('=')[1]
                except IndexError:
                    parameters[_.split('=')[0]] = ''
        else:
            for _ in string.split('\n'):
                _ = _.strip()
                try:
                    parameters[_.split(':')[0]] = _.split(':')[1]
                except IndexError:
                    parameters[_.split(':')[0]] = ''
        return parameters

    @staticmethod
    def parse_json(text):
        return js.loads(text[text.find('{'): text.rfind('}') + 1])

    @staticmethod
    def dump_json(text):
        return js.dumps(text, ensure_ascii=False, indent=4)

    def judge_json(self, response_json):
        if response_json["code"]:
            self.log(response_json["message"])
            return False
        else:
            return True

    def random_sleep(self, a=.5, b=1.5, p=True):
        sleep_time = uniform(a, b)
        if p:
            self.log(f'sleep {sleep_time:.2f}s')
        sleep(sleep_time)

    def get_url(self, url, params=None, retry=3, cookie=None, headers=None):
        for _ in range(retry):
            try:
                r = get(url, headers=headers or self.HEADERS, params=params, cookies={"cookie": cookie or self.settings['zone_cookie']}, timeout=10)
                if r.ok:
                    return r
            except exceptions.ConnectionError:
                self.log(f'Connection refused by {url}')
            except exceptions.ReadTimeout:
                self.log(f'Connection refused by {url}')
            self.random_sleep(.5, 1)

    def post_url(self, url, data=None, retry=3, cookie=None, headers=None):
        for _ in range(retry):
            try:
                r = post(url, headers=headers or self.HEADERS, data=data, cookies={"cookie": cookie or self.settings['zone_cookie']}, timeout=10)
                if r.ok:
                    return r
            except exceptions.ConnectionError:
                self.log(f'Connection refused by {url}')
            self.random_sleep(.5, 1)

    def log(self, value):
        self.scrolled_text.configure(state='normal')
        self.scrolled_text.insert('end', f'{value}\n')
        self.scrolled_text.see('end')
        self.update()
        self.scrolled_text.configure(state='disabled')

    def reptile(self):
        self.qq.configure(state='disabled')
        self.zone_cookie_entry.configure(state='disabled')
        self.qun_cookie_entry.configure(state='disabled')
        self.start.configure(state='disabled')
        self.scrolled_text.configure(state='normal')
        self.scrolled_text.delete('0.0', 'end')
        self.scrolled_text.configure(state='disabled')
        ok = True
        options = {
            '日志': self.blog.get(),
            '相册': self.photo.get(),
            '留言': self.message.get(),
            '说说': self.talk.get(),
            '好友': self.friends.get(),
            '群聊': self.groups.get()
        }
        if not self.zone_cookie_entry.get() and True in set(options.values()):
            self.log('请输入 QQ空间cookie ！')
            ok = False
        if not self.qun_cookie_entry.get() and (self.friends.get() or self.groups.get()):
            self.log('请输入 QQ群cookie ！')
            ok = False
        if ok:
            self.settings.update({
                'zone_cookie': self.zone_cookie_entry.get().strip(whitespace),
                'qun_cookie': self.qun_cookie_entry.get().strip(whitespace)
            })
            if self.settings['zone_cookie']:
                zone_cookies_dict = self.parse_cookies(self.settings['zone_cookie'])
                t = 5381
                for cc in zone_cookies_dict["p_skey"]:
                    t += (t << 5) + ord(cc)
                self.settings.update({
                    'g_tk': str(t & 2147483647),
                    'self_uin': zone_cookies_dict.get('uin', zone_cookies_dict.get('p_uin', f'o{self.qq.get().strip(whitespace)}'))[1:]
                })
                self.settings.update({'target_uin': self.qq.get().strip(whitespace) or self.settings['self_uin']})
                self.settings['主页']()
            if self.settings['qun_cookie']:
                qun_cookies_dict = self.parse_cookies(self.settings['qun_cookie'])
                t = 5381
                for cc in qun_cookies_dict["skey"]:
                    t += (t << 5) + ord(cc)
                self.settings.update({
                    'bkn': str(t & 2147483647)
                })
            self.settings.update({
                '好友': lambda: open(f"{self.settings['self_uin']}.json", 'w', encoding='utf-8').write(self.dump_json(self.all_friends(a=True))),
                '群聊': lambda: open(f"{self.settings['self_uin']}_group.json", 'w', encoding='utf-8').write(self.dump_json(self.all_groups(7)))
            })
            self.log(f'爬虫已启动，爬取内容：{[o for o in options if options[o]]}')
            self.start_time = time()
            for o in options:
                if options[o]:
                    self.log(f'即将爬取 {o} ...')
                    try:
                        self.settings[o]()
                    except Exception as e:
                        self.log(e)
                    self.random_sleep(1, 2)
            self.log(f'爬虫于 {self.str_time(self.start_time, hms=True)} 开始，于 {self.str_time(hms=True)} 结束，共用时 {time() - self.start_time:.2f} 秒。')
        self.qq.configure(state='normal')
        self.zone_cookie_entry.configure(state='normal')
        self.qun_cookie_entry.configure(state='normal')
        self.start.configure(state='normal')

    def get_main_page(self):
        if not os.path.exists(self.settings['target_uin']):
            os.makedirs(self.settings['target_uin'])
        payload = {
            "uin": self.settings['target_uin'],
            "param": f"3_{self.settings['target_uin']}_0|8_8_{self.settings['self_uin']}_1_1_0_1_1|16",
            "g_tk": self.settings['g_tk']
        }
        main_page_cgi = "https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/main_page_cgi"  # 获取日志、说说及相册的数量，并测试能否访问目标空间。
        payload["param"] = "16"
        res = self.get_url(main_page_cgi, params=payload).text
        json = self.parse_json(res)
        if self.judge_json(json):
            (RZ, SS, XC) = tuple(json["data"]["module_16"]["data"].values())
            self.settings.update({'RZ': RZ, 'SS': SS, 'XC': XC})
            self.log(f'日志：{RZ}，说说：{SS}，相册(照片总数)：{XC}。')
            open(f"{self.settings['target_uin']}/{self.settings['target_uin']}_main_page.json", 'w', encoding='utf-8').write(self.dump_json(json))

    def get_blog(self):
        if not os.path.exists(f"{self.settings['target_uin']}/blog"):
            os.makedirs(f"{self.settings['target_uin']}/blog")
        blog_payload = {
            "hostUin": self.settings['target_uin'],
            "blogType": "0",
            "reqInfo": "7",  # 1为list数据（所有日志列表）；2为cateInfo数据（日志分类）；4为month_num数据（在statYear参数年份内每个月日志数目）；可相加叠加数据（1-7）
            "g_tk": self.settings['g_tk']
        }
        blog_url = "https://h5.qzone.qq.com/proxy/domain/b.qzone.qq.com/cgi-bin/blognew/get_abs"  # 所有日志条目、分类等信息
        single_blog_payload = {
            "uin": self.settings['target_uin'],
            "blogid": "",
            "styledm": "qzonestyle.gtimg.cn",
            "imgdm": "qzs.qq.com",
            "bdm": "b.qzone.qq.com",
            "mode": "2",
            "numperpage": "15",
            "timestamp": str(time()),
            "dprefix": "",
            "inCharset": "utf-8",
            "outCharset": "utf-8 ",
            "ref": "qzone",
            "page": "1",
            "refererurl": "https://user.qzone.qq.com/proxy/domain/qzs.qq.com/qzone/app/blog/v6/bloglist.html#nojump=1&page=1&catalog=list",
            "g_iframUser": "1",
            "num": "100"  # 每次最多100篇日志
        }
        single_blog_url = "https://h5.qzone.qq.com/proxy/domain/b.qzone.qq.com/cgi-bin/blognew/blog_output_data"  # 日志详情
        blog_payload["reqInfo"] = "2"
        res = self.get_url(blog_url, params=blog_payload).text
        json = self.parse_json(res)
        if self.judge_json(json):
            open(f"{self.settings['target_uin']}/blog/category_list.json", 'w', encoding='utf-8').write(self.dump_json(json))
            for _ in json["data"]["cateInfo"]["categoryList"]:
                if _["num"]:
                    if not os.path.exists(f"{self.settings['target_uin']}/blog/{_['category']}"):
                        os.makedirs(f"{self.settings['target_uin']}/blog/{_['category']}")  # 创建日志分类文件夹
                    loop_num = ceil(_["num"] / 100)  # 循环次数
                    for __ in range(loop_num):
                        pos = __ * 100
                        current_num = 100 if __ < loop_num - 1 else _["num"] - __ * 100
                        blog_payload["reqInfo"] = "1"
                        blog_payload["pos"] = pos
                        blog_payload["num"] = current_num
                        # 按分类获取日志
                        blog_payload["cateName"] = _["category"]
                        blog_payload["cateHex"] = _["cateHex"]
                        if pos + 1 != pos + current_num:
                            filename = f"blog_list_{pos + 1:0>5}-{pos + current_num:0>5}.json"
                        else:
                            filename = f"blog_list_{pos + 1:0>5}.json"
                        res = self.get_url(blog_url, params=blog_payload).text
                        json = self.parse_json(res)
                        if self.judge_json(json):
                            open(f"{self.settings['target_uin']}/blog/{_['category']}/{filename}", 'w', encoding='utf-8').write(self.dump_json(json))
                            for blog in json["data"]["list"]:
                                single_blog_payload["blogid"] = blog["blogId"]
                                res = self.get_url(single_blog_url, params=single_blog_payload).text
                                res = bs4.BeautifulSoup(res, "html.parser")
                                html = res.find('div', attrs={'id': 'blogDetailDiv'})
                                res.title.string = blog["title"]
                                res.find("span", {"id": "pubTime"}).string = self.str_time(blog["blogId"], ymd=True, hms=True)
                                r = self.get_like_data(f"http://user.qzone.qq.com/{self.settings['target_uin']}/blog/{blog['blogId']}", blog)
                                res.find("span", {"id": "readNum"}).string = f'阅读({r or 0})\t评论({blog["commentNum"]})'
                                for ___ in ["script", "style"]:
                                    for ____ in res.find_all(___):
                                        if 'var g_oBlogData' not in ____.text:
                                            ____.extract()
                                for ___ in res.find_all(text=lambda _: isinstance(_, bs4.Comment)):
                                    ___.extract()
                                parse = self.parse_blog(str(html))
                                # 过滤图片多余的属性，留下有用的src属性
                                if 'img' in parse:
                                    soup = bs4.BeautifulSoup(parse, 'html.parser').find_all('img')
                                    old = []
                                    for ___ in res.find('div', attrs={'id': 'blogDetailDiv'}).find_all('img'):
                                        if ___.get('orgsrc', ''):
                                            temp = ___["src"]
                                            ___["src"] = ___["orgsrc"]
                                            ___["orgsrc"] = temp
                                    for ___ in soup:
                                        old.append(str(___))
                                        if ___.get('orgsrc', ''):
                                            ___["src"] = ___["orgsrc"]
                                            del ___["orgsrc"]
                                        del ___["alt"], ___["class"], ___["data-albumname"], ___["data-albumpriv"], ___["data-from"], ___["style"]
                                    for ___ in range(len(old)):
                                        parse = parse.replace(old[___], str(soup[___]))
                                open(f"{self.settings['target_uin']}/blog/{_['category']}/{blog['title']}_{blog['blogId']}.txt", 'w', encoding='utf-8').write(parse)
                                open(f"{self.settings['target_uin']}/blog/{_['category']}/{blog['title']}_{blog['blogId']}.html", 'w', encoding='utf-8').write(res.prettify())
                                if blog["commentNum"]:
                                    self.get_blog_comment(blog)
                                self.random_sleep(.5, 1)
                self.random_sleep(1, 2)

    def get_blog_comment(self, blog):
        comment_payload = {
            "uin": self.settings['target_uin'],
            "num": "50",  # 每次最多50条评论
            "topicId": f"{self.settings['target_uin']}_{blog['blogId']}",
            "start": "0",
            "r": str(__import__('random').random()),
            "iNotice": "0",
            "inCharset": "gb2312",
            "outCharset": "gb2312",
            "format": "jsonp",
            "ref": "qzone",
            "g_tk": self.settings['g_tk']
        }
        comment_url = "https://h5.qzone.qq.com/proxy/domain/b.qzone.qq.com/cgi-bin/blognew/get_comment_list"  # 日志评论列表
        total = 0
        loop_num = ceil(blog["commentNum"] / 50)
        data = []
        for _ in range(loop_num):
            comment_payload["start"] = _ * 50
            comment_payload["num"] = 50 if _ < loop_num - 1 else blog["commentNum"] - _ * 50
            res = self.get_url(comment_url, params=comment_payload).text
            json = self.parse_json(res)
            if self.judge_json(json):
                if "comments" in json["data"]:
                    total += json["data"]["total"]
                    data.append(json)
        if total != blog["commentNum"]:
            self.log('评论数据有误！')
        if len(data) == 1:
            data = data[0]
        else:
            temp = data[0]
            for dd in data[1:]:
                temp["data"]["total"] += dd["data"]["total"]
                temp["data"]["comments"] += dd["data"]["comments"]
            data = temp
        open(f"{self.settings['target_uin']}/blog/{blog['cate']}/{blog['title']}_{blog['blogId']}_comments.json", 'w', encoding='utf-8').write(self.dump_json(data))

    def get_photo(self):
        if not os.path.exists(f"{self.settings['target_uin']}/photo"):
            os.makedirs(f"{self.settings['target_uin']}/photo")
        album_list_payload = {
            "g_tk": self.settings['g_tk'],
            "uin": self.settings['self_uin'],
            "hostUin": self.settings['target_uin'],
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "source": "qzone",
            "plat": "qzone",
            "mode": "3",  # 分类视图
            "pageStart": "0",
            "pageNum": "100"
        }
        album_list_url = "https://h5.qzone.qq.com/proxy/domain/photo.qzone.qq.com/fcgi-bin/fcg_list_album_v3"
        album_list_payload["mode"] = "2"  # 普通视图
        res = self.get_url(album_list_url, params=album_list_payload).text
        json = self.parse_json(res)
        if self.judge_json(json):
            if 'albumListModeSort' in json["data"] and json["data"]["albumListModeSort"]:
                albums_list = json["data"]["albumListModeSort"]  # 普通视图
            # elif 'albumListModeClass' in json["data"] and json["data"]["albumList"]:
            #     albums_list = json["data"]["albumListModeClass"]  # 分类视图
            elif 'albumList' in json["data"] and json["data"]["albumList"]:
                albums_list = json["data"]["albumList"]  # 普通视图
            else:
                self.log('相册分类数据未找到或为空！')
                return
            while json["data"]["nextPageStart"] != json["data"]["albumsInUser"]:
                album_list_payload["pageStart"] = json["data"]["nextPageStart"]
                res = self.get_url(album_list_url, params=album_list_payload).text
                json = self.parse_json(res)
                if self.judge_json(json):
                    if 'albumListModeSort' in json["data"] and json["data"]["albumListModeSort"]:
                        albums_list = json["data"]["albumListModeSort"]
                    elif 'albumList' in json["data"] and json["data"]["albumList"]:
                        albums_list += json["data"]["albumList"]
                    else:
                        break
            if len(list(set([_["name"] for _ in albums_list]))) == len(albums_list):
                open(f"{self.settings['target_uin']}/photo/album_info.json", 'w', encoding='utf-8').write(self.dump_json(albums_list))
            else:
                # 当相册名字不唯一时，后缀加上id值
                for album in albums_list:
                    album["name"] += f'_{album["id"]}'
                open(f"{self.settings['target_uin']}/photo/album_info.json", 'w', encoding='utf-8').write(self.dump_json(albums_list))
            if 'albumListModeSort' in json["data"] and json["data"]["albumListModeSort"]:
                json["data"]["albumListModeSort"] = albums_list  # 普通视图
            # elif 'albumListModeClass' in json["data"] and json["data"]["albumList"]:
            #     json["data"]["albumListModeClass"] = albums_list  # 分类视图
            elif 'albumList' in json["data"] and json["data"]["albumList"]:
                json["data"]["albumList"] = albums_list  # 普通视图
            else:
                self.log('相册分类数据未找到或为空！')
                return
            open(f"{self.settings['target_uin']}/photo/category_info.json", 'w', encoding='utf-8').write(self.dump_json(json))
            for album_data in albums_list:
                if not os.path.exists(f"{self.settings['target_uin']}/photo/{album_data['name']}/downloads"):
                    os.makedirs(f"{self.settings['target_uin']}/photo/{album_data['name']}/downloads")
                need = False
                if album_data["comment"]:  # 虽然得到的不是实际数字，但感觉有数字就有评论
                    need = self.get_album_comment(album_data)  # 【证实和comment中的total一致，暂时不知道是什么意义】
                self.log(f'into {album_data["name"]} 【{album_data["total"]}】')
                self.get_album_photo_data(album_data, need)
                self.get_like_data(f"http://user.qzone.qq.com/{self.settings['target_uin']}/photo/{album_data['id']}", album_data)
                self.random_sleep(1, 2)

    def get_album_comment(self, album):
        comment_payload = {
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "g_tk": self.settings['g_tk'],
            "hostUin": self.settings['target_uin'],
            "uin": self.settings['self_uin'],
            "topicId": album["id"],
            "order": "1",
            "start": "0",
            "num": "100"
        }
        comment_url = "https://h5.qzone.qq.com/proxy/domain/app.photo.qzone.qq.com/cgi-bin/app/cgi_pcomment_xml_v2"
        comment_data = None
        while 1:
            res = self.get_url(comment_url, params=comment_payload)
            if not res:
                return None
            json = self.parse_json(res.text)
            try:
                self.judge_json(json)
            except Warning:
                self.log(json)
                return None
            if self.judge_json(json):
                if "comments" not in json["data"] or not json["data"]["comments"]:
                    if comment_data is None:
                        return 0
                    media_list = []
                    for c in comment_data["data"]["comments"]:
                        if c["poster"]["id"] != self.settings['self_uin']:
                            """
                            o_url【原图】 == (b_url【大图】 == hd_url【高清图】 网址相同) 图片相同
                            s_url【小图】
                            """
                            for media_type in ["video", "pic"]:
                                if media_type in c:
                                    for media in c[media_type]:
                                        media_url = ""
                                        for url in ["o_url", "b_url", "hd_url", "s_url"]:
                                            if url in media:
                                                media_url = media[url]
                                                break
                                        media_list.append(media_url)
                    if media_list:
                        open(f"{self.settings['target_uin']}/photo/{album['name']}/comments_media_list_url.json", 'w', encoding='utf-8').write(self.dump_json(media_list))
                    open(f"{self.settings['target_uin']}/photo/{album['name']}/comments.json", 'w', encoding='utf-8').write(self.dump_json(comment_data))
                    return comment_data["data"]["cmt_reply_total"]
                if not comment_data:
                    comment_data = json
                else:
                    comment_data["data"]["cmt_reply_total"] += json["data"]["cmt_reply_total"]
                    comment_data["data"]["comments"] += json["data"]["comments"]
                comment_payload["start"] = int(comment_payload["start"]) + int(comment_payload["num"])
                self.random_sleep(1, 2)
            else:
                return None

    def get_album_photo_data(self, album, get_comment=False):
        d = DownloaderThread(self.auto_downloader)
        list_photo_payload = {
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "g_tk": self.settings['g_tk'],
            "hostUin": self.settings['target_uin'],
            "uin": self.settings['self_uin'],
            "topicId": album["id"],
            "pageStart": "0",
            "pageNum": "500",
        }
        list_photo_url = "https://h5.qzone.qq.com/proxy/domain/photo.qzone.qq.com/fcgi-bin/cgi_list_photo"  # 获取照片列表
        float_view_photo_payload = {
            "g_tk": self.settings['g_tk'],
            "topicId": album["id"],
            "hostUin": self.settings['target_uin'],
            "uin": self.settings['self_uin'],
            "fupdate": "1",
            "plat": "qzone",
            "source": "qzone",
            "cmtNum": "0",
            "sortOrder": "1",
            "need_private_comment": "1",
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "appid": "4",
            "isFirst": "1",
            "picKey": "",
            "prevNum": "0",  # 获取之前照片数量
            "postNum": "0"  # 获取后续照片数量
        }
        float_view_photo_list_url = "https://h5.qzone.qq.com/proxy/domain/photo.qzone.qq.com/fcgi-bin/cgi_floatview_photo_list_v2"  # 获取原图及视频url
        num = 500
        loop_num = ceil(album["total"] / num)
        now = 1
        for _ in range(loop_num):
            list_photo_payload["pageStart"] = _ * num
            list_photo_payload["pageNum"] = num if _ < loop_num - 1 else album["total"] - _ * num
            res = self.get_url(list_photo_url, params=list_photo_payload).text
            json = self.parse_json(res)
            if self.judge_json(json):
                if "photoList" in json["data"] and json["data"]["photoList"]:
                    self.log(f'get photo_{_ * num + 1:0>5}-{_ * num + int(list_photo_payload["pageNum"]):0>5}')
                    open(f"{self.settings['target_uin']}/photo/{album['name']}/photo_{_ * num + 1:0>5}-{_ * num + int(list_photo_payload['pageNum']):0>5}.json", 'w', encoding='utf-8').write(self.dump_json(json))
                    float_view_photo_payload["picKey"] = json["data"]["photoList"][0]["lloc"]
                    float_view_photo_payload["postNum"] = num - 1
                    res = self.get_url(float_view_photo_list_url, params=float_view_photo_payload).text
                    json2 = self.parse_json(res)
                    if self.judge_json(json2):
                        self.log(f'get float-view_{_ * num + 1:0>5}-{_ * num + int(list_photo_payload["pageNum"]):0>5}')
                        open(f"{self.settings['target_uin']}/photo/{album['name']}/float-view_{_ * num + 1:0>5}-{_ * num + int(list_photo_payload['pageNum']):0>5}.json", 'w', encoding='utf-8').write(self.dump_json(json2))
                        for photo in json2["data"]["photos"]:
                            if photo["is_video"]:
                                url = photo["video_info"]["video_url"]
                            elif photo["raw_upload"]:
                                url = photo["raw"]
                            elif "origin" in photo and photo["origin"]:
                                url = photo["origin"]
                            else:
                                url = photo["url"]
                            # 多线程下载
                            d.download(url, f"{self.settings['target_uin']}/photo/{album['name']}/downloads/{photo['picKey']}", f'\r{album["name"]}  【{now}/{album["total"]}】')
                            now += 1
                if get_comment:
                    for photo in json["data"]["photoList"]:
                        comment = photo["forum"]
                        if comment:
                            float_view_photo_payload["cmtNum"] = comment if comment > 99 else 99
                            float_view_photo_payload["picKey"] = photo["lloc"]
                            float_view_photo_payload["postNum"] = 0
                            res = self.get_url(float_view_photo_list_url, params=float_view_photo_payload).text
                            json2 = self.parse_json(res)
                            if self.judge_json(json2):
                                if "single" in json2["data"] and json2["data"]["single"]:
                                    self.log(f'get single_comment_{photo["lloc"]}')
                                    open(f"{self.settings['target_uin']}/photo/{album['name']}/single_comment_{photo['lloc']}.json", 'w', encoding='utf-8').write(self.dump_json(json2["data"]["single"]))
                                    self.random_sleep(0, 1)
        d.wait_clean()

    def downloader(self, url, filename, retry=3, recover=False, headers=None):
        for _ in range(retry):
            try:
                # 加上 headers(referer) 解决相册中视频 vwecam.gtimg.com 域名的跨域访问，否则返回 403 Forbidden ！
                # 对于 vwecam.gtimg.com 或 vqzone.gtimg.com  域名的资源的 vkey 参数，有时效限制，超过一定时间就要重新获取，否则无法访问！
                r = get(url, headers=headers or self.HEADERS, stream=True)
                if r.ok:
                    if recover and os.path.exists(f'{filename}.{r.headers["Content-Type"].split("/")[-1]}'):
                        return True
                    while 1:
                        try:
                            open(f'{filename}.{r.headers["Content-Type"].split("/")[-1]}', 'wb').write(r.content)
                            return True
                        except PermissionError:
                            self.log(f'请在5秒内将文件 {filename}.{r.headers["Content-Type"].split("/")[-1]} 关闭！将自动重试！')
                            self.random_sleep(5, 5.5)
                        except ConnectionResetError:
                            self.log('远程主机强迫关闭了一个现有的连接。')
                            self.random_sleep()
                        except exceptions.ChunkedEncodingError:
                            self.log("ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None))")
                            self.random_sleep()
            except exceptions.ConnectionError:
                self.log(f'Connection refused by {url}')
            except exceptions.ReadTimeout:
                self.log(f'Connection timeout by {url}')
        return False

    def auto_downloader(self, url, filename, string='', retry=3, recover=False):
        self.log(string)
        res = self.downloader(url=url, filename=filename, retry=retry, recover=recover)
        if not res:
            self.log(f'遇到 vwecam.gtimg.com 或 vqzone.gtimg.com 域名的资源，可能 vkey 过期，请重新下载链接数据')
            open(f"{self.settings['target_uin']}/photo/download-failed.txt", 'a', encoding='utf-8').write(f'{url}\t{filename}\n')

    def get_message(self):
        if not os.path.exists(f"{self.settings['target_uin']}/message"):
            os.makedirs(f"{self.settings['target_uin']}/message")
        message_payload = {
            "format": "jsonp",
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "uin": self.settings['self_uin'],
            "hostUin": self.settings['target_uin'],
            "start": "0",
            "num": "20",  # 一次最多20条
            "g_tk": self.settings['g_tk']
        }
        message_url = "https://user.qzone.qq.com/proxy/domain/m.qzone.qq.com/cgi-bin/new/get_msgb"
        res = self.get_url(message_url, params=message_payload).text
        json = self.parse_json(res)
        if self.judge_json(json):
            total = json["data"]["total"]
            message = json
            now = len(message["data"]["commentList"])
            open(f"{self.settings['target_uin']}/message/message_{1:0>5}-{20 if now < total - 20 else total:0>5}.json", 'w', encoding='utf-8').write(self.dump_json(json))
            while now < total:
                message_payload["start"] = now
                message_payload["num"] = 20 if now < total - 20 else total - now
                res = self.get_url(message_url, params=message_payload).text
                json = self.parse_json(res)
                if self.judge_json(json):
                    open(f"{self.settings['target_uin']}/message/message_list_{now + 1:0>5}-{now + message_payload['num']:0>5}.json", 'w', encoding='utf-8').write(self.dump_json(json))
                    message["data"]["commentList"] += json["data"]["commentList"]
                    now = len(message["data"]["commentList"])
            if now > total:
                self.log('留言板数据有误！请检查爬取的留言板数据进行调试！')
                return
            open(f"{self.settings['target_uin']}/message/message_list_all.json", 'w', encoding='utf-8').write(self.dump_json(message))

    def get_talk(self):
        if not os.path.exists(f"{self.settings['target_uin']}/talk"):
            os.makedirs(f"{self.settings['target_uin']}/talk")
        msglist_payload = {
            "format": "jsonp",
            "need_private_comment": "1",
            "uin": self.settings['target_uin'],
            "pos": "0",
            "num": "40",  # 一次最多40条，参考QQ空间原版20条稳健
            "g_tk": self.settings['g_tk']
        }
        msglist_url = "https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6"
        msgdetail_payload = {
            "tid": "",
            "uin": self.settings['target_uin'],
            "t1_source": "1",
            "not_trunc_con": "1",
            "hostuin": self.settings['self_uin'],
            "code_version": "1",
            "format": "json",  # fs
            "qzreferrer": f"https://user.qzone.qq.com/{self.settings['target_uin']}/main"
        }
        msgdetail_url = f"https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msgdetail_v6?g_tk={self.settings['g_tk']}"
        float_view_photo_payload = {
            "g_tk": self.settings['g_tk'],
            "topicId": "",
            "hostUin": self.settings['target_uin'],
            "uin": self.settings['self_uin'],
            "fupdate": "1",
            "plat": "qzone",
            "source": "qzone",
            "cmtNum": "99",
            "need_private_comment": "1",
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "appid": "311",
            "isFirst": "1",
            "picKey": ""
        }
        float_view_photo_url = "https://h5.qzone.qq.com/proxy/domain/photo.qzone.qq.com/fcgi-bin/cgi_floatview_photo_list_v2"
        loop_num = ceil(self.settings['SS'] / 40)
        media_list = []
        tid = []
        for i in range(loop_num):
            msglist_payload["pos"] = i * 40
            msglist_payload["num"] = 40 if i < loop_num - 1 else self.settings['SS'] - i * 40
            res = self.get_url(msglist_url, params=msglist_payload).text
            json = self.parse_json(res)
            if self.judge_json(json):
                if "msglist" not in json or not json["msglist"]:
                    break
                count = {}
                data = {}
                for n, t in enumerate(json["msglist"]):
                    tid.append(t["tid"])
                    self.log(f"\rget tid {t['tid']} 【{i * 40 + n + 1}/{self.settings['SS']}】")
                    if "commentlist" in t and t["commentlist"]:
                        if len(t["commentlist"]) != t["cmtnum"]:
                            t["commentlist"] = self.talk_single_parser(t["tid"], t["cmtnum"])
                            if len(t["commentlist"]) != t["cmtnum"]:
                                self.log('说说评论数据有误！请检查爬取的说说评论数据进行调试！')
                                return
                        for c in t["commentlist"]:
                            if c["uin"] != self.settings['self_uin']:
                                """
                                o_url【原图】 == (b_url【大图】 == hd_url【高清图】 网址相同) 图片相同
                                s_url【小图】
                                """
                                for media_type in ["video", "pic"]:
                                    if media_type in c:
                                        for media in c[media_type]:
                                            media_url = ""
                                            for url in ["o_url", "b_url", "hd_url", "s_url"]:
                                                if url in media and media[url]:
                                                    media_url = media[url]
                                                    break
                                            media_list.append(media_url)
                    if "pic" in t and len(t["pic"]) == 9 and "pictotal" in t and t["pictotal"] > 9:
                        float_view_photo_payload["topicId"] = f"{self.settings['target_uin']}_{t['tid']}_1"
                        float_view_photo_payload["picKey"] = f'{t["tid"]},{t["pic"][0]["url1"]}'  # url1 == url2 == url3 == smallurl
                        res = self.get_url(float_view_photo_url, params=float_view_photo_payload).text
                        json2 = self.parse_json(res)
                        if self.judge_json(json2):
                            t["QzoneExporter"] = json2["data"]["photos"]
                    if t.get("has_more_con", 0):
                        msgdetail_payload["tid"] = t["tid"]
                        res = self.post_url(msgdetail_url, data=msgdetail_payload)
                        json2 = res.json()
                        if self.judge_json(json2):
                            t["conlist"] = json2["conlist"]
                            t["content"] = json2["content"]
                        else:
                            self.log(f'说说 tid {t["tid"]} 获取全文失败！')
                    if self.settings['target_uin'] != self.settings['self_uin']:
                        for media_type in ["video", "pic"]:
                            if media_type in t:
                                for media in t[media_type]:
                                    media_url = ""
                                    for url in ["o_url", "b_url", "hd_url", "s_url"]:
                                        if url in media and media[url]:
                                            media_url = media[url]
                                            break
                                    media_list.append(media_url)
                    res = self.get_like_data(f"http://user.qzone.qq.com/{self.settings['target_uin']}/mood/{t['tid']}", t)
                    if res:
                        count[t["tid"]] = res[0]
                        data[t["tid"]] = res[1]
                if count and data:
                    open(f"{self.settings['target_uin']}/talk/like_count_{i * 40 + 1:0>5}-{i * 40 + msglist_payload['num']:0>5}.json", 'w', encoding='utf-8').write(self.dump_json(count))
                    open(f"{self.settings['target_uin']}/talk/like_data_{i * 40 + 1:0>5}-{i * 40 + msglist_payload['num']:0>5}.json", 'w', encoding='utf-8').write(self.dump_json(data))
                open(f"{self.settings['target_uin']}/talk/talk_list_{i * 40 + 1:0>5}-{i * 40 + msglist_payload['num']:0>5}.json", 'w', encoding='utf-8').write(self.dump_json(json))
                self.random_sleep(0, 1, False)
        if msglist_payload["pos"] + msglist_payload["num"] != self.settings['SS']:
            self.log('说说数据有误！请检查爬取的说说数据进行调试！')
            return
        if media_list:
            open(f"{self.settings['target_uin']}/talk/talk_media_list_url.json", 'w', encoding='utf-8').write(self.dump_json(media_list))
        self.log(f"说说实际数目情况：{len(tid)}/{self.settings['SS']}")
        open(f"{self.settings['target_uin']}/talk/talk_list_tid.json", 'w', encoding='utf-8').write(self.dump_json(tid))

    def talk_single_parser(self, tid, comments):
        single_msglist_payload = {
            "format": "jsonp",
            "need_private_comment": "1",
            "uin": self.settings['target_uin'],
            "tid": tid,
            "g_tk": self.settings['g_tk'],
            "pos": "0",
            "num": "20",
        }
        single_msglist_url = "https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msgdetail_v6"
        loop = ceil(comments / 20)
        comment = []
        for c in range(loop):
            single_msglist_payload["pos"] = c * 20
            single_msglist_payload["num"] = 20 if c < loop - 1 else comments - c * 20
            res = self.get_url(single_msglist_url, params=single_msglist_payload).text
            json = self.parse_json(res)
            if self.judge_json(json):
                comment += json["commentlist"]
        return comment

    def get_like_data(self, url, obj=None):
        like_count_payload = {
            "fupdate": "1",
            "unikey": url,
            "g_tk": self.settings['g_tk']
        }
        like_count_url = "https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/user/qz_opcnt2"  # 判断是否有赞、统计点赞个数
        like_data_payload = {
            "uin": self.settings['self_uin'],
            "unikey": url,
            "begin_uin": "0",
            "query_count": "60",
            "if_first_page": "1",
            "g_tk": self.settings['g_tk']
        }
        like_data_url = "https://user.qzone.qq.com/proxy/domain/users.qzone.qq.com/cgi-bin/likes/get_like_list_app"  # 所有点赞信息列表
        res = self.get_url(like_count_url, params=like_count_payload).text
        json = self.parse_json(res)
        if self.judge_json(json):
            if json["data"][0]["current"]["likedata"]["cnt"]:
                total_num = 0
                data = []
                res = self.get_url(like_data_url, params=like_data_payload).text.encode("iso8859")
                try:
                    json2 = self.parse_json(res.decode("utf-8"))
                except UnicodeError:
                    json2 = self.parse_json(res.decode("gb2312"))
                except Exception as e:
                    json2 = None
                    self.log(e)
                while self.judge_json(json2) and "data" in json2 and json2["data"]["total_number"] and total_num < json["data"][0]["current"]["likedata"]["cnt"]:
                    data.append(json2)
                    like_data_payload["begin_uin"] = json2["data"]["like_uin_info"][-1]["fuin"]
                    like_data_payload["if_first_page"] = 0
                    total_num += json2["data"]["total_number"]
                    res = self.get_url(like_data_url, params=like_data_payload).text.encode("iso8859")
                    try:
                        json2 = self.parse_json(res.decode("utf-8"))
                    except UnicodeError:
                        json2 = self.parse_json(res.decode("gb2312"))
                    except Exception as e:
                        self.log(e)
                        break
                    self.random_sleep(0, 1, False)
                if len(data) == 1:
                    data = data[0]
                elif data:
                    temp = data[0]
                    for dd in data[1:]:
                        temp["data"]["total_number"] += dd["data"]["total_number"]
                        temp["data"]["like_uin_info"] += dd["data"]["like_uin_info"]
                    data = temp
                res = None
                if '/blog/' in url:  # 日志点赞
                    open(f"{self.settings['target_uin']}/blog/{obj['cate']}/{obj['title']}_{obj['blogId']}_like_count.json", 'w', encoding='utf-8').write(self.dump_json(json))
                    open(f"{self.settings['target_uin']}/blog/{obj['cate']}/{obj['title']}_{obj['blogId']}_like_data.json", 'w', encoding='utf-8').write(self.dump_json(data))
                    res = json["data"][0]["current"]["newdata"]["RZRD"]
                elif '/photo/' in url:  # 照片点赞
                    open(f"{self.settings['target_uin']}/photo/{obj['name']}/like_count.json", 'w', encoding='utf-8').write(self.dump_json(json))
                    open(f"{self.settings['target_uin']}/photo/{obj['name']}/like_data.json", 'w', encoding='utf-8').write(self.dump_json(data))
                    res = None
                elif '/mood/' in url:  # 说说点赞
                    res = (json, data)
        return res

    def top200_friend_ship(self, do=1):
        """
        获取亲密度前200位好友，默认前200名以内才有特别关心，不计算200以外的特别关心。
        :param do: 我在意谁【do: 1】；谁在意我【do: 2】
        :return: friend_ship好友关系【'排序', 'QQ号', '备注', '亲密度', '特别关心'】, special特别关心QQ号列表
        """
        assert do in [1, 2], '我在意谁【do: 1】；谁在意我【do: 2】'
        url = "https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/tfriend/friend_ship_manager.cgi"
        parameters = self.parse_parameters("""
            uin: 
            do: 
            rd: 
            fupdate: 1
            clean: 1
            g_tk: 
        """)
        parameters["uin"] = self.settings['self_uin']
        parameters["do"] = str(do)
        parameters["rd"] = str(__import__('random').random())
        parameters["g_tk"] = self.settings['g_tk']
        r = self.get_url(url, params=parameters).text
        json = self.parse_json(r)
        if self.judge_json(json):
            friend_ship = [['排序', 'QQ号', '备注', '亲密度', '特别关心']]
            special = []
            for _ in json["data"]["items_list"]:
                friend_ship.append([_["index"], _["uin"], _["name"], _["score"], _["special_flag"] == "1" and "是" or "否"])
                if _["special_flag"] == "1":
                    special.append(_["uin"])
            return friend_ship, special
        return None

    def one_friend_ship(self, passive=None):
        """
        获取单个好友的所有信息。
        :param passive: 目标QQ号（仅限好友）
        :return: 双向亲密度、加好友日期、加好友天数、共有的群
        """
        if self.settings['self_uin'] == passive:
            self.log('亲密度关系必须是两个不同的QQ号！')
            return
        res = {}
        url = "https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/friendship/cgi_friendship"
        parameters = self.parse_parameters("""
            activeuin: 
            passiveuin: 
            situation: 1
            isCalendar: 1
            g_tk: 
        """)
        parameters["g_tk"] = self.settings['g_tk']
        parameters["activeuin"] = self.settings['self_uin']
        parameters["passiveuin"] = passive
        r = self.get_url(url, params=parameters).text
        json = self.parse_json(r)
        if self.judge_json(json):
            if json["data"]["isFriend"] != 1:
                return None
            start = self.str_time(json["data"]["addFriendTime"])
            differ = int((time() - json["data"]["addFriendTime"]) / 3600 / 24) + 2
            res[f"{self.settings['self_uin']}->{passive}"] = {
                "亲密度": int(json["data"]["intimacyScore"]),
                "加好友日期": start,
                "加好友天数": differ,
                "共有的群": [_["name"] for _ in json["data"]["common"]["group"]]
            }
        else:
            return None
        self.random_sleep(1, 2)
        parameters["activeuin"] = passive
        parameters["passiveuin"] = self.settings['self_uin']
        r = self.get_url(url, params=parameters).text
        json = self.parse_json(r)
        if self.judge_json(json):
            if json["data"]["isFriend"] != 1:
                return None
            start = self.str_time(json["data"]["addFriendTime"])
            differ = int((time() - json["data"]["addFriendTime"]) / 3600 / 24) + 2
            res[f"{passive}->{self.settings['self_uin']}"] = {
                "亲密度": int(json["data"]["intimacyScore"]),
                "加好友日期": start,
                "加好友天数": differ,
                "共有的群": [_["name"] for _ in json["data"]["common"]["group"]]
            }
        else:
            return None
        return res

    def all_groups(self, info=0):
        """
        获取所有群概括信息。
        :param info: 除了【0】选项，可叠加返回
            【0】返回创建、管理、加入的群概括信息
            【1】返回创建群的详情信息
            【2】返回管理群的详情信息
            【4】返回加入群的详情信息
        :return: 根据 info 改变输出
        """
        url = "https://qun.qq.com/cgi-bin/qun_mgr/get_group_list"
        data = self.parse_parameters("""
            bkn: 
        """)
        data["bkn"] = self.settings['bkn']
        r = self.post_url(url, data=data, cookie=self.settings['qun_cookie']).text
        json = self.parse_json(r)
        groups = {}
        groups_information = {}
        if not (json["ec"] or json["errcode"]):
            create = json["create"]  # 创建的群
            manage = json["manage"]  # 管理的群
            join = json["join"]  # 加入的群
            if not info:
                return create, manage, join
            if info - 4 >= 0:
                info -= 4
                groups.update({_["gc"]: _["gn"] for _ in join})
            if info - 2 >= 0:
                info -= 2
                groups.update({_["gc"]: _["gn"] for _ in manage})
            if info - 1 >= 0:
                info -= 1
                groups.update({_["gc"]: _["gn"] for _ in create})
            assert not info, '参数输入错误！'
            now = 0
            al = len(groups)
            for g in groups:
                now += 1
                self.log(f'当前第 {now}/{al} 个群，群号：{g}')
                member = self.group_member(int(g))
                if member:
                    member[int(g)]["群名"] = groups[g]
                    groups_information.update(member)
                else:
                    return None
                self.random_sleep(1, 2)
            return groups_information
        self.log('出现问题！')
        return None

    def group_member(self, group: int):
        """
        获取单个群详细信息。
        :param group: 群号码
        :return: 返回群详细信息（字典）
        :rtype: dict
        """
        url = "https://qun.qq.com/cgi-bin/qun_mgr/search_group_members"
        # end 最多比 st 大 40，即每次最多获取41个，序号从0开始，0为创建者
        """
        sort 参数表：（0为没有任何排序）
            Q龄⬆【9】     入群时间⬆【11】        等级(记分)⬆【15】      最后发言⬆【17】
            Q龄⬇【8】     入群时间⬇【10】        等级(记分)⬇【14】      最后发言⬇【16】
        条件筛选：（左0为0，右0无限大，可以灵活调整）
            性别（是女）：g: 【0】【1】
            Q龄（年）：qage: 【0|1】【1|3】【3-5】【5-7】【7|0】
            入群时长（月）：join_time: 【0|1】【1|3】【3-6】【6-12】【12|0】
            等级（levelname）：lv: 【1】【2】【3】【4】【5】【6】
                【101】【102】【103】【104】【105】【106】【107】【108】【109】
                【110】【111】【112】【113】【114】【115】【116】【117】【118】
                【197】【198】【199】【10】【11】【12】【13】【14】【15】
            最后发言（月）：last_speak_time: 【0|1】【1|3】【3-6】【6-12】【12|0】
        """
        data = self.parse_parameters("""
            gc: 
            st: 0
            end: 0
            sort: 0
            bkn: 
        """)
        data["gc"] = group
        data["bkn"] = self.settings['bkn']
        r = self.post_url(url, data=data, cookie=self.settings['qun_cookie']).text
        json = self.parse_json(r)
        members = {group: {}}
        if 'mems' in json and not json["mems"][0]["role"]:
            create = {json["mems"][0]["uin"]: {
                "昵称": json["mems"][0]["nick"],
                "群昵称": json["mems"][0]["card"],
                "性别": "女" if json["mems"][0]["g"] else "男",
                "Q龄": json["mems"][0]["qage"],
                "入群时间": self.str_time(json["mems"][0]["join_time"], ymd=True, hms=True),
                "最后发言": self.str_time(json["mems"][0]["last_speak_time"], ymd=True, hms=True)
            }}
            count = json["count"]
            max_count = json["max_count"]
            members[group]["群名"] = ""
            members[group]["当前人数"] = count
            members[group]["最多人数"] = max_count
            members[group]["创建者"] = create
            members[group]["管理员"] = {}
            members[group]["群成员"] = {}
            num = 40
            count -= 1
            for n in range(count // num + (1 if count % num else 0)):
                data["st"] = n * num + 1
                data["end"] = (n + 1) * num if (n + 1) * num < count else count
                r = self.post_url(url, data=data, cookie=self.settings['qun_cookie']).text
                json = self.parse_json(r)
                if 'mems' in json:
                    for p in json["mems"]:
                        person = {
                            "昵称": p["nick"],
                            "群昵称": p["card"],
                            "性别": "女" if p["g"] else "男",
                            "Q龄": p["qage"],
                            "入群时间": self.str_time(p["join_time"], ymd=True, hms=True),
                            "最后发言": self.str_time(p["last_speak_time"], ymd=True, hms=True)
                        }
                        if p["role"] == 1:
                            members[group]["管理员"][p["uin"]] = person
                        elif p["role"] == 2:
                            members[group]["群成员"][p["uin"]] = person
                self.random_sleep(1, 2)
            return members
        return None

    def get_special_friends(self):
        """
        获取所有特别关心好友QQ号。
        """
        url = "https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/tfriend/specialcare_get.cgi"
        parameters = self.parse_parameters("""
            uin: 
            do: 3
            fupdate: 1
            rd: 
            g_tk: 
        """)
        parameters["uin"] = self.settings['self_uin']
        parameters["rd"] = str(__import__('random').random())
        parameters["g_tk"] = self.settings['g_tk']
        r = self.get_url(url, params=parameters).text
        json = self.parse_json(r)
        if self.judge_json(json):
            return [friends["uin"] for friends in json["data"]["items_special"]]
        return None

    def all_friends(self, s: int = True, a: int = False):
        """
        获取所有好友概括信息。
        :param s: 获取特别关心好友QQ号
        :param a: 获取所有好友全部信息（爬取时间较长）
        :return: 好友分组字典、好友昵称、好友备注、黄钻等级、特别关心(s)【非a】
        """
        if a:
            s = True
        url = "https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/tfriend/friend_show_qqfriends.cgi"
        parameters = self.parse_parameters("""
            uin: 
            follow_flag: 0
            groupface_flag: 0
            fupdate: 1
            g_tk: 
        """)
        parameters["uin"] = self.settings['self_uin']
        parameters["g_tk"] = self.settings['g_tk']
        r = self.get_url(url, params=parameters).text
        json = self.parse_json(r)
        if self.judge_json(json):
            groups = {_["gpid"]: _["gpname"] for _ in json["data"]["gpnames"]}
            friends = json["data"]["items"]
            if a:
                group_friends = {groups[_]: [] for _ in groups}
            else:
                group_friends = {groups[_]: {} for _ in groups}
            special = None
            if s:
                special = self.get_special_friends()
            now = 0
            al = len(friends)
            for f in friends:
                now += 1
                self.log(f'当前第 {now}/{al} 个好友，QQ号：{f["uin"]}')
                if not a:
                    group_friends[groups[f["groupid"]]][f["uin"]] = {
                        "好友昵称": f["name"],
                        "好友备注": f["remark"],
                        "黄钻等级": f["yellow"] if f["yellow"] > 0 else "目前未开通黄钻",
                        "特别关心": "未知"
                    }
                    if s:
                        group_friends[groups[f["groupid"]]][f["uin"]]["特别关心"] = "是" if f["uin"] in special else "否"
                else:
                    if f["uin"] != int(self.settings['self_uin']):
                        while 1:
                            try:
                                friend = self.one_friend_ship(f["uin"])
                                break
                            except Warning:
                                self.random_sleep(2, 3)
                    else:
                        res = self.all_groups()
                        if res:
                            create, manage, join = res
                            group = [_["gn"] for _ in create] + [_["gn"] for _ in manage] + [_["gn"] for _ in join]
                        else:
                            group = []
                        # birth = qq_birth()["register_time"]
                        birth = int(time())
                        friend = {f"{self.settings['self_uin']}->{f['uin']}": {"亲密度": 100, "加好友日期": self.str_time(birth), "加好友天数": f"{int(time() - 1367197112) // 3600 // 24}", "共有的群": group}}
                    if friend is None:
                        group_friends[groups[f["groupid"]]].append([f["uin"], f["name"], f["remark"], '好友状态异常', '好友状态异常', "是" if f["uin"] in special else "否",
                                                                    '好友状态异常', '好友状态异常', f["yellow"] if f["yellow"] > 0 else "目前未开通黄钻", '好友状态异常'])
                        continue
                    group_friends[groups[f["groupid"]]].append([f["uin"], f["name"], f["remark"],
                                                                f"""{friend[f"{self.settings['self_uin']}->{f['uin']}"]["亲密度"]}""",
                                                                f"""{friend[f"{f['uin']}->{self.settings['self_uin']}"]["亲密度"]}""",
                                                                "是" if f["uin"] in special else "否", friend[f"{self.settings['self_uin']}->{f['uin']}"]["加好友日期"],
                                                                f"""{friend[f"{self.settings['self_uin']}->{f['uin']}"]["加好友天数"]}天""",
                                                                f["yellow"] if f["yellow"] > 0 else "目前未开通黄钻",
                                                                friend[f"{self.settings['self_uin']}->{f['uin']}"]["共有的群"]])
                    self.random_sleep(1, 2)
            return group_friends
        return None


if __name__ == '__main__':
    qq = Crawler()
    qq.mainloop()
