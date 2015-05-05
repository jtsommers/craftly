run:
	python p5.py

time:
	time -p python p5.py

profile:
	python -m cProfile -s time p5.py
