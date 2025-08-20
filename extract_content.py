# extract_content.py
import sys
import trafilatura

def extract_article_from_url(url):
    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        return "Error: Could not retrieve the webpage. Please check the URL and your internet connection."
    text = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=False,
        no_fallback=True
    )
    if text:
        return text
    else:
        return "Error: Could not extract any main content from the provided URL."

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_content.py <URL>")
        print("Example: python extract_content.py https://www.example.com/news-article")
        sys.exit(1)

    input_url = sys.argv[1]

    print(f"--> Fetching and extracting content from: {input_url}")
    
    content = extract_article_from_url(input_url)
    
    if content.startswith("Error:"):
        print(content) 
        sys.exit(1) 

    file_name = "content.txt"
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"--> Successfully extracted content and saved it to '{file_name}'")

    except IOError as e:
        print(f"Error: Could not write to file '{file_name}'.")
        print(f"Details: {e}")
        sys.exit(1)