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
    text = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=False,
        no_fallback=True
    )

    # 3. Return the result
    if text:
        return text
    else:
        return "Error: Could not extract any main content from the provided URL."

if __name__ == "__main__":
    # Check if a command-line argument (the URL) was provided.
    if len(sys.argv) != 2:
        print("Usage: python extract_content.py <URL>")
        print("Example: python extract_content.py https://www.example.com/news-article")
        sys.exit(1)

    # The URL is the second element in the sys.argv list
    input_url = sys.argv[1]

    print(f"--> Fetching and extracting content from: {input_url}")
    
    # Call the main function to get the article content
    content = extract_article_from_url(input_url)
    
    # --- NEW: Code to save the content to a file ---

    # Check if the content contains an error message before writing
    if content.startswith("Error:"):
        print(content) # Print the error to the console
        sys.exit(1) # Exit without creating the file

    file_name = "content.txt"
    try:
        # 'with open' handles opening and automatically closing the file.
        # 'w' mode means write (it will overwrite the file if it already exists).
        # 'encoding="utf-8"' is important to handle special characters from any language.
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Let the user know the process was successful.
        print(f"--> Successfully extracted content and saved it to '{file_name}'")

    except IOError as e:
        # Handle potential file writing errors (e.g., permissions issues)
        print(f"Error: Could not write to file '{file_name}'.")
        print(f"Details: {e}")
        sys.exit(1)