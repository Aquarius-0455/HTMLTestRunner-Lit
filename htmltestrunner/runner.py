# -*- coding: utf-8 -*-
"""
HTMLTestRunner Modern - 现代化的 Python 测试报告生成器

🎨 Features:
    - Bootstrap 5 + ECharts 5 现代 UI
    - 深色/浅色主题切换
    - 响应式设计，完美支持移动端
    - 环形图表可视化展示通过率
    - 测试详情支持复制、展开/折叠
    - 支持 subTest 子测试用例
    - 支持自定义主题配色
    - 支持导出 JSON 格式结果

🔧 Usage:
    >>> import unittest
    >>> from HTMLTestRunner_Modern import HTMLTestRunner
    >>> 
    >>> # 创建测试套件
    >>> suite = unittest.TestLoader().loadTestsFromTestCase(YourTestCase)
    >>> 
    >>> # 生成报告
    >>> with open('report.html', 'wb') as f:
    ...     runner = HTMLTestRunner(
    ...         stream=f,
    ...         title='API 测试报告',
    ...         description='项目接口自动化测试',
    ...         tester='QA Team'
    ...     )
    ...     runner.run(suite)

📝 License: MIT
👤 Author: Lit
🔗 GitHub: https://github.com/Lit-CAO/htmltestrunner-modern
"""

__author__ = "Lit"
__version__ = "2.0.0"
__license__ = "MIT"

import datetime
import sys
import io
import time
import json
import unittest
from xml.sax import saxutils
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import IntEnum


# ============================================================================
# Constants & Enums
# ============================================================================

class TestStatus(IntEnum):
    """测试状态枚举"""
    PASS = 0
    FAIL = 1
    ERROR = 2
    SKIP = 3


STATUS_LABELS = {
    TestStatus.PASS: '通过',
    TestStatus.FAIL: '失败',
    TestStatus.ERROR: '错误',
    TestStatus.SKIP: '跳过',
}


# ============================================================================
# Output Redirector
# ============================================================================

class OutputRedirector:
    """标准输出重定向器，用于捕获测试过程中的输出"""
    
    def __init__(self, fp):
        self.fp = fp

    def write(self, s: str) -> None:
        self.fp.write(s)

    def writelines(self, lines: List[str]) -> None:
        self.fp.writelines(lines)

    def flush(self) -> None:
        self.fp.flush()


stdout_redirector = OutputRedirector(sys.stdout)
stderr_redirector = OutputRedirector(sys.stderr)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class TestCaseResult:
    """单个测试用例的结果"""
    status: TestStatus
    test: unittest.TestCase
    output: str
    traceback: str
    duration: float = 0.0


@dataclass
class TestClassResult:
    """测试类的汇总结果"""
    name: str
    description: str
    pass_count: int = 0
    fail_count: int = 0
    error_count: int = 0
    skip_count: int = 0
    test_cases: List[TestCaseResult] = field(default_factory=list)
    
    @property
    def total_count(self) -> int:
        return self.pass_count + self.fail_count + self.error_count + self.skip_count
    
    @property
    def status_class(self) -> str:
        if self.error_count > 0:
            return 'errorClass'
        elif self.fail_count > 0:
            return 'failClass'
        elif self.skip_count > 0:
            return 'skipClass'
        return 'passClass'


@dataclass
class ReportConfig:
    """报告配置"""
    title: str = 'Test Report'
    description: str = ''
    tester: str = 'QA Team'
    theme: str = 'light'  # 'light' or 'dark'
    chart_height: int = 400
    show_pass_cases: bool = True
    language: str = 'zh-CN'  # 'zh-CN' or 'en-US'


# ============================================================================
# Theme Configuration
# ============================================================================

class ThemeConfig:
    """主题配置"""
    
    LIGHT = {
        'primary': '#1890ff',
        'success': '#52c41a',
        'warning': '#faad14',
        'danger': '#f5222d',
        'info': '#13c2c2',
        'border': '#d9d9d9',
        'text': '#262626',
        'text_secondary': '#8c8c8c',
        'bg': '#f0f2f5',
        'card_bg': '#ffffff',
    }
    
    DARK = {
        'primary': '#177ddc',
        'success': '#49aa19',
        'warning': '#d89614',
        'danger': '#d32029',
        'border': '#434343',
        'text': '#e8e8e8',
        'text_secondary': '#a6a6a6',
        'bg': '#141414',
        'card_bg': '#1f1f1f',
    }
    
    # 可扩展更多主题
    THEMES = {
        'light': LIGHT,
        'dark': DARK,
    }


# ============================================================================
# HTML Templates
# ============================================================================

class TemplateEngine:
    """HTML 模板引擎"""
    
    # 多语言支持
    I18N = {
        'zh-CN': {
            'title': '测试报告',
            'start_time': '开始时间',
            'duration': '运行时长',
            'status': '状态',
            'tester': '测试人',
            'test_details': '测试详情',
            'summary': '总结',
            'failed': '失败',
            'all': '全部',
            'test_suite': '测试套件/测试用例',
            'total': '总数',
            'pass': '通过',
            'fail': '失败',
            'error': '错误',
            'skip': '跳过',
            'view': '查看',
            'detail': '详情',
            'total_summary': '总计',
            'execution_details': '执行详情',
            'copy': '复制',
            'copied': '已复制',
            'close': '关闭',
            'no_output': '无输出信息',
            'pass_rate': '通过率',
            'test_execution': '测试执行情况',
            'powered_by': '由 HTMLTestRunner Modern 驱动',
            'generated_on': '生成于',
            'toggle_theme': '切换主题',
        },
        'en-US': {
            'title': 'Test Report',
            'start_time': 'Start Time',
            'duration': 'Duration',
            'status': 'Status',
            'tester': 'Tester',
            'test_details': 'Test Details',
            'summary': 'Summary',
            'failed': 'Failed',
            'all': 'All',
            'test_suite': 'Test Suite / Test Case',
            'total': 'Total',
            'pass': 'Pass',
            'fail': 'Fail',
            'error': 'Error',
            'skip': 'Skip',
            'view': 'View',
            'detail': 'Detail',
            'total_summary': 'Total',
            'execution_details': 'Execution Details',
            'copy': 'Copy',
            'copied': 'Copied',
            'close': 'Close',
            'no_output': 'No output',
            'pass_rate': 'Pass Rate',
            'test_execution': 'Test Execution',
            'powered_by': 'Powered by HTMLTestRunner Modern',
            'generated_on': 'Generated on',
            'toggle_theme': 'Toggle Theme',
        }
    }
    
    @classmethod
    def get_text(cls, key: str, language: str = 'zh-CN') -> str:
        """获取多语言文本"""
        return cls.I18N.get(language, cls.I18N['zh-CN']).get(key, key)

    HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="%(lang)s">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="HTMLTestRunner Modern %(version)s">
    <meta name="author" content="%(author)s">
    <title>%(title)s</title>
    
    <!-- External Resources -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    %(stylesheet)s
</head>
<body>
    %(scripts)s
    <div class="container-fluid">
        %(heading)s
        %(report)s
        %(ending)s
    </div>
    %(chart_script)s
</body>
</html>'''

    STYLESHEET = '''
<style>
:root {
    --primary: #1890ff;
    --success: #52c41a;
    --warning: #faad14;
    --danger: #f5222d;
    --info: #13c2c2;
    --border: #d9d9d9;
    --text: #262626;
    --text-secondary: #8c8c8c;
    --bg: #f0f2f5;
    --card-bg: #ffffff;
    --table-header-bg: #fafafa;
    --hover-bg: #fafafa;
}

[data-bs-theme="dark"] {
    --primary: #177ddc;
    --success: #49aa19;
    --warning: #d89614;
    --danger: #d32029;
    --border: #434343;
    --text: #e8e8e8;
    --text-secondary: #a6a6a6;
    --bg: #141414;
    --card-bg: #1f1f1f;
    --table-header-bg: #141414;
    --hover-bg: #262626;
}

* { box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    background: var(--bg);
    min-height: 100vh;
    padding: 24px;
    margin: 0;
    color: var(--text);
    transition: background-color 0.3s, color 0.3s;
}

.container-fluid { max-width: 1400px; margin: 0 auto; }

/* Cards */
.card-custom {
    background: var(--card-bg);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    border: 1px solid var(--border);
    transition: all 0.3s;
}

.card-custom:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

/* Header */
.report-title {
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(135deg, var(--primary), var(--info));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
}

.report-title i {
    font-size: 32px;
    color: var(--primary);
    -webkit-text-fill-color: var(--primary);
}

/* Theme Toggle */
.theme-toggle {
    position: fixed;
    top: 24px;
    right: 24px;
    z-index: 1000;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 50%;
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transition: all 0.3s;
    color: var(--text);
    font-size: 20px;
}

.theme-toggle:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
}

/* Stats Grid */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
}

.stat-card {
    background: var(--card-bg);
    border-radius: 12px;
    padding: 20px;
    border: 1px solid var(--border);
    transition: all 0.3s;
    position: relative;
    overflow: hidden;
}

.stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    border-radius: 12px 12px 0 0;
}

.stat-card.info::before { background: var(--info); }
.stat-card.primary::before { background: var(--primary); }
.stat-card.success::before { background: var(--success); }
.stat-card.secondary::before { background: var(--text-secondary); }

.stat-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.stat-label {
    font-size: 14px;
    color: var(--text-secondary);
    margin-bottom: 8px;
    font-weight: 500;
}

.stat-value {
    font-size: 22px;
    font-weight: 700;
    color: var(--text);
}

.stat-icon {
    position: absolute;
    right: 20px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 32px;
    opacity: 0.15;
}

/* Table */
.table-card {
    overflow: hidden;
}

#result_table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
}

#result_table thead th {
    background: var(--table-header-bg);
    color: var(--text);
    font-weight: 600;
    padding: 14px 16px;
    font-size: 14px;
    border-bottom: 2px solid var(--border);
    text-align: left;
    position: sticky;
    top: 0;
    z-index: 10;
}

#result_table tbody tr {
    transition: all 0.2s;
    border-bottom: 1px solid var(--border);
}

#result_table tbody tr:hover {
    background: var(--hover-bg);
}

#result_table td {
    padding: 14px 16px;
    vertical-align: middle;
    font-size: 14px;
}

/* Status Classes */
.passClass { background: rgba(82, 196, 26, 0.08); }
.failClass { background: rgba(250, 173, 20, 0.08); }
.errorClass { background: rgba(245, 34, 45, 0.08); }
.skipClass { background: rgba(24, 144, 255, 0.08); }

.passCase { color: var(--success); }
.failCase { color: var(--warning); }
.errorCase { color: var(--danger); }
.skipCase { color: var(--primary); }

/* Badges */
.badge {
    padding: 4px 10px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 12px;
}

/* Filter Buttons */
.filter-btn {
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.3s;
    background: var(--card-bg);
    color: var(--text);
}

.filter-btn:hover {
    border-color: var(--primary);
    color: var(--primary);
}

.filter-btn.active {
    background: linear-gradient(135deg, var(--primary), #40a9ff);
    border-color: var(--primary);
    color: white;
}

/* Test Case Row */
.testcase {
    margin-left: 28px;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Popup Window */
.popup_window {
    display: none;
    margin-top: 12px;
    background: var(--table-header-bg);
    border-radius: 8px;
    border: 1px solid var(--border);
    overflow: hidden;
    animation: slideDown 0.3s ease;
}

@keyframes slideDown {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

.popup_window_header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
    background: var(--card-bg);
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
    font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
    font-size: 13px;
    line-height: 1.7;
    color: var(--text);
}

/* Action Buttons */
.action-btn {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
    color: var(--text);
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.action-btn:hover {
    border-color: var(--primary);
    color: var(--primary);
}

.copy-success {
    color: var(--success) !important;
    border-color: var(--success) !important;
}

/* Footer */
.footer-card {
    text-align: center;
    padding: 32px;
    background: linear-gradient(135deg, var(--card-bg), var(--bg));
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.card-custom { animation: fadeIn 0.5s ease forwards; }
.stats-grid .stat-card:nth-child(1) { animation-delay: 0.1s; }
.stats-grid .stat-card:nth-child(2) { animation-delay: 0.2s; }
.stats-grid .stat-card:nth-child(3) { animation-delay: 0.3s; }
.stats-grid .stat-card:nth-child(4) { animation-delay: 0.4s; }

/* Scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.2); border-radius: 4px; }
[data-bs-theme="dark"] ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); }

/* Responsive */
@media (max-width: 768px) {
    body { padding: 12px; }
    .card-custom { padding: 16px; }
    .report-title { font-size: 20px; }
    .stats-grid { grid-template-columns: 1fr 1fr; }
    .theme-toggle { width: 40px; height: 40px; top: 12px; right: 12px; }
}

@media (max-width: 480px) {
    .stats-grid { grid-template-columns: 1fr; }
    .filter-btn { padding: 6px 12px; font-size: 12px; }
}
</style>'''

    SCRIPTS = '''
<script>
// Theme Management
const ThemeManager = {
    init() {
        const saved = localStorage.getItem('theme') || 'light';
        this.setTheme(saved);
    },
    toggle() {
        const current = document.documentElement.getAttribute('data-bs-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        this.setTheme(next);
    },
    setTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);
        this.updateIcon(theme);
        this.updateChart(theme);
    },
    updateIcon(theme) {
        const icon = document.getElementById('theme-icon');
        if (icon) icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
    },
    updateChart(theme) {
        const chartDom = document.getElementById('chart');
        if (chartDom && window.initChart) {
            const chart = echarts.getInstanceByDom(chartDom);
            if (chart) chart.dispose();
            window.initChart();
        }
    }
};

// Case Filter
function showCase(level) {
    const rows = document.querySelectorAll('tr[id^="ft"], tr[id^="pt"], tr[id^="st"]');
    rows.forEach(row => {
        const prefix = row.id.substring(0, 2);
        let show = false;
        if (level === 0) show = false;  // Summary
        else if (level === 1) show = prefix === 'ft';  // Failed only
        else show = true;  // All
        row.style.display = show ? 'table-row' : 'none';
        if (!show) {
            const popup = document.getElementById('div_' + row.id);
            if (popup) popup.style.display = 'none';
        }
    });
    document.querySelectorAll('.filter-btn').forEach((btn, idx) => {
        btn.classList.toggle('active', idx === level);
    });
}

// Class Detail Toggle
function showClassDetail(cid, count) {
    const baseId = cid.substring(1);
    let firstRow = null;
    for (let i = 1; i <= count; i++) {
        const tid = `t${baseId}.${i}`;
        const row = document.getElementById('f' + tid) || document.getElementById('p' + tid) || document.getElementById('s' + tid);
        if (row && !firstRow) firstRow = row;
    }
    if (!firstRow) return;
    
    const isHidden = firstRow.style.display === 'none' || !firstRow.style.display;
    for (let i = 1; i <= count; i++) {
        const tid = `t${baseId}.${i}`;
        const row = document.getElementById('f' + tid) || document.getElementById('p' + tid) || document.getElementById('s' + tid);
        if (row) {
            row.style.display = isHidden ? 'table-row' : 'none';
            if (!isHidden) {
                const popup = document.getElementById('div_' + row.id);
                if (popup) popup.style.display = 'none';
            }
        }
    }
}

// Test Detail Toggle
function showTestDetail(divId) {
    const div = document.getElementById(divId);
    if (div) div.style.display = div.style.display === 'block' ? 'none' : 'block';
}

// Copy to Clipboard
async function copyTestDetail(contentId, button) {
    const content = document.getElementById(contentId);
    if (!content) return;
    
    try {
        await navigator.clipboard.writeText(content.textContent);
        showCopySuccess(button);
    } catch {
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = content.textContent;
        textarea.style.cssText = 'position:fixed;opacity:0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showCopySuccess(button);
    }
}

function showCopySuccess(button) {
    const original = button.innerHTML;
    button.innerHTML = '<i class="bi bi-check-lg"></i> 已复制';
    button.classList.add('copy-success');
    setTimeout(() => {
        button.innerHTML = original;
        button.classList.remove('copy-success');
    }, 2000);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
});
</script>'''

    HEADING_TEMPLATE = '''
<button class="theme-toggle" onclick="ThemeManager.toggle()" title="%(toggle_theme)s">
    <i class="bi bi-moon-stars-fill" id="theme-icon"></i>
</button>

<div class="card-custom">
    <h1 class="report-title">
        <i class="bi bi-clipboard-data-fill"></i>
        %(title)s
    </h1>
    
    <div class="stats-grid">
        %(stats_cards)s
    </div>
    
    <p class="text-muted mb-0" style="font-size: 15px;">%(description)s</p>
</div>

<div class="card-custom">
    <div id="chart" style="width:100%%;height:%(chart_height)spx;"></div>
</div>'''

    STAT_CARD_TEMPLATE = '''
<div class="stat-card %(card_class)s">
    <i class="bi %(icon)s stat-icon"></i>
    <div class="stat-label">%(label)s</div>
    <div class="stat-value">%(value)s</div>
</div>'''

    REPORT_TEMPLATE = '''
<div class="card-custom table-card">
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
        <h2 class="mb-0" style="font-size: 20px; font-weight: 600;">
            <i class="bi bi-list-check"></i> %(test_details)s
        </h2>
        <div class="btn-group" role="group">
            <button class="filter-btn active" onclick="showCase(0)">
                <i class="bi bi-clipboard-data"></i> %(summary)s
            </button>
            <button class="filter-btn" onclick="showCase(1)">
                <i class="bi bi-exclamation-triangle"></i> %(failed)s
            </button>
            <button class="filter-btn" onclick="showCase(2)">
                <i class="bi bi-list-ul"></i> %(all)s
            </button>
        </div>
    </div>
    
    <div class="table-responsive">
        <table id="result_table">
            <thead>
                <tr>
                    <th style="min-width: 300px;"><i class="bi bi-folder2-open"></i> %(test_suite)s</th>
                    <th class="text-center" style="width: 80px;"><i class="bi bi-hash"></i> %(total)s</th>
                    <th class="text-center" style="width: 80px;"><i class="bi bi-check-circle"></i> %(pass)s</th>
                    <th class="text-center" style="width: 80px;"><i class="bi bi-x-circle"></i> %(fail)s</th>
                    <th class="text-center" style="width: 80px;"><i class="bi bi-exclamation-circle"></i> %(error)s</th>
                    <th class="text-center" style="width: 80px;"><i class="bi bi-dash-circle"></i> %(skip)s</th>
                    <th class="text-center" style="width: 100px;"><i class="bi bi-eye"></i> %(view)s</th>
                </tr>
            </thead>
            <tbody>
                %(test_list)s
                %(total_row)s
            </tbody>
        </table>
    </div>
</div>'''

    TOTAL_ROW_TEMPLATE = '''
<tr style="font-weight: 600; background: var(--table-header-bg); border-top: 2px solid var(--border);">
    <td><i class="bi bi-calculator"></i> %(total_summary)s</td>
    <td class="text-center"><strong>%(count)s</strong></td>
    <td class="text-center"><span class="badge bg-success">%(pass)s</span></td>
    <td class="text-center"><span class="badge bg-warning">%(fail)s</span></td>
    <td class="text-center"><span class="badge bg-danger">%(error)s</span></td>
    <td class="text-center"><span class="badge bg-primary">%(skip)s</span></td>
    <td>&nbsp;</td>
</tr>'''

    CLASS_ROW_TEMPLATE = '''
<tr class="%(style)s">
    <td><strong><i class="bi bi-folder-fill"></i> %(desc)s</strong></td>
    <td class="text-center">%(count)s</td>
    <td class="text-center"><span class="badge bg-success">%(pass)s</span></td>
    <td class="text-center"><span class="badge bg-warning">%(fail)s</span></td>
    <td class="text-center"><span class="badge bg-danger">%(error)s</span></td>
    <td class="text-center"><span class="badge bg-primary">%(skip)s</span></td>
    <td class="text-center">
        <button class="action-btn" onclick="showClassDetail('%(cid)s', %(count)s)">
            <i class="bi bi-chevron-down"></i> %(detail)s
        </button>
    </td>
</tr>'''

    TEST_ROW_TEMPLATE = '''
<tr id="%(tid)s" style="display:none;">
    <td class="%(style)s">
        <div class="testcase">
            <i class="bi bi-file-earmark-code"></i> %(desc)s
        </div>
    </td>
    <td colspan="5">
        <div class="text-center">
            <button class="action-btn" onclick="showTestDetail('div_%(tid)s')">
                <i class="bi bi-info-circle"></i> %(status)s
            </button>
        </div>
        <div id="div_%(tid)s" class="popup_window">
            <div class="popup_window_header">
                <strong><i class="bi bi-terminal"></i> %(execution_details)s</strong>
                <div style="display: flex; gap: 8px;">
                    <button class="action-btn" onclick="copyTestDetail('content_%(tid)s', this)">
                        <i class="bi bi-clipboard"></i> %(copy)s
                    </button>
                    <button class="action-btn" onclick="showTestDetail('div_%(tid)s')">
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>
            </div>
            <div class="popup_window_content">
                <pre id="content_%(tid)s">%(script)s</pre>
            </div>
        </div>
    </td>
</tr>'''

    ENDING_TEMPLATE = '''
<div class="card-custom footer-card">
    <p class="text-muted mb-2">
        <i class="bi bi-code-square"></i>
        %(powered_by)s v%(version)s
    </p>
    <p class="text-muted mb-2" style="font-size: 14px;">
        <i class="bi bi-person-circle"></i>
        %(tester)s
    </p>
    <p class="text-muted mb-0" style="font-size: 14px;">
        <i class="bi bi-calendar3"></i>
        %(generated_on)s %(time)s
    </p>
</div>'''

    CHART_SCRIPT_TEMPLATE = '''
<script>
window.initChart = function() {
    const chartDom = document.getElementById('chart');
    if (!chartDom) return;
    
    const chart = echarts.init(chartDom);
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    
    const data = {
        pass: %(pass)s,
        fail: %(fail)s,
        error: %(error)s,
        skip: %(skip)s
    };
    const total = data.pass + data.fail + data.error + data.skip;
    const passRate = total > 0 ? ((data.pass / total) * 100).toFixed(1) : 0;

    chart.setOption({
        title: {
            text: '%(test_execution)s',
            subtext: '%(pass_rate)s: ' + passRate + '%%',
            left: 'center',
            top: '5%%',
            textStyle: { fontSize: 18, fontWeight: 600, color: isDark ? '#e8e8e8' : '#262626' },
            subtextStyle: { fontSize: 14, color: isDark ? '#a6a6a6' : '#8c8c8c' }
        },
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c} ({d}%%)',
            backgroundColor: isDark ? 'rgba(0,0,0,0.9)' : 'rgba(255,255,255,0.95)',
            borderColor: isDark ? '#434343' : '#d9d9d9',
            textStyle: { color: isDark ? '#e8e8e8' : '#262626' }
        },
        legend: {
            orient: 'horizontal',
            bottom: '5%%',
            textStyle: { color: isDark ? '#e8e8e8' : '#262626' },
            data: ['%(pass_label)s', '%(fail_label)s', '%(error_label)s', '%(skip_label)s']
        },
        series: [{
            name: 'Result',
            type: 'pie',
            radius: ['45%%', '70%%'],
            center: ['50%%', '50%%'],
            avoidLabelOverlap: true,
            itemStyle: { borderRadius: 8, borderColor: isDark ? '#141414' : '#fff', borderWidth: 3 },
            label: {
                formatter: p => p.value === 0 ? '' : p.name + '\\n' + p.value + ' (' + p.percent + '%%)',
                color: isDark ? '#e8e8e8' : '#262626'
            },
            labelLine: { length: 20, length2: 40, lineStyle: { color: isDark ? '#434343' : '#d9d9d9' } },
            emphasis: {
                scale: true,
                scaleSize: 8,
                itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0,0,0,0.3)' }
            },
            data: [
                { value: data.pass, name: '%(pass_label)s', itemStyle: { color: '#52c41a' } },
                { value: data.fail, name: '%(fail_label)s', itemStyle: { color: '#faad14' } },
                { value: data.error, name: '%(error_label)s', itemStyle: { color: '#f5222d' } },
                { value: data.skip, name: '%(skip_label)s', itemStyle: { color: '#1890ff' } }
            ],
            animationType: 'scale',
            animationEasing: 'elasticOut'
        }]
    });
    
    window.addEventListener('resize', () => chart.resize());
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', window.initChart);
} else {
    window.initChart();
}
</script>'''


# ============================================================================
# Test Result Class
# ============================================================================

class HTMLTestResult(unittest.TestResult):
    """增强的测试结果收集器"""
    
    def __init__(self, verbosity: int = 1):
        super().__init__()
        self.verbosity = verbosity
        self.success_count = 0
        self.failure_count = 0
        self.error_count = 0
        self.skip_count = 0
        self.results: List[Tuple[TestStatus, unittest.TestCase, str, str, float]] = []
        self.subtest_list = []
        self.output_buffer = io.StringIO()
        self.start_time = time.time()
        self._stdout = None
        self._stderr = None
        self._test_start_time = 0

    def startTest(self, test: unittest.TestCase) -> None:
        super().startTest(test)
        self._test_start_time = time.time()
        self.output_buffer = io.StringIO()
        stdout_redirector.fp = self.output_buffer
        stderr_redirector.fp = self.output_buffer
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector

    def _get_output(self) -> str:
        """获取并重置输出缓冲"""
        if self._stdout:
            sys.stdout = self._stdout
            sys.stderr = self._stderr
            self._stdout = None
            self._stderr = None
        return self.output_buffer.getvalue()

    def _get_duration(self) -> float:
        """获取测试用时"""
        return round(time.time() - self._test_start_time, 3)

    def stopTest(self, test: unittest.TestCase) -> None:
        self._get_output()

    def addSuccess(self, test: unittest.TestCase) -> None:
        if test not in self.subtest_list:
            self.success_count += 1
            super().addSuccess(test)
            self.results.append((TestStatus.PASS, test, self._get_output(), '', self._get_duration()))
            self._log_result('S', test)

    def addError(self, test: unittest.TestCase, err) -> None:
        self.error_count += 1
        super().addError(test, err)
        _, exc_str = self.errors[-1]
        self.results.append((TestStatus.ERROR, test, self._get_output(), exc_str, self._get_duration()))
        self._log_result('E', test)

    def addFailure(self, test: unittest.TestCase, err) -> None:
        self.failure_count += 1
        super().addFailure(test, err)
        _, exc_str = self.failures[-1]
        self.results.append((TestStatus.FAIL, test, self._get_output(), exc_str, self._get_duration()))
        self._log_result('F', test)

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:
        self.skip_count += 1
        super().addSkip(test, reason)
        self.results.append((TestStatus.SKIP, test, self._get_output(), f'Skipped: {reason}', self._get_duration()))
        self._log_result('s', test)

    def addSubTest(self, test: unittest.TestCase, subtest, err) -> None:
        if err is not None:
            if issubclass(err[0], test.failureException):
                self.failure_count += 1
                self.failures.append((subtest, self._exc_info_to_string(err, subtest)))
                output = self._get_output() + f'\nSubTest Failed: {subtest}'
                self.results.append((TestStatus.FAIL, test, output, self._exc_info_to_string(err, subtest), self._get_duration()))
                self._log_result('F', subtest)
            else:
                self.error_count += 1
                self.errors.append((subtest, self._exc_info_to_string(err, subtest)))
                output = self._get_output() + f'\nSubTest Error: {subtest}'
                self.results.append((TestStatus.ERROR, test, output, self._exc_info_to_string(err, subtest), self._get_duration()))
                self._log_result('E', subtest)
        else:
            self.subtest_list.extend([subtest, test])
            self.success_count += 1
            output = self._get_output() + f'\nSubTest Pass: {subtest}'
            self.results.append((TestStatus.PASS, test, output, '', self._get_duration()))
            self._log_result('S', subtest)

    def _log_result(self, status: str, test) -> None:
        """日志输出"""
        if self.verbosity > 1:
            sys.stderr.write(f'{status}  {test}\n')
        else:
            sys.stderr.write(status)

    @property
    def total_count(self) -> int:
        return self.success_count + self.failure_count + self.error_count + self.skip_count

    def to_dict(self) -> Dict[str, Any]:
        """导出为字典格式"""
        return {
            'total': self.total_count,
            'pass': self.success_count,
            'fail': self.failure_count,
            'error': self.error_count,
            'skip': self.skip_count,
            'pass_rate': round(self.success_count / self.total_count * 100, 2) if self.total_count else 0,
        }


# ============================================================================
# HTML Test Runner
# ============================================================================

class HTMLTestRunner:
    """现代化 HTML 测试报告生成器"""
    
    def __init__(
        self,
        stream=sys.stdout,
        verbosity: int = 1,
        title: Optional[str] = None,
        description: str = '',
        tester: str = 'QA Team',
        language: str = 'zh-CN',
        chart_height: int = 400,
    ):
        self.stream = stream
        self.verbosity = verbosity
        self.title = title or TemplateEngine.get_text('title', language)
        self.description = description
        self.tester = tester
        self.language = language
        self.chart_height = chart_height
        self.start_time: Optional[datetime.datetime] = None
        self.stop_time: Optional[datetime.datetime] = None
        self.template = TemplateEngine()

    def run(self, test: unittest.TestSuite) -> HTMLTestResult:
        """运行测试并生成报告"""
        result = HTMLTestResult(self.verbosity)
        self.start_time = datetime.datetime.now()
        
        test(result)
        
        self.stop_time = datetime.datetime.now()
        self._generate_report(result)
        
        duration = self.stop_time - self.start_time
        print(f'\n运行时长: {duration}', file=sys.stderr)
        
        return result

    def _get_text(self, key: str) -> str:
        """获取当前语言的文本"""
        return TemplateEngine.get_text(key, self.language)

    def _generate_report(self, result: HTMLTestResult) -> None:
        """生成 HTML 报告"""
        output = TemplateEngine.HTML_TEMPLATE % {
            'lang': self.language,
            'version': __version__,
            'author': __author__,
            'title': saxutils.escape(self.title),
            'stylesheet': TemplateEngine.STYLESHEET,
            'scripts': TemplateEngine.SCRIPTS,
            'heading': self._generate_heading(result),
            'report': self._generate_report_body(result),
            'ending': self._generate_ending(),
            'chart_script': self._generate_chart_script(result),
        }
        self.stream.write(output.encode('utf-8'))

    def _generate_heading(self, result: HTMLTestResult) -> str:
        """生成头部区域"""
        duration = str(self.stop_time - self.start_time) if self.stop_time and self.start_time else '0:00:00'
        start_time_str = self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else ''
        
        # 状态汇总
        status_parts = []
        if result.success_count:
            status_parts.append(f'{self._get_text("pass")} {result.success_count}')
        if result.failure_count:
            status_parts.append(f'{self._get_text("fail")} {result.failure_count}')
        if result.error_count:
            status_parts.append(f'{self._get_text("error")} {result.error_count}')
        if result.skip_count:
            status_parts.append(f'{self._get_text("skip")} {result.skip_count}')
        status_str = ' | '.join(status_parts) or 'N/A'
        
        # 统计卡片
        stats = [
            {'label': self._get_text('start_time'), 'value': start_time_str, 'class': 'info', 'icon': 'bi-clock-history'},
            {'label': self._get_text('duration'), 'value': duration, 'class': 'primary', 'icon': 'bi-stopwatch'},
            {'label': self._get_text('status'), 'value': status_str, 'class': 'success', 'icon': 'bi-flag-fill'},
            {'label': self._get_text('tester'), 'value': self.tester, 'class': 'secondary', 'icon': 'bi-person-fill'},
        ]
        
        stats_html = ''.join(
            TemplateEngine.STAT_CARD_TEMPLATE % {
                'label': s['label'],
                'value': saxutils.escape(s['value']),
                'card_class': s['class'],
                'icon': s['icon'],
            }
            for s in stats
        )
        
        return TemplateEngine.HEADING_TEMPLATE % {
            'title': saxutils.escape(self.title),
            'description': saxutils.escape(self.description),
            'stats_cards': stats_html,
            'chart_height': self.chart_height,
            'toggle_theme': self._get_text('toggle_theme'),
        }

    def _generate_report_body(self, result: HTMLTestResult) -> str:
        """生成报告主体"""
        # 按类分组
        sorted_results = self._sort_results(result.results)
        rows = []
        
        for cid, (cls, cls_results) in enumerate(sorted_results):
            # 统计类级别数据
            np = nf = ne = ns = 0
            for status, _, _, _, _ in cls_results:
                if status == TestStatus.PASS:
                    np += 1
                elif status == TestStatus.FAIL:
                    nf += 1
                elif status == TestStatus.ERROR:
                    ne += 1
                else:
                    ns += 1
            
            # 类名和描述
            name = f'{cls.__module__}.{cls.__name__}' if cls.__module__ != '__main__' else cls.__name__
            doc = (cls.__doc__ or '').split('\n')[0]
            desc = f'{name}: {doc}' if doc else name
            
            # 确定样式
            if ne > 0:
                style = 'errorClass'
            elif nf > 0:
                style = 'failClass'
            elif ns > 0:
                style = 'skipClass'
            else:
                style = 'passClass'
            
            rows.append(TemplateEngine.CLASS_ROW_TEMPLATE % {
                'style': style,
                'desc': saxutils.escape(desc),
                'count': np + nf + ne + ns,
                'pass': np,
                'fail': nf,
                'error': ne,
                'skip': ns,
                'cid': f'c{cid + 1}',
                'detail': self._get_text('detail'),
            })
            
            # 生成测试用例行
            for tid, (status, test, output, trace, duration) in enumerate(cls_results):
                rows.append(self._generate_test_row(cid, tid, status, test, output, trace, duration))
        
        # 总计行
        total_row = TemplateEngine.TOTAL_ROW_TEMPLATE % {
            'total_summary': self._get_text('total_summary'),
            'count': result.total_count,
            'pass': result.success_count,
            'fail': result.failure_count,
            'error': result.error_count,
            'skip': result.skip_count,
        }
        
        return TemplateEngine.REPORT_TEMPLATE % {
            'test_details': self._get_text('test_details'),
            'summary': self._get_text('summary'),
            'failed': self._get_text('failed'),
            'all': self._get_text('all'),
            'test_suite': self._get_text('test_suite'),
            'total': self._get_text('total'),
            'pass': self._get_text('pass'),
            'fail': self._get_text('fail'),
            'error': self._get_text('error'),
            'skip': self._get_text('skip'),
            'view': self._get_text('view'),
            'test_list': ''.join(rows),
            'total_row': total_row,
        }

    def _generate_test_row(
        self,
        cid: int,
        tid: int,
        status: TestStatus,
        test: unittest.TestCase,
        output: str,
        trace: str,
        duration: float
    ) -> str:
        """生成单个测试用例行"""
        # ID 前缀
        prefix_map = {TestStatus.PASS: 'p', TestStatus.FAIL: 'f', TestStatus.ERROR: 'f', TestStatus.SKIP: 's'}
        prefix = prefix_map.get(status, 'p')
        row_id = f'{prefix}t{cid + 1}.{tid + 1}'
        
        # 测试名和描述
        name = test.id().split('.')[-1]
        doc = test.shortDescription() or ''
        desc = f'{name}: {doc}' if doc else name
        
        # 样式
        style_map = {
            TestStatus.PASS: 'none',
            TestStatus.FAIL: 'failCase',
            TestStatus.ERROR: 'errorCase',
            TestStatus.SKIP: 'skipCase',
        }
        
        # 输出内容
        content = output + trace if (output or trace) else self._get_text('no_output')
        
        return TemplateEngine.TEST_ROW_TEMPLATE % {
            'tid': row_id,
            'style': style_map.get(status, 'none'),
            'desc': saxutils.escape(desc),
            'status': STATUS_LABELS.get(status, ''),
            'execution_details': self._get_text('execution_details'),
            'copy': self._get_text('copy'),
            'script': saxutils.escape(f'{row_id}: {content}'),
        }

    def _generate_ending(self) -> str:
        """生成页脚"""
        return TemplateEngine.ENDING_TEMPLATE % {
            'powered_by': self._get_text('powered_by'),
            'version': __version__,
            'tester': self.tester,
            'generated_on': self._get_text('generated_on'),
            'time': self.stop_time.strftime('%Y-%m-%d %H:%M:%S') if self.stop_time else '',
        }

    def _generate_chart_script(self, result: HTMLTestResult) -> str:
        """生成图表脚本"""
        return TemplateEngine.CHART_SCRIPT_TEMPLATE % {
            'pass': result.success_count,
            'fail': result.failure_count,
            'error': result.error_count,
            'skip': result.skip_count,
            'test_execution': self._get_text('test_execution'),
            'pass_rate': self._get_text('pass_rate'),
            'pass_label': self._get_text('pass'),
            'fail_label': self._get_text('fail'),
            'error_label': self._get_text('error'),
            'skip_label': self._get_text('skip'),
        }

    def _sort_results(self, results: List) -> List:
        """按测试类分组排序"""
        class_map = {}
        class_order = []
        
        for item in results:
            status, test, output, trace, duration = item
            cls = test.__class__
            if cls not in class_map:
                class_map[cls] = []
                class_order.append(cls)
            class_map[cls].append(item)
        
        return [(cls, class_map[cls]) for cls in class_order]


# ============================================================================
# Command Line Support
# ============================================================================

class TestProgram(unittest.TestProgram):
    """命令行测试程序"""
    
    def runTests(self):
        if self.testRunner is None:
            self.testRunner = HTMLTestRunner(verbosity=self.verbosity)
        unittest.TestProgram.runTests(self)


main = TestProgram


if __name__ == '__main__':
    main(module=None)

