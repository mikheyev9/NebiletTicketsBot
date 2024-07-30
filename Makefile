.PHONY: install run check_deps

# Проверить и установить зависимости, если необходимо
check_deps:
	@if [ ! -f poetry.lock ]; then \
		echo "Dependencies are not installed. Installing..."; \
		poetry install; \
	else \
		echo "Dependencies are already installed."; \
	fi

# Активировать виртуальное окружение и установить зависимости
install:
	poetry install

# Запустить main.py через Poetry, предварительно проверив зависимости
run: check_deps
	poetry run python main.py