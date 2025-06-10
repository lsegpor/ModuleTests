# 
# i.keshelashvili@gsi.de
# 
CC = pyuic5

SRCS = $(shell ls gui_*.ui)

MODULES = $(echo .ui=.py)

all: compiling ${MODULES}
	@echo 'done!'


mylist:
	@echo ${SRCS}
	@echo ${MODULES}

compiling:
	@echo 'compiling ui files...'
	@echo '---------------------'

	## COMMON
	${CC} gui_ModuleScanner.ui      -o gui_ModuleScanner.py                   
	@echo '---------------------'

clean:
	rm -rv __pycache__
