all: test

test: 
	@${PYTHON} runalltests.py

clean: 
	@find . -name "*.pyc" -exec rm {} \;
	@find . -name "*~" -exec rm {} \;
	@find . -name "hotspot*" -exec rm {} \;
	@find . -name "callgrind.out*" -exec rm {} \;

tags:


