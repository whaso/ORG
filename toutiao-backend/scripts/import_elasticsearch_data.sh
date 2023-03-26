#! /bin/bash

curl -X DELETE 127.0.0.1:9200/articles

curl -X DELETE 127.0.0.1:9200/completions

curl -X PUT 127.0.0.1:9200/articles -H 'Content-Type: application/json' -d'
{
   "settings" : {
        "index": {
            "number_of_shards" : 3,
            "number_of_replicas" : 1
        }
   }
}'

curl -X PUT 127.0.0.1:9200/articles/_mapping/article -H 'Content-Type: application/json' -d'
{
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
}'


curl -X PUT 127.0.0.1:9200/completions -H 'Content-Type: application/json' -d'
{
   "settings" : {
       "index": {
           "number_of_shards" : 3,
           "number_of_replicas" : 1
       }
   }
}'

curl -X PUT 127.0.0.1:9200/completions/_mapping/words -H 'Content-Type: application/json' -d'
{
     "words": {
          "properties": {
              "suggest": {
                  "type": "completion",
                  "analyzer": "ik_max_word"
              }
          }
     }
}'

source ~/.bash_profile

sudo /usr/share/logstash/bin/logstash -f /home/python/toutiao-backend/scripts/logstash_mysql_completion.conf

sudo /usr/share/logstash/bin/logstash -f /home/python/toutiao-backend/scripts/logstash_mysql.conf