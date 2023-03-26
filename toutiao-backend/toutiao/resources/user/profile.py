from flask_restful import Resource
from flask import g, current_app
from flask_restful.reqparse import RequestParser
from flask_restful import inputs
from sqlalchemy.exc import IntegrityError

from utils.decorators import login_required
# from cache import user as cache_user
from models.user import User, UserProfile
from utils import parser
from models import db
from utils.storage import upload_image
from utils.decorators import set_db_to_write, set_db_to_read
from cache.user import UserProfileCache, UserAdditionalProfileCache
from cache import user as cache_user


class UserResource(Resource):
    """
    用户数据资源
    """

    method_decorators = {
        'get': [set_db_to_read],
    }

    def get(self, target):
        """
        获取target用户的数据
        :param target: 目标用户id
        """
        cache = cache_user.UserProfileCache(target)
        exists = cache.exists()
        if not exists:
            return {'message': 'Invalid target user.'}, 400

        user_data = cache.get()

        user_data['is_following'] = False
        user_data['is_blacklist'] = False
        if g.user_id:
            relation_cache = cache_user.UserRelationshipCache(g.user_id)
            user_data['is_following'] = relation_cache.determine_follows_target(target)
            user_data['is_blacklist'] = relation_cache.determine_blacklist_target(target)

        user_data['id'] = target
        del user_data['mobile']
        return user_data


class CurrentUserResource(Resource):
    """
    用户自己的数据
    """
    method_decorators = [set_db_to_read, login_required]

    def get(self):
        """
        获取当前用户自己的数据
        """
        user_data = UserProfileCache(g.user_id).get()
        user_data['id'] = g.user_id
        return user_data


class ProfileResource(Resource):
    """
    用户资料
    """
    method_decorators = {
        'get': [set_db_to_read, login_required],
        'patch': [set_db_to_write, login_required],
    }

    def get(self):
        """
        获取用户资料
        """
        user_id = g.user_id
        user = UserProfileCache(user_id).get()
        result = {
            'id': user_id,
            'name': user['name'],
            'photo': user['photo'],
            'mobile': user['mobile']
        }
        # 补充性别生日等信息
        result.update(UserAdditionalProfileCache(user_id).get())
        return result

    def _gender(self, value):
        """
        判断性别参数值
        """
        try:
            value = int(value)
        except Exception:
            raise ValueError('Invalid gender.')

        if value in [UserProfile.GENDER.MALE, UserProfile.GENDER.FEMALE]:
            return value
        else:
            raise ValueError('Invalid gender.')

    def patch(self):
        """
        编辑用户的信息
        """
        # 获取参数
        json_parser = RequestParser()
        json_parser.add_argument('name', type=inputs.regex(r'^.{1,7}$'), required=False, location='json')
        json_parser.add_argument('photo', type=parser.image_base64, required=False, location='json')
        json_parser.add_argument('gender', type=self._gender, required=False, location='json')
        json_parser.add_argument('birthday', type=parser.date, required=False, location='json')
        json_parser.add_argument('intro', type=inputs.regex(r'^.{0,60}$'), required=False, location='json')
        json_parser.add_argument('real_name', type=inputs.regex(r'^.{1,7}$'), required=False, location='json')
        json_parser.add_argument('id_number', type=parser.id_number, required=False, location='json')
        json_parser.add_argument('id_card_front', type=parser.image_base64, required=False, location='json')
        json_parser.add_argument('id_card_back', type=parser.image_base64, required=False, location='json')
        json_parser.add_argument('id_card_handheld', type=parser.image_base64, required=False, location='json')
        args = json_parser.parse_args()

        user_id = g.user_id
        # 表示有user_basic有修改的数据
        new_user_values = {}
        # 表示user_profile有修改的数据
        new_profile_values = {}
        # return_values：需要返回的字典数据
        return_values = {'id': user_id}

        if args.name:
            # 如果有name参数，在new_user_values和return_values中标志需要修改name字段
            new_user_values['name'] = args.name
            return_values['name'] = args.name

        if args.photo:
            # 如果有photo参数, 把图片上传到七牛云，并在new_user_values标志要修改头像profile_photo字段
            try:
                photo_url = upload_image(args.photo)
            except Exception as e:
                current_app.logger.error('upload failed {}'.format(e))
                return {'message': 'Uploading profile photo image failed.'}, 507
            new_user_values['profile_photo'] = photo_url
            return_values['photo'] = current_app.config['QINIU_DOMAIN'] + photo_url

        if args.gender:
            # 如果存在gender, 标志需要修改性别
            new_profile_values['gender'] = args.gender
            return_values['gender'] = args.gender

        if args.birthday:
            # 如果存在birthday，标志需要修改生日
            new_profile_values['birthday'] = args.birthday
            return_values['birthday'] = args.birthday.strftime('%Y-%m-%d')

        if args.intro:
            # 如果存在intro,标志需要修改简介
            new_user_values['introduction'] = args.intro
            return_values['intro'] = args.intro

        if args.real_name:
            # 标志
            new_profile_values['real_name'] = args.real_name
            return_values['real_name'] = args.real_name

        if args.id_number:
            # 标志
            new_profile_values['id_number'] = args.id_number
            return_values['id_number'] = args.id_number

        if args.id_card_front:
            try:
                id_card_front_url = upload_image(args.id_card_front)
            except Exception as e:
                current_app.logger.error('upload failed {}'.format(e))
                return {'message': 'Uploading id_card_front image failed.'}, 507
            new_profile_values['id_card_front'] = id_card_front_url
            return_values['id_card_front'] = current_app.config['QINIU_DOMAIN'] + id_card_front_url

        if args.id_card_back:
            try:
                id_card_back_url = upload_image(args.id_card_back)
            except Exception as e:
                current_app.logger.error('upload failed {}'.format(e))
                return {'message': 'Uploading id_card_back image failed.'}, 507
            new_profile_values['id_card_back'] = id_card_back_url
            return_values['id_card_back'] = current_app.config['QINIU_DOMAIN'] + id_card_back_url

        if args.id_card_handheld:
            try:
                id_card_handheld_url = upload_image(args.id_card_handheld)
            except Exception as e:
                current_app.logger.error('upload failed {}'.format(e))
                return {'message': 'Uploading id_card_handheld image failed.'}, 507
            new_profile_values['id_card_handheld'] = id_card_handheld_url
            return_values['id_card_handheld'] = current_app.config['QINIU_DOMAIN'] + id_card_handheld_url

        try:
            # 最后统一修改
            if new_user_values:
                # 如果new_user_values存在数据，修改user_basic表
                User.query.filter_by(id=user_id).update(new_user_values)
                # 清除缓存数据
                UserProfileCache(user_id).clear()
            if new_profile_values:
                # 如果new_profile_values存在数据，修改user_profile表
                profile = UserProfile.query.filter_by(id=user_id).first()
                if not profile:
                    profile = UserProfile(id=user_id)
                    db.session.add(profile)
                    db.session.flush()
                UserProfile.query.filter_by(id=user_id).update(new_profile_values)
                # 清除缓存数据
                UserAdditionalProfileCache(user_id).clear()
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {'message': 'User name has existed.'}, 409

        return return_values, 201


class PhotoResource(Resource):
    """
    用户图像 （头像，身份证）
    """
    method_decorators = [set_db_to_write, login_required]

    def patch(self):
        file_parser = RequestParser()
        file_parser.add_argument('photo', type=parser.image_file, required=False, location='files')
        file_parser.add_argument('id_card_front', type=parser.image_file, required=False, location='files')
        file_parser.add_argument('id_card_back', type=parser.image_file, required=False, location='files')
        file_parser.add_argument('id_card_handheld', type=parser.image_file, required=False, location='files')
        files = file_parser.parse_args()

        user_id = g.user_id
        new_user_values = {}
        new_profile_values = {}
        return_values = {'id': user_id}
        need_delete_profile = False

        if files.photo:
            try:
                photo_url = upload_image(files.photo.read())
            except Exception as e:
                current_app.logger.error('upload failed {}'.format(e))
                return {'message': 'Uploading profile photo image failed.'}, 507
            new_user_values['profile_photo'] = photo_url
            return_values['photo'] = current_app.config['QINIU_DOMAIN'] + photo_url
            need_delete_profile = True

        if files.id_card_front:
            try:
                id_card_front_url = upload_image(files.id_card_front.read())
            except Exception as e:
                current_app.logger.error('upload failed {}'.format(e))
                return {'message': 'Uploading id_card_front image failed.'}, 507
            new_profile_values['id_card_front'] = id_card_front_url
            return_values['id_card_front'] = current_app.config['QINIU_DOMAIN'] + id_card_front_url

        if files.id_card_back:
            try:
                id_card_back_url = upload_image(files.id_card_back.read())
            except Exception as e:
                current_app.logger.error('upload failed {}'.format(e))
                return {'message': 'Uploading id_card_back image failed.'}, 507
            new_profile_values['id_card_back'] = id_card_back_url
            return_values['id_card_back'] = current_app.config['QINIU_DOMAIN'] + id_card_back_url

        if files.id_card_handheld:
            try:
                id_card_handheld_url = upload_image(files.id_card_handheld.read())
            except Exception as e:
                current_app.logger.error('upload failed {}'.format(e))
                return {'message': 'Uploading id_card_handheld image failed.'}, 507
            new_profile_values['id_card_handheld'] = id_card_handheld_url
            return_values['id_card_handheld'] = current_app.config['QINIU_DOMAIN'] + id_card_handheld_url

        if new_user_values:
            User.query.filter_by(id=user_id).update(new_user_values)
        if new_profile_values:
            UserProfile.query.filter_by(id=user_id).update(new_profile_values)

        db.session.commit()

        if need_delete_profile:
            cache_user.UserProfileCache(user_id).clear()

        return return_values, 201

