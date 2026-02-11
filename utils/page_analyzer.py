"""
頁面元素分析器

自動掃描頁面上所有可互動的元素，產生結構化報告。
用於：拿到 URL 後，先跑分析 → 再自動產生 Page Object 和測試案例。
"""

import json
import os
from datetime import datetime

# 用 JS 掃描頁面所有互動元素的腳本
SCAN_ELEMENTS_JS = """
return (function() {
    var results = {
        url: window.location.href,
        title: document.title,
        forms: [],
        inputs: [],
        buttons: [],
        links: [],
        selects: [],
        textareas: [],
        checkboxes: [],
        radios: [],
        images: [],
        tables: [],
        iframes: []
    };

    // 取得元素最佳定位器
    function getBestLocator(el) {
        if (el.id) return {by: 'id', value: el.id};
        if (el.name) return {by: 'name', value: el.name};
        if (el.getAttribute('data-testid'))
            return {by: 'css', value: '[data-testid="' + el.getAttribute('data-testid') + '"]'};
        if (el.getAttribute('data-cy'))
            return {by: 'css', value: '[data-cy="' + el.getAttribute('data-cy') + '"]'};
        if (el.className && typeof el.className === 'string' && el.className.trim()) {
            var cls = '.' + el.className.trim().split(/\\s+/).join('.');
            if (document.querySelectorAll(cls).length === 1)
                return {by: 'css', value: cls};
        }
        // fallback: xpath
        var path = [];
        var node = el;
        while (node && node.nodeType === 1) {
            var tag = node.tagName.toLowerCase();
            var idx = 1;
            var sibling = node.previousElementSibling;
            while (sibling) {
                if (sibling.tagName.toLowerCase() === tag) idx++;
                sibling = sibling.previousElementSibling;
            }
            path.unshift(tag + '[' + idx + ']');
            node = node.parentElement;
        }
        return {by: 'xpath', value: '/' + path.join('/')};
    }

    // 取得元素基本屬性
    function getAttrs(el) {
        var rect = el.getBoundingClientRect();
        return {
            tag: el.tagName.toLowerCase(),
            locator: getBestLocator(el),
            text: (el.innerText || '').substring(0, 100).trim(),
            type: el.type || '',
            name: el.name || '',
            id: el.id || '',
            placeholder: el.placeholder || '',
            value: el.value || '',
            required: el.required || false,
            disabled: el.disabled || false,
            visible: rect.width > 0 && rect.height > 0,
            maxlength: el.maxLength > 0 ? el.maxLength : null,
            minlength: el.minLength > 0 ? el.minLength : null,
            pattern: el.pattern || '',
            min: el.min || '',
            max: el.max || ''
        };
    }

    // 掃描 forms
    document.querySelectorAll('form').forEach(function(el) {
        results.forms.push({
            locator: getBestLocator(el),
            action: el.action || '',
            method: el.method || 'get',
            id: el.id || '',
            name: el.name || '',
            field_count: el.elements.length
        });
    });

    // 掃描 input
    document.querySelectorAll('input').forEach(function(el) {
        var info = getAttrs(el);
        if (['checkbox'].includes(el.type)) {
            info.checked = el.checked;
            results.checkboxes.push(info);
        } else if (['radio'].includes(el.type)) {
            info.checked = el.checked;
            results.radios.push(info);
        } else if (!['hidden', 'submit', 'button', 'image', 'reset'].includes(el.type)) {
            results.inputs.push(info);
        }
    });

    // 掃描 button / input[type=submit]
    document.querySelectorAll('button, input[type="submit"], input[type="button"]').forEach(function(el) {
        results.buttons.push(getAttrs(el));
    });

    // 掃描 select
    document.querySelectorAll('select').forEach(function(el) {
        var info = getAttrs(el);
        info.options = [];
        Array.from(el.options).forEach(function(opt) {
            info.options.push({text: opt.text, value: opt.value, selected: opt.selected});
        });
        results.selects.push(info);
    });

    // 掃描 textarea
    document.querySelectorAll('textarea').forEach(function(el) {
        results.textareas.push(getAttrs(el));
    });

    // 掃描 a[href]
    document.querySelectorAll('a[href]').forEach(function(el) {
        var rect = el.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
            results.links.push({
                locator: getBestLocator(el),
                text: (el.innerText || '').substring(0, 100).trim(),
                href: el.href || ''
            });
        }
    });

    // 掃描 table
    document.querySelectorAll('table').forEach(function(el) {
        results.tables.push({
            locator: getBestLocator(el),
            rows: el.rows.length,
            headers: Array.from(el.querySelectorAll('th')).map(function(th) {
                return th.innerText.trim();
            })
        });
    });

    // 掃描 iframe
    document.querySelectorAll('iframe').forEach(function(el) {
        results.iframes.push({
            locator: getBestLocator(el),
            src: el.src || '',
            id: el.id || '',
            name: el.name || ''
        });
    });

    return results;
})();
"""


class PageAnalyzer:
    """
    頁面元素分析器。

    Usage:
        analyzer = PageAnalyzer(driver)
        report = analyzer.analyze('https://example.com/login')
        analyzer.save_report(report, 'scenarios/login_test/results/')
    """

    def __init__(self, driver):
        self.driver = driver

    def analyze(self, url=None):
        """
        掃描當前頁面（或先開啟 url）的所有互動元素。

        Returns:
            dict: 結構化的頁面元素報告
        """
        if url:
            self.driver.get(url)

        report = self.driver.execute_script(SCAN_ELEMENTS_JS)
        report['analyzed_at'] = datetime.now().isoformat()
        report['page_source_length'] = len(self.driver.page_source)

        # 統計摘要
        report['summary'] = {
            'forms': len(report.get('forms', [])),
            'inputs': len(report.get('inputs', [])),
            'buttons': len(report.get('buttons', [])),
            'links': len(report.get('links', [])),
            'selects': len(report.get('selects', [])),
            'textareas': len(report.get('textareas', [])),
            'checkboxes': len(report.get('checkboxes', [])),
            'radios': len(report.get('radios', [])),
            'tables': len(report.get('tables', [])),
            'iframes': len(report.get('iframes', [])),
        }

        return report

    def save_report(self, report, output_dir):
        """將分析報告存為 JSON。"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(output_dir, f'page_analysis_{timestamp}.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return filepath

    def print_summary(self, report):
        """印出分析摘要。"""
        print(f'\n{"=" * 50}')
        print(f'頁面分析報告')
        print(f'{"=" * 50}')
        print(f'URL:   {report.get("url", "")}')
        print(f'Title: {report.get("title", "")}')
        print(f'時間:  {report.get("analyzed_at", "")}')
        print(f'{"─" * 50}')

        summary = report.get('summary', {})
        for element_type, count in summary.items():
            if count > 0:
                print(f'  {element_type:15s}: {count}')

        print(f'{"─" * 50}')

        # 列出 input 欄位細節
        for inp in report.get('inputs', []):
            loc = inp['locator']
            required = ' [必填]' if inp.get('required') else ''
            maxlen = f' [最大{inp["maxlength"]}字]' if inp.get('maxlength') else ''
            pattern = f' [pattern: {inp["pattern"]}]' if inp.get('pattern') else ''
            print(f'  INPUT  {loc["by"]}={loc["value"]}'
                  f'  type={inp["type"]}'
                  f'  placeholder="{inp["placeholder"]}"'
                  f'{required}{maxlen}{pattern}')

        for sel in report.get('selects', []):
            loc = sel['locator']
            opts = [o['text'] for o in sel.get('options', [])[:5]]
            print(f'  SELECT {loc["by"]}={loc["value"]}  options={opts}')

        for btn in report.get('buttons', []):
            loc = btn['locator']
            print(f'  BUTTON {loc["by"]}={loc["value"]}  text="{btn["text"]}"')

        print(f'{"=" * 50}\n')

    def get_input_constraints(self, report):
        """
        從分析結果提取每個 input 的驗證限制，
        用於自動推測正向/反向/邊界測試資料。

        Returns:
            list[dict]: 每個 input 的限制條件
        """
        constraints = []
        for inp in report.get('inputs', []):
            c = {
                'locator': inp['locator'],
                'type': inp.get('type', 'text'),
                'name': inp.get('name', ''),
                'placeholder': inp.get('placeholder', ''),
                'required': inp.get('required', False),
                'maxlength': inp.get('maxlength'),
                'minlength': inp.get('minlength'),
                'pattern': inp.get('pattern', ''),
                'min': inp.get('min', ''),
                'max': inp.get('max', ''),
            }
            constraints.append(c)

        for ta in report.get('textareas', []):
            c = {
                'locator': ta['locator'],
                'type': 'textarea',
                'name': ta.get('name', ''),
                'placeholder': ta.get('placeholder', ''),
                'required': ta.get('required', False),
                'maxlength': ta.get('maxlength'),
                'minlength': ta.get('minlength'),
                'pattern': '',
                'min': '',
                'max': '',
            }
            constraints.append(c)

        return constraints
