export PYTHON=python

all: test 
	@echo "make doc will produce documentation in the ./doc/ dir"

test: 
	@${MAKE} -C tests test

regression:
	@${MAKE} -C tests regression

clean: 
	@find . -name "*.pyc" -exec rm {} \;
	@find . -name "*~" -exec rm {} \;
	@rm -rf build	
