all: test

test: 
	@${PYTHON} runalltests.py


regression: 
	@${PYTHON} seeWhatBreaks.py

clean: 
	@find . -name "*.pyc" -exec rm {} \;
	@find . -name "*~" -exec rm {} \;

tags:


