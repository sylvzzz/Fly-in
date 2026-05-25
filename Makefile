MAP_FILE = maps/challenger/01_the_impossible_dream.txt

# MAP_FILE = maps/hard/01_maze_nightmare.txt
# MAP_FILE = maps/hard/02_capacity_hell.txt
# MAP_FILE = maps/hard/03_ultimate_challenge.txt

# MAP_FILE = maps/medium/01_dead_end_trap.txt
# MAP_FILE = maps/medium/02_circular_loop.txt
# MAP_FILE = maps/medium/03_priority_puzzle.txt
    
# MAP_FILE = maps/easy/01_linear_path.txt
# MAP_FILE = maps/easy/02_simple_fork.txt
# MAP_FILE = maps/easy/03_basic_capacity.txt

MAIN	= Fly-in.py

build:
	pip install -r requirements.txt

install: build
	pip install build
	python3 -m build


run:
	python3 $(MAIN) $(MAP_FILE)

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