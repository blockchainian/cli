build: clean
	@python setup.py sdist bdist_wheel

release: build
	@twine upload dist/*

clean:
	@rm -fr build/ dist/ leetcode_cli.egg-info/

.PHONY: build clean release
