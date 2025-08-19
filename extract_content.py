# extract_content.py

# Import necessary libraries
# 'sys' is used to access command-line arguments
# 'trafilatura' is the library for web scraping and text extraction
import sys
import trafilatura

def extract_article_from_url(url):
    """
    Fetches a URL, extracts the main text content, and returns it.
    
    Args:
        url (str): The URL of the news article or webpage.
        
    Returns:
        str: The extracted main text content, or an error message if extraction fails.
    """
    # 1. Download the webpage's HTML content.
    # The fetch_url function handles the network request to get the page.
    downloaded = trafilatura.fetch_url(url)
    
    # Check if the download was successful
    if downloaded is None:
        return "Error: Could not retrieve the webpage. Please check the URL and your internet connection."

    # 2. Extract the main text from the downloaded HTML.
    # The extract function intelligently finds and cleans the main article body.
    # The 'include_comments=False' argument ensures we don't get the comments section.
    # The 'target_language' can help with accuracy if you know the language beforehand.
    text = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=False, # Set to True if you need tables
        no_fallback=True # Use this for cleaner, but potentially less, output
    )

    # 3. Return the result
    if text:
        return text
    else:
        return "Error: Could not extract any main content from the provided URL."

if __name__ == "__main__":
    # This block runs when the script is executed directly from the terminal.
    
    # Check if a command-line argument (the URL) was provided.
    # sys.argv is a list containing the script name and its arguments.
    # len(sys.argv) should be 2: [script_name, url]
    if len(sys.argv) != 2:
        print("Usage: python extract_content.py <URL>")
        print("Example: python extract_content.py https://www.example.com/news-article")
        sys.exit(1) # Exit the script with an error code

    # The URL is the second element in the sys.argv list
    input_url = sys.argv[1]

    print(f"--> Fetching and extracting content from: {input_url}\n")
    
    # Call the main function to get the article content
    content = extract_article_from_url(input_url)
    
    # Print the final extracted content to the terminal
    print("--- EXTRACTED CONTENT ---")
    print(content)
    print("-------------------------\n")