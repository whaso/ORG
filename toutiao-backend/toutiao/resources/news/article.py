from flask_restful import Resource, abort
from flask import g, current_app
from sqlalchemy.orm import load_only
from flask_restful.reqparse import RequestParser
from flask_restful import inputs
import re
import random
from datetime import datetime
import time
from redis.exceptions import ConnectionError
from sqlalchemy.exc import SQLAlchemyError

from models.news import Article, ArticleContent, Attitude
from rpc.recommend import user_reco_pb2, user_reco_pb2_grpc
from . import constants
from utils import parser
from cache import article as cache_article
from cache import user as cache_user
from cache import statistic as cache_statistic
from models import db
from utils.decorators import login_required, validate_token_if_using, set_db_to_write, set_db_to_read
from utils.logging import write_trace_log


class ArticleResource(Resource):
    """
    文章
    """
    method_decorators = [set_db_to_read, validate_token_if_using]

    def _feed_similar_articles(self, article_id):
        """
        获取相似文章
        :param article_id:
        :return:
        """
        req = user_reco_pb2.Article()
        req.article_id = article_id
        req.article_num = constants.RECOMMENDED_SIMILAR_ARTICLE_MAX

        stub = user_reco_pb2_grpc.UserRecommendStub(current_app.rpc_reco)
        resp = stub.article_recommend(req)

        return resp.article_id

    def get(self, article_id):
        """
        获取文章详情
        :param article_id: int 文章id
        """
        # 写入埋点日志
        qs_parser = RequestParser()
        qs_parser.add_argument('Trace', type=inputs.regex(r'^.+$'), required=False, location='headers')
        args = qs_parser.parse_args()

        user_id = g.user_id

        # 查询文章数据
        exist = cache_article.ArticleInfoCache(article_id).exists()
        if not exist:
            abort(404, message='The article does not exist.')

        article = cache_article.ArticleDetailCache(article_id).get()

        # 推荐系统所需埋点
        if args.Trace:
            write_trace_log(args.Trace, channel_id=article['ch_id'])

        article['is_followed'] = False
        article['attitude'] = None
        # 增加用户是否收藏了文章
        article['is_collected'] = False

        if user_id:
            # 非匿名用户添加用户的阅读历史
            try:
                cache_user.UserReadingHistoryStorage(user_id).save(article_id)
            except ConnectionError as e:
                current_app.logger.error(e)

            # 查询关注
            # article['is_followed'] = cache_user.UserFollowingCache(user_id).determine_follows_target(article['aut_id'])
            article['is_followed'] = cache_user.UserRelationshipCache(user_id).determine_follows_target(article['aut_id'])

            # 查询登录用户对文章的态度（点赞or不喜欢）
            try:
                # article['attitude'] = cache_article.ArticleUserAttitudeCache(user_id, article_id).get()
                article['attitude'] = cache_user.UserArticleAttitudeCache(user_id).get_article_attitude(article_id)
            except SQLAlchemyError as e:
                current_app.logger.error(e)
                article['attitude'] = -1

            # 增加用户是否收藏了文章
            article['is_collected'] = cache_user.UserArticleCollectionsCache(g.user_id).determine_collect_target(article_id)

        # 获取相关文章推荐
        article['recomments'] = []
        try:
            similar_articles = self._feed_similar_articles(article_id)
            for _article_id in similar_articles:
                _article = cache_article.ArticleInfoCache(_article_id).get()
                article['recomments'].append({
                    'art_id': _article['art_id'],
                    'title': _article['title']
                })
        except Exception as e:
            current_app.logger.error(e)

        # 更新阅读数
        cache_statistic.ArticleReadingCountStorage.incr(article_id)
        cache_statistic.UserArticlesReadingCountStorage.incr(article['aut_id'])

        return article


class ArticleListResourceV1D1(Resource):
    """
    获取推荐文章列表数据
    """
    method_decorators = [set_db_to_read, validate_token_if_using]


    def _feed_articles(self, channel_id, timestamp, feed_count):
        """
        获取推荐文章
        :param channel_id: 频道id
        :param feed_count: 推荐数量
        :param timestamp: 时间戳
        :return: [{article_id, trace_params}, ...], timestamp
        """
        # 组装调用gRPC方法的参数
        req = user_reco_pb2.User()

        if g.user_id:
            req.user_id = str(g.user_id)
        elif g.anonymous_id:
            req.user_id = str(g.anonymous_id)
        else:
            req.user_id = ''

        req.channel_id = channel_id
        req.article_num = feed_count
        req.time_stamp = timestamp

        # 使用跟推荐系统通讯的通道，创建存根。
        stub = user_reco_pb2_grpc.UserRecommendStub(current_app.rpc_reco)
        try:
            # 使用存根stub调用推荐系统user_recommend方法，获取文章推荐列表
            resp = stub.user_recommend(req, timeout=5)
        except Exception as e:
            current_app.logger.error(e)
            return [], timestamp

        return resp.recommends, resp.time_stamp

    def get(self):
        """
        获取文章列表
        /v1_1/articles?channel_id&timestamp
        """
        qs_parser = RequestParser()
        qs_parser.add_argument('channel_id', type=parser.channel_id, required=True, location='args')
        qs_parser.add_argument('timestamp', type=inputs.positive, required=True, location='args')
        args = qs_parser.parse_args()
        channel_id = args.channel_id
        timestamp = args.timestamp

        # 默认推荐数量
        per_page = constants.DEFAULT_ARTICLE_PER_PAGE_MIN


        # 获取推荐文章列表
        feeds, pre_timestamp = self._feed_articles(channel_id, timestamp, per_page)

        results = []
        # 使用article_id从缓存工具类中，获取其他文章信息
        for feed in feeds:
            article = cache_article.ArticleInfoCache(feed.article_id).get()
            if article:
                article['trace'] = {
                    'click': feed.params.click,
                    'collect': feed.params.collect,
                    'share': feed.params.share,
                    'read': feed.params.read
                }
                results.append(article)

        return {'pre_timestamp': pre_timestamp, 'results': results}


class UserArticleListResource(Resource):
    """
    用户文章列表
    """
    method_decorators = [set_db_to_read]

    def get(self, user_id):
        """
        获取user_id 用户的文章数据
        """
        exist = cache_user.UserProfileCache(user_id).exists()
        if not exist:
            return {'message': 'Invalid request.'}, 400
        qs_parser = RequestParser()
        qs_parser.add_argument('page', type=inputs.positive, required=False, location='args')
        qs_parser.add_argument('per_page', type=inputs.int_range(constants.DEFAULT_ARTICLE_PER_PAGE_MIN,
                                                                 constants.DEFAULT_ARTICLE_PER_PAGE_MAX,
                                                                 'per_page'),
                               required=False, location='args')
        args = qs_parser.parse_args()
        page = 1 if args.page is None else args.page
        per_page = args.per_page if args.per_page else constants.DEFAULT_ARTICLE_PER_PAGE_MIN

        results = []

        # 已废弃
        # articles = cache_user.get_user_articles(user_id)
        # total_count = len(articles)
        # page_articles = articles[(page - 1) * per_page:page * per_page]

        total_count, page_articles = cache_user.UserArticlesCache(user_id).get_page(page, per_page)

        for article_id in page_articles:
            article = cache_article.ArticleInfoCache(article_id).get()
            if article:
                results.append(article)

        return {'total_count': total_count, 'page': page, 'per_page': per_page, 'results': results}


class CurrentUserArticleListResource(Resource):
    """
    当前用户的文章列表
    """
    method_decorators = [set_db_to_read, login_required]

    def get(self):
        """
        获取当前用户的文章列表
        """
        qs_parser = RequestParser()
        qs_parser.add_argument('page', type=inputs.positive, required=False, location='args')
        qs_parser.add_argument('per_page', type=inputs.int_range(constants.DEFAULT_ARTICLE_PER_PAGE_MIN,
                                                                 constants.DEFAULT_ARTICLE_PER_PAGE_MAX,
                                                                 'per_page'),
                               required=False, location='args')
        args = qs_parser.parse_args()
        page = 1 if args.page is None else args.page
        per_page = args.per_page if args.per_page else constants.DEFAULT_ARTICLE_PER_PAGE_MIN

        results = []

        total_count, page_articles = cache_user.UserArticlesCache(g.user_id).get_page(page, per_page)

        user_article_attitude_cache = cache_user.UserArticleAttitudeCache(g.user_id)
        for article_id in page_articles:
            article = cache_article.ArticleInfoCache(article_id).get()
            if article:
                article['is_liking'] = user_article_attitude_cache.determine_liking_article(article_id)
                results.append(article)

        return {'total_count': total_count, 'page': page, 'per_page': per_page, 'results': results}


