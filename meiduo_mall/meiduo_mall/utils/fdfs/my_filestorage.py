from django.core.files.storage import Storage
from django.conf import settings
"""
自定义文件存储类
1, 自定义类继承,django.core.files.storage.Storage
2, 保证任务情况都能初始化,自己的存储类
3, 必须实现open, save,exists, url方法

"""

class MyFileStorage(Storage):

    def __init__(self, base_url=None):
        if not base_url:
            self.base_url = settings.BASE_URL

    def open(self, name, mode='rb'):
        """打开文件的时候调用"""
        pass

    def save(self, name, content, max_length=None):
        """保存文件的时候调用"""
        pass

    def exists(self, name):
        """判断图片是否已经存在了"""
        return False

    def url(self, name):
        """返回图片路径"""
        # print(name)
        return self.base_url + name