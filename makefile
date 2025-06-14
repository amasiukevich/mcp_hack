run_mcp:
	lsof -i :8000 | awk 'NR!=1 {print $2}' | xargs kill -9
	python run_mcp.py


run_processing:
	python run_processing.py
