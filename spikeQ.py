import json
import pandas as pd
import requests
from io import BytesIO
import re

def join_spike_sentences(sentences):
    return (
        " \n".join(
            f"[{i + 1}] {str(sentence)}"
            for i, sentence in enumerate(sentences.unique())
        )
        if len(sentences.unique()) > 1
        else sentences
    )
def query_spike(
    queries: list,
    query_type: str = "boolean",
    query_data_set_name: str = "pubmed",
    query_include_annotations: bool = True,
    drop_duplicate_articles: bool = False,
    aggregate_sentences: bool = True,
    results_limit: int = 20,
) -> pd.DataFrame:
    """Runs a spike query using the spike API
    Performs a POST request to the /api/3/search/query endpoint.
    Then performs a GET request to the /api/3/search/query/<location_id> endpoint.
    Args:
        queries: The query that we want to send to the API endpoint.
        query_type: either "boolean", "token", or "syntactic"
        query_data_set_name: either "pubmed", "wikipedia", or "covid19"
        query_include_annotations: not sure what this parameter does tbh
        drop_duplicate_articles: if we want to remove articles that are duplicates,
        aggregate_sentences: if we want to put all the sentences from the same article into one row
        results_limit: how many results we want to receive
    Returns:
        A DataFrame with the following columns: "sentence_text", "title", "article_link", "paragraph_text", "abstract_text".
    """
    protocol = "https://"
    authority = "spike.pubmed.apps.allenai.org"
    api_endpoint = "/api/3/search/query"

    dataframes = []
    for query_value in queries:

        print(f"Running query: {query_value}")

        query = {}
        query["data_set_name"] = query_data_set_name
        query["include_annotations"] = query_include_annotations
        query["queries"] = {query_type: query_value.strip()}

        # Gets the location from which to query the actual results
        payload = json.dumps(query)
        headers = {
            "authority": authority,
            "pragma": "no-cache",
            "cache-control": "no-cache",
            "accept": "application/json, text/plain, */*",
            # 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
            "content-type": "application/json;charset=UTF-8",
            "origin": f"{protocol}{authority}",
            # 'sec-fetch-site': 'same-origin',
            # 'sec-fetch-mode': 'cors',
            # 'sec-fetch-dest': 'empty',
            "referer": f"{protocol}{authority}/search/pubmed",
            # 'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            # 'cookie': 'ajs_user_id=%22f5ce0ea9-9208-598d-b9a2-31f16872589b%22; ajs_anonymous_id=%224d768ca2-7f76-4ed1-b15f-287d15e548e2%22'
        }
        url = f"{protocol}{authority}{api_endpoint}"
        response = requests.request("POST", url, headers=headers, data=payload)
        # spike_location = "/".join(response.headers['Location'].split("/")[:6])
        print(response.headers)
        spike_csv_location = response.headers["CSV-Location"]

        # Gets the results of the query (based on the location) as a .csv file (formatted as a Byte string)
        payload = {}
        headers = {}
        url = f"{protocol}{authority}{spike_csv_location}?sentence_id=true&sentence_text=true&paragraph_text=true&title=true&article_link=true&doc_ids=true&capture_indices=true&limit={results_limit}"
        response = requests.request("GET", url, headers=headers, data=payload)

        # transforms the Byte String into a pandas Dataframe, removes unnecessary columns
        df = pd.read_csv(BytesIO(response.text.encode("utf8")))[
            ["sentence_id", "sentence_text", "title", "article_link", "paragraph_text"]
        ]

        if drop_duplicate_articles:
            df = df.drop_duplicates(subset=["article_link"]).reset_index(drop=True)

        dataframes.append(df)

    pubmed_results = pd.concat(dataframes)

    if aggregate_sentences:
        # Aggregates all the sentences into one row if the article link is duplicate
        aggregation_functions = {
            "sentence_id": "first",
            "sentence_text": join_spike_sentences,
            "title": "first",
            "article_link": "first",
            "paragraph_text": "first",
        }
        pubmed_results = pubmed_results.groupby(
            ["article_link"], as_index=False
        ).aggregate(aggregation_functions)

    # fills in the abstract by querying from pubmed API
    pubmed_results["PMID"] = pubmed_results["article_link"].apply(
        lambda link: re.findall(".*/([0-9]+)/?$", link)[-1]
    )
#     pubmed_abstracts = pd.DataFrame(
#         load(pubmed_results["article_link"].unique(), PUBMED_CONTENT="INFO")
#     )

    return pubmed_results #.merge(pubmed_abstracts, on="PMID")