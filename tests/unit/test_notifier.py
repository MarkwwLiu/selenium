"""
utils/notifier.py 單元測試
"""

import os
from unittest.mock import patch, MagicMock
import pytest

from utils.notifier import SlackNotifier, EmailNotifier


# === SlackNotifier ===

class TestSlackNotifierInit:
    @pytest.mark.positive
    def test_with_url(self):
        n = SlackNotifier(webhook_url='https://hooks.slack.com/test')
        assert n.webhook_url == 'https://hooks.slack.com/test'

    @pytest.mark.positive
    def test_from_env(self):
        os.environ['SLACK_WEBHOOK'] = 'https://hooks.slack.com/env'
        try:
            n = SlackNotifier()
            assert n.webhook_url == 'https://hooks.slack.com/env'
        finally:
            del os.environ['SLACK_WEBHOOK']


class TestSlackSendReport:
    @pytest.mark.negative
    def test_no_url(self):
        n = SlackNotifier(webhook_url='')
        with pytest.raises(ValueError, match='未設定'):
            n.send_report(passed=10)

    @pytest.mark.positive
    @patch('utils.notifier.requests')
    def test_success(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_resp

        n = SlackNotifier(webhook_url='https://hooks.slack.com/test')
        result = n.send_report(passed=8, failed=2, total=10, title='Test')
        assert result is True
        mock_requests.post.assert_called_once()

    @pytest.mark.positive
    @patch('utils.notifier.requests')
    def test_all_pass(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_resp

        n = SlackNotifier(webhook_url='https://hooks.slack.com/test')
        result = n.send_report(passed=10, failed=0, total=10)
        assert result is True

    @pytest.mark.positive
    @patch('utils.notifier.requests')
    def test_with_extra(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_resp

        n = SlackNotifier(webhook_url='https://hooks.slack.com/test')
        n.send_report(passed=5, failed=1, extra='CI Build #123')
        payload = mock_requests.post.call_args[1]['json']
        assert len(payload['blocks']) == 3  # header + section + extra

    @pytest.mark.positive
    @patch('utils.notifier.requests')
    def test_auto_total(self, mock_requests):
        """total=0 時自動計算。"""
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_resp

        n = SlackNotifier(webhook_url='https://hooks.slack.com/test')
        n.send_report(passed=5, failed=2, error=1, skipped=2)
        mock_requests.post.assert_called_once()


class TestSlackSendMessage:
    @pytest.mark.negative
    def test_no_url(self):
        n = SlackNotifier(webhook_url='')
        with pytest.raises(ValueError, match='未設定'):
            n.send_message('hello')

    @pytest.mark.positive
    @patch('utils.notifier.requests')
    def test_success(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_resp

        n = SlackNotifier(webhook_url='https://hooks.slack.com/test')
        result = n.send_message('hello')
        assert result is True


# === EmailNotifier ===

class TestEmailNotifierInit:
    @pytest.mark.positive
    def test_with_params(self):
        n = EmailNotifier(
            smtp_host='smtp.example.com',
            smtp_port=587,
            username='user',
            password='pass',
            sender='from@example.com',
            recipients=['to@example.com'],
        )
        assert n.smtp_host == 'smtp.example.com'
        assert n.recipients == ['to@example.com']

    @pytest.mark.positive
    def test_from_env(self):
        os.environ['SMTP_HOST'] = 'smtp.env.com'
        os.environ['SMTP_USER'] = 'envuser'
        os.environ['SMTP_PASSWORD'] = 'envpass'
        os.environ['SMTP_RECIPIENTS'] = 'a@b.com, c@d.com'
        try:
            n = EmailNotifier()
            assert n.smtp_host == 'smtp.env.com'
            assert n.username == 'envuser'
            assert len(n.recipients) == 2
        finally:
            for key in ('SMTP_HOST', 'SMTP_USER', 'SMTP_PASSWORD', 'SMTP_RECIPIENTS'):
                os.environ.pop(key, None)

    @pytest.mark.positive
    def test_sender_defaults_to_username(self):
        n = EmailNotifier(smtp_host='smtp.com', username='user@test.com')
        assert n.sender == 'user@test.com'


class TestEmailSendReport:
    @pytest.mark.negative
    def test_no_host(self):
        n = EmailNotifier(smtp_host='', recipients=['a@b.com'])
        with pytest.raises(ValueError, match='未設定 SMTP_HOST'):
            n.send_report(passed=1)

    @pytest.mark.negative
    def test_no_recipients(self):
        n = EmailNotifier(smtp_host='smtp.com', recipients=[])
        with pytest.raises(ValueError, match='未設定收件者'):
            n.send_report(passed=1)

    @pytest.mark.positive
    @patch('utils.notifier.smtplib.SMTP')
    def test_success(self, MockSMTP):
        mock_server = MagicMock()
        MockSMTP.return_value.__enter__ = MagicMock(return_value=mock_server)
        MockSMTP.return_value.__exit__ = MagicMock(return_value=False)

        n = EmailNotifier(
            smtp_host='smtp.com', smtp_port=587,
            username='user', password='pass',
            recipients=['to@b.com'],
        )
        result = n.send_report(passed=8, failed=2, total=10)
        assert result is True

    @pytest.mark.positive
    @patch('utils.notifier.smtplib.SMTP')
    def test_no_tls(self, MockSMTP):
        mock_server = MagicMock()
        MockSMTP.return_value.__enter__ = MagicMock(return_value=mock_server)
        MockSMTP.return_value.__exit__ = MagicMock(return_value=False)

        n = EmailNotifier(
            smtp_host='smtp.com', recipients=['to@b.com'],
            use_tls=False, username='', password='',
        )
        n.send_report(passed=5)

    @pytest.mark.positive
    @patch('utils.notifier.smtplib.SMTP')
    def test_auto_total(self, MockSMTP):
        mock_server = MagicMock()
        MockSMTP.return_value.__enter__ = MagicMock(return_value=mock_server)
        MockSMTP.return_value.__exit__ = MagicMock(return_value=False)

        n = EmailNotifier(
            smtp_host='smtp.com', recipients=['to@b.com'],
            username='u', password='p',
        )
        n.send_report(passed=3, failed=1, error=0, skipped=1)
