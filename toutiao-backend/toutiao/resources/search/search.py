from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask_restful import inputs
from flask import g, current_app
from redis.exceptions import RedisError

from . import constants
from cache import article as cache_article
from cache import user as cache_user
from models.user import Search
from models import db


class SuggestionResource(Resource):
    """
    联想建议
    """
    def get(self):
        """
        获取联想建议
        """
        qs_parser = RequestParser()
        qs_parser.add_argument('q', type=inputs.regex(r'^.{1,50}$'), required=True, location='args')
        args = qs_parser.parse_args()
        q = args.q

        query = {
            'from': 0, # 从第0个文档开始
            'size': 10, # 返回10条数据
            '_source': False, # 不用返回文档中的字段
            'suggest': { # 建议查询
                'word-completion': { # 指定建议查询返回结果的字段名称
                    'prefix': q, # 需要补全的前缀
                    'completion': { # 从哪个字段获取补全的数据
                        'field': 'suggest' # 指定从suggest字段中获取补全的数据
                    }
                }
            }
        }
        # 先从completions索引库，获取自动补全数据
        ret = current_app.es.search(index='completions', body=query)
        options = ret['suggest']['word-completion'][0]['options']
        # 自动补全没数据，再从自动纠错中获取数据
        if not options:
            query = {
                'from': 0,
                'size': 10,
                '_source': False,
                'suggest': { # 建议查询
                    'text': q, # 需要纠错的数据
                    'word-phrase': { # 指定建议查询返回结果的字段名称
                        'phrase': { # 短语
                            'field': '_all', # 从_all字段中获取纠错数据
                            'size': 1, # 返回一个纠错结果
                            'direct_generator': [{
                                'field': '_all',
                                'suggest_mode': 'always'
                            }]
                        }
                    }
                }
            }
            ret = current_app.es.search(index='articles', doc_type='article', body=query)
            options = ret['suggest']['word-phrase'][0]['options']

        results = []
        for option in options:
            if option['text'] not in results:
                results.append(option['text'])

        return {'options': results}


class SearchResource(Resource):
    """
    搜索结果
    """
    def get(self):
        """
        获取搜索结果
        """
        if g.use_token and not g.user_id:
            return {'message': 'Token has some errors.'}, 401

        qs_parser = RequestParser()
        qs_parser.add_argument('q', type=inputs.regex(r'^.{1,50}$'), required=True, location='args')
        qs_parser.add_argument('page', type=inputs.positive, required=False, location='args')
        qs_parser.add_argument('per_page', type=inputs.int_range(constants.DEFAULT_SEARCH_PER_PAGE_MIN,
                                                                 constants.DEFAULT_SEARCH_PER_PAGE_MAX,
                                                                 'per_page'),
                               required=False, location='args')
        args = qs_parser.parse_args()
        q = args.q
        page = 1 if args.page is None else args.page
        per_page = args.per_page if args.per_page else constants.DEFAULT_SEARCH_PER_PAGE_MIN

        # Search from Elasticsearch
        query = {
            'from': (page-1)*per_page, # 偏移
            'size': per_page, # 返回数量
            '_source': False,
            'query': {
                'bool': {
                    'must': [
                        {'match': {'_all': q}} # 对q进行全文检索
                    ],
                    'filter': [
                        {'term': {'status': 2}} # 必须是通过审核的文章
                    ]
                }
            }
        }
        ret = current_app.es.search(index='articles', doc_type='article', body=query)

        total_count = ret['hits']['total']

        results = []

        hits = ret['hits']['hits']
        for result in hits:
            article_id = int(result['_id'])
            # 从缓存中获取文章数据
            article = cache_article.ArticleInfoCache(article_id).get()
            # 如果缓存中存在就添加到返回结果
            if article:
                results.append(article)

        # 记录用户的搜索记录
        if g.user_id and page == 1:
            try:
                cache_user.UserSearchingHistoryStorage(g.user_id).save(q)
            except RedisError as e:
                current_app.logger.error(e)

        # 添加elasticsearch索引文档
        if total_count and page == 1:
            query = {
                '_source': False,
                'query': {
                    'match': {
                        'suggest': q
                    }
                }
            }
            # 查询自动补全是否有该搜索词
            ret = current_app.es.search(index='completions', doc_type='words', body=query)
            if ret['hits']['total'] == 0:
                doc = {
                    'suggest': {
                        'input': q,
                        'weight': constants.USER_KEYWORD_ES_SUGGEST_WEIGHT
                    }
                }
                try:
                    # 没有就添加一个文档记录
                    current_app.es.index(index='completions', doc_type='words', body=doc)
                except Exception:
                    pass

        return {'total_count': total_count, 'page': page, 'per_page': per_page, 'results': results}
