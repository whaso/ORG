from flask import Blueprint
from flask_restful import Api

from . import passport
from . import profile, following, blacklist, channel, figure
from utils.output import output_json

user_bp = Blueprint('user', __name__)
user_api = Api(user_bp, catch_all_404s=True)
user_api.representation('application/json')(output_json)

# 绑定试图类和视图路由的关系
# 发送短信验证码
user_api.add_resource(passport.SMSVerificationCodeResource, '/v1_0/sms/codes/<mobile:mobile>',
                      endpoint='SMSVerificationCode')

# jwt登录认证
user_api.add_resource(passport.AuthorizationResource, '/v1_0/authorizations',
                      endpoint='Authorization')

# 获取当前用户信息
user_api.add_resource(profile.CurrentUserResource, '/v1_0/user',
                      endpoint='CurrentUser')

# 修改用户信息
user_api.add_resource(profile.ProfileResource, '/v1_0/user/profile',
                      endpoint='Profile')

# 用户关注列表
user_api.add_resource(following.FollowingListResource, '/v1_0/user/followings',
                      endpoint='Followings')

# 取消关注
user_api.add_resource(following.FollowingResource, '/v1_0/user/followings/<int(min=1):target>',
                      endpoint='Following')

# 粉丝列表
user_api.add_resource(following.FollowerListResource, '/v1_0/user/followers',
                      endpoint='Followers')

user_api.add_resource(profile.UserResource, '/v1_0/users/<int(min=1):target>',
                      endpoint='User')

user_api.add_resource(profile.PhotoResource, '/v1_0/user/photo',
                      endpoint='Photo')

user_api.add_resource(blacklist.BlacklistListResource, '/v1_0/user/blacklists',
                      endpoint='Blacklists')

user_api.add_resource(blacklist.BlacklistResource, '/v1_0/user/blacklists/<int(min=1):target>',
                      endpoint='Blacklist')

user_api.add_resource(channel.ChannelListResource, '/v1_0/user/channels',
                      endpoint='Channels')

user_api.add_resource(channel.ChannelResource, '/v1_0/user/channels/<int(min=1):target>',
                      endpoint='Channel')

user_api.add_resource(figure.FigureResource, '/v1_0/user/figure',
                      endpoint='Figure')