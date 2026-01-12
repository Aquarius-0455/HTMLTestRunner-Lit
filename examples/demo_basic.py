# -*- coding: utf-8 -*-
"""
HTMLTestRunner Modern 使用示例
"""

import unittest
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from htmltestrunner import HTMLTestRunner


class TestExample(unittest.TestCase):
    """示例测试用例"""
    
    def test_pass(self):
        """通过的测试"""
        self.assertEqual(1 + 1, 2)
    
    def test_pass_with_output(self):
        """带输出的通过测试"""
        print("这是测试输出信息")
        self.assertTrue(True)
    
    def test_fail(self):
        """失败的测试"""
        self.assertEqual(1, 2, "1 不等于 2")
    
    def test_error(self):
        """错误的测试"""
        raise ValueError("这是一个错误")
    
    @unittest.skip("跳过原因说明")
    def test_skip(self):
        """跳过的测试"""
        pass
    
    def test_subtest(self):
        """子测试示例"""
        for i in range(3):
            with self.subTest(i=i):
                self.assertLess(i, 3)


class TestMath(unittest.TestCase):
    """数学计算测试"""
    
    def test_addition(self):
        """加法测试"""
        self.assertEqual(2 + 3, 5)
    
    def test_subtraction(self):
        """减法测试"""
        self.assertEqual(5 - 3, 2)
    
    def test_multiplication(self):
        """乘法测试"""
        self.assertEqual(3 * 4, 12)


if __name__ == '__main__':
    # 创建测试套件
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestExample))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMath))
    
    # 生成报告
    with open('report_basic.html', 'wb') as f:
        runner = HTMLTestRunner(
            stream=f,
            title='HTMLTestRunner Modern 基础演示',
            description='这是一个演示测试报告，展示 HTMLTestRunner 的基础功能',
            tester='Lit',
            open_in_browser=True  # 测试完成后自动打开报告
        )
        runner.run(suite)
    
    print("\n报告已生成: report_basic.html")

