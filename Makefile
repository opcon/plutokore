test :
	python setup.py test

coverage-run :
	coverage run setup.py test

coverage : coverage-run
	coverage report

py3-lint : 
	pylint --py3k ./plutokore

yapf : 
	yapf -d --recursive ./plutokore

.PHONY: test
