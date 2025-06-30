"""
Citation Verification System

This Python script verifies statements in text by:
1. Splitting text into statements
2. Using OpenAI's API to extract key searchable information
3. Searching for sources using Legal Wires web scraper
4. Analyzing alignment between statements and sources
5. Adding citations to statements with good matches
"""

import re
import json
import requests
import openai
import os
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import urllib.parse
import time

# Load environment variables
load_dotenv()

# Configure API keys
openai.api_key = os.getenv("OPENAI_API_KEY")

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

    def search(self, query, max_results=5):
        """Search Legal Wires and return structured results"""
        try:
            # Encode the search query
            encoded_query = urllib.parse.quote(query)
            search_url = f"{self.base_url}/search?q={encoded_query}"
            
            print(f"Searching Legal Wires for: '{query}'")
            
            # Make the request
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract search results
            results = self.parse_results(soup, max_results)
            
            return results
            
        except requests.RequestException as e:
            print(f"Error making request to Legal Wires: {e}")
            return []
        except Exception as e:
            print(f"Error parsing Legal Wires results: {e}")
            return []

    def parse_results(self, soup, max_results):
        """Parse the search results from the HTML"""
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
        """Extract data from a single result element"""
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
                'source_name': 'Legal Wires'
            }
            
        except Exception as e:
            print(f"Error extracting result data: {e}")
            return None

class CitationVerifier:
    """Main class for citation verification"""
    
    def __init__(self):
        """Initialize the citation verifier with Legal Wires searcher"""
        self.searcher = LegalWiresSearcher()
    
    def process_text(self, text: str) -> Dict[str, Any]:
        """Process entire text for citations
        
        Args:
            text: Input text to verify and cite
            
        Returns:
            Dict containing original and cited text
        """
        print("Starting citation verification process...")
        
        # Split the text into statements
        statements = self._split_into_statements(text)
        print(f"Text split into {len(statements)} statements")
        
        # Process each statement
        processed_statements = []
        statement_details = []
        
        for i, statement in enumerate(statements):
            print(f"Processing statement {i+1}/{len(statements)}")
            result = self._process_statement(statement)
            processed_statements.append(result["with_citation"])
            statement_details.append(result)
        
        # Combine processed statements
        cited_text = " ".join(processed_statements)
        
        return {
            "original_text": text,
            "cited_text": cited_text,
            "statements": statement_details
        }
    
    def _split_into_statements(self, text: str) -> List[str]:
        """Split text into individual statements"""
        # Split on sentence ending punctuation
        statements = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter empty statements
        return [stmt for stmt in statements if stmt.strip()]
    
    def _process_statement(self, statement: str) -> Dict[str, Any]:
        """Process a single statement for citation"""
        try:
            # Extract key information for searching
            key_info = self._extract_key_information(statement)
            
            # Search for sources using Legal Wires
            sources = self.searcher.search(key_info, max_results=5)
            
            # Convert to expected format and rank sources by alignment
            formatted_sources = []
            for source in sources:
                formatted_source = {
                    'title': source['title'],
                    'snippet': source['description'],
                    'link': source['url'],
                    'source_name': source['source_name']
                }
                formatted_sources.append(formatted_source)
            
            # Rank sources by alignment
            ranked_sources = self._rank_sources_by_alignment(statement, formatted_sources)
            
            # Create a citation if we have a good match
            best_source = ranked_sources[0] if ranked_sources else None
            with_citation = statement
            
            if best_source and best_source.get("alignment_score", 0) > 0.7:
                with_citation = f"{statement} ({best_source['source_name']})"
            
            return {
                "original": statement,
                "key_info": key_info,
                "with_citation": with_citation,
                "top_sources": ranked_sources[:5]
            }
        
        except Exception as e:
            print(f"Error processing statement: {e}")
            return {
                "original": statement,
                "with_citation": statement,
                "error": str(e)
            }
    
    def _extract_key_information(self, statement: str) -> str:
        """Extract key searchable information from a statement using LLM"""
        try:
            # Use OpenAI to extract key information
            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # Using a more standard model name
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant that extracts key searchable information from statements. Extract the most important factual claims, names, dates, and unique details that would help verify this statement. Be concise."
                    },
                    {
                        "role": "user",
                        "content": f"Extract the key searchable information from this statement: \"{statement}\""
                    }
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error extracting key information: {e}")
            # Fallback: extract important words
            words = statement.split()
            # Prioritize proper nouns (capitalized words)
            important_words = [word for word in words if word[0].isupper()]
            # Add other non-stopwords
            stopwords = {"a", "an", "the", "in", "on", "at", "by", "for", "with", "about", "to", "and", "or", "that", "this", "was", "is", "are", "were"}
            important_words += [word for word in words if len(word) > 3 and word.lower() not in stopwords and word not in important_words]
            
            return " ".join(important_words[:6])  # Limit to 6 words
    
    def _rank_sources_by_alignment(self, statement: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank sources by alignment with the statement"""
        if not sources:
            return []
        
        try:
            # Prepare sources for OpenAI
            sources_info = "\n\n".join([
                f"Source {i+1}:\nName: {source['source_name']}\nTitle: {source['title']}\nSnippet: {source['snippet']}"
                for i, source in enumerate(sources[:5])  # Limit to top 5 sources
            ])
            
            # Use OpenAI to evaluate alignment
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant that evaluates how well sources support a statement. For each source, provide an alignment score from 0 to 1, where 1 means perfect alignment (the source directly confirms the statement) and 0 means no alignment (unrelated or contradicts)."
                    },
                    {
                        "role": "user",
                        "content": f"Statement: \"{statement}\"\n\nPotential sources:\n{sources_info}\n\nFor each source, provide ONLY the source number and alignment score in this format: \"Source 1: 0.85\""
                    }
                ],
                temperature=0.2,
                max_tokens=250
            )
            
            alignment_text = response.choices[0].message.content
            return self._parse_alignment_scores(alignment_text, sources)
        
        except Exception as e:
            print(f"Error ranking sources: {e}")
            # Fallback: simple keyword matching
            return self._keyword_match_ranking(statement, sources)
    
    def _parse_alignment_scores(self, text: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse alignment scores from LLM output"""
        score_map = {}
        pattern = r"Source\s+(\d+):\s*([0-9.]+)"
        
        for match in re.finditer(pattern, text):
            index = int(match.group(1)) - 1
            score = float(match.group(2))
            
            if 0 <= index < len(sources) and 0 <= score <= 1:
                score_map[index] = score
        
        # Apply scores to sources
        result = []
        for i, source in enumerate(sources):
            if i in score_map:
                source_copy = source.copy()
                source_copy["alignment_score"] = score_map[i]
                result.append(source_copy)
        
        # Sort by alignment score
        return sorted(result, key=lambda x: x.get("alignment_score", 0), reverse=True)
    
    def _keyword_match_ranking(self, statement: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback method: Rank sources by keyword matching"""
        # Extract keywords from statement
        keywords = set(re.findall(r'\b\w{4,}\b', statement.lower()))
        
        # Score each source
        scored_sources = []
        for source in sources:
            source_text = f"{source.get('title', '')} {source.get('snippet', '')}".lower()
            source_keywords = set(re.findall(r'\b\w{4,}\b', source_text))
            
            # Calculate score based on keyword overlap
            overlap = keywords.intersection(source_keywords)
            score = len(overlap) / max(1, len(keywords))
            
            source_copy = source.copy()
            source_copy["alignment_score"] = min(0.9, score)  # Cap at 0.9 for the simple method
            scored_sources.append(source_copy)
        
        # Sort by score
        return sorted(scored_sources, key=lambda x: x.get("alignment_score", 0), reverse=True)


def main():
    """Main function to demonstrate the citation verifier"""
    
    # Sample text from the prompt
    sample_text = """On May 15, 2025, Justice B.R. Gavai was sworn in as the 52nd Chief Justice of India, becoming the first Buddhist and only the second Dalit to hold this esteemed position. In a significant development, U.S. President Donald Trump announced that India has offered to remove all tariffs on U.S. goods, signaling a potential shift in trade relations between the two nations. Meanwhile, shares of the Indian IT firm Persistent Systems dropped by 3% following reports that its key client, UnitedHealth, is facing a criminal probe. In the realm of international relations, President Trump also stated that hostilities between Pakistan and India have been settled, indicating a move towards peace in the region. Lastly, in the world of sports, the 2025 Khelo India Youth Games concluded today in Bihar, showcasing the talents of over 8,500 athletes across 28 sports disciplines."""
    
    # Initialize the verifier
    verifier = CitationVerifier()
    
    # Process the text
    result = verifier.process_text(sample_text)
    
    # Print results
    print("\n" + "="*60)
    print("CITATION VERIFICATION RESULTS")
    print("="*60)
    
    print("\nOriginal Text:")
    print("-" * 40)
    print(result["original_text"])
    
    print("\nText with Citations:")
    print("-" * 40)
    print(result["cited_text"])
    
    # Print detailed results for each statement
    print("\nDetailed Results:")
    print("-" * 40)
    for i, stmt in enumerate(result["statements"]):
        print(f"\nStatement {i+1}:")
        print(f"Original: {stmt['original']}")
        if 'key_info' in stmt:
            print(f"Search Terms: {stmt['key_info']}")
        print(f"With Citation: {stmt['with_citation']}")
        
        if "top_sources" in stmt and stmt["top_sources"]:
            print(f"Top Source: {stmt['top_sources'][0]['source_name']} (Score: {stmt['top_sources'][0].get('alignment_score', 0):.2f})")
            if stmt['top_sources'][0].get('link'):
                print(f"URL: {stmt['top_sources'][0]['link']}")
        
        if "error" in stmt:
            print(f"Error: {stmt['error']}")
        
        print("-" * 30)


if __name__ == "__main__":
    main()
