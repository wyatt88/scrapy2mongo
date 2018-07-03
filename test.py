from urllib.request import urlopen
from bs4 import BeautifulSoup
import pymongo

mainTag = 'nginx'

myclient = pymongo.MongoClient("mongodb://localhost:32768")
mydb = myclient['tech-questions']
mycol = mydb[mainTag]

pagesize = 50
stackoverflowURL = "https://stackoverflow.com"
initURL = stackoverflowURL + \
    ("/questions/tagged/%s?sort=newest&pagesize=%d" % (mainTag, pagesize))
# testURL = "/questions/tagged/nginx?page=635&sort=newest&pagesize=50"
# questionDict = {}

page = 1


def getQuestionDetail(detailURL):
    detailhtml = urlopen(stackoverflowURL+detailURL)
    detailhtmlStr = detailhtml.read()
    questionObj = BeautifulSoup(detailhtmlStr, 'html5lib')
    param = questionObj.find_all('div', {'class': 'post-text'})[0].text
    return str(param)


for i in range(1, 1000):

    if i == 1:
        html = urlopen(initURL)
    else:
        html = urlopen(initURL+("&page=%d" % i))
    htmlStr = html.read()
    bsObj = BeautifulSoup(htmlStr, 'html5lib')
    questionList = bsObj.find_all('div', attrs={'class': 'question-summary'})
    for question in questionList:
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
