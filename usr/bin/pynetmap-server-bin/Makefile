
build: clean
		bash -c " \
			mkdir -p build &&\
			rsync -rv --exclude=build --exclude=.git . build &&\
			cd build &&\
			python3 setup.py build &&\
			python3 . \
			"
			

clean: 
		@echo "########################## CLEAN #############################"
		@rm build -R || true
		@find . -path "*/__pycache__/*.py" -not -name "__init__.py" -delete 
		@find . -path "*/__pycache__/*.pyc" -delete 

run: clean
		python3 . 

