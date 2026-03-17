import asyncio
import logging
import httpx
from pathlib import Path
from typing import Optional, Dict, Any

from local_openalex import LocalOpenAlexClient

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

class OpenAlexAPIClient:
    """Minimal OpenAlex REST API client."""
    def __init__(self, email: Optional[str] = None):
        self.base_url = "https://api.openalex.org/works"
        self.params = {"mailto": email} if email else {}

    async def get_work(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Fetch a work from the OpenAlex REST API."""
        # identifier can be a DOI, arXiv ID, or OpenAlex ID
        url = f"{self.base_url}/{identifier}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=self.params, timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"Work not found in API: {identifier}")
                else:
                    logger.error(f"API error {response.status_code} for {identifier}")
            except Exception as e:
                logger.error(f"Request failed for {identifier}: {e}")
        return None

class HybridOpenAlexClient:
    """Combines local SQLite lookups with an API fallback."""
    def __init__(self, db_path: str = "openalex_local.db", email: Optional[str] = None):
        self.db_path = Path(db_path)
        self.local = None
        if self.db_path.exists():
            self.local = LocalOpenAlexClient(self.db_path)
            logger.info(f"Loaded local database: {db_path}")
        else:
            logger.warning(f"Local database not found at {db_path}. All calls will go to API.")
        
        self.api = OpenAlexAPIClient(email=email)

    def close(self):
        if self.local:
            self.local.close()

    async def get_work(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get a work, trying the local database first, then falling back to the API.
        Always returns the full OpenAlex JSON format if possible.
        """
        if self.local:
            work_id = None
            # 1. If it's an OpenAlex ID
            if identifier.startswith("W") and identifier[1:].isdigit():
                work_id = identifier
            # 2. If it's a DOI, look up the ID first
            elif "doi.org" in identifier or identifier.startswith("10."):
                row = self.local.get_work_by_doi(identifier)
                if row:
                    work_id = row["id"]
            
            if work_id:
                raw = self.local.get_raw_work(work_id)
                if raw:
                    logger.info(f"Local match found for {identifier}")
                    return raw

        # 3. Fallback to API
        logger.info(f"No local match for {identifier}, calling OpenAlex API...")
        # Clean identifier for API: ensure DOI prefix or arXiv prefix
        api_id = identifier
        if "doi.org/" in api_id:
            # Already has it, but ensure it's https
            if api_id.startswith("http:"):
                api_id = "https" + api_id[4:]
        elif api_id.startswith("10."):
            # Add DOI prefix
            api_id = f"https://doi.org/{api_id}"
        elif "arxiv.org/abs/" in api_id:
            api_id = api_id.split("arxiv.org/abs/")[-1]
            if not api_id.startswith("arXiv:"):
                api_id = f"arXiv:{api_id}"
                
        return await self.api.get_work(api_id)

async def example():
    # Initialize the hybrid client
    client = HybridOpenAlexClient(db_path="openalex_local.db", email="your-email@example.com")

    # Example 1: A DOI that might be in your local DB if you ran download_targeted.sh
    # (Constitutional AI paper)
    doi = "10.48550/arXiv.2212.01381"
    print(f"\n--- Looking up DOI: {doi} ---")
    work = await client.get_work(doi)
    if work:
        print(f"Result: {work.get('title')}")
        print(f"Source: {'Local DB' if 'raw_json' not in work else 'Local DB (Raw)'}")
    else:
        print("Work not found.")

    # Example 2: An arXiv ID (usually forces API call unless already indexed by DOI locally)
    arxiv_id = "https://arxiv.org/abs/2303.08774" # GPT-4 Technical Report
    print(f"\n--- Looking up arXiv: {arxiv_id} ---")
    work = await client.get_work(arxiv_id)
    if work:
        print(f"Result: {work.get('title')}")
    else:
        print("Work not found.")

    client.close()

if __name__ == "__main__":
    asyncio.run(example())
