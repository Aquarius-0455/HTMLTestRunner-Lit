# -*- coding: utf-8 -*-
__author__ = "Lit"
__version__ = "1.0.6"

"""
Version 1.0.0
* 使用Bootstrap 5和ECharts 5 UI
* 深色模式支持 (可切换主题)
* 专业简洁的Ant Design风格配色
* 响应式设计优化 - 完美支持移动端
* 统计卡片可视化展示
* 环形图表设计与通过率展示
* 支持跳过测试用例显示
* 测试详情支持复制和滚动
* 图表标签优化避免重叠
* Author: Lit

"""

# TODO: color stderr
# TODO: simplify javascript using ,ore than 1 class in the class attribute?

import datetime
import sys
import io
import os
import time
import webbrowser
import unittest
from xml.sax import saxutils
import base64
from io import BytesIO


# ------------------------------------------------------------------------
# The redirectors below are used to capture output during testing. Output
# sent to sys.stdout and sys.stderr are automatically captured. However
# in some cases sys.stdout is already cached before HTMLTestRunner is
# invoked (e.g. calling logging.basicConfig). In order to capture those
# output, use the redirectors for the cached stream.
#
# e.g.
#   >>> logging.basicConfig(stream=HTMLTestRunner.stdout_redirector)
#   >>>

class OutputRedirector(object):
    """ Wrapper to redirect stdout or stderr """
    def __init__(self, fp):
        self.fp = fp

    def write(self, s):
        self.fp.write(s)

    def writelines(self, lines):
        self.fp.writelines(lines)

    def flush(self):
        self.fp.flush()

stdout_redirector = OutputRedirector(sys.stdout)
stderr_redirector = OutputRedirector(sys.stderr)


# ------------------------------------------------------------------------
# Screenshot Manager
#

class ScreenshotManager:
    """截图管理器 - 负责将各种格式的图片转换为 base64"""
    
    @staticmethod
    def to_base64(image_source, description=""):
        """
        将图片转换为 base64 格式
        
        参数:
            image_source: 支持以下类型
                - str: 文件路径
                - bytes: 图片二进制数据  
                - PIL.Image: PIL 图片对象
                - selenium.webdriver: Selenium WebDriver 对象
            description: 截图描述
            
        返回:
            dict: {'data': base64_string, 'description': description}
            None: 转换失败
        """
        try:
            # 1. 处理文件路径
            if isinstance(image_source, str):
                if os.path.exists(image_source):
                    with open(image_source, 'rb') as f:
                        img_data = f.read()
                    return {
                        'data': base64.b64encode(img_data).decode('utf-8'),
                        'description': description or os.path.basename(image_source)
                    }
            
            # 2. 处理 bytes
            elif isinstance(image_source, bytes):
                return {
                    'data': base64.b64encode(image_source).decode('utf-8'),
                    'description': description or 'Screenshot'
                }
            
            # 3. 处理 PIL Image
            elif hasattr(image_source, 'save'):
                buffer = BytesIO()
                image_source.save(buffer, format='PNG')
                img_data = buffer.getvalue()
                return {
                    'data': base64.b64encode(img_data).decode('utf-8'),
                    'description': description or 'PIL Image'
                }
            
            # 4. 处理 Selenium WebDriver
            elif hasattr(image_source, 'get_screenshot_as_png'):
                img_data = image_source.get_screenshot_as_png()
                return {
                    'data': base64.b64encode(img_data).decode('utf-8'),
                    'description': description or 'Selenium Screenshot'
                }
                
        except Exception as e:
            sys.stderr.write(f"截图转换失败: {e}\n")
            return None
        
        return None


# 全局变量，用于存储当前的 TestResult 实例
_current_result = None


def attach_screenshot(image_source, description=""):
    """
    全局函数：在测试用例中添加截图
    
    使用示例:
        from htmltestrunner import attach_screenshot
        
        # Selenium 截图
        attach_screenshot(driver, "登录页面")
        
        # 文件路径
        attach_screenshot("/path/to/image.png", "错误截图")
        
        # PIL Image
        attach_screenshot(pil_image, "处理后的图片")
    """
    if _current_result:
        _current_result.attach_screenshot(image_source, description)
    else:
        sys.stderr.write("警告: 无法添加截图，测试未在运行中\n")


# ----------------------------------------------------------------------
# Template


class Template_mixin(object):
    """
    Define a HTML template for report customerization and generation.

    Overall structure of an HTML report

    HTML
    +------------------------+
    |<html>                  |
    |  <head>                |
    |                        |
    |   STYLESHEET           |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |  </head>               |
    |                        |
    |  <body>                |
    |                        |
    |   HEADING              |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |   REPORT               |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |   ENDING               |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |  </body>               |
    |</html>                 |
    +------------------------+
    """

    STATUS = {
        0: u'通过',
        1: u'失败',
        2: u'错误',
        3: u'跳过',
    }

    DEFAULT_TITLE = 'Unit Test Report'
    DEFAULT_DESCRIPTION = ''

    # ------------------------------------------------------------------------
    # HTML Template

    HTML_TMPL = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="%(generator)s"/>
    <title>%(title)s</title>
    
    <!-- Bootstrap 5.3 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <!-- ECharts 5.x -->
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <!-- Bootstrap 5 JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    %(stylesheet)s
    
</head>
<body>
    <script type="text/javascript">
    /* level - 0:Summary; 1:Failed; 2:All */
    function showCase(level) {
        const trs = document.getElementsByTagName("tr");
        for (let i = 0; i < trs.length; i++) {
            const tr = trs[i];
            const id = tr.id;
            // ft: fail test, pt: pass test, st: skip test
            if (id.substr(0,2) === 'ft') {
                // 失败/错误用例：总结时隐藏，失败和全部时显示
                tr.style.display = level < 1 ? 'none' : 'table-row';
            }
            if (id.substr(0,2) === 'pt') {
                // 通过用例：只在全部时显示
                tr.style.display = level > 1 ? 'table-row' : 'none';
            }
            if (id.substr(0,2) === 'st') {
                // 跳过用例：只在全部时显示
                tr.style.display = level > 1 ? 'table-row' : 'none';
            }
        }
        
        // 更新按钮激活状态
        document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');
    }

    function showClassDetail(cid, count) {
        // 找到第一个测试用例元素，判断当前是显示还是隐藏
        const tid0 = 't' + cid.substr(1) + '.1';
        let firstTid = 'f' + tid0;
        let firstElem = document.getElementById(firstTid);
        if (!firstElem) {
            firstTid = 'p' + tid0;
            firstElem = document.getElementById(firstTid);
        }
        
        if (!firstElem) return;
        
        // 判断当前状态：如果是隐藏的，则展开；如果是显示的，则隐藏
        const isHidden = firstElem.style.display === 'none' || firstElem.style.display === '';
        
        // 切换所有测试用例的显示状态
        for (let i = 0; i < count; i++) {
            const tid0 = 't' + cid.substr(1) + '.' + (i+1);
            let tid = 'f' + tid0;
            let elem = document.getElementById(tid);
            if (!elem) {
                tid = 'p' + tid0;
                elem = document.getElementById(tid);
            }
            
            if (elem) {
                elem.style.display = isHidden ? 'table-row' : 'none';
                // 如果隐藏测试用例，同时隐藏其详情窗口
                const divElem = document.getElementById('div_' + tid);
                if (divElem && !isHidden) {
                    divElem.style.display = 'none';
                }
            }
        }
    }

    function showTestDetail(div_id){
        const details_div = document.getElementById(div_id);
        const displayState = details_div.style.display;
        details_div.style.display = (displayState !== 'block') ? 'block' : 'none';
    }
    
    // 复制测试详情内容
    function copyTestDetail(contentId, button) {
        const content = document.getElementById(contentId);
        if (!content) return;
        
        const text = content.textContent;
        
        // 使用现代浏览器的Clipboard API
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(() => {
                showCopySuccess(button);
            }).catch(() => {
                // 降级到旧方法
                fallbackCopy(text, button);
            });
        } else {
            // 降级到旧方法
            fallbackCopy(text, button);
        }
    }
    
    // 降级复制方法
    function fallbackCopy(text, button) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            showCopySuccess(button);
        } catch (err) {
            console.error('复制失败:', err);
        }
        document.body.removeChild(textarea);
    }
    
    // 显示复制成功提示
    function showCopySuccess(button) {
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="bi bi-check-lg"></i> 已复制';
        button.classList.add('copy-success');
        
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.classList.remove('copy-success');
        }, 2000);
    }
    
    // 主题切换功能
    function toggleTheme() {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // 更新图表主题
        const chart = echarts.getInstanceByDom(document.getElementById('chart'));
        if (chart) {
            chart.dispose();
            initChart();
        }
    }
    
    // 页面加载时恢复主题
    document.addEventListener('DOMContentLoaded', function() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-bs-theme', savedTheme);
    });
    </script>

    <div class="container-fluid">
        %(heading)s
        %(report)s
        %(ending)s
    </div>
    %(chart_script)s
</body>
</html>
"""  # variables: (title, generator, stylesheet, heading, report, ending, chart_script)

    ECHARTS_SCRIPT = """
    <script type="text/javascript">
    function initChart() {
        const chartDom = document.getElementById('chart');
        const myChart = echarts.init(chartDom);
        const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
        
        const passCount = %(Pass)s;
        const failCount = %(fail)s;
        const errorCount = %(error)s;
        const skipCount = %(skip)s;
        const total = passCount + failCount + errorCount + skipCount;
        const passRate = total > 0 ? ((passCount / total) * 100).toFixed(1) : 0;

        const option = {
            title: {
                text: '测试执行情况',
                subtext: '通过率: ' + passRate + '%%',
                left: 'center',
                top: '2%%',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 600,
                    color: isDark ? '#e8e8e8' : '#262626'
                },
                subtextStyle: {
                    fontSize: 13,
                    color: isDark ? '#a6a6a6' : '#8c8c8c',
                    lineHeight: 24
                }
            },
            tooltip: {
                trigger: 'item',
                formatter: '{a} <br/>{b}: {c} ({d}%%)',
                backgroundColor: isDark ? 'rgba(0, 0, 0, 0.85)' : 'rgba(255, 255, 255, 0.95)',
                borderColor: isDark ? '#434343' : '#d9d9d9',
                borderWidth: 1,
                textStyle: {
                    color: isDark ? '#e8e8e8' : '#262626',
                    fontSize: 13
                }
            },
            legend: {
                orient: 'horizontal',
                bottom: '5%%',
                left: 'center',
                itemGap: 24,
                textStyle: {
                    fontSize: 13,
                    color: isDark ? '#e8e8e8' : '#262626'
                },
                data: ['通过', '失败', '错误', '跳过'],
                formatter: function(name) {
                    const dataMap = {
                        '通过': passCount,
                        '失败': failCount,
                        '错误': errorCount,
                        '跳过': skipCount
                    };
                    return name + ': ' + dataMap[name];
                }
            },
            series: [
                {
                    name: '测试结果',
                    type: 'pie',
                    radius: ['40%%', '60%%'],
                    center: ['50%%', '50%%'],
                    avoidLabelOverlap: true,
                    itemStyle: {
                        borderRadius: 4,
                        borderColor: isDark ? '#141414' : '#fff',
                        borderWidth: 2
                    },
                    label: {
                        show: true,
                        position: 'outside',
                        formatter: function(params) {
                            if (params.value === 0) {
                                return '';  // 不显示值为0的标签
                            }
                            return params.name + '\\n' + params.value + ' (' + params.percent + '%%)';
                        },
                        fontSize: 13,
                        fontWeight: 500,
                        color: isDark ? '#e8e8e8' : '#262626',
                        distanceToLabelLine: 5
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: 14,
                            fontWeight: 600
                        },
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.2)'
                        },
                        scale: true,
                        scaleSize: 5
                    },
                    labelLine: {
                        show: true,
                        length: 15,
                        length2: 60,
                        smooth: true,
                        lineStyle: {
                            color: isDark ? '#434343' : '#d9d9d9',
                            width: 1
                        }
                    },
                    data: [
                        {
                            value: passCount,
                            name: '通过',
                            itemStyle: { color: '#52c41a' }
                        },
                        {
                            value: failCount,
                            name: '失败',
                            itemStyle: { color: '#faad14' }
                        },
                        {
                            value: errorCount,
                            name: '错误',
                            itemStyle: { color: '#f5222d' }
                        },
                        {
                            value: skipCount,
                            name: '跳过',
                            itemStyle: { color: '#1890ff' }
                        }
                    ],
                    animationType: 'scale',
                    animationEasing: 'cubicOut',
                    animationDelay: function (idx) {
                        return idx * 100;
                    }
                }
            ]
        };

        myChart.setOption(option);
        
        // 响应式调整
        window.addEventListener('resize', function() {
            myChart.resize();
        });
    }
    
    // 页面加载完成后初始化图表
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initChart);
    } else {
        initChart();
    }
    </script>
    """  # variables: (Pass, fail, error)

    # ------------------------------------------------------------------------
    # Stylesheet
    #
    # alternatively use a <link> for external style sheet, e.g.
    #   <link rel="stylesheet" href="$url" type="text/css">

    STYLESHEET_TMPL = """
<style type="text/css">
:root {
        --primary-color: #1890ff;
        --success-color: #52c41a;
        --warning-color: #faad14;
        --danger-color: #f5222d;
        --info-color: #13c2c2;
        --border-color: #d9d9d9;
        --text-color: #262626;
    --text-secondary: #8c8c8c;
        --bg-color: #f0f2f5;
}

[data-bs-theme="dark"] {
        --primary-color: #177ddc;
        --success-color: #49aa19;
        --warning-color: #d89614;
        --danger-color: #d32029;
        --border-color: #434343;
        --text-color: #e8e8e8;
    --text-secondary: #a6a6a6;
        --bg-color: #141414;
}

    * {
        box-sizing: border-box;
    }

body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
        background: var(--bg-color);
    min-height: 100vh;
    padding: 24px;
    margin: 0;
        color: var(--text-color);
}

    .container-fluid {
        max-width: 1400px;
        margin: 0 auto;
    }

    /* 头部样式 */
    .header-card {
        background: white;
        border-radius: 8px;
    padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02);
        border: 1px solid var(--border-color);
    }

    [data-bs-theme="dark"] .header-card {
        background: #1f1f1f;
        border-color: var(--border-color);
}

.report-title {
        font-size: 24px;
        font-weight: 600;
        color: var(--text-color);
        margin-bottom: 16px;
    display: flex;
    align-items: center;
        gap: 8px;
}

.report-title i {
        color: var(--primary-color);
}

.theme-toggle {
    position: fixed;
    top: 24px;
    right: 24px;
    z-index: 1000;
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        width: 36px;
        height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        transition: all 0.2s;
        color: var(--text-color);
    }

    [data-bs-theme="dark"] .theme-toggle {
        background: #1f1f1f;
        border-color: var(--border-color);
}

.theme-toggle:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
        border-color: var(--primary-color);
}

    /* 统计卡片 */
.stats-grid {
    display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
        margin-bottom: 16px;
}

.stat-card {
        background: white;
        border-radius: 8px;
    padding: 20px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02);
        border: 1px solid var(--border-color);
        transition: all 0.2s;
    }

    [data-bs-theme="dark"] .stat-card {
        background: #1f1f1f;
        border-color: var(--border-color);
    }

.stat-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border-color: var(--primary-color);
}

    .stat-card.info .stat-icon { color: var(--info-color); }
    .stat-card.primary .stat-icon { color: var(--primary-color); }
    .stat-card.success .stat-icon { color: var(--success-color); }
    .stat-card.secondary .stat-icon { color: var(--text-secondary); }

.stat-label {
    font-size: 14px;
    color: var(--text-secondary);
    margin-bottom: 8px;
}

.stat-value {
        font-size: 24px;
        font-weight: 600;
        color: var(--text-color);
}

.stat-icon {
        font-size: 20px;
        float: right;
        opacity: 0.8;
    }

    /* 图表卡片 */
    .chart-card {
        background: white;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02);
        border: 1px solid var(--border-color);
    }

    [data-bs-theme="dark"] .chart-card {
        background: #1f1f1f;
        border-color: var(--border-color);
    }

    /* 过滤按钮 */
    .filter-buttons {
        margin-bottom: 0;
    }

    .filter-btn {
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 6px 16px;
        font-size: 14px;
        transition: all 0.2s;
        background: white;
        color: var(--text-color);
    }

    [data-bs-theme="dark"] .filter-btn {
        background: #1f1f1f;
        border-color: var(--border-color);
}

    .filter-btn:hover {
        border-color: var(--primary-color);
        color: var(--primary-color);
    }

    .filter-btn.active {
        background: var(--primary-color);
        border-color: var(--primary-color);
        color: white;
    }

    /* 表格样式 */
.table-card {
        background: white;
        border-radius: 8px;
        padding: 24px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02);
        border: 1px solid var(--border-color);
    overflow: hidden;
}

    [data-bs-theme="dark"] .table-card {
        background: #1f1f1f;
        border-color: var(--border-color);
    }
    
    .table-card h2 {
        font-size: 18px;
        font-weight: 600;
        color: var(--text-color);
    }

#result_table {
        width: 100%%;
        margin-bottom: 0;
        border-collapse: collapse;
}

#result_table thead th {
        background: #fafafa;
        color: var(--text-color);
    font-weight: 600;
        padding: 12px 16px;
    font-size: 14px;
        border-bottom: 1px solid var(--border-color);
    text-align: left;
    }

    [data-bs-theme="dark"] #result_table thead th {
        background: #141414;
}

#result_table tbody tr {
        transition: background 0.2s;
        border-bottom: 1px solid var(--border-color);
}

#result_table tbody tr:hover {
        background-color: #fafafa;
    }

    [data-bs-theme="dark"] #result_table tbody tr:hover {
        background-color: #262626;
}

#result_table td {
        padding: 12px 16px;
    vertical-align: middle;
    font-size: 14px;
}

    .passClass {
        background: #f6ffed;
    }

    [data-bs-theme="dark"] .passClass {
        background: rgba(82, 196, 26, 0.1);
    }

    .failClass {
        background: #fffbe6;
    }

    [data-bs-theme="dark"] .failClass {
        background: rgba(250, 173, 20, 0.1);
    }

    .errorClass {
        background: #fff1f0;
    }

    [data-bs-theme="dark"] .errorClass {
        background: rgba(245, 34, 45, 0.1);
    }

    .skipClass {
        background: #f0f5ff;
    }

    [data-bs-theme="dark"] .skipClass {
        background: rgba(24, 144, 255, 0.1);
    }

    #total_row {
        font-weight: 600;
        background: #fafafa;
        border-top: 2px solid var(--border-color);
    }

    [data-bs-theme="dark"] #total_row {
        background: #141414;
    }

    .passCase { color: var(--success-color); }
    .failCase { color: var(--warning-color); }
    .errorCase { color: var(--danger-color); }
    .skipCase { color: var(--primary-color); }

.testcase {
        margin-left: 24px;
    font-size: 14px;
    }

    /* 详情弹窗 */
    .popup_link {
        display: inline-flex;
    align-items: center;
        gap: 4px;
        padding: 4px 12px;
        border-radius: 4px;
        text-decoration: none;
        font-size: 14px;
        transition: all 0.2s;
    }

    .popup_link:hover {
        opacity: 0.8;
    }

.popup_window {
    display: none;
    margin-top: 12px;
        background: #fafafa;
        border-radius: 6px;
        border: 1px solid var(--border-color);
        position: relative;
}

    [data-bs-theme="dark"] .popup_window {
        background: #141414;
        border-color: var(--border-color);
}

.popup_window_header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
        border-bottom: 1px solid var(--border-color);
}

    .popup_window_header strong {
        font-size: 14px;
        color: var(--text-color);
}

    .popup_window_actions {
        display: flex;
        gap: 8px;
    }

    .popup_window_actions button {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 4px;
        padding: 4px 12px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
        color: var(--text-color);
        display: flex;
    align-items: center;
        gap: 4px;
}

    [data-bs-theme="dark"] .popup_window_actions button {
        background: #1f1f1f;
    }

    .popup_window_actions button:hover {
        border-color: var(--primary-color);
        color: var(--primary-color);
}

    .popup_window_content {
        max-height: 400px;
        overflow-y: auto;
        padding: 16px;
    }

    .popup_window_content pre {
        white-space: pre-wrap;
        word-wrap: break-word;
        margin: 0;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.6;
        color: var(--text-color);
    }
    
    .copy-success {
        color: var(--success-color) !important;
        border-color: var(--success-color) !important;
    }

    /* 响应式设计 */
@media (max-width: 768px) {
        body {
            padding: 16px;
        }

        .header-card, .chart-card, .table-card {
            padding: 16px;
        }

        .report-title {
            font-size: 20px;
        }

        .stats-grid {
            grid-template-columns: 1fr;
        }

        #result_table {
            font-size: 13px;
        }

        #result_table td, #result_table th {
            padding: 8px;
        }
    }

    /* 徽章样式 */
    .badge {
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 500;
        font-size: 12px;
        }

    /* 滚动条美化 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: transparent;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(0, 0, 0, 0.2);
        border-radius: 4px;
            }

    [data-bs-theme="dark"] ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 0, 0, 0.3);
    }

    [data-bs-theme="dark"] ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
}

    /* 截图样式 */
    .screenshot-section {
        margin-top: 20px;
        padding-top: 20px;
        border-top: 1px solid var(--border-color);
    }

    .screenshot-header {
        font-weight: 600;
        font-size: 14px;
        color: var(--text-color);
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .screenshot-header-left {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .screenshot-view-toggle {
        display: flex;
        gap: 4px;
    }

    .screenshot-view-btn {
        padding: 2px 8px;
        font-size: 12px;
        border: 1px solid var(--border-color);
        background: white;
        color: var(--text-color);
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s;
    }

    [data-bs-theme="dark"] .screenshot-view-btn {
        background: #1f1f1f;
    }

    .screenshot-view-btn:hover {
        border-color: var(--primary-color);
        color: var(--primary-color);
    }

    .screenshot-view-btn.active {
        background: var(--primary-color);
        border-color: var(--primary-color);
        color: white;
    }

    /* 轮播模式 */
    .screenshot-carousel {
        position: relative;
        width: 100%;
        overflow: hidden;
        border-radius: 8px;
        background: #fafafa;
    }

    [data-bs-theme="dark"] .screenshot-carousel {
        background: #141414;
    }

    .screenshot-carousel-inner {
        display: flex;
        transition: transform 0.3s ease-in-out;
    }

    .screenshot-carousel-item {
        min-width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 20px;
    }

    .screenshot-carousel-item img {
        max-width: 100%;
        max-height: 500px;
        border-radius: 6px;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        cursor: pointer;
    }

    .screenshot-carousel-description {
        margin-top: 12px;
        font-size: 14px;
        color: var(--text-color);
        text-align: center;
    }

    .screenshot-carousel-control {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        width: 40px;
        height: 40px;
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(0,0,0,0.1);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        color: #555;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10;
        opacity: 0;
        transition: all 0.3s;
    }

    .screenshot-carousel:hover .screenshot-carousel-control {
        opacity: 1;
    }

    .screenshot-carousel-control:hover {
        background: #fff;
        color: var(--primary-color);
        transform: translateY(-50%) scale(1.1);
        box-shadow: 0 6px 16px rgba(0,0,0,0.2);
    }

    .screenshot-carousel-control.prev { left: 20px; }
    .screenshot-carousel-control.next { right: 20px; }

    .screenshot-carousel-indicators {
        display: flex;
        justify-content: center;
        gap: 8px;
        padding: 12px;
    }

    .screenshot-carousel-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--border-color);
        cursor: pointer;
        transition: all 0.2s;
    }

    .screenshot-carousel-indicator.active {
        background: var(--primary-color);
        width: 24px;
        border-radius: 4px;
    }

    /* 网格模式 */
    .screenshot-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 16px;
    }

    .screenshot-item {
        margin-bottom: 0;
    }

    .screenshot-description {
        font-size: 13px;
        color: #8c8c8c;
        margin-bottom: 8px;
        font-style: italic;
    }

    .screenshot-image {
        max-width: 100%;
        border-radius: 6px;
        border: 1px solid var(--border-color);
        cursor: pointer;
        transition: all 0.3s;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    .screenshot-image:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    }

    /* 图片预览模态框 */
    .image-modal {
        display: none;
        position: fixed;
        z-index: 9999;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
        animation: fadeIn 0.3s;
    }

    .image-modal-content {
        margin: auto;
        display: block;
        max-width: 90%;
        max-height: 90%;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        animation: zoomIn 0.3s;
    }

    .image-modal-caption {
        text-align: center;
        color: #fff;
        padding: 10px;
        position: absolute;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 16px;
        background: rgba(0, 0, 0, 0.5);
        border-radius: 4px;
        padding: 8px 16px;
    }

    .image-modal-close {
        position: absolute;
        top: 30px;
        right: 30px;
        width: 50px;
        height: 50px;
        color: rgba(255, 255, 255, 0.8);
        font-size: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        background: transparent;
        cursor: pointer;
        transition: all 0.2s;
        z-index: 10002;
    }

    .image-modal-close:hover {
        background: transparent;
        color: #ff4d4f;
        transform: rotate(90deg);
    }

    .image-modal-nav {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        color: rgba(255, 255, 255, 0.7);
        font-size: 50px;
        font-weight: bold;
        cursor: pointer;
        padding: 0 20px;
        user-select: none;
        transition: all 0.3s;
        z-index: 10001;
        height: 100%;
        display: flex;
        align-items: center;
    }

    .image-modal-nav:hover {
        color: #fff;
        background: rgba(0, 0, 0, 0.2);
    }

    .image-modal-prev { left: 0; }
    .image-modal-next { right: 0; }

    .image-modal-counter {
        position: absolute;
        top: 20px;
        left: 20px;
        color: rgba(255, 255, 255, 0.9);
        font-size: 14px;
        background: rgba(0, 0, 0, 0.5);
        padding: 4px 10px;
        border-radius: 4px;
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes zoomIn {
        from { transform: translate(-50%, -50%) scale(0.8); }
        to { transform: translate(-50%, -50%) scale(1); }
    }
</style>
"""

    # ------------------------------------------------------------------------
    # Heading
    #

    HEADING_TMPL = """
    <!-- 主题切换按钮 -->
    <button class="theme-toggle" onclick="toggleTheme()" title="切换主题">
    <i class="bi bi-moon-stars-fill" id="theme-icon"></i>
</button>

    <!-- 头部卡片 -->
    <div class='header-card'>
        <h1 class='report-title'>
            <i class="bi bi-clipboard-check"></i>
        %(title)s
    </h1>
    
        <!-- 统计卡片网格 -->
        <div class='stats-grid'>
            %(parameters)s
    </div>
    
        <p class='description text-muted' style='font-size: 1.1rem; margin-top: 1.5rem;'>%(description)s</p>
</div>

    <!-- 图表卡片 -->
    <div class='chart-card'>
        <div id="chart" style="width:100%%;height:500px;"></div>
    </div>
    
    <script>
    // 更新主题图标
    function updateThemeIcon() {
        const icon = document.getElementById('theme-icon');
        const theme = document.documentElement.getAttribute('data-bs-theme');
        icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
    }
    
    document.addEventListener('DOMContentLoaded', updateThemeIcon);
    
    // 在toggleTheme函数中更新图标
    const originalToggleTheme = window.toggleTheme;
    window.toggleTheme = function() {
        originalToggleTheme();
        updateThemeIcon();
    };
    </script>
"""  # variables: (title, parameters, description)

    HEADING_ATTRIBUTE_TMPL = """
            <div class='stat-card %(card_class)s'>
                <i class='%(icon)s stat-icon'></i>
                <div class='stat-label'>%(name)s</div>
                <div class='stat-value'>%(value)s</div>
            </div>
"""  # variables: (name, value, card_class, icon)

    # ------------------------------------------------------------------------
    # Report
    #

    REPORT_TMPL = u"""
    <div class="table-card">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="mb-0">
                <i class="bi bi-list-check"></i> 测试详情
        </h2>
            <div class="filter-buttons btn-group" role="group">
                <button type="button" class="filter-btn active" onclick='showCase(0)'>
                    <i class="bi bi-clipboard-data"></i> 总结
            </button>
                <button type="button" class="filter-btn" onclick='showCase(1)'>
                    <i class="bi bi-exclamation-triangle"></i> 失败
            </button>
                <button type="button" class="filter-btn" onclick='showCase(2)'>
                    <i class="bi bi-list-ul"></i> 全部
            </button>
        </div>
    </div>
    
    <div class="table-responsive">
            <table id='result_table' class="table table-hover align-middle">
            <thead>
                <tr>
                        <th style="min-width: 300px;"><i class="bi bi-folder2-open"></i> 测试套件/测试用例</th>
                        <th class="text-center" style="width: 100px;"><i class="bi bi-hash"></i> 总数</th>
                        <th class="text-center" style="width: 100px;"><i class="bi bi-check-circle"></i> 通过</th>
                        <th class="text-center" style="width: 100px;"><i class="bi bi-x-circle"></i> 失败</th>
                        <th class="text-center" style="width: 100px;"><i class="bi bi-exclamation-circle"></i> 错误</th>
                        <th class="text-center" style="width: 100px;"><i class="bi bi-dash-circle"></i> 跳过</th>
                        <th class="text-center" style="width: 120px;"><i class="bi bi-eye"></i> 查看</th>
                </tr>
            </thead>
            <tbody>
                %(test_list)s
                    <tr id='total_row'>
                        <td><strong><i class="bi bi-calculator"></i> 总计</strong></td>
    <td class="text-center"><strong>%(count)s</strong></td>
                        <td class="text-center"><span class="badge bg-success">%(Pass)s</span></td>
    <td class="text-center"><span class="badge bg-warning">%(fail)s</span></td>
    <td class="text-center"><span class="badge bg-danger">%(error)s</span></td>
    <td class="text-center"><span class="badge bg-primary">%(skip)s</span></td>
    <td>&nbsp;</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
"""  # variables: (test_list, count, Pass, fail, error, skip)

    REPORT_CLASS_TMPL = u"""
    <tr class='%(style)s'>
        <td>
            <strong><i class="bi bi-folder-fill"></i> %(desc)s</strong>
        </td>
    <td class="text-center">%(count)s</td>
        <td class="text-center"><span class="badge bg-success">%(Pass)s</span></td>
    <td class="text-center"><span class="badge bg-warning">%(fail)s</span></td>
    <td class="text-center"><span class="badge bg-danger">%(error)s</span></td>
    <td class="text-center"><span class="badge bg-primary">%(skip)s</span></td>
    <td class="text-center">
            <a href="javascript:showClassDetail('%(cid)s',%(count)s)" class="btn btn-sm btn-outline-primary">
                <i class="bi bi-chevron-down"></i> 详情
            </a>
    </td>
    </tr>
"""  # variables: (style, desc, count, Pass, fail, error, skip, cid)

    REPORT_TEST_WITH_OUTPUT_TMPL = r"""
<tr id='%(tid)s' style='display:none;'>
    <td class='%(style)s'>
        <div class='testcase'>
            <i class="bi bi-file-earmark-code"></i> %(desc)s
        </div>
    </td>
    <td colspan='5'>
        <div class="text-center">
            <a class="popup_link btn btn-sm btn-outline-info" onfocus='this.blur();' href="javascript:showTestDetail('div_%(tid)s')">
                <i class="bi bi-info-circle"></i> %(status)s
            </a>
        </div>
        <div id='div_%(tid)s' class="popup_window">
            <div class="popup_window_header">
                <strong><i class="bi bi-terminal"></i> 执行详情</strong>
                <div class="popup_window_actions">
                    <button onclick="copyTestDetail('content_%(tid)s', this)" title="复制内容">
                        <i class="bi bi-clipboard"></i> 复制
                    </button>
                    <button onclick="showTestDetail('div_%(tid)s')" title="关闭">
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>
            </div>
            <div class="popup_window_content">
                <pre id='content_%(tid)s'>%(script)s</pre>
                %(screenshots)s
            </div>
        </div>
    </td>
</tr>
"""  # variables: (tid, Class, style, desc, status, screenshots)

    REPORT_TEST_OUTPUT_TMPL = r"""%(id)s: %(output)s"""  # variables: (id, output)

    SCREENSHOT_TMPL = """
    <div class="screenshot-container mt-3" id="screenshot-%(tid)s">
        <div class="d-flex justify-content-between align-items-center mb-2">
            <h6 class="mb-0"><i class="bi bi-card-image"></i> 截图 (%(count)s)</h6>
            <div class="screenshot-view-toggle" style="%(toggle_style)s">
                <button class="btn btn-sm btn-outline-secondary screenshot-view-btn %(btn_carousel_active)s" onclick="switchScreenshotView('%(tid)s', 'carousel')" title="轮播视图">
                    <i class="bi bi-collection-play"></i>
                </button>
                <button class="btn btn-sm btn-outline-secondary screenshot-view-btn %(btn_grid_active)s" onclick="switchScreenshotView('%(tid)s', 'grid')" title="网格视图">
                    <i class="bi bi-grid-3x3-gap"></i>
                </button>
            </div>
        </div>
        
        <!-- 轮播视图 -->
        <div class="screenshot-carousel" id="carousel-%(tid)s" style="%(carousel_style)s">
            <div class="screenshot-carousel-inner" id="carousel-inner-%(tid)s">
                %(carousel_items)s
            </div>
            <button class="screenshot-carousel-control prev" onclick="moveCarousel('%(tid)s', -1)">
                <i class="bi bi-chevron-left"></i>
            </button>
            <button class="screenshot-carousel-control next" onclick="moveCarousel('%(tid)s', 1)">
                <i class="bi bi-chevron-right"></i>
            </button>
            <div class="screenshot-carousel-indicators" id="indicators-%(tid)s">
                %(indicators)s
            </div>
        </div>
        
        <!-- 网格视图 -->
        <div class="screenshot-grid" id="grid-%(tid)s" style="%(grid_style)s">
            %(grid_items)s
        </div>
    </div>
    """

    SCREENSHOT_CAROUSEL_ITEM_TMPL = """
<div class="screenshot-carousel-item">
    <img src="data:image/png;base64,%(data)s" 
         alt="%(description)s"
         onclick="openImageModal('%(tid)s', %(index)s)">
    <div class="screenshot-carousel-description">%(description)s</div>
</div>
"""

    SCREENSHOT_GRID_ITEM_TMPL = """
<div class="screenshot-item">
    <div class="screenshot-description">%(description)s</div>
    <img src="data:image/png;base64,%(data)s" 
         alt="%(description)s" 
         class="screenshot-image"
         onclick="openImageModal('%(tid)s', %(index)s)">
</div>
"""

    # ------------------------------------------------------------------------
    # ENDING
    #

    ENDING_TMPL = """
    <div id='ending' class='text-center py-5'>
        <div class='card' style='background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-radius: 15px; padding: 2rem; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);'>
            <p class='text-muted mb-2'>
        <i class="bi bi-code-square"></i>
                Powered by <strong>HTMLTestRunner</strong> v1.0.5 - Modern UI Edition
    </p>
            <p class='text-muted mb-2' style='font-size: 0.875rem;'>
        <i class="bi bi-person-circle"></i>
                Author: <strong>Lit</strong>
    </p>
            <p class='text-muted mb-0' style='font-size: 0.875rem;'>
        <i class="bi bi-calendar3"></i>
                Generated on <span id='generation-time'></span>
    </p>
        </div>
    </div>

<script>
    // 显示生成时间
    document.getElementById('generation-time').textContent = new Date().toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    // 图片预览模态框功能 - 支持轮播
    let currentModalImages = [];
    let currentModalIndex = 0;

    function openImageModal(tid, index) {
        // 1. 收集该组的所有图片信息
        const gridContainer = document.getElementById('grid-' + tid);
        if (!gridContainer) return;
        
        const imgs = gridContainer.querySelectorAll('img');
        currentModalImages = Array.from(imgs).map(img => ({
            src: img.src,
            description: img.getAttribute('alt') || ''
        }));
        currentModalIndex = index;
        
        let modal = document.getElementById('imageModal');
        if (!modal) {
            // 创建模态框 DOM
            const modalHtml = `
                <div id="imageModal" class="image-modal">
                    <div class="image-modal-close" onclick="closeImageModal()">
                        <i class="bi bi-x-lg"></i>
                    </div>
                    <div class="image-modal-nav image-modal-prev" onclick="changeModalImage(-1)">
                        <i class="bi bi-chevron-left"></i>
                    </div>
                    <div class="image-modal-nav image-modal-next" onclick="changeModalImage(1)">
                        <i class="bi bi-chevron-right"></i>
                    </div>
                    <div class="image-modal-counter" id="modalCounter"></div>
                    <img class="image-modal-content" id="modalImage">
                    <div class="image-modal-caption" id="modalCaption"></div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            modal = document.getElementById('imageModal');
            
            // 点击背景关闭
            modal.addEventListener('click', function(e) {
                if (e.target === modal) closeImageModal();
            });
        }
        
        updateModalContent();
        modal.style.display = 'block';
    }

    function updateModalContent() {
        if (!currentModalImages.length) return;
        
        const data = currentModalImages[currentModalIndex];
        const img = document.getElementById('modalImage');
        const caption = document.getElementById('modalCaption');
        const counter = document.getElementById('modalCounter');
        
        img.src = data.src;
        caption.textContent = data.description;
        counter.textContent = `${currentModalIndex + 1} / ${currentModalImages.length}`;
    }

    function changeModalImage(direction) {
        currentModalIndex += direction;
        if (currentModalIndex < 0) {
            currentModalIndex = currentModalImages.length - 1;
        } else if (currentModalIndex >= currentModalImages.length) {
            currentModalIndex = 0;
        }
        updateModalContent();
    }

    function closeImageModal() {
        const modal = document.getElementById('imageModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    // 键盘事件：ESC关闭，左右键切换
    document.addEventListener('keydown', function(event) {
        const modal = document.getElementById('imageModal');
        if (modal && modal.style.display === 'block') {
            if (event.key === 'Escape') {
                closeImageModal();
            } else if (event.key === 'ArrowLeft') {
                changeModalImage(-1);
            } else if (event.key === 'ArrowRight') {
                changeModalImage(1);
            }
        }
    });

    // 截图轮播功能
    const carouselStates = {};  // 存储每个轮播的当前索引

    function switchScreenshotView(tid, view) {
        const carousel = document.getElementById('carousel-' + tid);
        const grid = document.getElementById('grid-' + tid);
        const section = document.getElementById('screenshot-' + tid);
        const buttons = section.querySelectorAll('.screenshot-view-btn');
        
        buttons.forEach(btn => btn.classList.remove('active'));
        
        if (view === 'carousel') {
            carousel.style.display = 'block';
            grid.style.display = 'none';
            buttons[0].classList.add('active');
        } else {
            carousel.style.display = 'none';
            grid.style.display = 'grid';
            buttons[1].classList.add('active');
        }
    }

    function moveCarousel(tid, direction) {
        if (!carouselStates[tid]) {
            carouselStates[tid] = 0;
        }
        
        const inner = document.getElementById('carousel-inner-' + tid);
        const items = inner.children;
        const totalItems = items.length;
        
        carouselStates[tid] += direction;
        
        if (carouselStates[tid] < 0) {
            carouselStates[tid] = totalItems - 1;
        } else if (carouselStates[tid] >= totalItems) {
            carouselStates[tid] = 0;
        }
        
        updateCarousel(tid);
    }

    function goToSlide(tid, index) {
        carouselStates[tid] = index;
        updateCarousel(tid);
    }

    function updateCarousel(tid) {
        const inner = document.getElementById('carousel-inner-' + tid);
        const indicatorsContainer = document.getElementById('indicators-' + tid);
        const indicators = indicatorsContainer.querySelectorAll('.screenshot-carousel-indicator');
        const currentIndex = carouselStates[tid] || 0;
        
        inner.style.transform = `translateX(-${currentIndex * 100}%)`;
        
        indicators.forEach((indicator, index) => {
            if (index === currentIndex) {
                indicator.classList.add('active');
            } else {
                indicator.classList.remove('active');
            }
        });
    }

    // 初始化所有轮播
    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('.screenshot-carousel').forEach(carousel => {
            const tid = carousel.id.replace('carousel-', '');
            if (!carouselStates[tid]) {
                carouselStates[tid] = 0;
            }
        });
    });
    </script>
    """

# -------------------- The end of the Template class -------------------


TestResult = unittest.TestResult


class _TestResult(TestResult):
    # note: _TestResult is a pure representation of results.
    # It lacks the output and reporting ability compares to unittest._TextTestResult.
    
    def __init__(self, verbosity=1):
        TestResult.__init__(self)
        self.stdout0 = None
        self.stderr0 = None
        self.success_count = 0
        self.failure_count = 0
        self.error_count = 0
        self.skip_count = 0
        self.verbosity = verbosity

        # result is a list of result in 4 tuple
        # (
        #   result code (0: success; 1: fail; 2: error; 3: skip),
        #   TestCase object,
        #   Test output (byte string),
        #   stack trace,
        #   screenshots,  # 新增：截图列表
        # )
        self.result = []
        self.subtestlist = []
        self.outputBuffer = io.StringIO()
        self.test_start_time = round(time.time(), 2)
        self.current_screenshots = []  # 新增：当前测试的截图列表

    def startTest(self, test):
        TestResult.startTest(self, test)
        self.current_screenshots = []  # 新增：重置截图列表
        # just one buffer for both stdout and stderr
        self.outputBuffer = io.StringIO()
        stdout_redirector.fp = self.outputBuffer
        stderr_redirector.fp = self.outputBuffer
        self.stdout0 = sys.stdout
        self.stderr0 = sys.stderr
        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector

    def attach_screenshot(self, image_source, description=""):
        """添加截图到当前测试"""
        screenshot = ScreenshotManager.to_base64(image_source, description)
        if screenshot:
            self.current_screenshots.append(screenshot)

    def complete_output(self):
        """
        Disconnect output redirection and return buffer.
        Safe to call multiple times.
        """
        if self.stdout0:
            sys.stdout = self.stdout0
            sys.stderr = self.stderr0
            self.stdout0 = None
            self.stderr0 = None
        return self.outputBuffer.getvalue()

    def stopTest(self, test):
        # Usually one of addSuccess, addError or addFailure would have been called.
        # But there are some path in unittest that would bypass this.
        # We must disconnect stdout in stopTest(), which is guaranteed to be called.
        self.complete_output()

    def addSuccess(self, test):
        if test not in self.subtestlist:
            self.success_count += 1
            TestResult.addSuccess(self, test)
            output = self.complete_output()
            self.result.append((0, test, output, '', self.current_screenshots[:]))
            if self.verbosity > 1:
                sys.stderr.write('ok ')
                sys.stderr.write(str(test))
                sys.stderr.write('\n')
            else:
                sys.stderr.write('S  ')

    def addError(self, test, err):
        self.error_count += 1
        TestResult.addError(self, test, err)
        _, _exc_str = self.errors[-1]
        output = self.complete_output()
        self.result.append((2, test, output, _exc_str, self.current_screenshots[:]))
        if self.verbosity > 1:
            sys.stderr.write('E  ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            sys.stderr.write('E')

    def addFailure(self, test, err):
        self.failure_count += 1
        TestResult.addFailure(self, test, err)
        _, _exc_str = self.failures[-1]
        output = self.complete_output()
        self.result.append((1, test, output, _exc_str, self.current_screenshots[:]))
        if self.verbosity > 1:
            sys.stderr.write('F  ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            sys.stderr.write('F')

    def addSkip(self, test, reason):
        self.skip_count += 1
        TestResult.addSkip(self, test, reason)
        output = self.complete_output()
        self.result.append((3, test, output, 'Skipped: ' + reason, self.current_screenshots[:]))
        if self.verbosity > 1:
            sys.stderr.write('SKIP ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            sys.stderr.write('s')

    def addSubTest(self, test, subtest, err):
        if err is not None:
            if getattr(self, 'failfast', False):
                self.stop()
            if issubclass(err[0], test.failureException):
                self.failure_count += 1
                errors = self.failures
                errors.append((subtest, self._exc_info_to_string(err, subtest)))
                output = self.complete_output()
                self.result.append((1, test, output + '\nSubTestCase Failed:\n' + str(subtest),
                                    self._exc_info_to_string(err, subtest), self.current_screenshots[:]))
                if self.verbosity > 1:
                    sys.stderr.write('F  ')
                    sys.stderr.write(str(subtest))
                    sys.stderr.write('\n')
                else:
                    sys.stderr.write('F')
            else:
                self.error_count += 1
                errors = self.errors
                errors.append((subtest, self._exc_info_to_string(err, subtest)))
                output = self.complete_output()
                self.result.append(
                    (2, test, output + '\nSubTestCase Error:\n' + str(subtest), self._exc_info_to_string(err, subtest), self.current_screenshots[:]))
                if self.verbosity > 1:
                    sys.stderr.write('E  ')
                    sys.stderr.write(str(subtest))
                    sys.stderr.write('\n')
                else:
                    sys.stderr.write('E')
            self._mirrorOutput = True
        else:
            self.subtestlist.append(subtest)
            self.subtestlist.append(test)
            self.success_count += 1
            output = self.complete_output()
            self.result.append((0, test, output + '\nSubTestCase Pass:\n' + str(subtest), '', self.current_screenshots[:]))
            if self.verbosity > 1:
                sys.stderr.write('ok ')
                sys.stderr.write(str(subtest))
                sys.stderr.write('\n')
            else:
                sys.stderr.write('S')


class HTMLTestRunnerLit(Template_mixin):

    def __init__(self, stream=sys.stdout, verbosity=1, title=None, description=None, tester=None, open_in_browser=False):
        self.stream = stream
        self.verbosity = verbosity
        self.open_in_browser = open_in_browser
        if title is None:
            self.title = self.DEFAULT_TITLE
        else:
            self.title = title
        if description is None:
            self.description = self.DEFAULT_DESCRIPTION
        else:
            self.description = description
        if tester is None:
            self.tester = "QA Team"
        else:
            self.tester = tester

        self.startTime = datetime.datetime.now()
        
    def run(self, test):
        "Run the given test case or test suite."
        global _current_result
        result = _TestResult(self.verbosity)
        _current_result = result  # 新增：设置全局引用
        test(result)
        _current_result = None  # 新增：清除全局引用
        self.stopTime = datetime.datetime.now()
        self.generateReport(test, result)
        print('\nTime 运行时长: %s' % (self.stopTime-self.startTime), file=sys.stderr)
        
        # 自动打开报告
        if self.open_in_browser and hasattr(self.stream, 'name'):
            report_path = os.path.abspath(self.stream.name)
            webbrowser.open('file://' + report_path)
            print('报告已在浏览器中打开: %s' % report_path, file=sys.stderr)
        
        return result

    def sortResult(self, result_list):
        # unittest does not seems to run in any particular order.
        # Here at least we want to group them together by class.
        rmap = {}
        classes = []
        for n,t,o,e,*screenshots_list in result_list:
            cls = t.__class__
            if cls not in rmap:
                rmap[cls] = []
                classes.append(cls)
            screenshots = screenshots_list[0] if screenshots_list else []
            rmap[cls].append((n,t,o,e,screenshots))
        r = [(cls, rmap[cls]) for cls in classes]
        return r

    def getReportAttributes(self, result):
        """
        Return report attributes as a list of (name, value).
        Override this to add custom attributes.
        """
        startTime = str(self.startTime)[:19]
        duration = str(self.stopTime - self.startTime)
        status = []
        if result.success_count: status.append(u'通过 %s' % result.success_count)
        if result.failure_count: status.append(u'失败 %s' % result.failure_count)
        if result.error_count:   status.append(u'错误 %s' % result.error_count)
        if result.skip_count:    status.append(u'跳过 %s' % result.skip_count)
        if status:
            status = ' '.join(status)
        else:
            status = 'none'
        return [
            (u'开始时间', startTime),
            (u'运行时长', duration),
            (u'状态', status),
            (u'测试人', self.tester),
        ]

    def generateReport(self, test, result):
        report_attrs = self.getReportAttributes(result)
        generator = 'HTMLTestRunner %s' % __version__
        stylesheet = self._generate_stylesheet()
        heading = self._generate_heading(report_attrs)
        report = self._generate_report(result)
        ending = self._generate_ending()
        chart = self._generate_chart(result)
        output = self.HTML_TMPL % dict(
            title = saxutils.escape(self.title),
            generator = generator,
            stylesheet = stylesheet,
            heading = heading,
            report = report,
            ending = ending,
            chart_script = chart
        )
        self.stream.write(output.encode('utf8'))

    def _generate_stylesheet(self):
        return self.STYLESHEET_TMPL

    def _generate_heading(self, report_attrs):
        a_lines = []
        # 为每个属性定义图标和卡片样式
        attr_config = {
            u'开始时间': {'icon': 'bi bi-clock-history', 'class': 'info'},
            u'运行时长': {'icon': 'bi bi-stopwatch', 'class': 'primary'},
            u'状态': {'icon': 'bi bi-flag-fill', 'class': 'success'},
            u'测试人': {'icon': 'bi bi-person-fill', 'class': 'secondary'},
        }
        
        for name, value in report_attrs:
            config = attr_config.get(name, {'icon': 'bi bi-info-circle', 'class': 'info'})
            line = self.HEADING_ATTRIBUTE_TMPL % dict(
                name = saxutils.escape(name),
                value = saxutils.escape(value),
                card_class = config['class'],
                icon = config['icon'],
            )
            a_lines.append(line)
        heading = self.HEADING_TMPL % dict(
            title = saxutils.escape(self.title),
            parameters = ''.join(a_lines),
            description = saxutils.escape(self.description),
        )
        return heading

    def _generate_report(self, result):
        rows = []
        sortedResult = self.sortResult(result.result)
        for cid, (cls, cls_results) in enumerate(sortedResult):
            # subtotal for a class
            np = nf = ne = ns = 0
            for n,t,o,e,*screenshots_list in cls_results:
                if n == 0: np += 1
                elif n == 1: nf += 1
                elif n == 2: ne += 1
                else: ns += 1
            
            # format class description
            if cls.__module__ == "__main__":
                name = cls.__name__
            else:
                name = "%s.%s" % (cls.__module__, cls.__name__)
            doc = cls.__doc__ and cls.__doc__.split("\n")[0] or ""
            desc = doc and '%s: %s' % (name, doc) or name

            row = self.REPORT_CLASS_TMPL % dict(
                style = ne > 0 and 'errorClass' or nf > 0 and 'failClass' or ns > 0 and 'skipClass' or 'passClass',
                desc = desc,
                count = np+nf+ne+ns,
                Pass = np,
                fail = nf,
                error = ne,
                skip = ns,
                cid = 'c%s' % (cid+1),
            )
            rows.append(row)

            for tid, (n,t,o,e,*screenshots_list) in enumerate(cls_results):
                screenshots = screenshots_list[0] if screenshots_list else []
                self._generate_report_test(rows, cid, tid, n, t, o, e, screenshots)

        report = self.REPORT_TMPL % dict(
            test_list = ''.join(rows),
            count = str(result.success_count+result.failure_count+result.error_count+result.skip_count),
            Pass = str(result.success_count),
            fail = str(result.failure_count),
            error = str(result.error_count),
            skip = str(result.skip_count),
        )
        return report

    def _generate_chart(self, result):
        chart = self.ECHARTS_SCRIPT % dict(
            Pass=str(result.success_count),
            fail=str(result.failure_count),
            error=str(result.error_count),
            skip=str(result.skip_count),
        )
        return chart

    def _generate_report_test(self, rows, cid, tid, n, t, o, e, screenshots=None):
        # e.g. 'pt1.1', 'ft1.1', 'st1.1', etc
        # n == 0: pass, 1: fail, 2: error, 3: skip
        if n == 0:
            prefix = 'p'
        elif n == 3:
            prefix = 's'
        else:
            prefix = 'f'
        tid = prefix + 't%s.%s' % (cid+1,tid+1)
        name = t.id().split('.')[-1]
        doc = t.shortDescription() or ""
        desc = doc and ('%s: %s' % (name, doc)) or name
        
        # 所有测试用例都使用WITH_OUTPUT模板，即使没有输出也显示详情按钮
        tmpl = self.REPORT_TEST_WITH_OUTPUT_TMPL

        script = self.REPORT_TEST_OUTPUT_TMPL % dict(
            id=tid,
            output=saxutils.escape(o+e) if (o or e) else '无输出信息',
        )

        # 生成截图 HTML
        screenshot_html = ''
        if screenshots and len(screenshots) > 0:
            count = len(screenshots)
            
            # 判断默认视图：2张及以上使用轮播，否则使用网格
            if count >= 2:
                default_view = 'carousel'
                toggle_style = ''
                carousel_style = 'display: block;'
                grid_style = 'display: none;'
                btn_carousel_active = 'active'
                btn_grid_active = ''
            else:
                default_view = 'grid'
                toggle_style = ''
                carousel_style = 'display: none;'
                grid_style = 'display: grid;'
                btn_carousel_active = ''
                btn_grid_active = 'active'

            # 生成轮播项
            carousel_items = []
            for i, screenshot in enumerate(screenshots):
                item = self.SCREENSHOT_CAROUSEL_ITEM_TMPL % {
                    'data': screenshot['data'],
                    'description': saxutils.escape(screenshot['description']),
                    'tid': tid,
                    'index': i
                }
                carousel_items.append(item)
            
            # 生成网格项
            grid_items = []
            for i, screenshot in enumerate(screenshots):
                item = self.SCREENSHOT_GRID_ITEM_TMPL % {
                    'data': screenshot['data'],
                    'description': saxutils.escape(screenshot['description']),
                    'tid': tid,
                    'index': i
                }
                grid_items.append(item)
            
            # 生成指示器
            indicators = []
            for i in range(len(screenshots)):
                active_class = 'active' if i == 0 else ''
                indicators.append(f'<div class="screenshot-carousel-indicator {active_class}" onclick="goToSlide(\'{tid}\', {i})"></div>')
            
            screenshot_html = self.SCREENSHOT_TMPL % {
                'tid': tid,
                'count': count,
                'toggle_style': toggle_style,
                'carousel_style': carousel_style,
                'grid_style': grid_style,
                'btn_carousel_active': btn_carousel_active,
                'btn_grid_active': btn_grid_active,
                'carousel_items': ''.join(carousel_items),
                'grid_items': ''.join(grid_items),
                'indicators': ''.join(indicators)
            }

        if n == 0:
            style = 'none'
            badge = '<span class="badge bg-success"><i class="bi bi-check-lg"></i> %s</span>' % self.STATUS[n]
        elif n == 1:
            style = 'failCase'
            badge = '<span class="badge bg-warning"><i class="bi bi-x-lg"></i> %s</span>' % self.STATUS[n]
        elif n == 2:
            style = 'errorCase'
            badge = '<span class="badge bg-danger"><i class="bi bi-exclamation-triangle-fill"></i> %s</span>' % self.STATUS[n]
        else:  # n == 3 (skip)
            style = 'skipCase'
            badge = '<span class="badge bg-primary"><i class="bi bi-dash-circle"></i> %s</span>' % self.STATUS[n]

        row = tmpl % dict(
            tid=tid,
            Class=(n == 0 and 'hiddenRow' or 'none'),
            style=style,
            desc=desc,
            script=script,
            status=self.STATUS[n],
            screenshots=screenshot_html,
        )
        rows.append(row)

    def _generate_ending(self):
        return self.ENDING_TMPL


##############################################################################
# Facilities for running tests from the command line
##############################################################################

# Note: Reuse unittest.TestProgram to launch test. In the future we may
# build our own launcher to support more specific command line
# parameters like test title, CSS, etc.
class TestProgram(unittest.TestProgram):
    """
    A variation of the unittest.TestProgram. Please refer to the base
    class for command line parameters.
    """
    def runTests(self):
        # Pick HTMLTestRunner as the default test runner.
        # base class's testRunner parameter is not useful because it means
        # we have to instantiate HTMLTestRunner before we know self.verbosity.
        if self.testRunner is None:
            self.testRunner = HTMLTestRunnerLit(verbosity=self.verbosity)
        unittest.TestProgram.runTests(self)

main = TestProgram

##############################################################################
# Executing this module from the command line
##############################################################################

if __name__ == "__main__":
    main(module=None)
