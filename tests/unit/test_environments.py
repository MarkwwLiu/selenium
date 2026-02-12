"""
config/environments.py 單元測試
"""

import os
import pytest
from config.environments import (
    get_env_name, get_env_config, list_environments,
    register_environment, ENVIRONMENTS, DEFAULT_ENV,
)


class TestGetEnvName:
    @pytest.mark.positive
    def test_default(self):
        """未設定 TEST_ENV 時回傳預設值。"""
        orig = os.environ.pop('TEST_ENV', None)
        try:
            assert get_env_name() == DEFAULT_ENV
        finally:
            if orig is not None:
                os.environ['TEST_ENV'] = orig

    @pytest.mark.positive
    def test_from_env_var(self):
        """設定 TEST_ENV 時回傳環境變數值。"""
        os.environ['TEST_ENV'] = 'staging'
        try:
            assert get_env_name() == 'staging'
        finally:
            del os.environ['TEST_ENV']


class TestGetEnvConfig:
    @pytest.mark.positive
    def test_dev(self):
        config = get_env_config('dev')
        assert config['base_url'] == 'http://localhost:3000'
        assert config['env_name'] == 'dev'

    @pytest.mark.positive
    def test_staging(self):
        config = get_env_config('staging')
        assert 'staging' in config['base_url']
        assert config['env_name'] == 'staging'

    @pytest.mark.positive
    def test_prod(self):
        config = get_env_config('prod')
        assert config['env_name'] == 'prod'
        assert config['headless'] is True

    @pytest.mark.negative
    def test_invalid_env(self):
        with pytest.raises(ValueError, match='未知的環境'):
            get_env_config('nonexistent')

    @pytest.mark.positive
    def test_auto_detect(self):
        """env_name=None 時自動偵測。"""
        orig = os.environ.pop('TEST_ENV', None)
        try:
            config = get_env_config()
            assert config['env_name'] == DEFAULT_ENV
        finally:
            if orig is not None:
                os.environ['TEST_ENV'] = orig

    @pytest.mark.positive
    def test_returns_copy(self):
        """回傳的 dict 不應影響原始 ENVIRONMENTS。"""
        config = get_env_config('dev')
        config['base_url'] = 'modified'
        assert ENVIRONMENTS['dev']['base_url'] != 'modified'


class TestListEnvironments:
    @pytest.mark.positive
    def test_returns_all(self):
        envs = list_environments()
        assert 'dev' in envs
        assert 'staging' in envs
        assert 'prod' in envs


class TestRegisterEnvironment:
    @pytest.mark.positive
    def test_register_new(self):
        register_environment('qa', {
            'base_url': 'https://qa.example.com',
            'timeout': 15,
        })
        try:
            assert 'qa' in ENVIRONMENTS
            config = get_env_config('qa')
            assert config['base_url'] == 'https://qa.example.com'
        finally:
            ENVIRONMENTS.pop('qa', None)
