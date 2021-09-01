fast: pytest_fast flake mypy doctest
all: coverage flake mypy doctest
flake:
	flake8
mypy:
	mypy metapipe/*.py
doctest:
	python metapipe/file_processors.py
coverage:
	coverage run -m pytest
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
