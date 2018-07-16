# coding: utf-8

from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.request import Request
from urllib import parse
from bs4 import BeautifulSoup
import pymongo
import logging
import sys
from multiprocessing.dummy import Pool as ThreadPool
import time
import random


root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

mainTag = 'nginx'

myclient = pymongo.MongoClient("mongodb://10.122.43.177:27017")
mydb = myclient['tech-questions']
mycol = mydb[mainTag]

pagesize = 50
stackoverflowURL = "https://stackoverflow.com"
queryStr = "?sort=newest&pagesize=%d" % pagesize
initURL = stackoverflowURL + \
    ("/questions/tagged/%s?sort=newest&pagesize=%d" % (mainTag, pagesize))
tagIndexURL = stackoverflowURL + "/filter/tags-for-index"
values = {
    'filter': mainTag,
    'tab': 'Popular'
}
initPage = 1
endPage = 100000


def getQuestionDetail(detailURL):
    try:
        time.sleep(random.randint(1, 10))
        detailhtml = urlopen(stackoverflowURL+detailURL)
    except HTTPError as e:
        root.debug("Get detail is wrong,becauls is %s" % e)
        time.sleep(300)
    else:
        detailhtmlStr = detailhtml.read()
        questionObj = BeautifulSoup(detailhtmlStr, 'lxml')
        param = questionObj.find_all('div', {'class': 'post-text'})[0].text
        return str(param)
    return getQuestionDetail(detailURL)


def saveQuestion(question):
    questionDict = {}
    questionDict['question-id'] = question.attrs['id']
    questionDict['vote'] = int(question.find(
        'span', {'class': 'vote-count-post'}).strong.text)
    questionDict['answers'] = int(question.find(
        'div', {'class': 'status'}).strong.text)
    questionDict['summary'] = question.find(
        'div', {'class': 'summary'}).h3.a.text
    questionDict['question-hyperlink'] = question.find(
        'div', {'class': 'summary'}).h3.a['href']
    questionDict['main-tag'] = mainTag
    for tag in question.find_all('a', {'class': 'post-tag'}):
        tagList = []
        if tag.text != mainTag:
            tagList.append(tag.text)
        questionDict['other-tags'] = tagList
    date = ""
    try:
        date = question.find(
            'span', {'class': 'relativetime'})['title']
    except TypeError as e:
        date = "1970-01-01 00:00:01"
        root.debug("There is no span tag and class is relativetime, %s" % e)
    questionDict['date'] = date
    questionDict['question-detail'] = getQuestionDetail(
        questionDict['question-hyperlink'])
    mycol.insert_one(questionDict)


def requestURL(url):
    try:
        html = urlopen(url)
    except HTTPError as e:
        print(e.getcode())
        root.debug("Cant open tag url,Because is %s" % e)
        time.sleep(3)
    else:
        return html
    return ""


def postrequestURL(url, body):
    try:
        data = parse.urlencode(body).encode('utf-8')
        request = Request(url, data)
        response = urlopen(request)
    except HTTPError as e:
        print(e.getcode())
        root.error("Get tags error,because is %s" % e)
        time.sleep(3)
    else:
        return response
    return postrequestURL(url, body)


response = postrequestURL(tagIndexURL, values)
responseStr = response.read()
repbsObj = BeautifulSoup(responseStr, 'lxml')
try:
    tagsBrowser = repbsObj.find('div', attrs={'id': 'tags-browser'})
except TypeError as e:
    root.error("Reason is %s" % str(e))
else:
    try:
        tagsList = tagsBrowser.find_all('div', attrs={'class': "tag-cell"})
    except TypeError as e:
        root.debug("Can't find div tag,the reason is %s" % e)
    else:
        for pertag in tagsList:
            tagName = pertag.a.text
            tagLink = pertag.a['href']
            for i in range(initPage, endPage):
                html = requestURL(stackoverflowURL + tagLink +
                                  queryStr + ("&page=%d" % i))
                if html == "":
                    break
                root.debug("The tag is %s, current page is %d" % (tagName, i))
                htmlStr = html.read()
                bsObj = BeautifulSoup(htmlStr, 'lxml')
                try:
                    questionList = bsObj.find_all(
                        'div', attrs={'class': 'question-summary'})
                except TypeError as e:
                    root.debug(e)
                    root.debug("%s is Finished" % tagName)
                    break
                else:
                    pool = ThreadPool(10)
                    pool.map(saveQuestion, questionList)
                    pool.close()
                    pool.join()

# for i in range(initPage, endPage):
#    html = requestURL(initURL+("&page=%d" % i))
#    root.debug("The current page is %d" % i)
#    htmlStr = html.read()
#    bsObj = BeautifulSoup(htmlStr, 'lxml')
#    questionList = bsObj.find_all('div', attrs={'class': 'question-summary'})
#    pool = ThreadPool(10)
#    pool.map(saveQuestion, questionList)
#    pool.close()
#    pool.join()
