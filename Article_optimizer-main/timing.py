


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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced platform support with optimal posting frequency ranges
SUPPORTED_PLATFORMS = {
    # Long-form content platforms
    "medium.com": {
        "type": "long_form",
        "display_name": "Medium",
        "optimal_range": (1, 3),
        "peak_times": ["Tuesday 2PM", "Wednesday 10AM", "Thursday 1PM"]
    },
    "blogger.com": {
        "type": "long_form", 
        "display_name": "Blogger",
        "optimal_range": (1, 3),
        "peak_times": ["Wednesday 10AM", "Monday 9AM", "Friday 2PM"]
    },
    
    # Social media platforms
    "linkedin": {
        "type": "social",
        "display_name": "LinkedIn",
        "optimal_range": (1, 2),
        "peak_times": ["Wednesday 8AM", "Tuesday 10AM", "Thursday 9AM"]
    },
    "x.com": {
        "type": "social",
        "display_name": "X (Twitter)",
        "optimal_range": (2, 4),
        "peak_times": ["Wednesday 12PM", "Tuesday 1PM", "Thursday 3PM"]
    },
    "facebook": {
        "type": "social",
        "display_name": "Facebook", 
        "optimal_range": (1, 2),
        "peak_times": ["Wednesday 3PM", "Sunday 1PM", "Saturday 2PM"]
    },
    "instagram_threads": {
        "type": "social",
        "display_name": "Instagram Threads",
        "optimal_range": (1, 2), 
        "peak_times": ["Thursday 7PM", "Friday 8PM", "Sunday 6PM"]
    }
}

class ArticleNichePostingAnalyzer:
    def __init__(self, searxng_url="https://app.legal-wires.com"):
        # Get API key from environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables. Please add it to your .env file.")
        
        self.client = OpenAI(api_key=api_key)
        self.searxng_url = searxng_url.rstrip('/')
        self.search_sources = []
        self.raw_search_data = ""

    def get_article_content(self):
        """Get article content from user input or file"""
        print("\n=== Article Input ===")
        print("Choose an option:")
        print("1. Enter text directly")
        print("2. Load from .txt file")
        
        choice = input("Enter your choice (1 or 2): ").strip()
        
        if choice == "1":
            print("\nEnter your article content (press Ctrl+D on Unix/Linux/Mac or Ctrl+Z on Windows when done):")
            try:
                lines = []
                while True:
                    try:
                        line = input()
                        lines.append(line)
                    except EOFError:
                        break
                return "\n".join(lines)
            except KeyboardInterrupt:
                print("\nInput cancelled.")
                return None
                
        elif choice == "2":
            file_path = input("Enter the path to your .txt file: ").strip()
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            except FileNotFoundError:
                print(f"Error: File '{file_path}' not found.")
                return None
            except Exception as e:
                print(f"Error reading file: {e}")
                return None
        else:
            print("Invalid choice. Please try again.")
            return self.get_article_content()

    def identify_niche(self, article_content):
        """Use OpenAI to identify the niche/topic of the article"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content analyzer. Identify the main niche/topic of the given article content. Respond with just the niche name (e.g., 'fitness', 'technology', 'cooking', 'business', 'travel', etc.)"
                    },
                    {
                        "role": "user",
                        "content": f"Identify the main niche/topic of this article:\n\n{article_content[:2000]}..."  # Limit content to avoid token limits
                    }
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            niche = response.choices[0].message.content.strip().lower()
            return niche
            
        except Exception as e:
            logger.error(f"Error identifying niche: {e}")
            return None

    def search_best_posting_times(self, niche, platform):
        """Search for best posting times for the niche and platform with enhanced queries"""
        try:
            platform_info = SUPPORTED_PLATFORMS.get(platform, {})
            platform_display = platform_info.get('display_name', platform)
            platform_type = platform_info.get('type', 'unknown')
            
            # Enhanced search queries based on platform type
            if platform_type == "long_form":
                search_queries = [
                    f"Best time to post {niche} articles on {platform_display} for maximum readership",
                    f"Optimal publishing schedule for {niche} blog posts on {platform_display}",
                    f"When to publish {niche} content on {platform_display} for high engagement",
                    f"Peak reading hours for {niche} articles on {platform_display}",
                    f"Best day and time to post {niche} blogs on {platform_display}",
                    f"{platform_display} {niche} content posting strategy for writers"
                ]
            else:  # social platforms
                search_queries = [
                    f"Best time to post {niche} content on {platform_display} for viral reach",
                    f"Optimal posting times for {niche} posts on {platform_display} algorithm",
                    f"Peak engagement hours for {niche} content on {platform_display}",
                    f"When to post {niche} on {platform_display} for maximum likes and shares",
                    f"{platform_display} {niche} posting schedule for influencers",
                    f"Best time of day to post {niche} content on {platform_display} 2024"
                ]
            
            # Store all results
            self.search_sources = []
            content_pieces = []
            
            print(f"🔍 Starting comprehensive search for {niche} content on {platform_display}...")
            
            for i, query in enumerate(search_queries, 1):
                print(f"🔍 Query {i}/6: '{query}'")
                
                params = {
                    'q': query,
                    'format': 'json',
                    'engines': 'google,bing,duckduckgo',
                    'categories': 'general',
                    'time_range': 'year'
                }
                
                try:
                    response = requests.get(f"{self.searxng_url}/search", params=params, timeout=15)
                    
                    if response.status_code == 200:
                        search_results = response.json()
                        
                        # Process results from this query
                        query_results = 0
                        for result in search_results.get('results', [])[:5]:  # Top 5 from each query
                            source_info = {
                                'title': result.get('title', 'No title'),
                                'url': result.get('url', 'No URL'),
                                'content': result.get('content', 'No content'),
                                'query_used': f"Query {i}",
                                'platform': platform_display,
                                'niche': niche
                            }
                            
                            # Avoid duplicates by checking URL
                            if not any(source['url'] == source_info['url'] for source in self.search_sources):
                                self.search_sources.append(source_info)
                                query_results += 1
                                
                                if 'content' in result and result['content']:
                                    content_pieces.append(result['content'])
                                if 'title' in result:
                                    content_pieces.append(result['title'])
                        
                        print(f"   ✅ Found {query_results} new sources")
                    else:
                        print(f"   ❌ Query failed with status {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Query error: {str(e)[:50]}...")
                    continue
                
                # Small delay between queries to avoid rate limiting
                time.sleep(1)
                
                # Stop if we have enough sources
                if len(self.search_sources) >= 15:
                    print(f"   🛑 Stopping search - enough sources collected")
                    break
            
            # Store combined content for analysis
            self.raw_search_data = " ".join(content_pieces)
            
            print(f"\n🎯 SEARCH COMPLETE:")
            print(f"   📊 Total Sources Found: {len(self.search_sources)}")
            print(f"   📝 Content Length: {len(self.raw_search_data)} characters")
            
            # Filter and prioritize sources that mention the platform specifically
            platform_specific = [s for s in self.search_sources if platform_display.lower() in s['title'].lower() or platform_display.lower() in s['content'].lower()]
            print(f"   🎯 Platform-Specific Sources: {len(platform_specific)}")
            
            return self.raw_search_data if self.raw_search_data else None
                
        except Exception as e:
            logger.error(f"Error in comprehensive search: {e}")
            return None

    def analyze_posting_times(self, search_content, niche, platform):
        """Use OpenAI to analyze the search results and determine the best posting time"""
        try:
            platform_info = SUPPORTED_PLATFORMS.get(platform, {})
            platform_display = platform_info.get('display_name', platform)
            platform_type = platform_info.get('type', 'unknown')
            
            # Enhanced prompts based on platform type
            if platform_type == "long_form":
                system_prompt = f"""You are a content strategy expert specializing in {platform_display}. Analyze the research data about {niche} content on {platform_display}.

Consider:
1. Reader behavior patterns for long-form content
2. Professional vs casual reading habits
3. When people have time for in-depth articles
4. Platform algorithm preferences
5. Competition analysis

Provide EXACTLY 2 optimal times in this format:
TIME 1: [Day] [Hour] - [Brief logical reason in 5-8 words]
TIME 2: [Day] [Hour] - [Brief logical reason in 5-8 words]

Examples:
TIME 1: Wednesday 2PM - Professionals browse during lunch break
TIME 2: Sunday 10AM - Weekend readers seek inspiration quietly

Be extremely specific and logical. No ranges, no fluff."""

            else:  # social platforms
                system_prompt = f"""You are a social media strategist expert specializing in {platform_display}. Analyze the research data about {niche} content on {platform_display}.

Consider:
1. Platform algorithm peak hours
2. User engagement patterns
3. Competition posting schedules
4. Audience demographics for {niche}
5. Mobile vs desktop usage patterns

Provide EXACTLY 2 optimal times in this format:
TIME 1: [Day] [Hour] - [Brief logical reason in 5-8 words]
TIME 2: [Day] [Hour] - [Brief logical reason in 5-8 words]

Examples:
TIME 1: Wednesday 7PM - Evening scroll time peak engagement
TIME 2: Saturday 2PM - Weekend leisure browsing increases

Be extremely specific and logical. No ranges, no fluff."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"""Analyze this data about {niche} content on {platform_display}. Think step by step about audience behavior, then give 2 precise times with short logical reasons.

Platform Type: {platform_type.title()}
Research data:
{search_content[:4000]}

Think about:
- Who consumes {niche} content on {platform_display}?
- When are they most active and engaged?
- What's their daily routine?
- When do they have time to engage with {niche} content?"""
                    }
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            best_times = response.choices[0].message.content.strip()
            return best_times
            
        except Exception as e:
            logger.error(f"Error analyzing posting times: {e}")
            return None

    def get_platform_fallback_time(self, platform, niche):
        """Get platform-specific fallback times when search fails"""
        platform_info = SUPPORTED_PLATFORMS.get(platform, {})
        peak_times = platform_info.get('peak_times', ["Weekdays 10AM-2PM"])
        
        # Select best fallback based on niche
        niche_time_mapping = {
            'business': 0,  # First peak time (usually morning/professional hours)
            'technology': 0,
            'finance': 0,
            'health': 1,    # Second peak time (usually midday)
            'fitness': 1,
            'food': 1,
            'lifestyle': 2 if len(peak_times) > 2 else 1,  # Evening times
            'entertainment': 2 if len(peak_times) > 2 else 1,
            'travel': 2 if len(peak_times) > 2 else 1
        }
        
        time_index = niche_time_mapping.get(niche.lower(), 0)
        if time_index >= len(peak_times):
            time_index = 0
            
        selected_time = peak_times[time_index]
        
        return f"TIME 1: {selected_time} - Default optimal time for {niche} content"

    def select_platform(self):
        """Let user select a platform with enhanced display"""
        print("\n=== Platform Selection ===")
        print("Available platforms:")
        
        # Group by type
        long_form = [(k, v) for k, v in SUPPORTED_PLATFORMS.items() if v['type'] == 'long_form']
        social = [(k, v) for k, v in SUPPORTED_PLATFORMS.items() if v['type'] == 'social']
        
        print("\n📖 Long-form Content Platforms:")
        platform_list = []
        for i, (platform, info) in enumerate(long_form, 1):
            print(f"  {i}. {info['display_name']}")
            platform_list.append(platform)
        
        print("\n📱 Social Media Platforms:")
        for i, (platform, info) in enumerate(social, len(long_form) + 1):
            print(f"  {i}. {info['display_name']}")
            platform_list.append(platform)
        
        while True:
            try:
                choice = int(input(f"\nSelect platform (1-{len(platform_list)}): "))
                if 1 <= choice <= len(platform_list):
                    platform = platform_list[choice - 1]
                    return platform
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")

    def run_analysis(self):
        """Main method to run the complete analysis"""
        print("=== Enhanced Multi-Platform Article Niche and Optimal Posting Time Analyzer ===")
        
        # Step 1: Get article content
        article_content = self.get_article_content()
        if not article_content:
            print("No article content provided. Exiting.")
            return
        
        print(f"\nArticle content loaded ({len(article_content)} characters)")
        
        # Step 2: Identify niche
        print("\nIdentifying article niche...")
        niche = self.identify_niche(article_content)
        if not niche:
            print("Could not identify article niche. Exiting.")
            return
            
        print(f"✓ Identified niche: {niche.title()}")
        
        # Step 3: Select platform
        platform = self.select_platform()
        platform_info = SUPPORTED_PLATFORMS[platform]
        print(f"✓ Selected platform: {platform_info['display_name']} ({platform_info['type'].title()})")
        
        # Step 4: Search for best posting times
        print(f"\nSearching for best posting times for {niche} content on {platform_info['display_name']}...")
        search_results = self.search_best_posting_times(niche, platform)
        
        if not search_results:
            print("Could not find posting time data. Using fallback times.")
            best_time = self.get_platform_fallback_time(platform, niche)
        else:
            print("✓ Found posting time research data")
            
            # Step 5: Analyze and get best posting time
            print("\nAnalyzing data to determine optimal posting time...")
            best_time = self.analyze_posting_times(search_results, niche, platform)
            
            if not best_time:
                print("Could not analyze posting times. Using fallback.")
                best_time = self.get_platform_fallback_time(platform, niche)
        
        # Display results
        print("\n" + "="*70)
        print("🔍 COMPREHENSIVE SEARCH SOURCES ANALYZED")
        print("="*70)
        
        if self.search_sources:
            # Show platform-specific sources first
            platform_display = platform_info['display_name']
            platform_specific = [s for s in self.search_sources if platform_display.lower() in s['title'].lower() or platform_display.lower() in s['content'].lower()]
            other_sources = [s for s in self.search_sources if s not in platform_specific]
            
            print(f"🎯 PLATFORM-SPECIFIC SOURCES ({len(platform_specific)} found):")
            for i, source in enumerate(platform_specific[:3], 1):
                print(f"{i}. {source['title']}")
                print(f"   URL: {source['url']}")
                print(f"   Used: {source.get('query_used', 'N/A')}")
                print(f"   Content: {source['content'][:250]}...")
                print()
            
            print(f"📊 OTHER RELEVANT SOURCES ({len(other_sources)} found):")
            for i, source in enumerate(other_sources[:2], 1):
                print(f"{i}. {source['title']}")
                print(f"   URL: {source['url']}")
                print(f"   Used: {source.get('query_used', 'N/A')}")
                print(f"   Content: {source['content'][:200]}...")
                print()
            
            print("\n" + "="*70)
            print("📊 RAW SEARCH DATA SAMPLE")
            print("="*70)
            print(f"Total Data: {len(self.raw_search_data)} characters")
            if self.raw_search_data:
                print(f"Sample: {self.raw_search_data[:600]}...")
            print()
        
        print("\n" + "="*70)
        print("🎯 AI ANALYSIS RESULTS")
        print("="*70)
        print(f"Article Niche: {niche.title()}")
        print(f"Platform: {platform_info['display_name']} ({platform_info['type'].title()})")
        print(f"Sources Analyzed: {len(self.search_sources)}")
        print()
        print(f"{best_time}")
        print("="*70)


def main():
    try:
        analyzer = ArticleNichePostingAnalyzer()
        analyzer.run_analysis()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("\nPlease create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your_api_key_here")
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

