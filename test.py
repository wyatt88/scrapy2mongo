from urllib.request import urlopen
from bs4 import BeautifulSoup
import pymongo
import logging
import sys
from multiprocessing.dummy import Pool as ThreadPool

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

mainTag = 'nginx'

myclient = pymongo.MongoClient("mongodb://localhost:27017")
mydb = myclient['tech-questions']
mycol = mydb[mainTag]

pagesize = 50
stackoverflowURL = "https://stackoverflow.com"
initURL = stackoverflowURL + \
    ("/questions/tagged/%s?sort=newest&pagesize=%d" % (mainTag, pagesize))

initPage = 1
endPage = 1000


def getQuestionDetail(detailURL):
    detailhtml = urlopen(stackoverflowURL+detailURL)
    detailhtmlStr = detailhtml.read()
    questionObj = BeautifulSoup(detailhtmlStr, 'lxml')
    param = questionObj.find_all('div', {'class': 'post-text'})[0].text
    return str(param)


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
    questionDict['date'] = question.find(
        'span', {'class': 'relativetime'})['title']
    questionDict['question-detail'] = getQuestionDetail(
        questionDict['question-hyperlink'])
    mycol.insert_one(questionDict)


for i in range(initPage, endPage):
    html = urlopen(initURL+("&page=%d" % i))
    root.debug("The current page is %d" % i)
    htmlStr = html.read()
    bsObj = BeautifulSoup(htmlStr, 'lxml')
    questionList = bsObj.find_all('div', attrs={'class': 'question-summary'})
    pool = ThreadPool(len(questionList))
    pool.map(saveQuestion, questionList)
    pool.join()
