"""
測試結果通知模組

支援 Slack Webhook 與 Email (SMTP) 兩種通知方式。
測試完成後自動發送摘要，特別適合 CI/CD 或排程執行。

Usage:
    # Slack
    from utils.notifier import SlackNotifier
    notifier = SlackNotifier(webhook_url='https://hooks.slack.com/...')
    notifier.send_report(passed=10, failed=2, total=12, title='Nightly Run')

    # Email
    from utils.notifier import EmailNotifier
    notifier = EmailNotifier(
        smtp_host='smtp.gmail.com', smtp_port=587,
        username='test@gmail.com', password='app-password',
        sender='test@gmail.com', recipients=['team@company.com'],
    )
    notifier.send_report(passed=10, failed=2, total=12)

    # pytest plugin（自動通知）
    conftest.py 加上:
        from utils.notifier import SlackNotifier
        def pytest_terminal_summary(terminalreporter):
            stats = terminalreporter.stats
            notifier = SlackNotifier(webhook_url=os.environ['SLACK_WEBHOOK'])
            notifier.send_report(
                passed=len(stats.get('passed', [])),
                failed=len(stats.get('failed', [])),
                total=terminalreporter._numcollected,
            )
"""

import json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


class SlackNotifier:
    """Slack Webhook 通知器。"""

    def __init__(self, webhook_url: str = None):
        """
        Args:
            webhook_url: Slack Incoming Webhook URL。
                         若為 None，則嘗試讀取環境變數 SLACK_WEBHOOK。
        """
        self.webhook_url = webhook_url or os.environ.get('SLACK_WEBHOOK', '')

    def send_report(
        self,
        passed: int = 0,
        failed: int = 0,
        error: int = 0,
        skipped: int = 0,
        total: int = 0,
        title: str = 'Selenium 測試報告',
        extra: str = '',
    ):
        """
        發送測試摘要到 Slack。

        Args:
            passed: 通過數
            failed: 失敗數
            error: 錯誤數
            skipped: 跳過數
            total: 總計
            title: 訊息標題
            extra: 額外文字
        """
        if not self.webhook_url:
            raise ValueError('未設定 SLACK_WEBHOOK URL')

        if not _HAS_REQUESTS:
            raise ImportError('需要安裝 requests：pip install requests')

        total = total or (passed + failed + error + skipped)
        rate = (passed / total * 100) if total > 0 else 0
        icon = ':white_check_mark:' if failed == 0 else ':x:'
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        blocks = [
            {
                'type': 'header',
                'text': {'type': 'plain_text', 'text': f'{title}'},
            },
            {
                'type': 'section',
                'fields': [
                    {'type': 'mrkdwn', 'text': f'*狀態:* {icon} {"全部通過" if failed == 0 else f"{failed} 個失敗"}'},
                    {'type': 'mrkdwn', 'text': f'*時間:* {now}'},
                    {'type': 'mrkdwn', 'text': f'*通過率:* {rate:.1f}%'},
                    {'type': 'mrkdwn', 'text': f'*總計:* {total}'},
                    {'type': 'mrkdwn', 'text': f':white_check_mark: 通過: {passed}'},
                    {'type': 'mrkdwn', 'text': f':x: 失敗: {failed}'},
                    {'type': 'mrkdwn', 'text': f':warning: 錯誤: {error}'},
                    {'type': 'mrkdwn', 'text': f':fast_forward: 跳過: {skipped}'},
                ],
            },
        ]

        if extra:
            blocks.append({
                'type': 'section',
                'text': {'type': 'mrkdwn', 'text': extra},
            })

        payload = {'blocks': blocks}
        resp = requests.post(
            self.webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10,
        )
        resp.raise_for_status()
        return True

    def send_message(self, text: str):
        """發送純文字訊息到 Slack。"""
        if not self.webhook_url:
            raise ValueError('未設定 SLACK_WEBHOOK URL')
        if not _HAS_REQUESTS:
            raise ImportError('需要安裝 requests：pip install requests')

        resp = requests.post(
            self.webhook_url,
            json={'text': text},
            headers={'Content-Type': 'application/json'},
            timeout=10,
        )
        resp.raise_for_status()
        return True


class EmailNotifier:
    """Email (SMTP) 通知器。"""

    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = 587,
        username: str = None,
        password: str = None,
        sender: str = None,
        recipients: list = None,
        use_tls: bool = True,
    ):
        """
        Args:
            smtp_host: SMTP 主機，預設讀取環境變數 SMTP_HOST。
            smtp_port: SMTP 埠號。
            username: SMTP 帳號，預設讀取 SMTP_USER。
            password: SMTP 密碼，預設讀取 SMTP_PASSWORD。
            sender: 寄件者，預設同 username。
            recipients: 收件者列表，預設讀取 SMTP_RECIPIENTS（逗號分隔）。
            use_tls: 是否使用 TLS。
        """
        self.smtp_host = smtp_host or os.environ.get('SMTP_HOST', '')
        self.smtp_port = smtp_port
        self.username = username or os.environ.get('SMTP_USER', '')
        self.password = password or os.environ.get('SMTP_PASSWORD', '')
        self.sender = sender or self.username
        self.use_tls = use_tls

        if recipients:
            self.recipients = recipients
        else:
            env_recipients = os.environ.get('SMTP_RECIPIENTS', '')
            self.recipients = [r.strip() for r in env_recipients.split(',') if r.strip()]

    def send_report(
        self,
        passed: int = 0,
        failed: int = 0,
        error: int = 0,
        skipped: int = 0,
        total: int = 0,
        title: str = 'Selenium 測試報告',
        extra: str = '',
    ):
        """
        發送測試摘要 Email。

        Args:
            passed/failed/error/skipped/total: 測試統計
            title: 郵件標題
            extra: 額外內容
        """
        if not self.smtp_host:
            raise ValueError('未設定 SMTP_HOST')
        if not self.recipients:
            raise ValueError('未設定收件者')

        total = total or (passed + failed + error + skipped)
        rate = (passed / total * 100) if total > 0 else 0
        status = '全部通過' if failed == 0 else f'{failed} 個失敗'
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        subject = f'[{status}] {title} - {now}'

        body = f"""
<html>
<body>
<h2>{title}</h2>
<p><strong>狀態:</strong> {status}</p>
<p><strong>時間:</strong> {now}</p>

<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
<tr style="background:#f0f0f0;">
    <th>項目</th><th>數量</th>
</tr>
<tr><td>總計</td><td>{total}</td></tr>
<tr style="color:green;"><td>通過</td><td>{passed}</td></tr>
<tr style="color:red;"><td>失敗</td><td>{failed}</td></tr>
<tr style="color:orange;"><td>錯誤</td><td>{error}</td></tr>
<tr style="color:gray;"><td>跳過</td><td>{skipped}</td></tr>
<tr><td><strong>通過率</strong></td><td><strong>{rate:.1f}%</strong></td></tr>
</table>

{f'<p>{extra}</p>' if extra else ''}
</body>
</html>
"""

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.sender
        msg['To'] = ', '.join(self.recipients)
        msg.attach(MIMEText(body, 'html', 'utf-8'))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.use_tls:
                server.starttls()
            if self.username and self.password:
                server.login(self.username, self.password)
            server.sendmail(self.sender, self.recipients, msg.as_string())

        return True
