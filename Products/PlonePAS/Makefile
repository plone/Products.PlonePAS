export PYTHON=python

all: test 
	@echo "make doc will produce documentation in the ./doc/ dir"

test: 
	@${MAKE} -C tests test

clean: 
	@find . -name "*.pyc" -exec rm {} \;
	@find . -name "*~" -exec rm {} \;
	@find src -name "*.c" -exec rm {} \;
	@rm -rf build	
	@${MAKE} -C docs clean

