# HTMLTestRunner Lit 🎨

现代化的 Python unittest HTML 测试报告生成器

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📸 预览

![Report Preview](docs/screenshot.png)

## ✨ 特性

- 🎨 **Bootstrap 5 + ECharts 5** 现代 UI 设计
- 🌓 **深色/浅色主题** 一键切换
- 📸 **截图支持** 自动捕获 Selenium 截图，支持轮播/网格预览
- 📱 **响应式设计** 完美支持移动端
- 📊 **环形图表** 可视化展示通过率
- 📋 **测试详情** 支持复制、展开/折叠
- 🧪 **subTest 支持** 完整支持子测试用例
- 🎯 **自定义配色** 支持自定义主题颜色
- 🚀 **自动打开** 测试完成后自动打开报告

## 🚀 安装

### 方式 1：从 PyPI 安装（推荐）

```bash
pip install htmltestrunner-lit
```

### 方式 2：从 GitHub 安装

```bash
pip install git+https://github.com/Aquarius-0455/HTMLTestRunner-Lit.git
```

### 方式 3：克隆后本地安装

```bash
git clone https://github.com/Aquarius-0455/HTMLTestRunner-Lit.git
cd HTMLTestRunner-Lit
pip install -e .
```

## 📖 使用方法

### 基础用法

```python
import unittest
from htmltestrunner import HTMLTestRunner

# 创建测试套件
suite = unittest.TestLoader().loadTestsFromTestCase(YourTestCase)

# 生成报告
with open('report.html', 'wb') as f:
    runner = HTMLTestRunner(
        stream=f,
        title='API 测试报告',
        description='项目接口自动化测试',
        tester='QA Team'
    )
    runner.run(suite)
```

### 自定义配置

```python
runner = HTMLTestRunner(
    stream=f,
    title='测试报告',
    description='项目描述',
    tester='测试人员',
    verbosity=2,
    open_in_browser=True  # 测试完成后自动打开报告
)
```

## 📸 截图功能

在测试用例中导入并调用 `attach_screenshot` 即可将截图添加到报告中。

```python
import unittest
from selenium import webdriver
from htmltestrunner import attach_screenshot

class TestDemo(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome()
    
    def test_example(self):
        self.driver.get("https://www.baidu.com")
        
        # 关键步骤：调用 attach_screenshot 并传入 driver 对象
        attach_screenshot(self.driver, "页面截图描述")
    
    def tearDown(self):
        self.driver.quit()
```



## 🎨 主题配置

支持深色和浅色两种主题，用户可以在报告中手动切换。

## 📊 报告内容

- **测试概览**: 总数、通过、失败、错误、跳过统计
- **可视化图表**: 通过率环形图
- **详细结果**: 每个测试用例的执行详情
- **错误追踪**: 完整的错误堆栈信息
- **执行时间**: 每个用例的执行耗时

## 🔧 API 参考

### HTMLTestRunner

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| stream | file | - | 输出文件流 |
| title | str | "Unit Test Report" | 报告标题 |
| description | str | "" | 报告描述 |
| tester | str | "QA Team" | 测试人员 |
| verbosity | int | 1 | 详细程度 |
| open_in_browser | bool | False | 测试完成后自动打开报告 |

## 📝 更新日志

### v1.0.5
- 📸 新增截图轮播与网格视图，支持多图自动切换
- 🔍 优化大图预览体验，支持键盘/点击左右切换
- 🎨 全新 Bootstrap 5 + ECharts 5 UI
- 🌓 深色/浅色主题切换
- 📱 响应式设计，完美支持移动端
- 📊 环形图表可视化展示通过率
- 🧪 完整支持 subTest 子测试用例
- 📋 测试详情支持复制、展开/折叠
- 🚀 支持 `open_in_browser` 自动打开报告
- 👤 支持自定义 `tester` 测试人员

## 📄 许可证

本项目采用 [MIT](LICENSE) 许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ⭐ Star History

如果这个项目对你有帮助，请给一个 Star ⭐

