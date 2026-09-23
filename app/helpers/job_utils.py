import sys 
from pathlib import Path

from typing import List, Optional
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).resolve().parent))

from helpers.constants import JOBSEARCH_DEFAULT_LOCATION, JOBSEARCH_SITE_REF

def build_search_queries(target_roles: List[str],
                         cities: Optional[List[str]] = None,
                         country: str = JOBSEARCH_DEFAULT_LOCATION) -> List[str]:

    if not target_roles:
        return []

    generated_queries = []

    target_locations = [f'{city} {country}'.strip() for city in cities] if cities else [country]

    for role in target_roles:
        for location in target_locations:
            query_text = f'"{role}" {location}'.strip()
            query_text = " ".join(query_text.split())
            
            generated_queries.append(query_text)

    unique_queries = list(dict.fromkeys(generated_queries))

    return unique_queries


def add_site_refs_to_queries(queries: List[str], domains: List[str]) -> List[str]:
    sited_queries = []

    for domain in domains:
        ref_site = JOBSEARCH_SITE_REF.get(domain, "")

        if ref_site:
            core_queries =  [f"{ref_site} {query}" for query in queries]

            sited_queries.extend(core_queries)

    unique_queries = list(dict.fromkeys(sited_queries))

    return unique_queries
