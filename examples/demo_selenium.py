# -*- coding: utf-8 -*-
"""
HTMLTestRunner 截图功能演示
简单的 Selenium 测试 + 截图示例

运行方式：
    python demo_screenshot.py

注意：不要通过 IDE 的测试运行器运行，要直接运行此文件！
"""

import sys
import os
# 添加父目录到路径，使用本地开发版本
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from htmltestrunner import HTMLTestRunnerLit, attach_screenshot


class TestBaidu(unittest.TestCase):
    """百度测试示例"""
    
    def setUp(self):
        """初始化浏览器"""
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)
    
    def test_baidu_homepage(self):
        """访问百度首页并截图"""
        # 访问百度
        self.driver.get("https://www.baidu.com")
        
        # 添加截图到报告
        attach_screenshot(self.driver, "百度首页")

        sleep(2)
        # 添加截图到报告
        attach_screenshot(self.driver, "百度首页_1")
        sleep(1)
        # 添加截图到报告
        attach_screenshot(self.driver, "百度首页_2")
        sleep(1)
        # 添加截图到报告
        attach_screenshot(self.driver, "百度首页_3")
        
        # 验证标题
        self.assertIn("百度", self.driver.title)
    
    def tearDown(self):
        """关闭浏览器"""
        sleep(5)  # 等待5秒，
        self.driver.quit()

if __name__ == '__main__':
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBaidu)
    
    # 生成报告
    with open('report_selenium.html', 'wb') as f:
        runner = HTMLTestRunnerLit(
            stream=f,
            title='Selenium 测试报告',
            description='Selenium 自动化测试与截图演示',
            tester='QA Team',
            open_in_browser=True
        )
        runner.run(suite)
    
    print("\n✓ 报告已生成: report_selenium.html")
