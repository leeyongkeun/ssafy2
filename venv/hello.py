# -*- coding: utf-8 -*-
import re
import urllib.request

from bs4 import BeautifulSoup

from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter

SLACK_TOKEN = 'xoxb-685325156311-678240608162-DMWiL8E2Fz8DyzMvVL84FGRU'
SLACK_SIGNING_SECRET = 'f6e2e62b624489509ea37108dfe010b6'

app = Flask(__name__)
# /listening 으로 슬랙 이벤트를 받습니다.
slack_events_adaptor = SlackEventAdapter(SLACK_SIGNING_SECRET, "/listening", app)
slack_web_client = WebClient(token=SLACK_TOKEN)

# 딕셔너리 read 함수
def read_dictionary(fileName):
    dic = {}
    tmp =''
    with open("musicianDict.txt", "r") as file:
        tmp = file.read()
    # print(type(tmp))
    #print("첫 번째: " + tmp)
    tmp = tmp[1:len(tmp)-1].replace("'", "")
    #print("두 번째: " + tmp)
    secondtmp = tmp.split(',')
    #print(secondtmp)
    # tempList = []


    for i in range(0, len(secondtmp)-1):
        splited = secondtmp[i].split(":")
        dic[splited[0].strip()] = splited[1].strip()

    return dic
# Dictionary 안에 검색한 Musician의 이름이 있는지 Check
def isSearchable(text, musicianDict):
    tempTarget = text[13:]
    if tempTarget not in musicianDict:
        message = tempTarget + "님의 정보를 찾을 수 없습니다. 입력 정보를 확인하세요."
        return message, False
    else:
        return tempTarget + "님의 무엇이 궁금하신가요?\n 제공할 수 있는 정보는 다음과 같습니다. \n\t1. 기본 정보\n\t2. 공연 정보\n\t(입력 예시 : 공연 정보 알려줘.)", True
# 검색한 가수의 공연 정보를 return
def about_Performance(text, target, musicianDict):

    musicianNumber = musicianDict[target]

    url = "http://www.playdb.co.kr/artistdb/detail.asp?ManNo=" + musicianNumber
    source_code = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(source_code, "html.parser")

    title = []
    time = []
    location = []

    for line in soup.find_all('td', class_="ptitle"):
        title.append(line.get_text().strip('\n'))
    for line in soup.find_all('td', class_="time"):
        time.append(line.get_text().strip('\n'))
    for line in soup.find_all('td', class_="small"):
        location.append(line.get_text().strip('\n'))
    message = target + '의 공연 정보입니다.\n'

    for i in range(0, len(title)):
        message += title[i] + " / " + time[i] + " / " + location[i] + "\n"

    return message

def about_Info(text, target, musicianDict):
    musicianNumber = musicianDict[target]
    url = "http://www.playdb.co.kr/artistdb/detail.asp?ManNo=" + musicianNumber
    source_code = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(source_code, "html.parser")

    dtList = []
    ddList = []

    for data in soup.find_all("div", class_="detaillist2"):
        for i in data.find_all('dt'):
            dtList.append(str(i)[str(i).find('=')+1:str(i).find('src')].strip().replace('"', ''))
        for i in data.find_all('dd'):
            ddList.append(i.get_text().strip())

    message = target + '의 기본 정보입니다.\n'
    for i in range(0, len(dtList)):
        message += dtList[i] + " : " + ddList[i] + "\n"

    return message
def about_Article(target):
    message = ''
    articleList = []
    url = ''
    url1 = "https://www.dispatch.co.kr/search?q="
    url2 = str(target.encode("UTF-8")).replace("'", "")
    url = url1 + url2
    url = url[0:36] + url[37:].replace('\\x', '%').upper()

    source_code = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(source_code, "html.parser")
    for data in soup.find_all('a')[29:36]:
        if('href' in str(data)):
            articleList.append("www.dispatch.co.kr/" + str(data)[str(data).find('href')+7:17])

    data = soup.find_all('p')[0:14]
    cnt = 0
    for i in range(0, len(data)):
        if i%2==0:
            message += "제목 : " + data[i].get_text() + "\n\n기사 보러가기 : " + articleList[cnt] + "\n\n"
            cnt += 1
        else:
            message += "요약 : " + data[i].get_text() + "\n\n\n"

    return message
# 챗봇이 멘션을 받았을 경우
@slack_events_adaptor.on("app_mention")
def app_mentioned(event_data):
    musicianDict = read_dictionary("musicianDict.txt")

    channel = event_data["event"]["channel"]
    text = event_data["event"]["text"]

    global target

    if '공연' not in text and'기본' not in text and'근황' not in text and'기사' not in text:
        message, flag = isSearchable(text, musicianDict)
        if(flag):
            target = message[0:message.find('님')]
        else:
            target = ''
        slack_web_client.chat_postMessage(
        channel = channel,
        text = message,
        )
    elif '공연' in text:
        if(target==''):
            message = '먼저 뮤지션의 이름을 알려주세요.'
        else:
            message = about_Performance(text, target, musicianDict)
        slack_web_client.chat_postMessage(
            channel = channel,
            text = message
        )
    elif '기사' in text:
        if(target==''):
            message = '먼저 뮤지션의 이름을 알려주세요.'
        else:
            message = about_Article(target)
        slack_web_client.chat_postMessage(
            channel = channel,
            text = message
        )

    elif '기본' in text:
        if(target==''):
            message = '먼저 뮤지션의 이름을 알려주세요.'
        else:
            message = about_Info(text, target, musicianDict)
        slack_web_client.chat_postMessage(
            channel = channel,
            text = message
        )




# / 로 접속하면 서버가 준비되었다고 알려줍니다.
@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=4040)



# def _crawl(text):
#     musicianDict = read_dictionary("musicianDict.txt")
#     text2 = text[13:]
#     message = ''
#     if (text2 not in musicianDict):
#         return text2 + "님의 정보를 찾을 수 없습니다."
#
#
#     musicianNumber = musicianDict[text2]
#
#     url = "http://www.playdb.co.kr/artistdb/detail.asp?ManNo=" + musicianNumber
#     source_code = urllib.request.urlopen(url).read()
#     soup = BeautifulSoup(source_code, "html.parser")
#
#     title = []
#     time = []
#     location = []
#
#     for line in soup.find_all('td', class_="ptitle"):
#         title.append(line.get_text().strip('\n'))
#     for line in soup.find_all('td', class_="time"):
#         time.append(line.get_text().strip('\n'))
#     for line in soup.find_all('td', class_="small"):
#         location.append(line.get_text().strip('\n'))
#     message = text2 + '의 공연 정보입니다.\n'
#     for i in range(0, len(title)):
#         message += title[i] + " / " + time[i] + " / " + location[i] + "\n"
#     return message