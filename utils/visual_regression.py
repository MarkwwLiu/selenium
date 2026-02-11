"""
視覺回歸測試工具

透過截圖比對偵測 UI 變化，支援全頁面與元素級別的比對。
使用純 Python 實作像素比對，不需額外圖片處理套件。
"""

import os
import struct
import zlib


class VisualRegression:
    """
    視覺回歸比對工具。

    透過 PNG 像素比對來偵測 UI 變化。
    首次執行會建立 baseline 截圖，後續執行會與 baseline 比對。

    Usage:
        vr = VisualRegression(driver, baseline_dir='baselines/')
        vr.check('homepage', threshold=0.01)  # 允許 1% 差異
    """

    def __init__(self, driver, baseline_dir='baselines', diff_dir='diffs'):
        self.driver = driver
        self.baseline_dir = baseline_dir
        self.diff_dir = diff_dir
        os.makedirs(baseline_dir, exist_ok=True)
        os.makedirs(diff_dir, exist_ok=True)

    def check(self, name, threshold=0.01):
        """
        比對當前畫面與 baseline 截圖。

        Args:
            name: 截圖名稱（不含副檔名）
            threshold: 允許的差異比例（0.0~1.0），預設 1%

        Returns:
            dict: {
                'match': bool,        # 是否在允許範圍內
                'diff_ratio': float,  # 差異比例
                'baseline_path': str, # baseline 檔案路徑
                'actual_path': str,   # 當前截圖路徑
                'diff_path': str,     # 差異圖路徑（僅不匹配時）
                'is_new_baseline': bool,  # 是否為首次建立
            }
        """
        baseline_path = os.path.join(self.baseline_dir, f'{name}.png')
        actual_path = os.path.join(self.diff_dir, f'{name}_actual.png')

        # 擷取當前截圖
        self.driver.save_screenshot(actual_path)

        # 首次執行：建立 baseline
        if not os.path.exists(baseline_path):
            self.driver.save_screenshot(baseline_path)
            return {
                'match': True,
                'diff_ratio': 0.0,
                'baseline_path': baseline_path,
                'actual_path': actual_path,
                'diff_path': None,
                'is_new_baseline': True,
            }

        # 比對
        diff_ratio = self._compare_images(baseline_path, actual_path)
        match = diff_ratio <= threshold

        result = {
            'match': match,
            'diff_ratio': diff_ratio,
            'baseline_path': baseline_path,
            'actual_path': actual_path,
            'diff_path': None,
            'is_new_baseline': False,
        }

        if not match:
            diff_path = os.path.join(self.diff_dir, f'{name}_diff.png')
            self._generate_diff_image(baseline_path, actual_path, diff_path)
            result['diff_path'] = diff_path

        return result

    def check_element(self, name, by, value, threshold=0.01):
        """
        比對指定元素的截圖。

        Args:
            name: 截圖名稱
            by: 定位方式
            value: 定位值
            threshold: 允許差異比例
        """
        element = self.driver.find_element(by, value)
        baseline_path = os.path.join(self.baseline_dir, f'{name}.png')
        actual_path = os.path.join(self.diff_dir, f'{name}_actual.png')

        element.screenshot(actual_path)

        if not os.path.exists(baseline_path):
            element.screenshot(baseline_path)
            return {
                'match': True,
                'diff_ratio': 0.0,
                'baseline_path': baseline_path,
                'actual_path': actual_path,
                'diff_path': None,
                'is_new_baseline': True,
            }

        diff_ratio = self._compare_images(baseline_path, actual_path)
        match = diff_ratio <= threshold

        result = {
            'match': match,
            'diff_ratio': diff_ratio,
            'baseline_path': baseline_path,
            'actual_path': actual_path,
            'diff_path': None,
            'is_new_baseline': False,
        }

        if not match:
            diff_path = os.path.join(self.diff_dir, f'{name}_diff.png')
            self._generate_diff_image(baseline_path, actual_path, diff_path)
            result['diff_path'] = diff_path

        return result

    def update_baseline(self, name):
        """
        強制更新 baseline 截圖為當前畫面。

        Usage:
            vr.update_baseline('homepage')  # UI 改版後重新建立基準
        """
        baseline_path = os.path.join(self.baseline_dir, f'{name}.png')
        self.driver.save_screenshot(baseline_path)
        return baseline_path

    def _compare_images(self, path_a, path_b):
        """
        比對兩張 PNG 圖片，回傳差異比例 (0.0 ~ 1.0)。

        使用原始位元組比對，不需 PIL 等額外套件。
        """
        bytes_a = self._read_file_bytes(path_a)
        bytes_b = self._read_file_bytes(path_b)

        # 快速路徑：完全相同
        if bytes_a == bytes_b:
            return 0.0

        # 解析 PNG 取得像素資料
        pixels_a = self._decode_png_pixels(path_a)
        pixels_b = self._decode_png_pixels(path_b)

        if pixels_a is None or pixels_b is None:
            # 無法解析時回退到位元組比對
            return self._byte_compare(bytes_a, bytes_b)

        width_a, height_a, data_a = pixels_a
        width_b, height_b, data_b = pixels_b

        # 尺寸不同，直接回報不匹配
        if width_a != width_b or height_a != height_b:
            return 1.0

        total_pixels = width_a * height_a
        if total_pixels == 0:
            return 0.0

        diff_count = 0
        # 每 4 bytes 為一個像素 (RGBA)
        for i in range(0, len(data_a), 4):
            if i + 4 > len(data_a) or i + 4 > len(data_b):
                break
            if data_a[i:i+4] != data_b[i:i+4]:
                diff_count += 1

        return diff_count / total_pixels

    def _decode_png_pixels(self, path):
        """解析 PNG 檔案取得原始像素資料。"""
        try:
            with open(path, 'rb') as f:
                data = f.read()

            # 驗證 PNG 簽名
            if data[:8] != b'\x89PNG\r\n\x1a\n':
                return None

            pos = 8
            width = height = 0
            idat_chunks = []

            while pos < len(data):
                length = struct.unpack('>I', data[pos:pos+4])[0]
                chunk_type = data[pos+4:pos+8]

                if chunk_type == b'IHDR':
                    width = struct.unpack('>I', data[pos+8:pos+12])[0]
                    height = struct.unpack('>I', data[pos+12:pos+16])[0]
                elif chunk_type == b'IDAT':
                    idat_chunks.append(data[pos+8:pos+8+length])
                elif chunk_type == b'IEND':
                    break

                pos += 12 + length

            if not idat_chunks:
                return None

            # 解壓縮 IDAT 資料
            raw = zlib.decompress(b''.join(idat_chunks))

            # 移除每列開頭的 filter byte，簡化解析
            stride = width * 4 + 1  # RGBA + filter byte
            pixels = bytearray()
            for y in range(height):
                row_start = y * stride + 1  # 跳過 filter byte
                pixels.extend(raw[row_start:row_start + width * 4])

            return width, height, bytes(pixels)

        except Exception:
            return None

    def _byte_compare(self, bytes_a, bytes_b):
        """位元組級別的粗略比對。"""
        max_len = max(len(bytes_a), len(bytes_b))
        if max_len == 0:
            return 0.0
        min_len = min(len(bytes_a), len(bytes_b))
        diff = abs(len(bytes_a) - len(bytes_b))
        for i in range(min_len):
            if bytes_a[i] != bytes_b[i]:
                diff += 1
        return diff / max_len

    def _generate_diff_image(self, baseline_path, actual_path, diff_path):
        """
        產生差異標示圖（將不同的像素標紅色）。
        """
        pixels_a = self._decode_png_pixels(baseline_path)
        pixels_b = self._decode_png_pixels(actual_path)

        if pixels_a is None or pixels_b is None:
            return

        width, height, data_a = pixels_a
        width_b, height_b, data_b = pixels_b

        if width != width_b or height != height_b:
            return

        # 建立差異圖像素
        diff_pixels = bytearray(data_a)
        for i in range(0, len(data_a), 4):
            if i + 4 > len(data_a) or i + 4 > len(data_b):
                break
            if data_a[i:i+4] != data_b[i:i+4]:
                # 標記為紅色
                diff_pixels[i] = 255      # R
                diff_pixels[i+1] = 0      # G
                diff_pixels[i+2] = 0      # B
                diff_pixels[i+3] = 255    # A

        self._write_png(diff_path, width, height, bytes(diff_pixels))

    def _write_png(self, path, width, height, rgba_data):
        """將 RGBA 像素資料寫成 PNG 檔案。"""
        def make_chunk(chunk_type, data):
            chunk = chunk_type + data
            return (
                struct.pack('>I', len(data))
                + chunk
                + struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)
            )

        # 加入 filter bytes（每列前面加 0 = None filter）
        raw = bytearray()
        for y in range(height):
            raw.append(0)  # filter type: None
            offset = y * width * 4
            raw.extend(rgba_data[offset:offset + width * 4])

        with open(path, 'wb') as f:
            # PNG 簽名
            f.write(b'\x89PNG\r\n\x1a\n')
            # IHDR
            ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
            f.write(make_chunk(b'IHDR', ihdr_data))
            # IDAT
            compressed = zlib.compress(bytes(raw))
            f.write(make_chunk(b'IDAT', compressed))
            # IEND
            f.write(make_chunk(b'IEND', b''))

    @staticmethod
    def _read_file_bytes(path):
        """讀取檔案的原始位元組。"""
        with open(path, 'rb') as f:
            return f.read()
