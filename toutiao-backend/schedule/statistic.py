"""
用于修正redis存储中的统计数据
"""

# 这里如果用web项目中的db, 最好也是使用web项目中的app对象
from toutiao.main import app
from models import db
from cache import statistic as cache_statistic


def fix_process(count_storage_cls):
    """
    修复处理方法
    count_storage_cls：统计类
    """
    with app.app_context():
        # 设置db对象在从mysql中读取数据
        db.session().set_to_read()
        ret = count_storage_cls.db_query()
        data = []
        for value, score in ret:
            data.append(score)
            data.append(value)
        # 调用统计类的reset方法，修正统计数据
        count_storage_cls.reset(app.redis_master, *data)


def fix_statistics():
    """
    修正统计数据
    """
    fix_process(cache_statistic.UserArticlesCountStorage)
    fix_process(cache_statistic.ArticleCollectingCountStorage)
    fix_process(cache_statistic.UserArticleCollectingCountStorage)
    fix_process(cache_statistic.ArticleDislikeCountStorage)
    fix_process(cache_statistic.ArticleLikingCountStorage)
    fix_process(cache_statistic.CommentLikingCountStorage)
    fix_process(cache_statistic.ArticleCommentCountStorage)
    fix_process(cache_statistic.CommentReplyCountStorage)
    fix_process(cache_statistic.UserFollowingsCountStorage)
    fix_process(cache_statistic.UserFollowersCountStorage)
    fix_process(cache_statistic.UserLikedCountStorage)



