import requests
from bs4 import BeautifulSoup
from config import GOOGLE_API_KEY, IMAGE_ENGINE_ID, SEARCH_ENGINE_ID
from Agents.llms_manager_agent import LLMManager

class SearchAgent:
    """
    A class to perform Google Custom Search for images and articles,
    extract URLs from search results, and scrape article contents.
    """
    def __init__(self):
        self.llm = LLMManager()
    @staticmethod
    def search_images(query):
        """
        Search for images related to 'skin affected by {query}' using Google Custom Search API.

        Args:
            query (str): The search query term.

        Returns:
            dict: JSON response from the Google Custom Search API containing image search results.

        Raises:
            RuntimeError: If the API request fails or returns an error.
        """
        url = 'https://www.googleapis.com/customsearch/v1'
        params = {
            'q': f'skin affected by {query}',
            'key': GOOGLE_API_KEY,
            'cx': IMAGE_ENGINE_ID,
            'searchType': 'image',
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Referer": "https://www.google.com/"
        }
        try:
            res = requests.get(url, params=params, headers=headers, timeout=10)
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            raise RuntimeError(f'Image search error: {e}')

    @staticmethod
    def imgs_url(search_result, top_k=3):
        """
        Extract image URLs from the image search result JSON.

        Args:
            search_result (dict): JSON response from image search.
            top_k (int): Number of top image URLs to extract.

        Returns:
            list: List of image URLs (strings).
        """
        links = []
        try:
            if 'items' in search_result:
                for item in search_result['items'][:top_k]:
                    link = item.get('link')
                    if link:
                        links.append(link)
            return links
        except Exception:
            # In case of unexpected structure or missing keys, return empty list
            return []

    @staticmethod
    def search_articles(query,max_results=5):
        """
        Search for articles related to '{query} : Causes & Symptoms' using Google Custom Search API.

        Args:
            query (str): The search query term.

        Returns:
            dict: JSON response from the Google Custom Search API containing article search results.

        Raises:
            RuntimeError: If the API request fails or returns an error.
        """
        url = 'https://www.googleapis.com/customsearch/v1'
        params = {
            'q': f'{query} : Causes & Symptoms',
            'key': GOOGLE_API_KEY,
            'cx': SEARCH_ENGINE_ID,
            'num': max_results
        }
        try:
            res = requests.get(url, params=params, timeout=10)
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            raise RuntimeError(f'Article search error: {e}')

    @staticmethod
    def articles_url(search_results, max_urls=5):
        """
        Extract article URLs from the article search result JSON.
        Args:
            search_result (dict): JSON response from article search.
            max_urls (int): Number of top article URLs to extract.

        Returns:
            list: List of article URLs (strings).
        """
        links_with_metadata = []
        if search_results and 'items' in search_results:
            for item in search_results['items'][:max_urls]:  # Limit to max_urls
                link_data = {}
                link = item.get('link')  # Use .get for safety
                if link:
                    link_data['url'] = link
                    link_data['title'] = item.get('title', '')  # Extract title if available
                    link_data['snippet'] = item.get('snippet', '')  # Extract snippet if available
                    # For image search, sometimes the image URL is in 'image': {'contextLink': ...}
                    if 'image' in item and item['image'].get('contextLink'):
                        link_data['image_context'] = item['image']['contextLink']
                    links_with_metadata.append(link_data)
        return links_with_metadata
    @staticmethod
    def scrapper(links):
        """
        Scrape main textual content from a list of article URLs.

        Args:
            links (list): List of URLs (strings) to scrape.

        Returns:
            list: List of strings containing the scraped textual content from each URL.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0"
        }
        cookies = {"CONSENT": "YES+cb.20220419-08-p0.cs+FX+111"}
        contents = []
        for link in links:
            try:
                response = requests.get(link, headers=headers, cookies=cookies, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    main_content = (
                        soup.find('main') or
                        soup.find('article') or
                        soup.find('div', class_='content') or
                        soup.find('div', class_='page-content') or
                        soup.find('div', id='main-content')
                    )
                    if main_content:
                        text = main_content.get_text(separator=' ', strip=True)
                    else:
                        body = soup.find('body')
                        text = body.get_text(separator=' ', strip=True) if body else ''
                    if text:
                        contents.append(text)
            except requests.RequestException:
                # Skip URLs that cause request errors or timeouts
                continue
            except Exception:
                # Skip URLs that cause parsing errors or other exceptions
                continue
        return contents
    
    def deepsearch(self, query):
        """
        Perform a deep search for articles related to the query.

        Args:
            query (str): The search query term.

        Returns:
            list: List of strings containing the main textual content from the articles.
        """
        articles = self.search_articles(query)
        urls_with_metadata = self.articles_url(articles)
        urls=[urlmd['url'] for urlmd in urls_with_metadata]
        bodies = self.scrapper(urls)
        return bodies
    
    # function to summazrize articles
    def summarize_article(self, article_metadata: dict, query:str) ->str:
        """
        Summarizes the content of an article using the LLM.

        Args:
            article_metadata: Dictionary containing article metadata (title, snippet, URL).

        Returns:
            A summary string of the article.
        """
        #parse Article meta data
        if not isinstance(article_metadata, dict):
            raise ValueError("article_metadata must be a dictionary")
        if not all(key in article_metadata for key in ['title', 'snippet', 'url']):
            raise ValueError("article_metadata must contain 'title', 'snippet', and 'url' keys")
        
        Title = article_metadata.get('title', 'No Title')
        Snippet = article_metadata.get('snippet', Title)
        URL = article_metadata.get('url', 'No URL')
        article_content = self.scrapper([URL])
        if not article_content:
            raise ValueError("No content scraped from the provided URL")
        # Join the scraped content into a single string
        article_text = " ".join(article_content)
        # Check if the content is too long
        if len(article_text) > 5000:
            article_text = article_text[:5000] + "... [Truncated]"

        # Construct a prompt for summarization
        prompt = f"""
            You are a highly accomplished research scientist with over 10 years of experience and a proven record of impactful scientific analysis.
                Your task is to carefully analyze and summarize the following scientific article to assist a dermatologist in optimizing their research paper.

                ARTICLE DETAILS:
                - Title: {Title}
                - Full Text: {article_text}
                - Research Focus: {query}

                INSTRUCTIONS:
                1. Present your analysis using clearly defined sections:
                - Introduction
                - Methods
                - Key Findings
                - Discussion
                - Conclusion

                2. Under each section, highlight key points using **bullet points**.

                3. Ensure the summary is:
                - Concise and precise
                - Written in **simple and professional language**
                - Focused on extracting insights directly relevant to the query: **{query}**

                4. Emphasize information that will **enhance the efficiency and depth** of dermatology research.

                5. Avoid markdown, code formatting, or links—**plain text only**.

                Before finalizing:
                ✅ Double-check that all critical insights related to the research focus ({query}) are included.  
                ✅ Ensure the summary supports decision-making and scientific clarity.

        """

        # Send the prompt to the LLM and get the response
        summary = self.llm.send_message_to_llm(prompt)
        
        return summary
