# ===================================================
# Selenium 測試框架 - 統一指令入口
# ===================================================
# make test          → 執行所有測試
# make smoke         → 只跑冒煙測試
# make unit          → 只跑單元測試
# make scenario S=xx → 執行指定情境
# make parallel      → 平行執行
# make lint          → 程式碼檢查
# make format        → 自動格式化
# make install       → 安裝依賴
# ===================================================

PYTHON   ?= python
PYTEST   ?= $(PYTHON) -m pytest
BROWSER  ?= chrome
ENV      ?= dev

# === 安裝 ===

.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: install-dev
install-dev: install
	pip install pre-commit flake8 black isort
	pre-commit install

# === 測試執行 ===

.PHONY: test
test:
	$(PYTEST) tests/ -v --tb=short --browser=$(BROWSER) --env $(ENV)

.PHONY: test-headless
test-headless:
	$(PYTEST) tests/ -v --tb=short --browser=$(BROWSER) --headless-mode --env $(ENV)

.PHONY: smoke
smoke:
	$(PYTEST) tests/ -v --tb=short -m smoke --browser=$(BROWSER) --env $(ENV)

.PHONY: unit
unit:
	$(PYTEST) tests/unit/ -v --tb=short

.PHONY: scenario
scenario:
	@if [ -z "$(S)" ]; then \
		echo "用法: make scenario S=demo_search"; \
		echo "可用情境:"; \
		ls -d scenarios/*/tests 2>/dev/null | sed 's|scenarios/||;s|/tests||' | grep -v _template; \
		exit 1; \
	fi
	$(PYTEST) scenarios/$(S)/tests/ -v --tb=short --browser=$(BROWSER) --env $(ENV)

.PHONY: parallel
parallel:
	$(PYTEST) tests/ -v --tb=short -n auto --browser=$(BROWSER) --headless-mode --env $(ENV)

# === 報告 ===

.PHONY: report-html
report-html:
	$(PYTEST) tests/ -v --tb=short --html=reports/report.html --self-contained-html --browser=$(BROWSER) --env $(ENV)

.PHONY: report-allure
report-allure:
	$(PYTEST) tests/ -v --tb=short --alluredir=reports/allure-results --browser=$(BROWSER) --env $(ENV)

# === 重跑失敗 ===

.PHONY: rerun
rerun:
	$(PYTEST) tests/ -v --tb=short --reruns 2 --reruns-delay 3 --browser=$(BROWSER) --env $(ENV)

# === 程式碼品質 ===

.PHONY: lint
lint:
	$(PYTHON) -m flake8 pages/ utils/ config/ tests/ --max-line-length=120 --ignore=E501,W503

.PHONY: format
format:
	$(PYTHON) -m isort pages/ utils/ config/ tests/ conftest.py run.py --profile black
	$(PYTHON) -m black pages/ utils/ config/ tests/ conftest.py run.py --line-length=120

.PHONY: check-format
check-format:
	$(PYTHON) -m isort pages/ utils/ config/ tests/ conftest.py run.py --profile black --check-only
	$(PYTHON) -m black pages/ utils/ config/ tests/ conftest.py run.py --line-length=120 --check

# === 匯出拋棄式腳本 ===

.PHONY: export
export:
	@if [ -z "$(FILE)" ]; then \
		echo "用法: make export FILE=scenarios/demo_search/tests/test_search.py"; \
		echo "選項: OUT=output.py BROWSER=chrome HEADLESS=1"; \
		exit 1; \
	fi
	$(PYTHON) export_test.py $(FILE) \
		$(if $(OUT),-o $(OUT)) \
		--browser=$(BROWSER) \
		$(if $(HEADLESS),--headless)

# === 情境產生 ===

.PHONY: new-scenario
new-scenario:
	@if [ -z "$(NAME)" ]; then \
		echo "用法: make new-scenario NAME=login_test URL=https://example.com"; \
		exit 1; \
	fi
	$(PYTHON) generate_scenario.py $(NAME) $(if $(URL),--url $(URL))

# === 清理 ===

.PHONY: clean
clean:
	rm -rf reports/*.html reports/*.json reports/allure-results/
	rm -rf screenshots/*.png
	rm -rf diffs/*.png
	rm -rf logs/*.log
	rm -rf __pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# === 說明 ===

.PHONY: help
help:
	@echo ""
	@echo "  Selenium 測試框架指令"
	@echo "  ====================="
	@echo ""
	@echo "  安裝:"
	@echo "    make install           安裝專案依賴"
	@echo "    make install-dev       安裝開發工具（含 pre-commit）"
	@echo ""
	@echo "  測試:"
	@echo "    make test              執行所有測試"
	@echo "    make test-headless     無頭模式執行"
	@echo "    make smoke             只跑冒煙測試"
	@echo "    make unit              只跑單元測試"
	@echo "    make scenario S=xxx    執行指定情境"
	@echo "    make parallel          平行執行（需 pytest-xdist）"
	@echo "    make rerun             失敗自動重跑"
	@echo ""
	@echo "  報告:"
	@echo "    make report-html       產生 HTML 報告"
	@echo "    make report-allure     產生 Allure 報告"
	@echo ""
	@echo "  品質:"
	@echo "    make lint              flake8 檢查"
	@echo "    make format            black + isort 格式化"
	@echo "    make check-format      檢查格式（不修改）"
	@echo ""
	@echo "  其他:"
	@echo "    make new-scenario NAME=xx URL=xx  建立新情境"
	@echo "    make clean             清理產出檔案"
	@echo ""
	@echo "  變數:"
	@echo "    BROWSER=chrome|firefox|edge  (預設 chrome)"
	@echo "    ENV=dev|staging|prod         (預設 dev)"
	@echo ""
