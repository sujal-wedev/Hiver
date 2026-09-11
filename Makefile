.PHONY: all install data-prep cluster retrieval eval demo test clean

# Default: complete end-to-end pipeline execution
all: data-prep cluster retrieval eval

install:
	pip install -r requirements.txt

data-prep:
	python src/data_prep.py --csv-path data/raw/twcs.csv --output-dir data --sample-size 5000 --seed 42

cluster:
	python src/cluster_intents.py --data-path data/processed/amazonhelp_customer_msgs.parquet --output-dir results --sample-size 1500 --seed 42 --chosen-k 8

retrieval:
	python -c "import sys, os; sys.path.insert(0, '.'); from src.retrieval import HistoricalRetrievalIndex; idx = HistoricalRetrievalIndex(); print('Retrieval index ready:', len(idx.df))"

eval:
	python eval/run_eval.py

demo:
	python src/pipeline.py --message "Where is my package? It has been stuck at the transit hub for 4 days!"

test: demo
	python -c "import sys; sys.path.insert(0, '.'); from eval.metrics import evaluate_intent_classification; print('Metrics OK')"

clean:
	rm -rf __pycache__ src/__pycache__ eval/__pycache__
