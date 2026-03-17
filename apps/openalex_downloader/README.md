To get a proof of concept working:
1. Create a venv
2. python run.py
3. bash download_targeted.sh (you can change which queries are searched for in the bash script, they are currently hardcoded as QUERIES)
    If you want to see how many papers you are about to download you can run the same script with the --count-only flag first.
4. Rerun python run.py. It will now send off 1000 queries against the local database and save the results to example.txt. This is a simple proof of concept.

The HybridOpenAlexClient defined in hybrid_lookup.pyshould be a more or less plug and play replacement for the online openalex API and will allow you to replace api calls with the local lookup (using LocalOpenAlexClient class defined in local_openalex.py) but fall back to using the API if a given work is not already locally downloaded. 

To demonstrate this, you can runHybrid.py with a local paper and a not yet downloaded paper. For example:
1. python runHybrid.py "10.48550/arxiv.2204.05862" instantly retrieves the RLHF paper from the local cache.
2. python runHybrid.py "10.48550/arXiv.2212.01381" smoothly falls back to the API after failing to find the paper in the local cache. 

The database is a simple database with fast text search indexing so you can also query it directly using sqlite3 to connect to it. 