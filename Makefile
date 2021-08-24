test:
	coverage run -m pytest
	coverage report
	flake8
	mypy metapipe/*.py
	python metapipe/file_processors.py
clean:
	rm -f metapipe/*,cover
	rm -f metapipe/tests/*,cover
	rm -rf metapipe/__pycache__
	rm -f .coverage
	rm -rf .pytest_cache
	rm -rf .mypy_cache
