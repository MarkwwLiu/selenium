"""
utils/visual_regression.py 單元測試
"""

import os
import struct
import tempfile
import zlib
from unittest.mock import MagicMock
import pytest

from utils.visual_regression import VisualRegression


def _create_png(path, width, height, color=(255, 0, 0, 255)):
    """建立簡單的純色 PNG 檔案。"""
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter: None
        for x in range(width):
            raw.extend(color)

    def make_chunk(chunk_type, data):
        chunk = chunk_type + data
        return (
            struct.pack('>I', len(data))
            + chunk
            + struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)
        )

    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
        f.write(make_chunk(b'IHDR', ihdr))
        compressed = zlib.compress(bytes(raw))
        f.write(make_chunk(b'IDAT', compressed))
        f.write(make_chunk(b'IEND', b''))


@pytest.fixture
def mock_driver():
    return MagicMock()


@pytest.fixture
def tmpdir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestInit:
    @pytest.mark.positive
    def test_creates_dirs(self, mock_driver, tmpdir):
        baseline = os.path.join(tmpdir, 'baselines')
        diffs = os.path.join(tmpdir, 'diffs')
        vr = VisualRegression(mock_driver, baseline_dir=baseline, diff_dir=diffs)
        assert os.path.isdir(baseline)
        assert os.path.isdir(diffs)


class TestCheck:
    @pytest.mark.positive
    def test_new_baseline(self, mock_driver, tmpdir):
        baseline = os.path.join(tmpdir, 'baselines')
        diffs = os.path.join(tmpdir, 'diffs')
        vr = VisualRegression(mock_driver, baseline_dir=baseline, diff_dir=diffs)
        result = vr.check('page')
        assert result['is_new_baseline'] is True
        assert result['match'] is True
        assert result['diff_ratio'] == 0.0

    @pytest.mark.positive
    def test_matching_images(self, mock_driver, tmpdir):
        baseline_dir = os.path.join(tmpdir, 'baselines')
        diff_dir = os.path.join(tmpdir, 'diffs')
        os.makedirs(baseline_dir, exist_ok=True)
        os.makedirs(diff_dir, exist_ok=True)

        # 建立 baseline
        baseline_path = os.path.join(baseline_dir, 'page.png')
        _create_png(baseline_path, 2, 2, (255, 0, 0, 255))

        # mock driver 截圖也產生相同圖片
        def save_screenshot(path):
            _create_png(path, 2, 2, (255, 0, 0, 255))

        mock_driver.save_screenshot.side_effect = save_screenshot
        vr = VisualRegression(mock_driver, baseline_dir=baseline_dir, diff_dir=diff_dir)
        result = vr.check('page')
        assert result['match'] is True
        assert result['is_new_baseline'] is False

    @pytest.mark.negative
    def test_mismatching_images(self, mock_driver, tmpdir):
        baseline_dir = os.path.join(tmpdir, 'baselines')
        diff_dir = os.path.join(tmpdir, 'diffs')
        os.makedirs(baseline_dir, exist_ok=True)
        os.makedirs(diff_dir, exist_ok=True)

        baseline_path = os.path.join(baseline_dir, 'page.png')
        _create_png(baseline_path, 2, 2, (255, 0, 0, 255))

        def save_screenshot(path):
            _create_png(path, 2, 2, (0, 255, 0, 255))

        mock_driver.save_screenshot.side_effect = save_screenshot
        vr = VisualRegression(mock_driver, baseline_dir=baseline_dir, diff_dir=diff_dir)
        result = vr.check('page', threshold=0.0)
        assert result['match'] is False
        assert result['diff_ratio'] > 0
        assert result['diff_path'] is not None


class TestCheckElement:
    @pytest.mark.positive
    def test_new_baseline(self, mock_driver, tmpdir):
        baseline_dir = os.path.join(tmpdir, 'baselines')
        diff_dir = os.path.join(tmpdir, 'diffs')
        vr = VisualRegression(mock_driver, baseline_dir=baseline_dir, diff_dir=diff_dir)

        mock_el = MagicMock()
        mock_driver.find_element.return_value = mock_el
        result = vr.check_element('btn', 'id', 'submit')
        assert result['is_new_baseline'] is True


class TestUpdateBaseline:
    @pytest.mark.positive
    def test_saves_screenshot(self, mock_driver, tmpdir):
        baseline_dir = os.path.join(tmpdir, 'baselines')
        diff_dir = os.path.join(tmpdir, 'diffs')
        vr = VisualRegression(mock_driver, baseline_dir=baseline_dir, diff_dir=diff_dir)
        path = vr.update_baseline('page')
        assert path.endswith('page.png')
        mock_driver.save_screenshot.assert_called_once_with(path)


class TestCompareImages:
    @pytest.mark.positive
    def test_identical(self, mock_driver, tmpdir):
        baseline_dir = os.path.join(tmpdir, 'baselines')
        diff_dir = os.path.join(tmpdir, 'diffs')
        vr = VisualRegression(mock_driver, baseline_dir=baseline_dir, diff_dir=diff_dir)

        path_a = os.path.join(tmpdir, 'a.png')
        path_b = os.path.join(tmpdir, 'b.png')
        _create_png(path_a, 2, 2, (100, 100, 100, 255))
        _create_png(path_b, 2, 2, (100, 100, 100, 255))
        ratio = vr._compare_images(path_a, path_b)
        assert ratio == 0.0

    @pytest.mark.negative
    def test_different_size(self, mock_driver, tmpdir):
        baseline_dir = os.path.join(tmpdir, 'baselines')
        diff_dir = os.path.join(tmpdir, 'diffs')
        vr = VisualRegression(mock_driver, baseline_dir=baseline_dir, diff_dir=diff_dir)

        path_a = os.path.join(tmpdir, 'a.png')
        path_b = os.path.join(tmpdir, 'b.png')
        _create_png(path_a, 2, 2, (100, 100, 100, 255))
        _create_png(path_b, 4, 4, (100, 100, 100, 255))
        ratio = vr._compare_images(path_a, path_b)
        assert ratio == 1.0

    @pytest.mark.positive
    def test_all_different_pixels(self, mock_driver, tmpdir):
        baseline_dir = os.path.join(tmpdir, 'baselines')
        diff_dir = os.path.join(tmpdir, 'diffs')
        vr = VisualRegression(mock_driver, baseline_dir=baseline_dir, diff_dir=diff_dir)

        path_a = os.path.join(tmpdir, 'a.png')
        path_b = os.path.join(tmpdir, 'b.png')
        _create_png(path_a, 2, 2, (0, 0, 0, 255))
        _create_png(path_b, 2, 2, (255, 255, 255, 255))
        ratio = vr._compare_images(path_a, path_b)
        assert ratio == 1.0


class TestByteCompare:
    @pytest.mark.positive
    def test_identical(self, mock_driver, tmpdir):
        baseline_dir = os.path.join(tmpdir, 'baselines')
        diff_dir = os.path.join(tmpdir, 'diffs')
        vr = VisualRegression(mock_driver, baseline_dir=baseline_dir, diff_dir=diff_dir)
        assert vr._byte_compare(b'abc', b'abc') == 0.0

    @pytest.mark.positive
    def test_empty(self, mock_driver, tmpdir):
        baseline_dir = os.path.join(tmpdir, 'baselines')
        diff_dir = os.path.join(tmpdir, 'diffs')
        vr = VisualRegression(mock_driver, baseline_dir=baseline_dir, diff_dir=diff_dir)
        assert vr._byte_compare(b'', b'') == 0.0

    @pytest.mark.negative
    def test_all_different(self, mock_driver, tmpdir):
        baseline_dir = os.path.join(tmpdir, 'baselines')
        diff_dir = os.path.join(tmpdir, 'diffs')
        vr = VisualRegression(mock_driver, baseline_dir=baseline_dir, diff_dir=diff_dir)
        ratio = vr._byte_compare(b'aaa', b'zzz')
        assert ratio == 1.0


class TestDecodePngPixels:
    @pytest.mark.positive
    def test_valid_png(self, mock_driver, tmpdir):
        baseline_dir = os.path.join(tmpdir, 'baselines')
        diff_dir = os.path.join(tmpdir, 'diffs')
        vr = VisualRegression(mock_driver, baseline_dir=baseline_dir, diff_dir=diff_dir)

        path = os.path.join(tmpdir, 'test.png')
        _create_png(path, 3, 3, (255, 0, 0, 255))
        result = vr._decode_png_pixels(path)
        assert result is not None
        width, height, data = result
        assert width == 3
        assert height == 3

    @pytest.mark.negative
    def test_invalid_file(self, mock_driver, tmpdir):
        baseline_dir = os.path.join(tmpdir, 'baselines')
        diff_dir = os.path.join(tmpdir, 'diffs')
        vr = VisualRegression(mock_driver, baseline_dir=baseline_dir, diff_dir=diff_dir)

        path = os.path.join(tmpdir, 'not_png.txt')
        with open(path, 'w') as f:
            f.write('not a png')
        assert vr._decode_png_pixels(path) is None


class TestWritePng:
    @pytest.mark.positive
    def test_creates_valid_png(self, mock_driver, tmpdir):
        baseline_dir = os.path.join(tmpdir, 'baselines')
        diff_dir = os.path.join(tmpdir, 'diffs')
        vr = VisualRegression(mock_driver, baseline_dir=baseline_dir, diff_dir=diff_dir)

        path = os.path.join(tmpdir, 'output.png')
        pixel_data = bytes([255, 0, 0, 255] * 4)  # 2x2 red
        vr._write_png(path, 2, 2, pixel_data)
        assert os.path.exists(path)
        # 驗證可解析
        result = vr._decode_png_pixels(path)
        assert result is not None
        assert result[0] == 2
        assert result[1] == 2
