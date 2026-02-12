"""
測試資料工廠

基於 Faker 自動產生各類測試資料，支援：
- 基本欄位（姓名、Email、電話、地址）
- 密碼（各種強度）
- 表單資料（一次產生完整表單所需的資料）
- 批量產生（for parametrize）
- 自訂 locale（支援繁體中文）

Usage:
    from utils.data_factory import DataFactory

    factory = DataFactory(locale='zh_TW')

    # 單筆
    user = factory.user()
    print(user['name'], user['email'])

    # 批量 (for parametrize)
    users = factory.users(count=5)

    # 密碼
    pw = factory.password(length=12, special=True)

    # 表單資料
    form = factory.form_data(fields=['name', 'email', 'phone', 'address'])

    # pytest parametrize 整合
    @pytest.mark.parametrize('user', DataFactory().users(3), ids=lambda u: u['email'])
    def test_register(user):
        ...
"""

import string
import random
from datetime import datetime, timedelta

try:
    from faker import Faker
    _HAS_FAKER = True
except ImportError:
    _HAS_FAKER = False


class DataFactory:
    """測試資料工廠。"""

    def __init__(self, locale: str = 'zh_TW', seed: int = None):
        """
        Args:
            locale: Faker locale，預設繁體中文。
                    常用: 'zh_TW', 'en_US', 'ja_JP', 'zh_CN'
            seed: 隨機種子（設定後每次產生相同資料，方便重現）。
        """
        if not _HAS_FAKER:
            raise ImportError('需要安裝 faker：pip install faker')

        self.fake = Faker(locale)
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

    # === 使用者資料 ===

    def user(self) -> dict:
        """
        產生單一使用者資料。

        Returns:
            {'name': '...', 'email': '...', 'phone': '...', 'address': '...', 'birthday': '...'}
        """
        return {
            'name': self.fake.name(),
            'email': self.fake.email(),
            'phone': self.fake.phone_number(),
            'address': self.fake.address().replace('\n', ' '),
            'birthday': self.fake.date_of_birth(minimum_age=18, maximum_age=65).isoformat(),
            'username': self.fake.user_name(),
        }

    def users(self, count: int = 5) -> list[dict]:
        """批量產生使用者資料。"""
        return [self.user() for _ in range(count)]

    # === 密碼 ===

    def password(
        self,
        length: int = 12,
        upper: bool = True,
        digits: bool = True,
        special: bool = True,
    ) -> str:
        """
        產生密碼。

        Args:
            length: 密碼長度
            upper: 包含大寫
            digits: 包含數字
            special: 包含特殊字元
        """
        chars = string.ascii_lowercase
        required = [random.choice(string.ascii_lowercase)]

        if upper:
            chars += string.ascii_uppercase
            required.append(random.choice(string.ascii_uppercase))
        if digits:
            chars += string.digits
            required.append(random.choice(string.digits))
        if special:
            specials = '!@#$%^&*'
            chars += specials
            required.append(random.choice(specials))

        remaining = length - len(required)
        pw = required + [random.choice(chars) for _ in range(remaining)]
        random.shuffle(pw)
        return ''.join(pw)

    def weak_password(self) -> str:
        """產生弱密碼（用於 negative test）。"""
        options = ['123456', 'password', 'abc', '1234', 'qwerty', '111111', 'aaa']
        return random.choice(options)

    # === 表單資料 ===

    def form_data(self, fields: list[str] = None) -> dict:
        """
        依指定欄位產生表單資料。

        Args:
            fields: 欄位名稱列表。支援:
                name, email, phone, address, company,
                city, zip_code, country, url, text,
                date, number, credit_card, password

        Returns:
            {field_name: value, ...}
        """
        fields = fields or ['name', 'email', 'phone', 'address']
        generators = {
            'name': lambda: self.fake.name(),
            'first_name': lambda: self.fake.first_name(),
            'last_name': lambda: self.fake.last_name(),
            'email': lambda: self.fake.email(),
            'phone': lambda: self.fake.phone_number(),
            'address': lambda: self.fake.address().replace('\n', ' '),
            'company': lambda: self.fake.company(),
            'city': lambda: self.fake.city(),
            'zip_code': lambda: self.fake.zipcode(),
            'country': lambda: self.fake.country(),
            'url': lambda: self.fake.url(),
            'text': lambda: self.fake.text(max_nb_chars=100),
            'sentence': lambda: self.fake.sentence(),
            'paragraph': lambda: self.fake.paragraph(),
            'date': lambda: self.fake.date(),
            'number': lambda: str(random.randint(1, 9999)),
            'credit_card': lambda: self.fake.credit_card_number(),
            'password': lambda: self.password(),
            'username': lambda: self.fake.user_name(),
        }

        data = {}
        for field in fields:
            gen = generators.get(field)
            if gen:
                data[field] = gen()
            else:
                data[field] = self.fake.text(max_nb_chars=50)

        return data

    def form_data_batch(self, fields: list[str] = None, count: int = 5) -> list[dict]:
        """批量產生表單資料。"""
        return [self.form_data(fields) for _ in range(count)]

    # === 邊界值產生 ===

    def boundary_strings(self, max_length: int = 255) -> list[str]:
        """
        產生邊界值測試字串。

        Returns:
            包含空字串、單字元、最大長度、超長、特殊字元等。
        """
        return [
            '',                                      # 空字串
            ' ',                                     # 空白
            'a',                                     # 單字元
            'a' * max_length,                        # 最大長度
            'a' * (max_length + 1),                  # 超過最大長度
            '<script>alert(1)</script>',              # XSS
            "'; DROP TABLE users; --",               # SQL injection
            '中文測試字串',                            # Unicode
            'emoji 🎉🚀✅',                          # Emoji
            '   leading and trailing spaces   ',     # 前後空白
            'line1\nline2\nline3',                   # 換行
            'tab\there',                             # Tab
            'special!@#$%^&*()',                      # 特殊字元
            'a' * 1,                                 # 最小正常
            None,                                    # None
        ]

    def boundary_numbers(self, min_val: int = 0, max_val: int = 100) -> list:
        """
        產生邊界值數字。

        Returns:
            包含最小值、最大值、邊界值、負數等。
        """
        return [
            min_val,           # 最小值
            min_val - 1,       # 低於最小
            max_val,           # 最大值
            max_val + 1,       # 超過最大
            0,                 # 零
            -1,                # 負數
            min_val + 1,       # 最小+1
            max_val - 1,       # 最大-1
            (min_val + max_val) // 2,  # 中間值
        ]

    def boundary_emails(self) -> list[str]:
        """
        產生邊界值 Email。

        Returns:
            包含合法/非法 email。
        """
        return [
            self.fake.email(),           # 正常
            'user@example.com',          # 標準
            'a@b.co',                    # 最短合法
            '',                          # 空
            'no-at-sign',               # 無 @
            '@no-local.com',            # 無 local
            'no-domain@',               # 無 domain
            'double@@at.com',           # 雙 @
            'space in@email.com',       # 含空白
            'user@.com',                # domain 以 . 開頭
        ]

    # === 日期產生 ===

    def date_range(self, days_back: int = 30, days_forward: int = 30) -> dict:
        """
        產生日期範圍測試資料。

        Returns:
            {'today': '...', 'past': '...', 'future': '...', 'formatted': '...'}
        """
        today = datetime.now()
        return {
            'today': today.strftime('%Y-%m-%d'),
            'past': (today - timedelta(days=days_back)).strftime('%Y-%m-%d'),
            'future': (today + timedelta(days=days_forward)).strftime('%Y-%m-%d'),
            'timestamp': int(today.timestamp()),
            'iso': today.isoformat(),
        }
