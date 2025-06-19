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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_PLATFORMS = {
    "instagram": (15, 30),
    "tiktok": (3, 6),
    "linkedin": (3, 5),
    "twitter": (1, 2),
    "x": (1, 2),
    "facebook": (0, 2),
    "youtube": (3, 5),
    "pinterest": (2, 5),
}

class ArticleNicheHashtagAnalyzer:
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

    def read_article(self, filepath):
        """Read article content from file"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            return ""

    def get_niches(self, text):
        """Extract top 2-3 niches from article using improved GPT prompting"""
        # Enhanced prompt for better niche extraction
        prompt = (
            "Analyze the following content and identify the top 2-3 most specific and relevant niches/categories "
            "that best describe the main topics and themes. Focus on:\n"
            "1. The primary subject matter and domain\n"
            "2. The target audience or demographic\n"
            "3. The specific sub-category or specialization\n\n"
            "Return only niche names in single-word or hyphenated format (e.g., 'fitness', 'tech-gadgets', 'food-recipes'). "
            "Avoid generic terms like 'general' or 'content'. Be specific and actionable for social media optimization.\n"
            "Return 2-3 niches separated by commas.\n\n"
            f"Content to analyze:\n{text[:4000]}"
        )
        
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=150
            )
            
            # Parse and clean the response
            niches_text = resp.choices[0].message.content.strip()
            niches = [
                n.strip().lower().replace(" ", "-").replace("_", "-") 
                for n in niches_text.split(",")
            ]
            
            # Filter out empty strings and generic terms
            filtered_niches = []
            generic_terms = {"general", "content", "post", "social", "media", "marketing"}
            
            for niche in niches:
                if niche and len(niche) > 2 and niche not in generic_terms:
                    filtered_niches.append(niche)
            
            # Ensure we have at least 2 niches, add fallbacks if needed
            if len(filtered_niches) < 2:
                # Try to extract keywords from the text as fallback niches
                words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
                word_freq = {}
                for word in words:
                    if word not in generic_terms and len(word) > 3:
                        word_freq[word] = word_freq.get(word, 0) + 1
                
                # Add most frequent meaningful words as backup niches
                backup_niches = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]
                for word, freq in backup_niches:
                    if len(filtered_niches) < 3 and word not in filtered_niches:
                        filtered_niches.append(word)
            
            # Return top 2-3 niches
            result_niches = filtered_niches[:3] if len(filtered_niches) >= 3 else filtered_niches[:2]
            
            # If still no niches, use safe defaults
            if not result_niches:
                result_niches = ["lifestyle", "content"]
            
            logger.info(f"🎯 Extracted niches: {result_niches}")
            return result_niches
            
        except Exception as e:
            logger.error(f"Error getting niches: {e}")
            # Fallback to simple keyword extraction
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
            word_freq = {}
            for word in words:
                if len(word) > 3:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            if word_freq:
                top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:2]
                return [word for word, freq in top_words]
            else:
                return ["lifestyle", "content"]

    def search_best_hashtag_url(self, niche):
        """Generate multiple hashtag URLs for better coverage"""
        urls = []
        
        # Try different formats for better success rate
        hashtag_sites = [
            f"https://best-hashtags.com/hashtag/{quote(niche)}/",
            f"https://all-hashtag.com/hashtag/{quote(niche)}.html",
            f"https://www.all-hashtag.com/hashtag/{quote(niche)}.html"
        ]
        
        return hashtag_sites

    def scrape_hashtags_from_multiple_sources(self, niche):
        """Scrape hashtags from multiple sources for better coverage"""
        logger.info(f"📋 Searching hashtags for niche: {niche}")
        
        all_hashtag_text = ""
        
        # Method 1: Try hashtag websites
        hashtag_urls = self.search_best_hashtag_url(niche)
        
        for url in hashtag_urls:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
                
                response = requests.get(url, timeout=10, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # Look for hashtag patterns in the text
                    text_content = soup.get_text()
                    hashtags = re.findall(r'#\w+', text_content)
                    
                    if hashtags:
                        all_hashtag_text += " ".join(hashtags) + " "
                        logger.info(f"✅ Found hashtags from: {url}")
                        break  # If we found hashtags, no need to try other URLs
                    
            except Exception as e:
                logger.debug(f"Failed to scrape {url}: {e}")
                continue
        
        # Method 2: Generate hashtags using AI if scraping failed
        if not all_hashtag_text.strip():
            logger.info(f"🤖 Generating hashtags for '{niche}' using AI...")
            all_hashtag_text = self.generate_hashtags_with_ai(niche)
        
        return all_hashtag_text

    def generate_hashtags_with_ai(self, niche):
        """Generate relevant hashtags using AI when scraping fails"""
        prompt = f"""
        Generate 20-30 relevant and popular hashtags for the niche: "{niche}"
        
        Include:
        1. Main niche hashtags
        2. Related sub-niches
        3. Popular trending hashtags
        4. Community hashtags
        5. Engagement hashtags
        
        Format: Return hashtags with # symbol, separated by spaces.
        
        Example for 'fitness': #fitness #workout #gym #health #motivation #fitlife #exercise #training #bodybuilding #wellness
        
        Generate hashtags for: {niche}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=300
            )
            
            generated_hashtags = response.choices[0].message.content.strip()
            logger.info(f"✅ Generated AI hashtags for: {niche}")
            return generated_hashtags
            
        except Exception as e:
            logger.error(f"Error generating hashtags with AI: {e}")
            # Fallback to basic hashtags
            basic_hashtags = [
                f"#{niche.replace('-', '').replace('_', '')}",
                f"#{niche.replace('-', '').replace('_', '')}life",
                "#trending", "#viral", "#content", "#social", "#engagement"
            ]
            return " ".join(basic_hashtags)

    def analyze_hashtags(self, hashtag_text, platform):
        """Analyze and select optimal hashtags for the platform with improved logic"""
        platform_ranges = SUPPORTED_PLATFORMS.get(platform.lower(), (3, 5))
        opt_min, opt_max = platform_ranges
        
        # Enhanced prompt for better hashtag selection
        prompt = (
            f"From the following hashtag content, select the top {opt_min}-{opt_max} hashtags that "
            f"would maximize engagement and reach on {platform}. Consider:\n\n"
            f"PLATFORM-SPECIFIC GUIDELINES for {platform.upper()}:\n"
            f"• Target range: {opt_min}-{opt_max} hashtags\n"
            f"• Mix popular (high volume) with niche (targeted) hashtags\n"
            f"• Avoid banned or shadowbanned hashtags\n"
            f"• Focus on hashtags with active communities\n"
            f"• Include trending and evergreen hashtags\n\n"
            f"SELECTION CRITERIA:\n"
            f"1. Relevance to content (high priority)\n"
            f"2. Engagement potential on {platform}\n"
            f"3. Community size and activity\n"
            f"4. Trending status\n"
            f"5. Competition level (not oversaturated)\n\n"
            f"HASHTAG CONTENT:\n{hashtag_text[:3000]}\n\n"
            f"Return ONLY the selected hashtag names separated by commas (NO # symbols).\n"
            f"Focus on hashtags that will boost discoverability and engagement."
        )
        
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {
                        "role": "system", 
                        "content": f"You are a social media expert specializing in {platform} hashtag optimization. Select the most effective hashtags for maximum engagement."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result = resp.choices[0].message.content.strip()
            
            # Clean up the result
            hashtags = [tag.strip().replace('#', '') for tag in result.split(',')]
            hashtags = [tag for tag in hashtags if tag and len(tag) > 1 and len(tag) < 30]
            
            # Ensure we have the right number of hashtags
            if len(hashtags) < opt_min:
                # Add platform-specific fallback hashtags
                platform_fallbacks = self.get_platform_fallback_hashtags(platform)
                for fallback in platform_fallbacks:
                    if len(hashtags) >= opt_min:
                        break
                    if fallback not in hashtags:
                        hashtags.append(fallback)
            
            # Limit to maximum
            hashtags = hashtags[:opt_max]
            
            logger.info(f"✅ Selected {len(hashtags)} optimized hashtags for {platform}")
            return ', '.join(hashtags)
            
        except Exception as e:
            logger.error(f"Error analyzing hashtags: {e}")
            # Return platform-specific fallbacks
            fallback_hashtags = self.get_platform_fallback_hashtags(platform)
            return ', '.join(fallback_hashtags[:opt_max])

    def get_platform_fallback_hashtags(self, platform):
        """Get platform-specific fallback hashtags"""
        fallback_hashtags = {
            "instagram": [
                "instagood", "photooftheday", "love", "beautiful", "happy", 
                "picoftheday", "follow", "instadaily", "fashion", "art",
                "photography", "nature", "travel", "style", "life"
            ],
            "facebook": [
                "facebook", "social", "community", "share", "connect"
            ],
            "linkedin": [
                "linkedin", "professional", "business", "career", "networking",
                "leadership", "industry", "success", "growth", "innovation"
            ],
            "twitter": [
                "twitter", "trending", "news", "discussion", "thoughts"
            ],
            "x": [
                "trending", "viral", "discussion", "thoughts", "community"
            ],
            "tiktok": [
                "tiktok", "fyp", "foryou", "viral", "trending", "dance",
                "music", "entertainment", "funny", "creative"
            ],
            "pinterest": [
                "pinterest", "inspiration", "ideas", "diy", "creative",
                "design", "home", "fashion", "recipes", "art"
            ],
            "youtube": [
                "youtube", "video", "content", "subscribe", "creator",
                "tutorial", "entertainment", "education", "music", "gaming"
            ]
        }
        
        return fallback_hashtags.get(platform.lower(), [
            "content", "social", "trending", "community", "engagement"
        ])

    def process(self, filepath, platform):
        """Main processing function with improved hashtag retrieval"""
        logger.info("🚀 Starting hashtag analysis...")
        
        # Step 1: Read article
        logger.info("📖 Reading article...")
        text = self.read_article(filepath)
        if not text:
            logger.error("Failed to read article content")
            return

        # Step 2: Find niches with improved extraction
        logger.info("🎯 Identifying niches...")
        niches = self.get_niches(text)
        logger.info(f"✅ Identified niches: {niches}")

        # Step 3: Collect hashtags for each niche using multiple methods
        logger.info("🔄 Collecting hashtags from multiple sources...")
        
        all_hashtag_text = ""

        # Use ThreadPoolExecutor for parallel hashtag collection
        with ThreadPoolExecutor(max_workers=len(niches)) as executor:
            # Submit hashtag collection tasks
            hashtag_futures = {
                executor.submit(self.scrape_hashtags_from_multiple_sources, niche): niche 
                for niche in niches
            }

            # Collect hashtag results
            for future in as_completed(hashtag_futures):
                niche = hashtag_futures[future]
                try:
                    hashtag_text = future.result()
                    if hashtag_text:
                        all_hashtag_text += hashtag_text + "\n"
                        logger.info(f"✅ Hashtags collected for: {niche}")
                    else:
                        logger.warning(f"⚠️ No hashtags found for: {niche}")
                except Exception as e:
                    logger.error(f"❌ Failed hashtag collection for {niche}: {e}")

        # Step 4: If no hashtags found, generate them using AI
        if not all_hashtag_text.strip():
            logger.info("🤖 No hashtags scraped, generating with AI...")
            for niche in niches:
                ai_hashtags = self.generate_hashtags_with_ai(niche)
                all_hashtag_text += ai_hashtags + "\n"

        # Step 5: Analyze and select optimal hashtags
        logger.info("🧠 Analyzing optimal hashtags...")
        best_hashtags = self.analyze_hashtags(all_hashtag_text, platform)

        # Display results
        print("\n" + "="*80)
        print("🎯 HASHTAG ANALYSIS RESULTS")
        print("="*80)
        
        print(f"\n📊 Identified Niches:")
        for i, niche in enumerate(niches, 1):
            print(f"  {i}. {niche}")
        
        print(f"\n🏷️ Optimized Hashtags for {platform.title()}:")
        hashtag_list = best_hashtags.replace(', ', ' #').replace(',', ' #')
        if not hashtag_list.startswith('#'):
            hashtag_list = '#' + hashtag_list
        print(f"  {hashtag_list}")

        print(f"\n💡 Platform Optimization Tips for {platform.title()}:")
        platform_tips = {
            "instagram": [
                "Use a mix of popular and niche-specific hashtags",
                "Place hashtags in the first comment for cleaner posts",
                "Monitor hashtag performance with Instagram Insights",
                "Avoid banned or flagged hashtags",
                "Research trending hashtags in your niche"
            ],
            "tiktok": [
                "Use trending hashtags like #fyp and #foryou",
                "Mix viral hashtags with niche-specific ones",
                "Keep hashtags relevant to your content",
                "Check TikTok's Discover page for trending tags",
                "Use hashtags that match current trends"
            ],
            "linkedin": [
                "Use professional and industry-specific hashtags",
                "Mix broad professional tags with niche expertise tags",
                "Engage with hashtag communities",
                "Use hashtags that reflect your professional brand",
                "Focus on industry-relevant trending topics"
            ],
            "twitter": [
                "Use 1-2 relevant hashtags maximum",
                "Join trending conversations when relevant",
                "Create unique branded hashtags for campaigns",
                "Monitor hashtag analytics",
                "Participate in hashtag communities"
            ],
            "x": [
                "Use 1-2 relevant hashtags maximum", 
                "Join trending conversations when relevant",
                "Create unique branded hashtags for campaigns",
                "Monitor hashtag analytics",
                "Engage with trending topics"
            ],
            "facebook": [
                "Use hashtags sparingly (1-2 maximum)",
                "Focus on local and community hashtags",
                "Use hashtags that encourage engagement",
                "Research Facebook hashtag performance",
                "Join relevant Facebook groups"
            ],
            "pinterest": [
                "Use descriptive, searchable hashtags",
                "Mix broad and specific hashtags",
                "Use hashtags that describe the image content",
                "Research Pinterest trending topics",
                "Focus on seasonal and trending hashtags"
            ],
            "youtube": [
                "Use hashtags in video descriptions",
                "Focus on searchable, descriptive hashtags",
                "Use hashtags that match your video content",
                "Research YouTube trending hashtags",
                "Include hashtags in video titles when relevant"
            ]
        }
        
        tips = platform_tips.get(platform.lower(), [
            "Research platform-specific hashtag best practices",
            "Monitor hashtag performance and engagement",
            "Use relevant, targeted hashtags",
            "Stay updated with trending topics"
        ])
        
        for tip in tips:
            print(f"  • {tip}")
        
        print("\n" + "="*80)
        print("✅ Analysis Complete!")
        print("="*80)

        return {
            "niches": niches,
            "hashtags": best_hashtags,
            "platform": platform
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhanced Hashtag Analyzer for Social Media Optimization")
    parser.add_argument("filepath", type=str, help="Path to the .txt file containing the article")
    parser.add_argument("platform", type=str, help="Social media platform")
    parser.add_argument("--api_key", type=str, help="OpenAI API key (optional, will use OPENAI_API_KEY env var if not provided)")
    
    args = parser.parse_args()

    if args.platform.lower() not in SUPPORTED_PLATFORMS:
        print(f"❌ Unsupported platform. Choose: {', '.join(SUPPORTED_PLATFORMS.keys())}")
        sys.exit(1)

    try:
        analyzer = ArticleNicheHashtagAnalyzer(api_key=args.api_key)
        analyzer.process(args.filepath, args.platform)
    except ValueError as e:
        print(f"❌ {e}")
        print("\n💡 To set the environment variable:")
        print("   Linux/Mac: export OPENAI_API_KEY='your-api-key-here'")
        print("   Windows:   set OPENAI_API_KEY=your-api-key-here")
        sys.exit(1)