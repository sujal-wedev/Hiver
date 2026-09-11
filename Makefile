.PHONY: all install backend frontend dev eval demo clean

# Default: complete end-to-end evaluation
all: backend-eval

install:
	pip install -r backend/requirements.txt
	cd frontend && npm install

backend:
	python backend/app.py

frontend:
	cd frontend && npm run dev

dev:
	@echo "Launching Flask backend and Vite React frontend..."
	python backend/app.py

eval:
	python backend/eval/run_eval.py

demo:
	python backend/src/pipeline.py --message "Where is my package? It has been stuck at the carrier facility for 3 days!"

clean:
	rm -rf __pycache__ backend/__pycache__ backend/src/__pycache__ backend/eval/__pycache__ frontend/dist
