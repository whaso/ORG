from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

class Config(object):
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1/toutiao'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
app.config.from_object(Config)

db = SQLAlchemy(app)

class Article(db.Model):
    """
    文章基本信息表
    """
    __tablename__ = 'news_article_basic'

    class STATUS:
        DRAFT = 0  # 草稿
        UNREVIEWED = 1  # 待审核
        APPROVED = 2  # 审核通过
        FAILED = 3  # 审核失败
        DELETED = 4  # 已删除
        BANNED = 5  # 封禁

    STATUS_ENUM = [0, 1, 2, 3]

    id = db.Column('article_id', db.Integer, primary_key=True,  doc='文章ID')
    user_id = db.Column(db.Integer, db.ForeignKey('user_basic.user_id'), doc='用户ID')
    channel_id = db.Column(db.Integer, db.ForeignKey('news_channel.channel_id'), doc='频道ID')
    title = db.Column(db.String, doc='标题')
    cover = db.Column(db.JSON, doc='封面')
    is_advertising = db.Column(db.Boolean, default=False, doc='是否投放广告')
    ctime = db.Column('create_time', db.DateTime, default=datetime.now, doc='创建时间')
    status = db.Column(db.Integer, default=0, doc='帖文状态')
    reviewer_id = db.Column(db.Integer, doc='审核人员ID')
    review_time = db.Column(db.DateTime, doc='审核时间')
    delete_time = db.Column(db.DateTime, doc='删除时间')
    comment_count = db.Column(db.Integer, default=0, doc='评论数')
    allow_comment = db.Column(db.Boolean, default=True, doc='是否允许评论')
    reject_reason = db.Column(db.String, doc='驳回原因')
    utime = db.Column('update_time', db.DateTime, default=datetime.now, doc='更新时间')


class ArticleContent(db.Model):
    """
    文章内容表
    """
    __tablename__ = 'news_article_content'

    id = db.Column('article_id', db.Integer, db.ForeignKey('news_article_basic.article_id'), primary_key=True, doc='文章ID')
    content = db.Column(db.Text, doc='帖文内容')


