from dotenv import load_dotenv
import os

from tavily import TavilyClient
from typing import List, Dict

load_dotenv()


def get_tavily_client(api_key):
    return TavilyClient(api_key=api_key)


def get_websearch_by_date_result(query: str,
                                 start_date: str,
                                 end_date: str,
                                 search_domains: List[str],
                                 country: str, 
                                 max_results: int) -> List[Dict]:

    client = get_tavily_client(os.getenv('TAVILY_API_KEY'))
    
    response = client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_domains=search_domains,
                include_published_date=True,
                include_domains_mode="restrict",
                start_date=start_date,
                end_date=end_date,
                include_raw_content=False,
                include_answer=False,
                country=country,
                topic="general",
                safe_search=True)

    results = response.get("results", []) if isinstance(response, dict) and isinstance(response.get("results", []), list) else []

    return results


def get_websearch_result(query: str,
                         search_domains: List[str],
                         country: str, 
                         max_results: int) -> List[Dict]:

    client = get_tavily_client(os.getenv('TAVILY_API_KEY'))
    
    response = client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                time_range="month",
                include_domains=search_domains,
                include_published_date=True,
                include_domains_mode="restrict",
                #filter_by_published_date=True,
                include_raw_content=False,
                include_answer=False,
                country=country,
                topic="general",
                #auto_parameters=True,
                safe_search=True)

    results = response.get("results", []) if isinstance(response, dict) and isinstance(response.get("results", []), list) else []

    return results


def extract_contents(urls: List[str], batch_size) -> Dict:

    client = get_tavily_client(os.getenv('TAVILY_API_KEY'))

    final_response: Dict[str, str] = {}

    for i in range(0, len(urls), batch_size):
        batch = urls[i:i + batch_size]

        response = client.extract(urls=batch,
                                  extract_depth='advanced')

        results = response.get("results", []) if isinstance(response, dict) and isinstance(response.get("results", []), list) else []

        final_response.update({ res.get('url'): res.get('raw_content') for res in results })

    return final_response