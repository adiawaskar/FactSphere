from googlesearch import search

def get_google_urls(query, num_results=10):
    return list(search(query, num_results=num_results))

# Example usage
if __name__ == "__main__":
    topic = input("Search topic: ")
    urls = get_google_urls(topic)
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")
