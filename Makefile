fast: pytest_fast flake mypy
all: coverage flake mypy doctest
flake:
	flake8
mypy:
	mypy metapipe/*.py
coverage:
	coverage run -m pytest
	coverage report
doctests_coverage:
	coverage run metapipe/file_processors.py
	coverage report
pytest_fast:
	pytest -m "not slow"
clean:
	rm -f metapipe/*,cover
	rm -f metapipe/tests/*,cover
	rm -rf metapipe/__pycache__
	rm -f .coverage
	rm -rf .pytest_cache
	rm -rf .mypy_cache
