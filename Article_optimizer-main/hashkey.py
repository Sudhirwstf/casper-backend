
# import os
# import sys
# import argparse
# import logging
# import requests
# from bs4 import BeautifulSoup
# from openai import OpenAI
# from urllib.parse import quote
# import json
# import time
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import re
# import urllib.parse

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# SUPPORTED_PLATFORMS = {
#     "instagram": (3, 5),
#     "tiktok": (3, 6),
#     "linkedin": (3, 5),
#     "twitter": (1, 2),
#     "x": (1, 2),
#     "facebook": (0, 2),
#     "youtube": (3, 5),
#     "pinterest": (2, 5),
# }


# class LegalWiresSearcher:
#     def __init__(self):
#         self.base_url = "https://app.legal-wires.com"
#         self.session = requests.Session()
#         # Add headers to mimic a real browser
#         self.session.headers.update({
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
#             'Accept-Language': 'en-US,en;q=0.5',
#             'Accept-Encoding': 'gzip, deflate',
#             'Connection': 'keep-alive',
#             'Upgrade-Insecure-Requests': '1',
#         })

#     def search(self, query, max_results=10):
#         """
#         Search Legal Wires and return structured results
#         """
#         try:
#             # Encode the search query
#             encoded_query = urllib.parse.quote(query)
#             search_url = f"{self.base_url}/search?q={encoded_query}"
            
#             logger.info(f"Searching Legal Wires for: '{query}'")
            
#             # Make the request
#             response = self.session.get(search_url, timeout=15)
#             response.raise_for_status()
            
#             # Parse the HTML
#             soup = BeautifulSoup(response.content, 'html.parser')
            
#             # Extract search results
#             results = self.parse_results(soup, max_results)
            
#             return results
            
#         except requests.RequestException as e:
#             logger.error(f"Error making request to Legal Wires: {e}")
#             return []
#         except Exception as e:
#             logger.error(f"Error parsing Legal Wires results: {e}")
#             return []

#     def parse_results(self, soup, max_results):
#         """
#         Parse the search results from the HTML
#         """
#         results = []
        
#         # Common selectors to try
#         possible_selectors = [
#             '.search-result',
#             '.result-item',
#             '.search-item',
#             '[data-testid="search-result"]',
#             '.card',
#             '.list-item',
#             'article',
#         ]
        
#         result_elements = []
#         for selector in possible_selectors:
#             result_elements = soup.select(selector)
#             if result_elements:
#                 logger.info(f"Found results using selector: {selector}")
#                 break
        
#         if not result_elements:
#             # Fallback: try to find any elements with links that might be results
#             result_elements = soup.find_all('a', href=True)[:max_results*2]
        
#         count = 0
#         for element in result_elements:
#             if count >= max_results:
#                 break
                
#             result = self.extract_result_data(element)
#             if result and result['title']:
#                 results.append(result)
#                 count += 1
        
#         return results

#     def extract_result_data(self, element):
#         """
#         Extract data from a single result element
#         """
#         try:
#             # Try to find title
#             title = ""
#             title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.heading']
#             for selector in title_selectors:
#                 title_elem = element.select_one(selector)
#                 if title_elem:
#                     title = title_elem.get_text(strip=True)
#                     break
            
#             if not title:
#                 title = element.get_text(strip=True)[:100] if element.get_text(strip=True) else ""
            
#             # Try to find description/summary
#             description = ""
#             desc_selectors = ['.description', '.summary', '.excerpt', 'p']
#             for selector in desc_selectors:
#                 desc_elem = element.select_one(selector)
#                 if desc_elem:
#                     description = desc_elem.get_text(strip=True)[:300]
#                     break
            
#             # Try to find URL
#             url = ""
#             if element.name == 'a':
#                 url = element.get('href', '')
#             else:
#                 link_elem = element.select_one('a[href]')
#                 if link_elem:
#                     url = link_elem.get('href', '')
            
#             # Make URL absolute if it's relative
#             if url and not url.startswith('http'):
#                 url = urllib.parse.urljoin(self.base_url, url)
            
#             return {
#                 'title': title,
#                 'description': description,
#                 'url': url,
#                 'content': f"{title} {description}"  # Combined content for keyword extraction
#             }
            
#         except Exception as e:
#             logger.error(f"Error extracting result data: {e}")
#             return None

# class ArticleNicheHashtagSEOAnalyzer:
#     def __init__(self, api_key=DEFAULT_API_KEY):
#         self.client = OpenAI(api_key=api_key)
#         self.legal_wires_searcher = LegalWiresSearcher()

#     def read_article(self, filepath):
#         """Read article content from file"""
#         try:
#             with open(filepath, "r", encoding="utf-8") as f:
#                 return f.read()
#         except Exception as e:
#             logger.error(f"Error reading file {filepath}: {e}")
#             return ""

#     def get_niches(self, text):
#         """Extract top 2 niches from article using GPT"""
#         prompt = (
#             "Extract the top 2 most relevant categories that best describe the topic of the following article. "
#             "Reply with only the niche names in single word format (no spaces, use hyphens if needed). "
#             "Example: 'political-violence' should be 'politicalviolence'. "
#             "Return only the category names separated by commas.\n\n" + text[:3000]
#         )
        
#         try:
#             resp = self.client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=0.3,
#                 max_tokens=100
#             )
#             niches = [n.strip().lower().replace(" ", "").replace("-", "") for n in resp.choices[0].message.content.split(",")[:2]]
#             return [niche for niche in niches if niche]
#         except Exception as e:
#             logger.error(f"Error getting niches: {e}")
#             return ["general", "content"]

#     def search_legal_wires(self, query):
#         """Search using Legal Wires"""
#         try:
#             results = self.legal_wires_searcher.search(query, max_results=15)
#             return results
#         except Exception as e:
#             logger.error(f"Error searching Legal Wires for '{query}': {e}")
#             return []

#     def extract_keywords_from_web_results(self, search_results, niche):
#         """Extract keywords from web search results using text analysis"""
#         if not search_results:
#             return []

#         # Collect all text from search results
#         all_text = ""
#         for result in search_results:
#             title = result.get('title', '').lower()
#             description = result.get('description', '').lower()
#             content = result.get('content', '').lower()
#             url = result.get('url', '').lower()
#             all_text += f" {title} {description} {content} {url}"

#         # Extract potential keywords using regex and filtering
#         words = re.findall(r'\b[a-z]+(?:\s+[a-z]+){0,2}\b', all_text)
        
#         # Filter and score keywords
#         keyword_freq = {}
#         for word in words:
#             word = word.strip()
#             if (len(word) > 3 and len(word) < 30 and 
#                 word not in ['http', 'https', 'www', 'com', 'org', 'net'] and
#                 not word.isdigit()):
#                 keyword_freq[word] = keyword_freq.get(word, 0) + 1

#         # Sort by frequency and relevance to niche
#         sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        
#         # Filter keywords that are relevant to the niche
#         relevant_keywords = []
#         niche_words = niche.lower().split()
        
#         for keyword, freq in sorted_keywords[:50]:
#             # Include if keyword appears multiple times or contains niche terms
#             if (freq > 1 or 
#                 any(niche_word in keyword for niche_word in niche_words) or
#                 any(keyword in niche_word for niche_word in niche_words)):
#                 relevant_keywords.append(keyword)
        
#         return relevant_keywords[:20]

#     def get_seo_keywords_for_niche(self, niche):
#         """Get SEO keywords for a niche using Legal Wires web search"""
#         logger.info(f"🔍 Searching web for SEO keywords: {niche}")
        
#         all_keywords = set()
        
#         # SEO-focused search queries
#         search_queries = [
#             f"{niche} SEO keywords",
#             f"best {niche} keywords 2024",
#             f"{niche} trending searches",
#             f"{niche} popular terms",
#             f"{niche} content ideas",
#             f"top {niche} topics",
#             f"{niche} marketing keywords"
#         ]

#         # Search the web for each query
#         for query in search_queries:
#             try:
#                 logger.info(f"Searching: {query}")
#                 results = self.search_legal_wires(query)
#                 if results:
#                     keywords = self.extract_keywords_from_web_results(results, niche)
#                     all_keywords.update(keywords)
#                     logger.info(f"✅ Found {len(keywords)} keywords from: {query}")
#                 time.sleep(1)  # Rate limiting
#             except Exception as e:
#                 logger.error(f"Error searching for '{query}': {e}")

#         # Additional searches for long-tail keywords
#         longtail_queries = [
#             f"how to {niche}",
#             f"{niche} tips and tricks",
#             f"{niche} best practices",
#             f"{niche} guide 2024"
#         ]
        
#         for query in longtail_queries:
#             try:
#                 results = self.search_legal_wires(query)
#                 if results:
#                     keywords = self.extract_keywords_from_web_results(results, niche)
#                     all_keywords.update(keywords)
#                 time.sleep(1)
#             except Exception as e:
#                 logger.error(f"Error with longtail search '{query}': {e}")

#         return list(all_keywords)

#     def search_best_hashtag_url(self, niche):
#         """Generate best-hashtags.com URL for niche"""
#         return f"https://best-hashtags.com/hashtag/{quote(niche)}/"

#     def scrape_hashtags_from_url(self, url):
#         """Scrape hashtags from best-hashtags.com"""
#         logger.info(f"📋 Scraping hashtags from: {url}")
#         try:
#             headers = {
#                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
#             }
#             res = requests.get(url, timeout=15, headers=headers)
#             if res.status_code == 200:
#                 soup = BeautifulSoup(res.text, "html.parser")
#                 return soup.get_text()
#             else:
#                 logger.warning(f"Failed to scrape hashtags, status code: {res.status_code}")
#                 return ""
#         except Exception as e:
#             logger.error(f"Error scraping {url}: {e}")
#             return ""

#     def filter_relevant_keywords(self, article_text, all_keywords, niches):
#         """Filter SEO keywords to select only the most relevant ones using LLM"""
#         if not all_keywords:
#             return []
            
#         # Determine optimal number of keywords based on article length
#         article_word_count = len(article_text.split())
#         if article_word_count < 200:
#             target_keywords = 8
#         elif article_word_count < 500:
#             target_keywords = 12
#         elif article_word_count < 1000:
#             target_keywords = 15
#         else:
#             target_keywords = 20
            
#         logger.info(f"📊 Article has {article_word_count} words, targeting {target_keywords} keywords")
        
#         # Prepare keywords list for analysis
#         keywords_to_analyze = all_keywords[:100] if len(all_keywords) > 100 else all_keywords
#         keywords_string = ", ".join(keywords_to_analyze)
        
#         prompt = (
#             f"Analyze this article and select the {target_keywords} most relevant SEO keywords from the list below. "
#             f"Article niches: {', '.join(niches)}\n\n"
#             f"Article content (first 1500 chars): {article_text[:1500]}...\n\n"
#             f"Available keywords: {keywords_string}\n\n"
#             f"Select exactly {target_keywords} keywords that are:\n"
#             f"1. Directly related to the article content\n"
#             f"2. Have good SEO potential\n"
#             f"3. Match the identified niches\n"
#             f"4. Would help people find this content\n\n"
#             f"Return only the selected keywords as a comma-separated list."
#         )
        
#         try:
#             resp = self.client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=0.1,
#                 max_tokens=300
#             )
            
#             selected_keywords = [kw.strip().lower() for kw in resp.choices[0].message.content.split(",")]
#             # Filter out empty strings and ensure they were in original list
#             relevant_keywords = [kw for kw in selected_keywords if kw and kw in all_keywords]
            
#             logger.info(f"✅ Selected {len(relevant_keywords)} relevant keywords from {len(all_keywords)} total")
#             return relevant_keywords
            
#         except Exception as e:
#             logger.error(f"Error filtering keywords: {e}")
#             # Fallback: return top keywords that contain niche terms
#             fallback_keywords = []
#             niche_words = [word for niche in niches for word in niche.lower().split()]
            
#             for keyword in all_keywords[:target_keywords * 2]:
#                 if any(niche_word in keyword.lower() for niche_word in niche_words):
#                     fallback_keywords.append(keyword)
#                 if len(fallback_keywords) >= target_keywords:
#                     break
                    
#             return fallback_keywords[:target_keywords]

#     def analyze_hashtags(self, hashtag_text, platform, seo_keywords):
#         """Analyze hashtags with SEO keywords integration"""
#         opt_min, opt_max = SUPPORTED_PLATFORMS.get(platform.lower(), (3, 5))
        
#         seo_context = ""
#         if seo_keywords:
#             seo_context = f"\n\nConsider these trending SEO keywords: {', '.join(seo_keywords[:10])}"
        
#         prompt = (
#             f"From the following hashtag content, select the top {opt_min}-{opt_max} hashtags that "
#             f"would boost engagement on {platform}. Return only hashtag names separated by commas, no # symbols."
#             f"{seo_context}\n\n{hashtag_text[:2000]}"
#         )
        
#         try:
#             resp = self.client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=0.2,
#                 max_tokens=150
#             )
#             return resp.choices[0].message.content.strip()
#         except Exception as e:
#             logger.error(f"Error analyzing hashtags: {e}")
#             return "content, marketing, trending"

#     def process(self, filepath, platform):
#         """Main processing function"""
#         logger.info("🚀 Starting comprehensive analysis...")
        
#         # Step 1: Read article
#         logger.info("📖 Reading article...")
#         text = self.read_article(filepath)
#         if not text:
#             logger.error("Failed to read article content")
#             return

#         # Step 2: Find niches
#         logger.info("🎯 Identifying niches...")
#         niches = self.get_niches(text)
#         logger.info(f"✅ Identified niches: {niches}")

#         # Step 3: Parallel processing for hashtags and SEO keywords
#         logger.info("🔄 Starting parallel research...")
        
#         all_hashtag_text = ""
#         all_seo_keywords = []

#         # Use ThreadPoolExecutor for parallel processing
#         with ThreadPoolExecutor(max_workers=4) as executor:
#             # Submit hashtag scraping tasks
#             hashtag_futures = {
#                 executor.submit(self.scrape_hashtags_from_url, self.search_best_hashtag_url(niche)): niche 
#                 for niche in niches
#             }
            
#             # Submit SEO keyword research tasks  
#             seo_futures = {
#                 executor.submit(self.get_seo_keywords_for_niche, niche): niche 
#                 for niche in niches
#             }

#             # Collect hashtag results
#             for future in as_completed(hashtag_futures):
#                 niche = hashtag_futures[future]
#                 try:
#                     hashtag_text = future.result()
#                     all_hashtag_text += hashtag_text + "\n"
#                     logger.info(f"✅ Hashtags collected for: {niche}")
#                 except Exception as e:
#                     logger.error(f"❌ Failed hashtag collection for {niche}: {e}")

#             # Collect SEO keyword results
#             for future in as_completed(seo_futures):
#                 niche = seo_futures[future]
#                 try:
#                     keywords = future.result()
#                     all_seo_keywords.extend(keywords)
#                     logger.info(f"✅ SEO keywords found for {niche}: {len(keywords)}")
#                 except Exception as e:
#                     logger.error(f"❌ Failed SEO research for {niche}: {e}")

#         # Remove duplicates and clean keywords
#         all_seo_keywords = list(set([kw.strip().lower() for kw in all_seo_keywords if kw.strip()]))
        
#         # Step 4: Filter SEO keywords using LLM analysis
#         logger.info("🎯 Filtering relevant SEO keywords...")
#         relevant_seo_keywords = self.filter_relevant_keywords(text, all_seo_keywords, niches)
        
#         # Step 5: Analyze hashtags
#         logger.info("🧠 Analyzing optimal hashtags...")
#         best_hashtags = self.analyze_hashtags(all_hashtag_text, platform, relevant_seo_keywords)

#         # Display results
#         print("\n" + "="*80)
#         print("🎯 COMPREHENSIVE SEO & HASHTAG ANALYSIS")
#         print("="*80)
        
#         print(f"\n📊 Identified Niches:")
#         for i, niche in enumerate(niches, 1):
#             print(f"  {i}. {niche}")
        
#         print(f"\n🏷️ Optimized Hashtags for {platform.title()}:")
#         hashtag_list = best_hashtags.replace(', ', ' #').replace(',', ' #')
#         if not hashtag_list.startswith('#'):
#             hashtag_list = '#' + hashtag_list
#         print(f"  {hashtag_list}")
        
#         print(f"\n🔍 Relevant SEO Keywords ({len(relevant_seo_keywords)} selected from {len(all_seo_keywords)} found):")
#         if relevant_seo_keywords:
#             for i, keyword in enumerate(relevant_seo_keywords, 1):
#                 print(f"  {i:2d}. {keyword}")
#         else:
#             print("  ❌ No relevant SEO keywords found")

#         print(f"\n💡 Content Optimization Tips:")
#         print(f"  • Use these keywords in your {platform} post content")
#         print(f"  • Combine trending hashtags with niche-specific ones")
#         print(f"  • Monitor keyword performance and adjust strategy")
#         print(f"  • Create content around high-frequency keywords")
        
#         print("\n" + "="*80)
#         print("✅ Analysis Complete!")
#         print("="*80)


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="SEO Hashtag Analyzer with Legal Wires Search")
#     parser.add_argument("filepath", type=str, help="Path to the .txt file containing the article")
#     parser.add_argument("platform", type=str, help="Social media platform")
#     parser.add_argument("--api_key", type=str, help="OpenAI API key", default=DEFAULT_API_KEY)
    
#     args = parser.parse_args()

#     if args.platform.lower() not in SUPPORTED_PLATFORMS:
#         print(f"❌ Unsupported platform. Choose: {', '.join(SUPPORTED_PLATFORMS.keys())}")
#         sys.exit(1)

#     analyzer = ArticleNicheHashtagSEOAnalyzer(api_key=args.api_key)
#     analyzer.process(args.filepath, args.platform)





import os
import sys
import argparse
import logging
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from urllib.parse import quote
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_PLATFORMS = {
    "instagram": (3, 5),
    "tiktok": (3, 6),
    "linkedin": (3, 5),
    "twitter": (1, 2),
    "x": (1, 2),
    "facebook": (0, 2),
    "youtube": (3, 5),
    "pinterest": (2, 5),
}

class LegalWiresSearcher:
    def __init__(self):
        self.base_url = "https://app.legal-wires.com"
        self.session = requests.Session()
        # Add headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def search(self, query, max_results=10):
        """
        Search Legal Wires and return structured results
        """
        try:
            # Encode the search query
            encoded_query = urllib.parse.quote(query)
            search_url = f"{self.base_url}/search?q={encoded_query}"
            
            logger.info(f"Searching Legal Wires for: '{query}'")
            
            # Make the request
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract search results
            results = self.parse_results(soup, max_results)
            
            return results
            
        except requests.RequestException as e:
            logger.error(f"Error making request to Legal Wires: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing Legal Wires results: {e}")
            return []

    def parse_results(self, soup, max_results):
        """
        Parse the search results from the HTML
        """
        results = []
        
        # Common selectors to try
        possible_selectors = [
            '.search-result',
            '.result-item',
            '.search-item',
            '[data-testid="search-result"]',
            '.card',
            '.list-item',
            'article',
        ]
        
        result_elements = []
        for selector in possible_selectors:
            result_elements = soup.select(selector)
            if result_elements:
                logger.info(f"Found results using selector: {selector}")
                break
        
        if not result_elements:
            # Fallback: try to find any elements with links that might be results
            result_elements = soup.find_all('a', href=True)[:max_results*2]
        
        count = 0
        for element in result_elements:
            if count >= max_results:
                break
                
            result = self.extract_result_data(element)
            if result and result['title']:
                results.append(result)
                count += 1
        
        return results

    def extract_result_data(self, element):
        """
        Extract data from a single result element
        """
        try:
            # Try to find title
            title = ""
            title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.heading']
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title:
                title = element.get_text(strip=True)[:100] if element.get_text(strip=True) else ""
            
            # Try to find description/summary
            description = ""
            desc_selectors = ['.description', '.summary', '.excerpt', 'p']
            for selector in desc_selectors:
                desc_elem = element.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)[:300]
                    break
            
            # Try to find URL
            url = ""
            if element.name == 'a':
                url = element.get('href', '')
            else:
                link_elem = element.select_one('a[href]')
                if link_elem:
                    url = link_elem.get('href', '')
            
            # Make URL absolute if it's relative
            if url and not url.startswith('http'):
                url = urllib.parse.urljoin(self.base_url, url)
            
            return {
                'title': title,
                'description': description,
                'url': url,
                'content': f"{title} {description}"  # Combined content for keyword extraction
            }
            
        except Exception as e:
            logger.error(f"Error extracting result data: {e}")
            return None

class ArticleNicheHashtagSEOAnalyzer:
    def __init__(self, api_key=None):
        # Get API key from environment variable or parameter
        if api_key is None:
            api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable "
                "or pass it as a parameter."
            )
        
        self.client = OpenAI(api_key=api_key)
        self.legal_wires_searcher = LegalWiresSearcher()

    def read_article(self, filepath):
        """Read article content from file"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            return ""

    def get_niches(self, text):
        """Extract top 2 niches from article using GPT"""
        prompt = (
            "Extract the top 2 most relevant categories that best describe the topic of the following article. "
            "Reply with only the niche names in single word format (no spaces, use hyphens if needed). "
            "Example: 'political-violence' should be 'politicalviolence'. "
            "Return only the category names separated by commas.\n\n" + text[:3000]
        )
        
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100
            )
            niches = [n.strip().lower().replace(" ", "").replace("-", "") for n in resp.choices[0].message.content.split(",")[:2]]
            return [niche for niche in niches if niche]
        except Exception as e:
            logger.error(f"Error getting niches: {e}")
            return ["general", "content"]

    def search_legal_wires(self, query):
        """Search using Legal Wires"""
        try:
            results = self.legal_wires_searcher.search(query, max_results=15)
            return results
        except Exception as e:
            logger.error(f"Error searching Legal Wires for '{query}': {e}")
            return []

    def extract_keywords_from_web_results(self, search_results, niche):
        """Extract keywords from web search results using text analysis"""
        if not search_results:
            return []

        # Collect all text from search results
        all_text = ""
        for result in search_results:
            title = result.get('title', '').lower()
            description = result.get('description', '').lower()
            content = result.get('content', '').lower()
            url = result.get('url', '').lower()
            all_text += f" {title} {description} {content} {url}"

        # Extract potential keywords using regex and filtering
        words = re.findall(r'\b[a-z]+(?:\s+[a-z]+){0,2}\b', all_text)
        
        # Filter and score keywords
        keyword_freq = {}
        for word in words:
            word = word.strip()
            if (len(word) > 3 and len(word) < 30 and 
                word not in ['http', 'https', 'www', 'com', 'org', 'net'] and
                not word.isdigit()):
                keyword_freq[word] = keyword_freq.get(word, 0) + 1

        # Sort by frequency and relevance to niche
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Filter keywords that are relevant to the niche
        relevant_keywords = []
        niche_words = niche.lower().split()
        
        for keyword, freq in sorted_keywords[:50]:
            # Include if keyword appears multiple times or contains niche terms
            if (freq > 1 or 
                any(niche_word in keyword for niche_word in niche_words) or
                any(keyword in niche_word for niche_word in niche_words)):
                relevant_keywords.append(keyword)
        
        return relevant_keywords[:20]

    def get_seo_keywords_for_niche(self, niche):
        """Get SEO keywords for a niche using Legal Wires web search"""
        logger.info(f"🔍 Searching web for SEO keywords: {niche}")
        
        all_keywords = set()
        
        # SEO-focused search queries
        search_queries = [
            f"{niche} SEO keywords",
            f"best {niche} keywords 2024",
            f"{niche} trending searches",
            f"{niche} popular terms",
            f"{niche} content ideas",
            f"top {niche} topics",
            f"{niche} marketing keywords"
        ]

        # Search the web for each query
        for query in search_queries:
            try:
                logger.info(f"Searching: {query}")
                results = self.search_legal_wires(query)
                if results:
                    keywords = self.extract_keywords_from_web_results(results, niche)
                    all_keywords.update(keywords)
                    logger.info(f"✅ Found {len(keywords)} keywords from: {query}")
                time.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"Error searching for '{query}': {e}")

        # Additional searches for long-tail keywords
        longtail_queries = [
            f"how to {niche}",
            f"{niche} tips and tricks",
            f"{niche} best practices",
            f"{niche} guide 2024"
        ]
        
        for query in longtail_queries:
            try:
                results = self.search_legal_wires(query)
                if results:
                    keywords = self.extract_keywords_from_web_results(results, niche)
                    all_keywords.update(keywords)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error with longtail search '{query}': {e}")

        return list(all_keywords)

    def search_best_hashtag_url(self, niche):
        """Generate best-hashtags.com URL for niche"""
        return f"https://best-hashtags.com/hashtag/{quote(niche)}/"

    def scrape_hashtags_from_url(self, url):
        """Scrape hashtags from best-hashtags.com"""
        logger.info(f"📋 Scraping hashtags from: {url}")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            res = requests.get(url, timeout=15, headers=headers)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                return soup.get_text()
            else:
                logger.warning(f"Failed to scrape hashtags, status code: {res.status_code}")
                return ""
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return ""

    def filter_relevant_keywords(self, article_text, all_keywords, niches):
        """Filter SEO keywords to select only the most relevant ones using LLM"""
        if not all_keywords:
            return []
            
        # Determine optimal number of keywords based on article length
        article_word_count = len(article_text.split())
        if article_word_count < 200:
            target_keywords = 8
        elif article_word_count < 500:
            target_keywords = 12
        elif article_word_count < 1000:
            target_keywords = 15
        else:
            target_keywords = 20
            
        logger.info(f"📊 Article has {article_word_count} words, targeting {target_keywords} keywords")
        
        # Prepare keywords list for analysis
        keywords_to_analyze = all_keywords[:100] if len(all_keywords) > 100 else all_keywords
        keywords_string = ", ".join(keywords_to_analyze)
        
        prompt = (
            f"Analyze this article and select the {target_keywords} most relevant SEO keywords from the list below. "
            f"Article niches: {', '.join(niches)}\n\n"
            f"Article content (first 1500 chars): {article_text[:1500]}...\n\n"
            f"Available keywords: {keywords_string}\n\n"
            f"Select exactly {target_keywords} keywords that are:\n"
            f"1. Directly related to the article content\n"
            f"2. Have good SEO potential\n"
            f"3. Match the identified niches\n"
            f"4. Would help people find this content\n\n"
            f"Return only the selected keywords as a comma-separated list."
        )
        
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            selected_keywords = [kw.strip().lower() for kw in resp.choices[0].message.content.split(",")]
            # Filter out empty strings and ensure they were in original list
            relevant_keywords = [kw for kw in selected_keywords if kw and kw in all_keywords]
            
            logger.info(f"✅ Selected {len(relevant_keywords)} relevant keywords from {len(all_keywords)} total")
            return relevant_keywords
            
        except Exception as e:
            logger.error(f"Error filtering keywords: {e}")
            # Fallback: return top keywords that contain niche terms
            fallback_keywords = []
            niche_words = [word for niche in niches for word in niche.lower().split()]
            
            for keyword in all_keywords[:target_keywords * 2]:
                if any(niche_word in keyword.lower() for niche_word in niche_words):
                    fallback_keywords.append(keyword)
                if len(fallback_keywords) >= target_keywords:
                    break
                    
            return fallback_keywords[:target_keywords]

    def analyze_hashtags(self, hashtag_text, platform, seo_keywords):
        """Analyze hashtags with SEO keywords integration"""
        opt_min, opt_max = SUPPORTED_PLATFORMS.get(platform.lower(), (3, 5))
        
        seo_context = ""
        if seo_keywords:
            seo_context = f"\n\nConsider these trending SEO keywords: {', '.join(seo_keywords[:10])}"
        
        prompt = (
            f"From the following hashtag content, select the top {opt_min}-{opt_max} hashtags that "
            f"would boost engagement on {platform}. Return only hashtag names separated by commas, no # symbols."
            f"{seo_context}\n\n{hashtag_text[:2000]}"
        )
        
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=150
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error analyzing hashtags: {e}")
            return "content, marketing, trending"

    def process(self, filepath, platform):
        """Main processing function"""
        logger.info("🚀 Starting comprehensive analysis...")
        
        # Step 1: Read article
        logger.info("📖 Reading article...")
        text = self.read_article(filepath)
        if not text:
            logger.error("Failed to read article content")
            return

        # Step 2: Find niches
        logger.info("🎯 Identifying niches...")
        niches = self.get_niches(text)
        logger.info(f"✅ Identified niches: {niches}")

        # Step 3: Parallel processing for hashtags and SEO keywords
        logger.info("🔄 Starting parallel research...")
        
        all_hashtag_text = ""
        all_seo_keywords = []

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit hashtag scraping tasks
            hashtag_futures = {
                executor.submit(self.scrape_hashtags_from_url, self.search_best_hashtag_url(niche)): niche 
                for niche in niches
            }
            
            # Submit SEO keyword research tasks  
            seo_futures = {
                executor.submit(self.get_seo_keywords_for_niche, niche): niche 
                for niche in niches
            }

            # Collect hashtag results
            for future in as_completed(hashtag_futures):
                niche = hashtag_futures[future]
                try:
                    hashtag_text = future.result()
                    all_hashtag_text += hashtag_text + "\n"
                    logger.info(f"✅ Hashtags collected for: {niche}")
                except Exception as e:
                    logger.error(f"❌ Failed hashtag collection for {niche}: {e}")

            # Collect SEO keyword results
            for future in as_completed(seo_futures):
                niche = seo_futures[future]
                try:
                    keywords = future.result()
                    all_seo_keywords.extend(keywords)
                    logger.info(f"✅ SEO keywords found for {niche}: {len(keywords)}")
                except Exception as e:
                    logger.error(f"❌ Failed SEO research for {niche}: {e}")

        # Remove duplicates and clean keywords
        all_seo_keywords = list(set([kw.strip().lower() for kw in all_seo_keywords if kw.strip()]))
        
        # Step 4: Filter SEO keywords using LLM analysis
        logger.info("🎯 Filtering relevant SEO keywords...")
        relevant_seo_keywords = self.filter_relevant_keywords(text, all_seo_keywords, niches)
        
        # Step 5: Analyze hashtags
        logger.info("🧠 Analyzing optimal hashtags...")
        best_hashtags = self.analyze_hashtags(all_hashtag_text, platform, relevant_seo_keywords)

        # Display results
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE SEO & HASHTAG ANALYSIS")
        print("="*80)
        
        print(f"\n📊 Identified Niches:")
        for i, niche in enumerate(niches, 1):
            print(f"  {i}. {niche}")
        
        print(f"\n🏷️ Optimized Hashtags for {platform.title()}:")
        hashtag_list = best_hashtags.replace(', ', ' #').replace(',', ' #')
        if not hashtag_list.startswith('#'):
            hashtag_list = '#' + hashtag_list
        print(f"  {hashtag_list}")
        
        print(f"\n🔍 Relevant SEO Keywords ({len(relevant_seo_keywords)} selected from {len(all_seo_keywords)} found):")
        if relevant_seo_keywords:
            for i, keyword in enumerate(relevant_seo_keywords, 1):
                print(f"  {i:2d}. {keyword}")
        else:
            print("  ❌ No relevant SEO keywords found")

        print(f"\n💡 Content Optimization Tips:")
        print(f"  • Use these keywords in your {platform} post content")
        print(f"  • Combine trending hashtags with niche-specific ones")
        print(f"  • Monitor keyword performance and adjust strategy")
        print(f"  • Create content around high-frequency keywords")
        
        print("\n" + "="*80)
        print("✅ Analysis Complete!")
        print("="*80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SEO Hashtag Analyzer with Legal Wires Search")
    parser.add_argument("filepath", type=str, help="Path to the .txt file containing the article")
    parser.add_argument("platform", type=str, help="Social media platform")
    parser.add_argument("--api_key", type=str, help="OpenAI API key (optional, will use OPENAI_API_KEY env var if not provided)")
    
    args = parser.parse_args()

    if args.platform.lower() not in SUPPORTED_PLATFORMS:
        print(f"❌ Unsupported platform. Choose: {', '.join(SUPPORTED_PLATFORMS.keys())}")
        sys.exit(1)

    try:
        analyzer = ArticleNicheHashtagSEOAnalyzer(api_key=args.api_key)
        analyzer.process(args.filepath, args.platform)
    except ValueError as e:
        print(f"❌ {e}")
        print("\n💡 To set the environment variable:")
        print("   Linux/Mac: export OPENAI_API_KEY='your-api-key-here'")
        print("   Windows:   set OPENAI_API_KEY=your-api-key-here")
        sys.exit(1)

        