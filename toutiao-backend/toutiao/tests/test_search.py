import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR))
sys.path.insert(0, os.path.join(BASE_DIR, 'common'))


import unittest
from toutiao.main import app
import json


class SuggestionTest(unittest.TestCase):
    """搜索建议接口测试案例"""

    def setUp(self):
        """
        在执行测试方法前先被执行
        :return:
        """
        self.app = app
        self.client = self.app.test_client()

    def test_missing_request_q_param(self):
        """
        测试缺少q的请求参数
        """
        resp = self.client.get('/v1_0/suggestion')
        self.assertEqual(resp.status_code, 400)

    def test_request_q_param_error_length(self):
        """
        测试q参数错误长度
        """
        resp = self.client.get('/v1_0/suggestion?q='+'e'*51)
        self.assertEqual(resp.status_code, 400)

    def test_normal(self):
        """
        测试正常请求
        """
        resp = self.client.get('/v1_0/suggestion?q=ptyhon')
        self.assertEqual(resp.status_code, 200)

        resp_json = resp.data
        resp_dict = json.loads(resp_json)
        self.assertIn('message', resp_dict)
        self.assertIn('data', resp_dict)
        data = resp_dict['data']
        self.assertIn('options', data)


if __name__ == '__main__':
    unittest.main()