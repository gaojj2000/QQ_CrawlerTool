# _*_ coding:utf-8 _*_
# Project: 
# FileName: table_write.py
# UserName: 高俊佶
# ComputerUser：19305
# Day: 2022/11/10
# Time: 9:49
# IDE: PyCharm
# 2022年，所有bug都将会被丢到海里喂鲨鱼！我说的！不容反驳！

# pip install xlwings
import json
import xlwings
from os.path import isfile
from time import strftime, localtime


def parse_json(text):
    return json.loads(text[text.find('{'): text.rfind('}') + 1])


def str_time(time_number=None, ymd=True, hms=False):
    if ymd and hms:
        return strftime("%Y-%m-%d %H:%M:%S", localtime(time_number))
    if ymd:
        return strftime("%Y-%m-%d", localtime(time_number))
    if hms:
        return strftime("%H:%M:%S", localtime(time_number))
    return ''


def write_friend_table(self_uin):
    while not isfile(f'{self_uin}.json'):
        print(f'数据文件 {self_uin}.json 不存在！')
        self_uin = input('要写入表格的QQ号：')
    title = ['好友QQ号', '好友昵称', '好友备注', '亲密度->', '亲密度<-', '特别关心', '加好友日期', '加好友天数', '黄钻等级', '共有的群']
    data = parse_json(open(f'{self_uin}.json', 'r', encoding='utf-8').read())
    app = xlwings.App(visible=True, add_book=False)
    book = app.books.add()
    have = []
    for group in data:
        g = group.replace(':', '：').replace('：', '【冒号】').replace('\\', '【右斜杠】').replace('/', '【左斜杠】').replace('?', '？') \
                .replace('？', '【问号】').replace('*', '【星号】').replace('[', '【左括号】').replace(']', '【右括号】')[:30]
        print(f'当前分组名：\t{g}')
        have.append(g)
        book.sheets.add(g)
        sheet = book.sheets[g]
        for n, ti in enumerate(title):
            sheet.range(1, n + 1).value = ti
        for n, friend in enumerate(data[group]):
            for i, item in enumerate(friend):
                sheet.range(n + 2, i + 1).value = str(item) if item else ''
                if i == 6 and '-' in item:
                    sheet.range(n + 2, i + 1).api.NumberFormat = 'yyyy-mm-dd'
        sheet.range('A:F,H:J').api.NumberFormat = '@'
        sheet.range('A:J').autofit()
        sheet.range('A:J').api.HorizontalAlignment = -4108
        sheet.range('A:J').api.VerticalAlignment = -4108
    for s in [_.name for _ in book.sheets]:
        if s not in have:
            book.sheets[s].delete()
    book.save(f'{self_uin}_{str_time()}.xlsx')
    book.close()
    app.quit()


if __name__ == '__main__':
    write_friend_table(self_uin=input('要写入表格的QQ号：'))
