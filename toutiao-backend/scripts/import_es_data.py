import requests
import json
import time

# articles删除索引库
host = 'http://localhost:9200'
articles_index_url = host + '/articles'

ret = requests.delete(articles_index_url)

# 创建articles索引库
headers = {'Content-Type': 'application/json'}
data = {
   "settings" : {
        "index": {
            "number_of_shards" : 3,
            "number_of_replicas" : 1
        }
   }
}
ret = requests.put(articles_index_url, data=json.dumps(data), headers=headers)
print(articles_index_url, ret)

time.sleep(1)

# 创建articlies的类型和映射
articles_index_type_url = host + '/articles/_mapping/article'
data ={
     "_all": {
          "analyzer": "ik_max_word"
      },
      "properties": {
          "article_id": {
              "type": "long",
              "include_in_all": "false"
          },
          "user_id": {
              "type": "long",
              "include_in_all": "false"
          },
          "title": {
              "type": "text",
              "analyzer": "ik_max_word",
              "include_in_all": "true",
              "boost": 2
          },
          "content": {
              "type": "text",
              "analyzer": "ik_max_word",
              "include_in_all": "true"
          },
          "status": {
              "type": "byte",
              "include_in_all": "false"
          },
          "create_time": {
              "type": "date",
              "include_in_all": "false"
          }
      }
}
ret = requests.put(articles_index_type_url, data=json.dumps(data), headers=headers)
print(articles_index_type_url, ret)

time.sleep(1)



completions_index_url = host + '/completions'

# 删除自动补全索引库
ret = requests.delete(completions_index_url)

# 创建自动补全索引库
data = {
   "settings" : {
       "index": {
           "number_of_shards" : 3,
           "number_of_replicas" : 1
       }
   }
}
ret = requests.put(completions_index_url, data=json.dumps(data), headers=headers)
print(completions_index_url, ret)

time.sleep(1)

#创建自动补全类型映射
completions_index_type_url = host + '/completions/_mapping/words'

data = {
     "words": {
          "properties": {
              "suggest": {
                  "type": "completion",
                  "analyzer": "ik_max_word"
              }
          }
     }
}
ret = requests.put(completions_index_type_url, data=json.dumps(data), headers=headers)
print(completions_index_type_url, ret)

# 导入文章数据和自动补全数据
from public_app import app, db, Article, ArticleContent
t1 = time.time()
obj_arts = Article.query.limit(10000)
for art in obj_arts:
    con = ArticleContent.query.get(art.id)
    # 组装文档数据
    data = {
      "article_id": art.id,
      "user_id": art.user_id,
      "title": art.title,
      "content": con.content,
      "status": art.status,
      "create_time": art.ctime.strftime('%Y-%m-%dT%H:%H:%S')
    }
    # print(data.get('create_time'))
    url = host + '/articles/article/{}'.format(art.id)
    # 导入文章数据
    ret = requests.put(url, headers=headers, data=json.dumps(data))
    # 导入自动补全数据
    data = {
        "suggest": art.title
    }
    url = host + '/completions/words/{}'.format(art.id)
    ret = requests.put(url, headers=headers, data=json.dumps(data))
    # print(ret.content)
t2 = time.time()
print(t2 - t1)