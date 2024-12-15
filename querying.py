def query_biorxiv(start_date, end_date):
    """ Query bioarxiv for a given date range
    :param start_date: The start date of the range in the format 'YYYY-MM-DD'
    :param end_date: The end date of the range in the format 'YYYY-MM-DD'
    :return: A list of dictionaries of entries from bioarxiv
    """
    # URL to query the API
    base_url = "https://api.biorxiv.org/details/biorxiv"
    query_url = f"{base_url}/{start_date}/{end_date}/"

    # Make the API request
    print(query_url)
    # Initialize variables
    cursor = 0
    all_entries = []

    while True:
        # Construct the API URL with the current cursor
        url = f"{query_url}{str(cursor)}"
        logger.info(f"Querying {url}")
        # Make the API request
        response = requests.get(url)
        data = response.json()
        
        # Extract the total number of entries and the current batch of entries
        total = int(data['messages'][0]['total'])
        entries = data['collection']
        
        # Add the current batch of entries to the list of all entries
        all_entries.extend(entries)
        
        # Update the cursor for the next batch
        cursor += len(entries)
        print(cursor)
        # Check if we have collected all entries
        if cursor >= total:
            break
    return all_entries


def query_arxiv(start_date, end_date):
    """ Query Arxiv for a given date range
    :param start_date: The start date of the range in the format 'YYYY-MM-DD'
    :param end_date: The end date of the range in the format 'YYYY-MM-DD'
    :return: A list of dictionaries of entries from bioarxiv
    """
    # URL to query the API
    start_date, end_date = start_date.replace('-', ''), end_date.replace('-', '')
    base_url = 'https://export.arxiv.org/api/query?search_query=all:neurtinos&submittedDate:'
    query_url = f"{base_url}0000[{start_date}+TO+{end_date}0000]"

    # Make the API request
    print(query_url)
    # Initialize variables
    cursor = 0
    all_entries = []

    while True:
        # Construct the API URL with the current cursor
        url = f"{query_url}{str(cursor)}"
        logger.info(f"Querying {url}")
        # Make the API request
        response = requests.get(url)
        data = response.json()
        
        # Extract the total number of entries and the current batch of entries
        total = int(data['messages'][0]['total'])
        entries = data['collection']
        
        # Add the current batch of entries to the list of all entries
        all_entries.extend(entries)
        
        # Update the cursor for the next batch
        cursor += len(entries)
        print(cursor)
        # Check if we have collected all entries
        if cursor >= total:
            break
    return all_entries
