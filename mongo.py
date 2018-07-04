import pymongo

mainTag = 'nginx'

myclient = pymongo.MongoClient("mongodb://localhost:27017")
mydb = myclient['tech-questions']
mycol = mydb[mainTag]

count = 0
for x in mycol.find():
    count = count + 1
    print(x['question-detail'])
print(count)
