start_mcp:
	lsof -i :6274 | awk 'NR!=1 {print $2}' | xargs kill -9
	lsof -i :6277 | awk 'NR!=1 {print $2}' | xargs kill -9
	mcp dev mcp_stuff/mcp_code.py

start_mcp:
	lsof -i :8000 | awk 'NR!=1 {print $2}' | xargs kill -9
	python3 endpoints.py