MAP_FILE = maps/hard/01_maze_nightmare.txt
MAIN	= Fly-in.py

build:
	pip install -r requirements.txt

install: build
	pip install build
	python3 -m build


run:
	clear;python3 $(MAIN) $(MAP_FILE)

debug:
	python3 -m pdb $(MAIN) $(MAP_FILE)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type f -name "*.pyc" -exec rm -f {} +

lint:
	python3 -m flake8 . --exclude testing
	python3 -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	python3 -m flake8 . --exclude testing
	python3 -m mypy . --strict --exclude testing


.PHONY: build install run debug clean lint lint-strict