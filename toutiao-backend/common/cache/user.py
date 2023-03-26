from flask import current_app, g
import time
from sqlalchemy.orm import load_only
from sqlalchemy import func
import json
from redis.exceptions import RedisError, ConnectionError
from sqlalchemy.exc import SQLAlchemyError

from models.user import User, Relation, UserProfile
from models.news import Article, Collection, Attitude, CommentLiking, Comment
from models import db
from . import constants
from .statistic import UserArticlesCountStorage
from .statistic import UserFollowingsCountStorage
from .statistic import UserFollowersCountStorage
from .statistic import UserLikedCountStorage
from cache import statistic as cache_statistic


class UserProfileCache(object):
    """
    用户信息缓存
    """
    def __init__(self, user_id):
        self.key = 'user:{}:profile'.format(user_id)
        self.user_id = user_id

    def save(self, user=None, force=False):
        """
        设置用户数据缓存
        """
        # 使用redis集群做为缓存层
        rc = current_app.redis_cluster

        # 从数据库查询用户信息
        user = User.query.options(load_only(User.name,
                                            User.mobile,
                                            User.profile_photo,
                                            User.is_media,
                                            User.introduction,
                                            User.certificate)) \
            .filter_by(id=self.user_id).first()

        # 用户不存在返回None
        if user is None:
            # 如果用户为空，设置为-1，防止缓存攻击
            rc.setex(self.key, constants.UserProfileCacheTTL.get_val(), -1)
            return None

        # 组装用户信息数据
        user_data = {
            'mobile': user.mobile,
            'name': user.name,
            'photo': user.profile_photo or '',
            'is_media': user.is_media,
            'intro': user.introduction or '',
            'certi': user.certificate or '',
        }

        # 添加填充字段
        user_data = self._fill_fields(user_data)
        try:
            # 把用户信息设置到redis集群缓存中
            rc.setex(self.key, constants.UserProfileCacheTTL.get_val(), json.dumps(user_data))
        except RedisError as e:
            current_app.logger.error(e)
        return user_data

    def get(self):
        """
        获取用户数据
        :return:
        """
        rc = current_app.redis_cluster

        try:
            # 从集群中获取用户数据
            ret = rc.get(self.key)
        except RedisError as e:
            # 如果连接redis异常，写日志，把ret设置为None, 继续从数据库中获取数据
            current_app.logger.error(e)
            ret = None
        if ret:
            # 缓存中有用户数据(命中)
            user_data = json.loads(ret)
        else:
            # 缓存中没有获取到用户信息，从数据库中获取
            user_data = self.save(force=True)

        if not user_data['photo']:
            # 如果没有用户头像，设置默认头像
            user_data['photo'] = constants.DEFAULT_USER_PROFILE_PHOTO
        # 组装完整的头像链接
        user_data['photo'] = current_app.config['QINIU_DOMAIN'] + user_data['photo']
        return user_data

    def _fill_fields(self, user_data):
        """
        补充字段
        """
        user_data['art_count'] = UserArticlesCountStorage.get(self.user_id)
        user_data['follow_count'] = UserFollowingsCountStorage.get(self.user_id)
        user_data['fans_count'] = UserFollowersCountStorage.get(self.user_id)
        user_data['like_count'] = UserLikedCountStorage.get(self.user_id)
        return user_data


    def clear(self):
        """
        清除
        """
        try:
            current_app.redis_cluster.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

    def exists(self):
        """
        判断用户是否存在
        :return: bool
        """
        rc = current_app.redis_cluster

        try:
            # 从redis获取用户数据
            ret = rc.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None

        if ret is not None:
            # 如果获取到的用户数据为-1，证明用户不存在，只是为了防止缓存攻击而设置为-1
            return False if ret == b'-1' else True
        else:
            # 缓存中未查到，再从数据库中查询
            user_data = self.save(force=True)
            if user_data is None:
                # 用户不存在
                return False
            else:
                # 用户存在
                return True


class UserStatusCache(object):
    """
    用户状态缓存
    """
    def __init__(self, user_id):
        self.key = 'user:{}:status'.format(user_id)
        self.user_id = user_id

    def save(self, status):
        """
        设置用户状态缓存
        :param status:
        """
        try:
            current_app.redis_cluster.setex(self.key, constants.UserStatusCacheTTL.get_val(), status)
        except RedisError as e:
            current_app.logger.error(e)

    def get(self):
        """
        获取用户状态
        :return:
        """
        rc = current_app.redis_cluster

        try:
            status = rc.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            status = None

        if status is not None:
            return status
        else:
            user = User.query.options(load_only(User.status)).filter_by(id=self.user_id).first()
            if user:
                self.save(user.status)
                return user.status
            else:
                return False


class UserAdditionalProfileCache(object):
    """
    用户附加资料缓存（如性别、生日等）
    """
    def __init__(self, user_id):
        self.key = 'user:{}:profilex'.format(user_id)
        self.user_id = user_id

    def save(self):
        rc = current_app.redis_cluster
        profile = UserProfile.query.options(load_only(UserProfile.gender, UserProfile.birthday)) \
            .filter_by(id=self.user_id).first()
        profile_dict = {
            'gender': profile.gender,
            'birthday': profile.birthday.strftime('%Y-%m-%d') if profile.birthday else ''
        }
        try:
            rc.setex(self.key, constants.UserAdditionalProfileCacheTTL.get_val(), json.dumps(profile_dict))
        except RedisError as e:
            current_app.logger.error(e)
        return profile_dict

    def get(self):
        """
        获取用户的附加资料（如性别、生日等）
        :return:
        """
        rc = current_app.redis_cluster

        try:
            ret = rc.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None

        if ret:
            return json.loads(ret)
        else:
            return self.save()

    def clear(self):
        """
        清除用户的附加资料
        :return:
        """
        try:
            current_app.redis_cluster.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)


class UserFollowingCache(object):
    """
    用户关注缓存数据
    """
    def __init__(self, user_id):
        self.key = 'user:{}:following'.format(user_id)
        self.user_id = user_id

    def save(self):
        rc = current_app.redis_cluster
        # redis中没有关注数据，再从数据库中查询
        ret = Relation.query.options(load_only(Relation.target_user_id, Relation.utime)) \
            .filter_by(user_id=self.user_id, relation=Relation.RELATION.FOLLOW) \
            .order_by(Relation.utime.desc()).all()

        followings = []
        cache = []
        for relation in ret:
            # 组装关注列表. [target_user_id1, target_user_id2]
            followings.append(relation.target_user_id)
            # 组装zadd命令要用到的数据. [score1, member1, socre2, member2]
            cache.append(relation.utime.timestamp())
            cache.append(relation.target_user_id)

        if cache:
            # 如果存在关注数据，把关注列表数据缓存到redis集群中
            try:
                # 使用pipeline执行redis事务
                pl = rc.pipeline()
                # zadd(self.key, score1, member1, score2, member2)
                pl.zadd(self.key, *cache)
                # 设置缓存时间
                pl.expire(self.key, constants.UserFollowingsCacheTTL.get_val())
                # 执行redis事务
                pl.execute()
            except RedisError as e:
                current_app.logger.error(e)
        else:
            # 如果不存在关注列表，也往redis中插入一条，member为-1(防止缓存攻击). 在获取用户信息的时候过滤一下即可
            rc.zadd(self.key, 1, -1)
            rc.expire(self.key, constants.UserFollowingsCacheTTL.get_val())

        return followings

    def get(self):
        """
        获取用户的关注列表
        :return:
        """
        rc = current_app.redis_cluster

        try:
            # 获取用户所有的关注id列表
            ret = rc.zrevrange(self.key, 0, -1)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None

        if ret:
            # 从redis中获取到的都是bytes数据类型，用户id是整形，需要转换再返回
            followings = []
            for uid in ret:
                # 把-1过滤掉
                target_user_id = int(uid)
                if target_user_id != -1:
                    followings.append(target_user_id)
            return followings
        else:
            # 如果redis中没有获取到，再从数据库中查询
            followings = self.save()
            return followings

    def update(self, target_user_id, timestamp, increment=1):
        """
        更新用户的关注缓存数据
        :param target_user_id: 被关注的目标用户
        :param timestamp: 关注时间戳
        :param increment: 增量
        :return:
        """
        rc = current_app.redis_cluster

        try:
            # increment > 0表示关注，< 0 表示取消关注
            if increment > 0:
                rc.zadd(self.key, timestamp, target_user_id)
            else:
                rc.zrem(self.key, target_user_id)
        except RedisError as e:
            current_app.logger.error(e)

    def determine_follows_target(self, target_user_id):
        """
        判断用户是否关注了目标用户
        :param target_user_id: 被关注的用户id
        :return:
        """
        followings = self.get()

        return int(target_user_id) in followings


class UserFollowersCache(object):
    """
    用户粉丝缓存
    """
    def __init__(self, user_id):
        self.key = 'user:{}:fans'.format(user_id)
        self.user_id = user_id

    def save(self):
        rc = current_app.redis_cluster
        ret = Relation.query.options(load_only(Relation.user_id, Relation.utime)) \
            .filter_by(target_user_id=self.user_id, relation=Relation.RELATION.FOLLOW) \
            .order_by(Relation.utime.desc()).all()

        followers = []
        cache = []
        for relation in ret:
            followers.append(relation.user_id)
            cache.append(relation.utime.timestamp())
            cache.append(relation.user_id)

        if cache:
            try:
                pl = rc.pipeline()
                pl.zadd(self.key, *cache)
                pl.expire(self.key, constants.UserFansCacheTTL.get_val())
                results = pl.execute()
                if results[0] and not results[1]:
                    rc.delete(self.key)
            except RedisError as e:
                current_app.logger.error(e)
        else:
            rc.zadd(self.key, 1, -1)
            rc.expire(self.key, constants.UserFansCacheTTL.get_val())
        return followers

    def get(self):
        """
        获取用户的粉丝列表
        :return:
        """
        rc = current_app.redis_cluster

        try:
            ret = rc.zrevrange(self.key, 0, -1)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None

        if ret:
            # 从redis中获取到的都是bytes数据类型，用户id是整形，需要转换再返回
            followers = []
            for uid in ret:
                # 把-1过滤掉
                target_user_id = int(uid)
                if target_user_id != -1:
                    followers.append(target_user_id)
            return followers
        else:
            return self.save()



    def update(self, target_user_id, timestamp, increment=1):
        """
        更新粉丝数缓存
        """
        rc = current_app.redis_cluster
        try:
            if increment > 0:
                rc.zadd(self.key, timestamp, target_user_id)
            else:
                rc.zrem(self.key, target_user_id)
        except RedisError as e:
            current_app.logger.error(e)


class UserRelationshipCache(object):
    """
    用户关系缓存数据
    """

    def __init__(self, user_id):
        self.key = 'user:{}:relationship'.format(user_id)
        self.user_id = user_id

    def get(self):
        """
        获取用户的关系数据
        :return:
        """
        rc = current_app.redis_cluster

        try:
            ret = rc.hgetall(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None

        if ret:
            # 为了防止缓存击穿
            if b'-1' in ret:
                return {}
            else:
                # In order to be consistent with db data type.
                return {int(uid): int(relation) for uid, relation in ret.items()}

        ret = Relation.query.options(load_only(Relation.target_user_id, Relation.utime, Relation.relation)) \
            .filter(Relation.user_id == self.user_id, Relation.relation != Relation.RELATION.DELETE) \
            .order_by(Relation.utime.desc()).all()

        relations = {}
        for relation in ret:
            relations[relation.target_user_id] = relation.relation

        pl = rc.pipeline()
        try:
            if relations:
                pl.hmset(self.key, relations)
                pl.expire(self.key, constants.UserFollowingsCacheTTL.get_val())
            else:
                pl.hmset(self.key, {-1: -1})
                pl.expire(self.key, constants.UserRelationshipNotExistsCacheTTL.get_val())
            results = pl.execute()
            if results[0] and not results[1]:
                rc.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

        return relations

    def determine_follows_target(self, target_user_id):
        """
        判断用户是否关注了目标用户
        :param target_user_id: 被关注的用户id
        :return:
        """
        relations = self.get()

        return relations.get(target_user_id) == Relation.RELATION.FOLLOW

    def determine_blacklist_target(self, target_user_id):
        """
        判断是否已拉黑目标用户
        :param target_user_id:
        :return:
        """
        relations = self.get()

        return relations.get(target_user_id) == Relation.RELATION.BLACKLIST

    def clear(self):
        """
        清除
        """
        current_app.redis_cluster.delete(self.key)


class UserReadingHistoryStorage(object):
    """
    用户阅读历史
    """
    def __init__(self, user_id):
        self.key = 'user:{}:his:reading'.format(user_id)
        self.user_id = user_id

    def save(self, article_id):
        """
        保存用户阅读历史
        :param article_id: 文章id
        :return:
        """
        try:
            pl = current_app.redis_master.pipeline()
            pl.zadd(self.key, time.time(), article_id)
            pl.zremrangebyrank(self.key, 0, -1*(constants.READING_HISTORY_COUNT_PER_USER+1))
            pl.execute()
        except RedisError as e:
            current_app.logger.error(e)

    def get(self, page, per_page):
        """
        获取阅读历史
        """
        r = current_app.redis_master
        try:
            total_count = r.zcard(self.key)
        except ConnectionError as e:
            r = current_app.redis_slave
            total_count = r.zcard(self.key)

        article_ids = []
        if total_count > 0 and (page - 1) * per_page < total_count:
            try:
                article_ids = r.zrevrange(self.key, (page - 1) * per_page, page * per_page - 1)
            except ConnectionError as e:
                current_app.logger.error(e)
                article_ids = current_app.redis_slave.zrevrange(self.key, (page - 1) * per_page, page * per_page - 1)

        return total_count, article_ids


class UserSearchingHistoryStorage(object):
    """
    用户搜索历史
    """
    def __init__(self, user_id):
        self.key = 'user:{}:his:searching'.format(user_id)
        self.user_id = user_id

    def save(self, keyword):
        """
        保存用户搜索历史
        :param keyword: 关键词
        :return:
        """
        pl = current_app.redis_master.pipeline()
        pl.zadd(self.key, time.time(), keyword)
        pl.zremrangebyrank(self.key, 0, -1*(constants.SEARCHING_HISTORY_COUNT_PER_USER+1))
        pl.execute()

    def get(self):
        """
        获取搜索历史
        """
        try:
            keywords = current_app.redis_master.zrevrange(self.key, 0, -1)
        except ConnectionError as e:
            current_app.logger.error(e)
            keywords = current_app.redis_slave.zrevrange(self.key, 0, -1)

        keywords = [keyword.decode() for keyword in keywords]
        return keywords

    def clear(self):
        """
        清除
        """
        current_app.redis_master.delete(self.key)


class UserArticlesCache(object):
    """
    用户文章缓存
    """
    def __init__(self, user_id):
        self.user_id = user_id
        self.key = 'user:{}:art'.format(user_id)

    def get_page(self, page, per_page):
        """
        获取用户的文章列表
        :param page: 页数
        :param per_page: 每页数量
        :return: total_count, [article_id, ..]
        """
        rc = current_app.redis_cluster

        try:
            pl = rc.pipeline()
            pl.zcard(self.key)
            pl.zrevrange(self.key, (page - 1) * per_page, page * per_page)
            total_count, ret = pl.execute()
        except RedisError as e:
            current_app.logger.error(e)
            total_count = 0
            ret = []

        if total_count > 0:
            # Cache exists.
            return total_count, [int(aid) for aid in ret]
        else:
            # No cache.
            total_count = cache_statistic.UserArticlesCountStorage.get(self.user_id)
            if total_count == 0:
                return 0, []

            ret = Article.query.options(load_only(Article.id, Article.ctime)) \
                .filter_by(user_id=self.user_id, status=Article.STATUS.APPROVED) \
                .order_by(Article.ctime.desc()).all()

            articles = []
            cache = []
            for article in ret:
                articles.append(article.id)
                cache.append(article.ctime.timestamp())
                cache.append(article.id)

            if cache:
                try:
                    pl = rc.pipeline()
                    pl.zadd(self.key, *cache)
                    pl.expire(self.key, constants.UserArticlesCacheTTL.get_val())
                    results = pl.execute()
                    if results[0] and not results[1]:
                        rc.delete(self.key)
                except RedisError as e:
                    current_app.logger.error(e)

            total_count = len(articles)
            page_articles = articles[(page - 1) * per_page:page * per_page]

            return total_count, page_articles

    def clear(self):
        """
        清除
        """
        rc = current_app.redis_cluster
        rc.delete(self.key)


class UserArticleCollectionsCache(object):
    """
    用户收藏文章缓存
    """
    def __init__(self, user_id):
        self.user_id = user_id
        self.key = 'user:{}:art:collection'.format(user_id)

    def get_page(self, page, per_page):
        """
        获取用户的文章列表
        :param page: 页数
        :param per_page: 每页数量
        :return: total_count, [article_id, ..]
        """
        rc = current_app.redis_cluster

        try:
            pl = rc.pipeline()
            pl.zcard(self.key)
            pl.zrevrange(self.key, (page - 1) * per_page, page * per_page)
            total_count, ret = pl.execute()
        except RedisError as e:
            current_app.logger.error(e)
            total_count = 0
            ret = []

        if total_count > 0:
            # Cache exists.
            return total_count, [int(aid) for aid in ret]
        else:
            # No cache.
            total_count = cache_statistic.UserArticleCollectingCountStorage.get(self.user_id)
            if total_count == 0:
                return 0, []

            ret = Collection.query.options(load_only(Collection.article_id, Collection.utime)) \
                .filter_by(user_id=self.user_id, is_deleted=False) \
                .order_by(Collection.utime.desc()).all()

            collections = []
            cache = []
            for collection in ret:
                collections.append(collection.article_id)
                cache.append(collection.utime.timestamp())
                cache.append(collection.article_id)

            if cache:
                try:
                    pl = rc.pipeline()
                    pl.zadd(self.key, *cache)
                    pl.expire(self.key, constants.UserArticleCollectionsCacheTTL.get_val())
                    results = pl.execute()
                    if results[0] and not results[1]:
                        rc.delete(self.key)
                except RedisError as e:
                    current_app.logger.error(e)

            total_count = len(collections)
            page_articles = collections[(page - 1) * per_page:page * per_page]

            return total_count, page_articles

    def clear(self):
        """
        清除
        """
        current_app.redis_cluster.delete(self.key)

    def determine_collect_target(self, target):
        """
        判断用户是否收藏了指定文章
        :param target:
        :return:
        """
        total_count, collections = self.get_page(1, -1)
        return target in collections


class UserArticleAttitudeCache(object):
    """
    用户文章态度缓存数据
    """

    def __init__(self, user_id):
        self.key = 'user:{}:art:attitude'.format(user_id)
        self.user_id = user_id

    def get_all(self):
        """
        获取用户文章态度数据
        :return:
        """
        rc = current_app.redis_cluster

        try:
            ret = rc.hgetall(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None

        if ret:
            # 为了防止缓存击穿
            if b'-1' in ret:
                return {}
            else:
                # In order to be consistent with db data type.
                return {int(aid): int(attitude) for aid, attitude in ret.items()}

        ret = Attitude.query.options(load_only(Attitude.article_id, Attitude.attitude)) \
            .filter(Attitude.user_id == self.user_id, Attitude.attitude != None).all()

        attitudes = {}
        for atti in ret:
            attitudes[atti.article_id] = atti.attitude

        pl = rc.pipeline()
        try:
            if attitudes:
                pl.hmset(self.key, attitudes)
                pl.expire(self.key, constants.UserArticleAttitudeCacheTTL.get_val())
            else:
                pl.hmset(self.key, {-1: -1})
                pl.expire(self.key, constants.UserArticleAttitudeNotExistsCacheTTL.get_val())
            results = pl.execute()
            if results[0] and not results[1]:
                rc.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

        return attitudes

    def get_article_attitude(self, article_id):
        """
        获取指定文章态度
        :param article_id:
        :return:
        """
        if hasattr(g, 'article_attitudes'):
            attitudes = g.article_attitudes
        else:
            attitudes = self.get_all()
            g.article_attitudes = attitudes

        return attitudes.get(article_id, -1)

    def determine_liking_article(self, article_id):
        """
        判断是否对文章点赞
        :param article_id:
        :return:
        """
        return self.get_article_attitude(article_id) == Attitude.ATTITUDE.LIKING

    def clear(self):
        """
        清除
        """
        current_app.redis_cluster.delete(self.key)


class UserCommentLikingCache(object):
    """
    用户评论点赞缓存数据
    """

    def __init__(self, user_id):
        self.key = 'user:{}:comm:liking'.format(user_id)
        self.user_id = user_id

    def get(self):
        """
        获取用户文章评论点赞数据
        :return:
        """
        rc = current_app.redis_cluster

        try:
            ret = rc.smembers(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None

        if ret:
            # 为了防止缓存击穿
            if b'-1' in ret:
                return []
            else:
                # In order to be consistent with db data type.
                return set([int(cid) for cid in ret])

        ret = CommentLiking.query.options(load_only(CommentLiking.comment_id)) \
            .filter(CommentLiking.user_id == self.user_id, CommentLiking.is_deleted == False).all()

        cids = [com.comment_id for com in ret]
        pl = rc.pipeline()
        try:
            if cids:
                pl.sadd(self.key, *cids)
                pl.expire(self.key, constants.UserCommentLikingCacheTTL.get_val())
            else:
                pl.sadd(self.key, -1)
                pl.expire(self.key, constants.UserCommentLikingNotExistsCacheTTL.get_val())
            results = pl.execute()
            if results[0] and not results[1]:
                rc.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

        return set(cids)

    def determine_liking_comment(self, comment_id):
        """
        判断是否对文章点赞
        :param comment_id:
        :return:
        """
        if hasattr(g, self.key):
            liking_comments = getattr(g, self.key)
        else:
            liking_comments = self.get()
            setattr(g, self.key, liking_comments)

        return comment_id in liking_comments

    def clear(self):
        """
        清除
        """
        current_app.redis_cluster.delete(self.key)


def get_user_articles(user_id):
    """
    获取用户的所有文章列表 已废弃
    :param user_id:
    :return:
    """
    r = current_app.redis_cli['user_cache']
    timestamp = time.time()

    ret = r.zrevrange('user:{}:art'.format(user_id), 0, -1)
    if ret:
        r.zadd('user:art', timestamp, user_id)
        return [int(aid) for aid in ret]

    ret = r.hget('user:{}'.format(user_id), 'art_count')
    if ret is not None and int(ret) == 0:
        return []

    ret = Article.query.options(load_only(Article.id, Article.ctime))\
        .filter_by(user_id=user_id, status=Article.STATUS.APPROVED)\
        .order_by(Article.ctime.desc()).all()

    articles = []
    cache = []
    for article in ret:
        articles.append(article.id)
        cache.append(article.ctime.timestamp())
        cache.append(article.id)

    if cache:
        pl = r.pipeline()
        pl.zadd('user:art', timestamp, user_id)
        pl.zadd('user:{}:art'.format(user_id), *cache)
        pl.execute()

    return articles





