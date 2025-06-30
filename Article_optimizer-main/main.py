#!/usr/bin/env python3
"""
Enhanced Multi-Platform Article Optimization Pipeline
Supports: Medium, Blogger, LinkedIn, X.com, Facebook, Instagram Threads
WITH ROBUST FALLBACK MECHANISMS FOR ALL COMPONENTS
NOW WITH INTEGRATED POST COMPILER FOR FINAL CONTENT
MULTI-USER SUPPORT WITH UUID-BASED FILE MANAGEMENT
"""

import os
import sys
import json
import logging
import asyncio
import tempfile
import base64
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
import re
from datetime import datetime
import random
import time

# Import our custom modules
from timing import ArticleNichePostingAnalyzer
from hashkey import ArticleNicheHashtagSEOAnalyzer
from profiles import CombinedSocialMediaPipeline  # Updated import
from citationverifier import CitationVerifier
from imgen import client as openai_client
from compiler import PlatformPostCompiler  # NEW: Import the compiler

# Cloudinary setup
import cloudinary
import cloudinary.uploader

# Configure Cloudinary
cloudinary.config(
    cloud_name="dmz4lknv4",
    api_key="666561538621679",
    api_secret="nGMt1pNjjiAtVVYzK2Sp2FVvcqA"
)

# Production output directory - shared across all users
PRODUCTION_OUTPUT_DIR = "shared_optimization_results"

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('article_optimizer.log'),
        # Remove console handler for production
    ]
)
logger = logging.getLogger('article_optimizer')

class MultiPlatformOptimizer:
    """Enhanced class for multi-platform article optimization with robust fallbacks and compiler integration"""
    
    # Platform configuration with specific rules
    PLATFORMS = {
        "medium": {
            "name": "Medium",
            "use_citations": True,
            "max_length": None,  # No specific limit for long-form
            "hashtag_count": (3, 5),
            "image_count": 2,
            "content_style": "long_form"
        },
        "blogger": {
            "name": "Blogger",
            "use_citations": True,
            "max_length": None,  # No specific limit for long-form
            "hashtag_count": (3, 5),
            "image_count": 2,
            "content_style": "long_form"
        },
        "linkedin": {
            "name": "LinkedIn",
            "use_citations": False,
            "max_length": 3000,  # LinkedIn post limit
            "hashtag_count": (3, 5),
            "image_count": 1,
            "content_style": "professional"
        },
        "x.com": {
            "name": "X.com (Twitter)",
            "use_citations": False,
            "max_length": 280,  # Twitter character limit
            "hashtag_count": (1, 3),
            "image_count": 1,
            "content_style": "microblog"
        },
        "facebook": {
            "name": "Facebook",
            "use_citations": False,
            "max_length": 2000,  # Recommended for better engagement
            "hashtag_count": (2, 4),
            "image_count": 1,
            "content_style": "social"
        },
        "instagram_threads": {
            "name": "Instagram Threads",
            "use_citations": False,
            "max_length": 500,  # Threads character limit
            "hashtag_count": (2, 4),
            "image_count": 1,
            "content_style": "casual"
        }
    }
    
    # FALLBACK DATA DICTIONARIES
    FALLBACK_HASHTAGS = {
        "technology": ["#tech", "#innovation", "#digital", "#future", "#AI"],
        "business": ["#business", "#entrepreneur", "#strategy", "#leadership", "#growth"],
        "health": ["#health", "#wellness", "#fitness", "#nutrition", "#medical"],
        "finance": ["#finance", "#investing", "#money", "#economics", "#fintech"],
        "education": ["#education", "#learning", "#knowledge", "#skills", "#development"],
        "marketing": ["#marketing", "#branding", "#content", "#social", "#advertising"],
        "lifestyle": ["#lifestyle", "#life", "#inspiration", "#motivation", "#tips"],
        "travel": ["#travel", "#adventure", "#explore", "#wanderlust", "#journey"],
        "food": ["#food", "#cooking", "#recipe", "#cuisine", "#dining"],
        "sports": ["#sports", "#fitness", "#training", "#athletic", "#competition"],
        "entertainment": ["#entertainment", "#movies", "#music", "#culture", "#arts"],
        "science": ["#science", "#research", "#discovery", "#innovation", "#study"],
        "politics": ["#politics", "#government", "#policy", "#democracy", "#society"],
        "environment": ["#environment", "#sustainability", "#green", "#climate", "#eco"],
        "general": ["#content", "#blog", "#article", "#trending", "#share"]
    }
    
    FALLBACK_SEO_KEYWORDS = {
        "technology": ["artificial intelligence", "machine learning", "software development", "digital transformation", "cybersecurity", "cloud computing", "data analytics", "automation", "blockchain", "IoT"],
        "business": ["business strategy", "entrepreneurship", "leadership skills", "market analysis", "customer acquisition", "revenue growth", "business development", "management", "productivity", "innovation"],
        "health": ["health tips", "wellness lifestyle", "medical research", "nutrition facts", "fitness routine", "mental health", "healthcare", "disease prevention", "healthy living", "medical advice"],
        "finance": ["investment strategies", "financial planning", "stock market", "cryptocurrency", "personal finance", "wealth building", "budgeting", "retirement planning", "economic trends", "financial literacy"],
        "education": ["online learning", "educational technology", "skill development", "career advancement", "professional training", "academic research", "teaching methods", "learning strategies", "certification", "knowledge management"],
        "marketing": ["digital marketing", "content strategy", "social media marketing", "SEO optimization", "brand building", "customer engagement", "marketing automation", "lead generation", "conversion optimization", "influencer marketing"],
        "lifestyle": ["life improvement", "personal development", "work life balance", "self care", "productivity tips", "mindfulness", "happiness", "goal setting", "time management", "life hacks"],
        "travel": ["travel destinations", "vacation planning", "budget travel", "travel tips", "adventure travel", "cultural experiences", "travel photography", "travel guides", "solo travel", "family travel"],
        "food": ["healthy recipes", "cooking tips", "food photography", "restaurant reviews", "meal planning", "nutrition guide", "culinary arts", "food trends", "diet plans", "cooking techniques"],
        "sports": ["sports training", "athletic performance", "fitness goals", "sports nutrition", "exercise routines", "team sports", "individual sports", "sports psychology", "injury prevention", "sports equipment"],
        "entertainment": ["movie reviews", "music trends", "celebrity news", "entertainment industry", "cultural events", "arts and culture", "gaming", "streaming", "concerts", "festivals"],
        "science": ["scientific research", "medical breakthroughs", "space exploration", "environmental science", "physics discoveries", "chemistry innovations", "biology studies", "research methodology", "scientific method", "academic publications"],
        "politics": ["political analysis", "government policy", "election coverage", "political commentary", "public affairs", "legislation", "political trends", "democracy", "civic engagement", "political science"],
        "environment": ["climate change", "sustainability practices", "renewable energy", "environmental conservation", "green technology", "eco friendly", "carbon footprint", "environmental science", "conservation efforts", "sustainable living"],
        "general": ["trending topics", "current events", "popular culture", "social trends", "viral content", "breaking news", "public interest", "community", "discussion", "awareness"]
    }
    
    FALLBACK_PROFILES = {
        "linkedin": {
            "tagging_accounts": [
                {"handle": "@linkedin", "description": "Official LinkedIn account for professional networking"},
                {"handle": "@microsoftlinkedin", "description": "Microsoft's LinkedIn for business insights"},
                {"handle": "@linkedinlearning", "description": "LinkedIn Learning for professional development"}
            ]
        },
        "x.com": {
            "tagging_accounts": [
                {"handle": "@x", "description": "Official X platform account"},
                {"handle": "@elonmusk", "description": "Tech leader and entrepreneur"},
                {"handle": "@sundarpichai", "description": "Google CEO and tech leader"}
            ]
        },
        "facebook": {
            "tagging_accounts": [
                {"handle": "@facebook", "description": "Official Facebook page"},
                {"handle": "@meta", "description": "Meta's official business page"},
                {"handle": "@techcrunch", "description": "Technology news and insights"}
            ]
        },
        "instagram_threads": {
            "tagging_accounts": [
                {"handle": "@threads", "description": "Official Threads account"},
                {"handle": "@instagram", "description": "Instagram official account"},
                {"handle": "@meta", "description": "Meta's social platform"}
            ]
        },
        "medium": {
            "tagging_accounts": [
                {"handle": "@medium", "description": "Official Medium publication"},
                {"handle": "@towardsdatascience", "description": "Data science and AI publication"},
                {"handle": "@freecodecamp", "description": "Programming and tech education"}
            ]
        },
        "blogger": {
            "tagging_accounts": [
                {"handle": "@blogger", "description": "Google's Blogger platform"},
                {"handle": "@google", "description": "Google's official blog"},
                {"handle": "@wordpress", "description": "WordPress blogging platform"}
            ]
        }
    }
    
    FALLBACK_POSTING_TIMES = {
        "medium": "Tuesday 2PM - Professional lunch break reading",
        "blogger": "Wednesday 10AM - Morning research time",
        "linkedin": "Wednesday 8AM - Professional morning routine",
        "x.com": "Wednesday 12PM - Midday engagement peak",
        "facebook": "Wednesday 3PM - Afternoon social browsing",
        "instagram_threads": "Thursday 7PM - Evening engagement time"
    }
    
    def __init__(self, user_id: str = None):
        """Initialize the enhanced pipeline with all required components including compiler and user ID"""
        self.user_id = user_id or str(uuid.uuid4())
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        logger.info(f"🚀 Initializing Multi-Platform Article Optimizer with Compiler for user {self.user_id}...")
        
        # Ensure production output directory exists
        os.makedirs(PRODUCTION_OUTPUT_DIR, exist_ok=True)
        
        # Initialize all analyzers with error handling
        try:
            self.timing_analyzer = ArticleNichePostingAnalyzer()
            logger.info("✅ Timing analyzer initialized")
        except Exception as e:
            logger.warning(f"⚠️ Timing analyzer failed: {e}")
            self.timing_analyzer = None
        
        try:
            self.hashtag_analyzer = ArticleNicheHashtagSEOAnalyzer()
            logger.info("✅ Hashtag analyzer initialized")
        except Exception as e:
            logger.warning(f"⚠️ Hashtag analyzer failed: {e}")
            self.hashtag_analyzer = None
        
        try:
            self.profile_processor = CombinedSocialMediaPipeline()
            logger.info("✅ Profile processor initialized")
        except Exception as e:
            logger.warning(f"⚠️ Profile processor failed: {e}")
            self.profile_processor = None
        
        try:
            self.citation_verifier = CitationVerifier()
            logger.info("✅ Citation verifier initialized")
        except Exception as e:
            logger.warning(f"⚠️ Citation verifier failed: {e}")
            self.citation_verifier = None
        
        # NEW: Initialize the post compiler
        try:
            self.post_compiler = PlatformPostCompiler()
            logger.info("✅ Post compiler initialized")
        except Exception as e:
            logger.warning(f"⚠️ Post compiler failed: {e}")
            self.post_compiler = None
        
        # Results storage
        self.results = {}
        
        logger.info(f"🎯 Multi-platform optimizer initialization complete with compiler support for user {self.user_id}")

    def get_article_from_file(self, file_path: str) -> str:
        """Get article content from .txt file (production version - no user interaction)"""
        logger.info(f"📁 Loading article from file: {file_path}")
        
        try:
            # Handle quoted paths
            if file_path.startswith('"') and file_path.endswith('"'):
                file_path = file_path[1:-1]
            elif file_path.startswith("'") and file_path.endswith("'"):
                file_path = file_path[1:-1]
            
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File '{file_path}' not found")
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                raise ValueError("File is empty")
            
            logger.info(f"✅ Article loaded successfully ({len(content)} characters)")
            return content
            
        except Exception as e:
            logger.error(f"❌ Error reading file: {e}")
            raise

    def get_selected_platforms(self, platforms_input: str) -> List[str]:
        """Parse platform selection from input string (production version)"""
        logger.info(f"🎯 Parsing platform selection: {platforms_input}")
        
        platforms_list = list(self.PLATFORMS.keys())
        
        try:
            # Handle "all" selection
            if platforms_input.lower().strip() in ['all', 'a']:
                logger.info("✅ Selected: All Platforms")
                return platforms_list
            
            # Parse comma-separated indices or names
            selections = [x.strip() for x in platforms_input.split(',')]
            selected_platforms = []
            
            for selection in selections:
                # Try to parse as index
                try:
                    index = int(selection)
                    if 1 <= index <= len(platforms_list):
                        platform_key = platforms_list[index - 1]
                        selected_platforms.append(platform_key)
                    else:
                        raise ValueError(f"Invalid platform number: {index}")
                except ValueError:
                    # Try to parse as platform name/key
                    selection_lower = selection.lower()
                    found = False
                    for platform_key in platforms_list:
                        if (platform_key.lower() == selection_lower or 
                            self.PLATFORMS[platform_key]['name'].lower() == selection_lower):
                            selected_platforms.append(platform_key)
                            found = True
                            break
                    if not found:
                        raise ValueError(f"Unknown platform: {selection}")
            
            if selected_platforms:
                platform_names = [self.PLATFORMS[p]['name'] for p in selected_platforms]
                logger.info(f"✅ Selected platforms: {', '.join(platform_names)}")
                return selected_platforms
            else:
                raise ValueError("No valid platforms selected")
                
        except Exception as e:
            logger.error(f"❌ Invalid platform selection: {e}")
            raise

    def get_image_platforms(self, image_platforms_input: str, selected_platforms: List[str]) -> List[str]:
        """Parse image platform selection from input string (production version)"""
        logger.info(f"🖼️ Parsing image platform selection: {image_platforms_input}")
        
        try:
            # Handle skip option
            if image_platforms_input.lower().strip() in ['none', 'n', 'skip', 's']:
                logger.info("✅ Skipping image generation")
                return []
            
            # Handle "all" selection
            if image_platforms_input.lower().strip() in ['all', 'a']:
                logger.info("✅ Generating images for all selected platforms")
                return selected_platforms
            
            # Parse similar to platform selection
            selections = [x.strip() for x in image_platforms_input.split(',')]
            image_platforms = []
            
            for selection in selections:
                try:
                    index = int(selection)
                    if 1 <= index <= len(selected_platforms):
                        platform_key = selected_platforms[index - 1]
                        image_platforms.append(platform_key)
                    else:
                        raise ValueError(f"Invalid platform number: {index}")
                except ValueError:
                    # Try to parse as platform name/key
                    selection_lower = selection.lower()
                    found = False
                    for platform_key in selected_platforms:
                        if (platform_key.lower() == selection_lower or 
                            self.PLATFORMS[platform_key]['name'].lower() == selection_lower):
                            image_platforms.append(platform_key)
                            found = True
                            break
                    if not found:
                        raise ValueError(f"Unknown platform: {selection}")
            
            if image_platforms:
                platform_names = [self.PLATFORMS[p]['name'] for p in image_platforms]
                logger.info(f"✅ Image generation for: {', '.join(platform_names)}")
                return image_platforms
            else:
                raise ValueError("No valid platforms selected for images")
                
        except Exception as e:
            logger.error(f"❌ Invalid image platform selection: {e}")
            raise

    def parse_compilation_choice(self, compilation_input: str) -> bool:
        """Parse compilation choice from input string (production version)"""
        logger.info(f"📝 Parsing compilation choice: {compilation_input}")
        
        try:
            choice = compilation_input.lower().strip()
            
            if choice in ['y', 'yes', 'true', '1']:
                logger.info("✅ Final post compilation will be included")
                return True
            elif choice in ['n', 'no', 'false', '0']:
                logger.info("⏭️ Skipping final post compilation")
                return False
            else:
                raise ValueError(f"Invalid compilation choice: {compilation_input}")
                
        except Exception as e:
            logger.error(f"❌ Invalid compilation choice: {e}")
            raise

    # [Keep all existing methods unchanged: detect_niche_with_fallback, generate_fallback_seo_and_hashtags, 
    # generate_fallback_profiles, _get_all_profiles_with_fallback, _generate_seo_and_hashtags_with_fallback,
    # _extract_citations_with_fallback, _get_optimal_times_with_fallback, gather_base_data,
    # optimize_content_for_platform, _manual_content_optimization, _get_platform_hashtags_with_fallback,
    # _get_platform_profiles_with_fallback, _create_platform_prompt, generate_images_for_platforms,
    # identify_key_entities_for_visualization, _parse_entities, generate_single_image,
    # _create_realistic_image_prompt, upload_to_cloudinary]

    def detect_niche_with_fallback(self, article_content: str) -> str:
        """Detect the niche/category of the article content with fallback"""
        logger.info("🔍 Detecting article niche...")
        
        try:
            if self.timing_analyzer:
                niche = self.timing_analyzer.identify_niche(article_content)
                if niche and niche.strip():
                    logger.info(f"✅ Detected niche: {niche}")
                    return niche.lower().strip()
        except Exception as e:
            logger.warning(f"⚠️ Primary niche detection failed: {e}")
        
        # Fallback: keyword-based niche detection
        try:
            logger.info("🔄 Using fallback niche detection...")
            content_lower = article_content.lower()
            
            # Check for keyword patterns
            niche_keywords = {
                "technology": ["ai", "artificial intelligence", "software", "app", "tech", "digital", "algorithm", "data", "computer", "programming"],
                "business": ["business", "company", "startup", "entrepreneur", "market", "sales", "revenue", "profit", "strategy", "leadership"],
                "health": ["health", "medical", "doctor", "disease", "treatment", "wellness", "fitness", "nutrition", "medicine", "hospital"],
                "finance": ["money", "investment", "stock", "financial", "bank", "economy", "trading", "cryptocurrency", "bitcoin", "finance"],
                "education": ["education", "learning", "school", "university", "student", "teacher", "course", "knowledge", "skill", "training"],
                "lifestyle": ["lifestyle", "life", "personal", "self", "motivation", "inspiration", "happiness", "relationship", "family", "home"],
                "travel": ["travel", "trip", "vacation", "journey", "destination", "hotel", "flight", "tourism", "adventure", "explore"],
                "food": ["food", "recipe", "cooking", "restaurant", "meal", "cuisine", "ingredient", "chef", "dining", "nutrition"],
                "sports": ["sport", "game", "player", "team", "competition", "athletic", "training", "fitness", "exercise", "championship"]
            }
            
            scores = {}
            for niche, keywords in niche_keywords.items():
                score = sum(1 for keyword in keywords if keyword in content_lower)
                if score > 0:
                    scores[niche] = score
            
            if scores:
                detected_niche = max(scores, key=scores.get)
                logger.info(f"✅ Fallback detected niche: {detected_niche}")
                return detected_niche
            
        except Exception as e:
            logger.warning(f"⚠️ Fallback niche detection failed: {e}")
        
        # Final fallback
        logger.info("🔄 Using default niche: general")
        return "general"

    def generate_fallback_seo_and_hashtags(self, niche: str, platform_key: str) -> Dict[str, Any]:
        """Generate fallback SEO keywords and hashtags"""
        logger.info(f"🔄 Generating fallback SEO and hashtags for {niche}")
        
        platform_config = self.PLATFORMS[platform_key]
        min_tags, max_tags = platform_config['hashtag_count']
        
        # Get hashtags
        base_hashtags = self.FALLBACK_HASHTAGS.get(niche, self.FALLBACK_HASHTAGS["general"])
        general_hashtags = self.FALLBACK_HASHTAGS["general"]
        
        # Combine and randomize
        all_hashtags = list(set(base_hashtags + general_hashtags))
        random.shuffle(all_hashtags)
        selected_hashtags = all_hashtags[:max_tags]
        
        # Get SEO keywords
        base_keywords = self.FALLBACK_SEO_KEYWORDS.get(niche, self.FALLBACK_SEO_KEYWORDS["general"])
        general_keywords = self.FALLBACK_SEO_KEYWORDS["general"]
        
        all_keywords = list(set(base_keywords + general_keywords))
        random.shuffle(all_keywords)
        selected_keywords = all_keywords[:15]
        
        return {
            'seo_keywords': selected_keywords,
            'hashtags': selected_hashtags
        }

    def generate_fallback_profiles(self, platform_key: str, niche: str) -> Dict[str, Any]:
        """Generate fallback profiles for platform"""
        logger.info(f"🔄 Generating fallback profiles for {platform_key}")
        
        base_profiles = self.FALLBACK_PROFILES.get(platform_key, self.FALLBACK_PROFILES["linkedin"])
        
        return {
            "tagging_accounts": base_profiles["tagging_accounts"],
            "platform": platform_key,
            "niche": niche,
            "fallback_used": True
        }

    def _get_all_profiles_with_fallback(self, article_content: str, platforms: List[str], article_file_path: str = None) -> Dict[str, Any]:
        """Get tagging profiles for all platforms with fallback using new profile processor"""
        logger.info("🔍 Getting tagging profiles...")
        
        profiles = {}
        niche = self.detect_niche_with_fallback(article_content)
        
        # Create a temporary file if we don't have one
        if not article_file_path:
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                    temp_file.write(article_content)
                    article_file_path = temp_file.name
                    temp_file_created = True
            except Exception as e:
                logger.error(f"Failed to create temporary file: {e}")
                article_file_path = None
                temp_file_created = False
        else:
            temp_file_created = False
        
        for platform_key in platforms:
            try:
                if self.profile_processor and article_file_path:
                    # Platform mapping for the new profile processor
                    platform_mapping = {
                        'linkedin': 'linkedin',
                        'facebook': 'facebook',
                        'instagram_threads': 'threads',  # Updated mapping
                        'x.com': 'twitter/x.com',        # Updated mapping
                        'medium': 'medium',
                        'blogger': 'blogger'
                    }
                    
                    mapped_platform = platform_mapping.get(platform_key, platform_key)
                    
                    logger.info(f"🔍 Getting profiles for {mapped_platform} using new processor...")
                    
                    # Read article content
                    article_content = self.profile_processor.read_article_file(article_file_path)
                    
                    # Analyze article for the specific platform
                    analysis = self.profile_processor.analyze_article_content(article_content, mapped_platform)
                    
                    # Create search prompt
                    search_prompt = self.profile_processor.create_gemini_search_prompt(analysis, mapped_platform)
                    
                    # Find accounts
                    discovery_results = self.profile_processor.find_accounts_with_gemini(search_prompt)
                    
                    # Extract usernames
                    extracted_usernames = self.profile_processor.extract_usernames_from_text(discovery_results)
                    
                    # Format the result to match expected structure
                    if extracted_usernames:
                        formatted_accounts = []
                        for username in extracted_usernames:
                            formatted_accounts.append({
                                "handle": username,
                                "description": f"Relevant account for {niche} content"
                            })
                        
                        result = {
                            "tagging_accounts": formatted_accounts,
                            "platform": mapped_platform,
                            "niche": niche,
                            "discovery_results": discovery_results,
                            "total_found": len(extracted_usernames)
                        }
                        profiles[platform_key] = result
                        logger.info(f"✅ Found {len(extracted_usernames)} profiles for {platform_key}")
                        continue
                
                # Use fallback if main processor failed or not available
                fallback_profiles = self.generate_fallback_profiles(platform_key, niche)
                profiles[platform_key] = fallback_profiles
                logger.info(f"⚠️ Using fallback profiles for {platform_key}")
                
            except Exception as e:
                logger.warning(f"⚠️ Error getting profiles for {platform_key}: {e}")
                fallback_profiles = self.generate_fallback_profiles(platform_key, niche)
                profiles[platform_key] = fallback_profiles
        
        # Clean up temporary file if we created one
        if temp_file_created and article_file_path:
            try:
                os.unlink(article_file_path)
            except:
                pass
        
        return profiles

    def _generate_seo_and_hashtags_with_fallback(self, article_content: str, niche: str, platform_key: str) -> Dict[str, Any]:
        """Generate SEO keywords and hashtags with robust fallback"""
        logger.info("🔍 Generating SEO keywords and hashtags...")
        
        try:
            if self.hashtag_analyzer:
                # Create temporary file for hashtag analyzer
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                    temp_file.write(article_content)
                    temp_file_path = temp_file.name
                
                try:
                    # Get niches from hashtag analyzer
                    niches = self.hashtag_analyzer.get_niches(article_content)
                    if not niches:
                        niches = [niche, "general"]
                    
                    logger.info(f"Identified niches: {niches}")
                    
                    # Get SEO keywords
                    seo_keywords = []
                    hashtags = []
                    
                    for detected_niche in niches[:2]:
                        try:
                            # Get SEO keywords with timeout
                            keywords = self.hashtag_analyzer.get_seo_keywords_for_niche(detected_niche)
                            if keywords:
                                seo_keywords.extend(keywords)
                            
                            # Get hashtags with timeout
                            hashtag_url = self.hashtag_analyzer.search_best_hashtag_url(detected_niche)
                            hashtag_text = self.hashtag_analyzer.scrape_hashtags_from_url(hashtag_url)
                            
                            if hashtag_text:
                                platform_hashtags = self.hashtag_analyzer.analyze_hashtags(hashtag_text, "medium", [])
                                if platform_hashtags and platform_hashtags.strip():
                                    hashtag_list = [f"#{tag.strip()}" if not tag.strip().startswith('#') else tag.strip() 
                                                  for tag in platform_hashtags.split(',') if tag.strip()]
                                    hashtags.extend(hashtag_list)
                        except Exception as e:
                            logger.warning(f"⚠️ Error processing niche {detected_niche}: {e}")
                            continue
                    
                    # Remove duplicates and filter
                    seo_keywords = list(set([kw for kw in seo_keywords if kw and kw.strip()]))
                    hashtags = list(set([tag for tag in hashtags if tag and tag.strip()]))
                    
                    # Filter relevant keywords if we have content
                    if seo_keywords and len(seo_keywords) > 20:
                        try:
                            filtered_keywords = self.hashtag_analyzer.filter_relevant_keywords(
                                article_content, seo_keywords, niches
                            )
                            if filtered_keywords:
                                seo_keywords = filtered_keywords
                        except Exception as e:
                            logger.warning(f"⚠️ Keyword filtering failed: {e}")
                            seo_keywords = seo_keywords[:20]
                    
                    # Check if we got useful results
                    if seo_keywords and hashtags:
                        return {
                            'seo_keywords': seo_keywords[:20],
                            'hashtags': hashtags[:15]
                        }
                    else:
                        logger.warning("⚠️ API returned empty results, using fallback")
                        
                finally:
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass
                        
        except Exception as e:
            logger.warning(f"⚠️ Primary SEO/hashtag generation failed: {e}")
        
        # Use fallback
        return self.generate_fallback_seo_and_hashtags(niche, platform_key)

    def _extract_citations_with_fallback(self, article_content: str) -> List[str]:
        """Extract citations from article with fallback"""
        logger.info("🔍 Extracting citations...")
        
        try:
            if self.citation_verifier:
                result = self.citation_verifier.process_text(article_content)
                citations = []
                
                for statement_info in result.get("statements", []):
                    top_sources = statement_info.get("top_sources", [])
                    for source in top_sources:
                        if source.get("alignment_score", 0) > 0.7:
                            citation_url = source.get("link", "")
                            if citation_url and citation_url not in citations:
                                citations.append(citation_url)
                
                if citations:
                    return citations[:10]
                else:
                    logger.warning("⚠️ No citations found, using fallback")
                    
        except Exception as e:
            logger.warning(f"⚠️ Citation extraction failed: {e}")
        
        # Fallback citations
        return [
            "https://www.wikipedia.org",
            "https://www.reuters.com",
            "https://www.bbc.com/news"
        ]

    def _get_optimal_times_with_fallback(self, niche: str, platforms: List[str]) -> Dict[str, str]:
        """Get optimal posting times for each platform with fallback"""
        logger.info("🔍 Getting optimal posting times...")
        
        times = {}
        
        for platform_key in platforms:
            try:
                if self.timing_analyzer:
                    platform_name = self.PLATFORMS[platform_key]['name']
                    search_results = self.timing_analyzer.search_best_posting_times(niche, platform_name)
                    
                    if search_results:
                        best_time = self.timing_analyzer.analyze_posting_times(search_results, niche, platform_name)
                        if best_time and best_time.strip():
                            times[platform_key] = best_time
                            continue
                
                # Use fallback
                fallback_time = self.FALLBACK_POSTING_TIMES.get(platform_key, "Weekdays 10AM-2PM - General optimal time")
                times[platform_key] = fallback_time
                logger.info(f"⚠️ Using fallback time for {platform_key}: {fallback_time}")
                
            except Exception as e:
                logger.warning(f"⚠️ Error getting optimal time for {platform_key}: {e}")
                fallback_time = self.FALLBACK_POSTING_TIMES.get(platform_key, "Weekdays 10AM-2PM - General optimal time")
                times[platform_key] = fallback_time
        
        return times

    def gather_base_data(self, article_content: str, selected_platforms: List[str], article_file_path: str = None) -> Dict[str, Any]:
        """Gather base data needed for all platforms with robust fallbacks"""
        logger.info("📊 Gathering base optimization data with fallback support...")
        
        # Detect niche first
        niche = self.detect_niche_with_fallback(article_content)
        
        # Initialize base data with guaranteed results
        base_data = {'niche': niche}
        
        # Run tasks with timeouts and fallbacks
        logger.info("🔄 Running data collection tasks...")
        
        # Task 1: SEO and Hashtags (with platform-specific fallback)
        logger.info("📊 Task 1: SEO Keywords and Hashtags...")
        try:
            # Use first platform for SEO generation (they're mostly universal)
            first_platform = selected_platforms[0] if selected_platforms else 'linkedin'
            seo_data = self._generate_seo_and_hashtags_with_fallback(article_content, niche, first_platform)
            base_data['seo_hashtags'] = seo_data
            logger.info(f"✅ SEO/Hashtags: {len(seo_data.get('seo_keywords', []))} keywords, {len(seo_data.get('hashtags', []))} hashtags")
        except Exception as e:
            logger.error(f"❌ SEO/Hashtags task failed: {e}")
            base_data['seo_hashtags'] = self.generate_fallback_seo_and_hashtags(niche, selected_platforms[0] if selected_platforms else 'linkedin')
        
        # Task 2: Citations
        logger.info("📊 Task 2: Citations...")
        try:
            citations = self._extract_citations_with_fallback(article_content)
            base_data['citations'] = citations
            logger.info(f"✅ Citations: {len(citations)} found")
        except Exception as e:
            logger.error(f"❌ Citations task failed: {e}")
            base_data['citations'] = ["https://www.wikipedia.org", "https://www.reuters.com"]
        
        # Task 3: Optimal Times
        logger.info("📊 Task 3: Optimal Posting Times...")
        try:
            optimal_times = self._get_optimal_times_with_fallback(niche, selected_platforms)
            base_data['optimal_posting_times'] = optimal_times
            logger.info(f"✅ Optimal times: {len(optimal_times)} platforms covered")
        except Exception as e:
            logger.error(f"❌ Optimal times task failed: {e}")
            base_data['optimal_posting_times'] = {p: self.FALLBACK_POSTING_TIMES.get(p, "Weekdays 10AM-2PM") for p in selected_platforms}
        
        # Task 4: Profiles (Updated to use new profile processor)
        logger.info("📊 Task 4: Tagging Profiles...")
        try:
            profiles = self._get_all_profiles_with_fallback(article_content, selected_platforms, article_file_path)
            base_data['tagging_profiles'] = profiles
            logger.info(f"✅ Profiles: {len(profiles)} platforms covered")
        except Exception as e:
            logger.error(f"❌ Profiles task failed: {e}")
            base_data['tagging_profiles'] = {p: self.generate_fallback_profiles(p, niche) for p in selected_platforms}
        
        # Validate all data is present
        logger.info("🔍 Validating base data completeness...")
        if not base_data.get('seo_hashtags', {}).get('hashtags'):
            logger.warning("⚠️ Empty hashtags detected, applying emergency fallback")
            base_data['seo_hashtags']['hashtags'] = self.FALLBACK_HASHTAGS.get(niche, self.FALLBACK_HASHTAGS['general'])[:5]
        
        if not base_data.get('seo_hashtags', {}).get('seo_keywords'):
            logger.warning("⚠️ Empty SEO keywords detected, applying emergency fallback") 
            base_data['seo_hashtags']['seo_keywords'] = self.FALLBACK_SEO_KEYWORDS.get(niche, self.FALLBACK_SEO_KEYWORDS['general'])[:15]
        
        if not base_data.get('citations'):
            logger.warning("⚠️ Empty citations detected, applying emergency fallback")
            base_data['citations'] = ["https://www.wikipedia.org", "https://www.reuters.com", "https://www.bbc.com/news"]
        
        logger.info("✅ Base data collection complete with guaranteed results")
        return base_data

    def optimize_content_for_platform(self, article_content: str, platform_key: str, 
                                    base_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize content for a specific platform with fallback"""
        platform_config = self.PLATFORMS[platform_key]
        logger.info(f"🎯 Optimizing content for {platform_config['name']}")
        
        try:
            # Get platform-specific optimization using OpenAI
            from openai import OpenAI
            client = OpenAI()
            
            # Create platform-specific prompt
            optimization_prompt = self._create_platform_prompt(
                article_content, platform_key, platform_config, base_data
            )
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert content optimizer for {platform_config['name']}. Create platform-optimized content that maximizes engagement while staying true to the original message."
                    },
                    {
                        "role": "user",
                        "content": optimization_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            optimized_content = response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"⚠️ AI optimization failed for {platform_config['name']}: {e}")
            # Fallback: Manual content adaptation
            optimized_content = self._manual_content_optimization(article_content, platform_config)
        
        # Apply platform-specific rules and get data
        result = {
            "platform": platform_config['name'],
            "content": optimized_content,
            "content_style": platform_config['content_style'],
            "character_count": len(optimized_content),
            "max_length": platform_config['max_length'],
            "hashtags": self._get_platform_hashtags_with_fallback(base_data, platform_key),
            "optimal_posting_time": base_data.get('optimal_posting_times', {}).get(platform_key, self.FALLBACK_POSTING_TIMES.get(platform_key, "Weekdays 10AM-2PM")),
            "tagging_profiles": self._get_platform_profiles_with_fallback(base_data, platform_key)
        }
        
        # Add citations only for long-form platforms
        if platform_config['use_citations']:
            result["citations"] = base_data.get('citations', [])
        
        logger.info(f"✅ Content optimized for {platform_config['name']} ({len(optimized_content)} chars)")
        return result

    def _manual_content_optimization(self, article_content: str, platform_config: Dict) -> str:
        """Manual content optimization fallback when AI fails"""
        logger.info(f"🔄 Applying manual optimization for {platform_config['name']}")
        
        content_style = platform_config['content_style']
        max_length = platform_config['max_length']
        
        # Extract first few sentences for summary
        sentences = article_content.split('. ')
        
        if content_style == 'microblog':  # X.com
            # Take first sentence and make it tweet-like
            first_sentence = sentences[0] if sentences else article_content[:200]
            optimized = f"{first_sentence}... 🧵 Read more in the comments!"
            if max_length and len(optimized) > max_length:
                optimized = first_sentence[:max_length-20] + "... 🧵"
                
        elif content_style == 'professional':  # LinkedIn
            # Create professional summary
            intro = sentences[0] if sentences else ""
            key_point = sentences[1] if len(sentences) > 1 else ""
            optimized = f"💡 Key Insight: {intro}\n\n🔍 {key_point}\n\nWhat are your thoughts? Share in the comments below.\n\n#ProfessionalDevelopment #Industry"
            if max_length and len(optimized) > max_length:
                optimized = f"{intro}\n\nThoughts? 💭\n\n#Professional"
                
        elif content_style == 'social':  # Facebook
            # Create engaging social post
            hook = "🚀 Here's something interesting..."
            summary = '. '.join(sentences[:2]) if len(sentences) >= 2 else sentences[0] if sentences else article_content[:300]
            optimized = f"{hook}\n\n{summary}\n\n👍 Like if you agree!\n💬 What's your experience with this?"
            if max_length and len(optimized) > max_length:
                optimized = f"{hook}\n\n{summary[:max_length-100]}\n\n💭 Thoughts?"
                
        elif content_style == 'casual':  # Instagram Threads
            # Create casual, relatable post
            optimized = f"Just read about this and had to share... 💭\n\n{sentences[0] if sentences else article_content[:400]}\n\nAnyone else think about this? 🤔"
            if max_length and len(optimized) > max_length:
                optimized = f"Interesting thought... 💭\n\n{sentences[0][:max_length-50] if sentences else article_content[:max_length-50]}\n\n🤔"
                
        else:  # long_form (Medium, Blogger)
            # Keep full content but add engaging intro
            optimized = f"# {sentences[0] if sentences else 'Interesting Topic'}\n\n{article_content}\n\n---\n\n*What are your thoughts on this topic? Share in the comments below.*"
        
        return optimized

    def _get_platform_hashtags_with_fallback(self, base_data: Dict, platform_key: str) -> List[str]:
        """Get platform-specific hashtags with guaranteed results"""
        platform_config = self.PLATFORMS[platform_key]
        min_tags, max_tags = platform_config['hashtag_count']
        
        # Try to get from base data
        all_hashtags = base_data.get('seo_hashtags', {}).get('hashtags', [])
        
        if not all_hashtags:
            # Use niche-based fallback
            niche = base_data.get('niche', 'general')
            all_hashtags = self.FALLBACK_HASHTAGS.get(niche, self.FALLBACK_HASHTAGS['general'])
            logger.warning(f"⚠️ Using fallback hashtags for {platform_key}")
        
        # Ensure we have enough hashtags
        if len(all_hashtags) < max_tags:
            general_tags = self.FALLBACK_HASHTAGS['general']
            all_hashtags.extend([tag for tag in general_tags if tag not in all_hashtags])
        
        # Return appropriate number for platform
        return all_hashtags[:max_tags]

    def _get_platform_profiles_with_fallback(self, base_data: Dict, platform_key: str) -> Dict:
        """Get platform-specific tagging profiles with guaranteed results"""
        # Try to get from base data
        all_profiles = base_data.get('tagging_profiles', {})
        platform_profiles = all_profiles.get(platform_key, {})
        
        # Check if we have valid profile data
        if platform_profiles and not platform_profiles.get('error') and platform_profiles.get('tagging_accounts'):
            return platform_profiles
        
        # Use fallback
        niche = base_data.get('niche', 'general')
        fallback_profiles = self.generate_fallback_profiles(platform_key, niche)
        logger.warning(f"⚠️ Using fallback profiles for {platform_key}")
        return fallback_profiles

    def _create_platform_prompt(self, article_content: str, platform_key: str, 
                               platform_config: Dict, base_data: Dict) -> str:
        """Create platform-specific optimization prompt"""
        
        niche = base_data.get('niche', 'general')
        seo_keywords = base_data.get('seo_hashtags', {}).get('seo_keywords', [])[:5]  # Top 5 keywords
        
        base_prompt = f"""
        Optimize this article content for {platform_config['name']}:
        
        ORIGINAL CONTENT:
        {article_content[:2000]}...
        
        OPTIMIZATION REQUIREMENTS:
        - Platform: {platform_config['name']}
        - Content Style: {platform_config['content_style']}
        - Niche: {niche}
        - Key SEO Terms: {', '.join(seo_keywords) if seo_keywords else 'N/A'}
        """
        
        # Platform-specific instructions
        if platform_config['content_style'] == 'microblog':  # X.com
            base_prompt += f"""
        - Maximum {platform_config['max_length']} characters
        - Make it punchy and attention-grabbing
        - Use thread format if needed (mark with 1/, 2/, etc.)
        - Include call-to-action
        - Focus on the most impactful point
        """
        
        elif platform_config['content_style'] == 'professional':  # LinkedIn
            base_prompt += f"""
        - Maximum {platform_config['max_length']} characters
        - Professional tone, thought leadership style
        - Include insights and takeaways
        - Use line breaks for readability
        - Add a professional call-to-action
        - Structure: Hook → Value → Call-to-action
        """
        
        elif platform_config['content_style'] == 'social':  # Facebook
            base_prompt += f"""
        - Maximum {platform_config['max_length']} characters
        - Conversational and engaging tone
        - Include storytelling elements
        - Encourage comments and sharing
        - Use emojis strategically
        """
        
        elif platform_config['content_style'] == 'casual':  # Instagram Threads
            base_prompt += f"""
        - Maximum {platform_config['max_length']} characters
        - Casual, authentic tone
        - Visual and engaging
        - Use natural language
        - Include relatable elements
        """
        
        elif platform_config['content_style'] == 'long_form':  # Medium, Blogger
            base_prompt += """
        - Maintain full article structure
        - Add engaging introduction and conclusion
        - Use subheadings and formatting
        - Include detailed explanations
        - Optimize for readability
        """
        
        base_prompt += f"""
        
        IMPORTANT:
        - Keep the core message and facts intact
        - Make it native to {platform_config['name']} style
        - Optimize for maximum engagement
        - DO NOT include hashtags in the content (they will be added separately)
        - Return only the optimized content, no explanations
        """
        
        return base_prompt

    def generate_images_for_platforms(self, article_content: str, image_platforms: List[str]) -> Dict[str, List[Dict]]:
        """Generate images for selected platforms with fallback"""
        if not image_platforms:
            return {}
        
        logger.info("🖼️ Generating images for selected platforms...")
        
        try:
            # Identify key entities for visualization
            entities = self.identify_key_entities_for_visualization(article_content)
        except Exception as e:
            logger.warning(f"⚠️ Entity identification failed: {e}, using fallback entities")
            entities = [
                {
                    "type": "situation",
                    "name": "Article Main Topic",
                    "context": "Key subject matter from the article",
                    "visual_description": "Professional representation of the main topic"
                },
                {
                    "type": "thing",
                    "name": "Supporting Concept", 
                    "context": "Important supporting element",
                    "visual_description": "Relevant visualization of supporting concept"
                }
            ]
        
        platform_images = {}
        
        for platform_key in image_platforms:
            platform_config = self.PLATFORMS[platform_key]
            image_count = platform_config['image_count']
            
            logger.info(f"Generating {image_count} image(s) for {platform_config['name']}")
            
            # Generate required number of images
            images = []
            entities_to_use = entities[:image_count]  # Use first N entities
            
            for i, entity in enumerate(entities_to_use):
                try:
                    image_result = self.generate_single_image(entity, article_content, platform_key, i+1)
                    if image_result:
                        images.append(image_result)
                    else:
                        # Create placeholder result for failed image
                        images.append({
                            "entity_type": entity["type"],
                            "entity_name": entity["name"],
                            "context": entity["context"],
                            "cloudinary_url": None,
                            "platform": platform_config['name'],
                            "error": "Image generation failed",
                            "fallback_used": True
                        })
                except Exception as e:
                    logger.error(f"Error generating image {i+1} for {platform_config['name']}: {e}")
                    # Add error result
                    images.append({
                        "entity_type": entity.get("type", "unknown"),
                        "entity_name": entity.get("name", f"Entity {i+1}"),
                        "context": entity.get("context", ""),
                        "cloudinary_url": None,
                        "platform": platform_config['name'],
                        "error": str(e),
                        "fallback_used": True
                    })
            
            platform_images[platform_key] = images
        
        return platform_images

    def identify_key_entities_for_visualization(self, article_content: str) -> List[Dict[str, str]]:
        """Identify key entities for image generation with fallback"""
        try:
            from openai import OpenAI
            client = OpenAI()
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """Identify exactly 2 key entities from the article that can be realistically visualized.
                        
                        Return in this format:
                        ENTITY 1:
                        TYPE: [person/event/place/situation/thing]
                        NAME: [specific name]
                        CONTEXT: [brief context]
                        VISUAL_DESC: [realistic description]
                        
                        ENTITY 2:
                        TYPE: [person/event/place/situation/thing]
                        NAME: [specific name]
                        CONTEXT: [brief context]
                        VISUAL_DESC: [realistic description]"""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this article and identify 2 key entities for visualization:\n\n{article_content[:3000]}..."
                    }
                ],
                temperature=0.3,
                max_tokens=400
            )
            
            return self._parse_entities(response.choices[0].message.content)
            
        except Exception as e:
            logger.warning(f"⚠️ AI entity identification failed: {e}")
            # Return fallback entities
            return [
                {
                    "type": "situation",
                    "name": "Article main topic",
                    "context": "Key subject matter",
                    "visual_description": "Professional representation"
                },
                {
                    "type": "thing",
                    "name": "Supporting concept", 
                    "context": "Important element",
                    "visual_description": "Relevant visualization"
                }
            ]

    def _parse_entities(self, content: str) -> List[Dict[str, str]]:
        """Parse entities from LLM response with fallback"""
        entities = []
        current_entity = {}
        
        try:
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('ENTITY'):
                    if current_entity:
                        entities.append(current_entity)
                    current_entity = {}
                elif line.startswith('TYPE:'):
                    current_entity['type'] = line.split(':', 1)[1].strip()
                elif line.startswith('NAME:'):
                    current_entity['name'] = line.split(':', 1)[1].strip()
                elif line.startswith('CONTEXT:'):
                    current_entity['context'] = line.split(':', 1)[1].strip()
                elif line.startswith('VISUAL_DESC:'):
                    current_entity['visual_description'] = line.split(':', 1)[1].strip()
            
            if current_entity:
                entities.append(current_entity)
        except Exception as e:
            logger.warning(f"⚠️ Entity parsing failed: {e}")
        
        # Ensure we have exactly 2 entities with fallbacks
        while len(entities) < 2:
            entities.append({
                "type": "situation",
                "name": f"Key element {len(entities) + 1}",
                "context": "Important aspect",
                "visual_description": "Professional representation"
            })
        
        return entities[:2]

    def generate_single_image(self, entity: Dict[str, str], article_content: str, 
                            platform_key: str, image_num: int) -> Optional[Dict[str, Any]]:
        """Generate a single image for an entity with error handling"""
        try:
            # Create realistic image prompt
            prompt = self._create_realistic_image_prompt(entity, article_content)
            
            # Generate image
            result = openai_client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size="1024x1024",
                quality="high"
            )
            
            image_base64 = result.data[0].b64_json
            
            # Create temporary file with user ID
            temp_filename = f"temp_{self.user_id}_{platform_key}_image_{image_num}_{self.timestamp}.png"
            temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
            
            # Save temporarily
            image_bytes = base64.b64decode(image_base64)
            with open(temp_path, "wb") as f:
                f.write(image_bytes)
            
            # Upload to Cloudinary
            cloudinary_url = self.upload_to_cloudinary(temp_path)
            
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
            
            return {
                "entity_type": entity["type"],
                "entity_name": entity["name"],
                "context": entity["context"],
                "cloudinary_url": cloudinary_url,
                "platform": self.PLATFORMS[platform_key]['name'],
                "prompt_used": prompt[:200] + "...",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None

    def _create_realistic_image_prompt(self, entity: Dict[str, str], article_content: str) -> str:
        """Create realistic image prompt"""
        entity_type = entity["type"].lower()
        entity_name = entity["name"]
        context = entity["context"]
        visual_desc = entity.get("visual_description", "")
        
        base_style = "Professional high-quality photograph, realistic lighting, sharp focus, detailed"
        
        if entity_type == "person":
            return f"""Professional portrait of {entity_name}. {visual_desc}.
            
            Context: {context}
            Style: {base_style}, professional headshot
            Lighting: Natural professional lighting
            Setting: Professional environment
            Details: Professional attire, confident pose
            Quality: High-resolution photography
            
            Avoid: Cartoonish features, unrealistic lighting"""
            
        elif entity_type == "event":
            return f"""Professional event photography of {entity_name}. {visual_desc}.
            
            Context: {context}
            Style: {base_style}, documentary photography
            Setting: Appropriate venue
            Elements: Professional atmosphere, engaged participants
            Lighting: Professional event lighting
            Quality: High-resolution event photography
            
            Avoid: Staged scenes, poor lighting"""
            
        elif entity_type == "place":
            return f"""Professional architectural photograph of {entity_name}. {visual_desc}.
            
            Context: {context}
            Style: {base_style}, architectural photography
            Composition: Well-framed view
            Lighting: Natural daylight
            Details: Clear architectural features
            Quality: High-resolution photography
            
            Avoid: Unrealistic colors, distorted perspective"""
            
        elif entity_type == "situation":
            return f"""Professional documentary photograph of {entity_name}. {visual_desc}.
            
            Context: {context}
            Style: {base_style}, documentary photography
            Setting: Realistic environment
            Elements: Authentic atmosphere
            Lighting: Natural lighting
            Quality: High-resolution photography
            
            Avoid: Artificial scenarios"""
            
        else:  # thing
            return f"""Professional photograph of {entity_name}. {visual_desc}.
            
            Context: {context}
            Style: {base_style}, product photography
            Setting: Clean professional background
            Lighting: Professional lighting
            Details: Sharp focus, realistic materials
            Quality: High-resolution photography
            
            Avoid: Unrealistic materials"""

    def upload_to_cloudinary(self, file_path: str) -> Optional[str]:
        """Upload image to Cloudinary"""
        try:
            response = cloudinary.uploader.upload(file_path, resource_type="image")
            return response.get("secure_url")
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}")
            return None

    def compile_final_posts(self, optimization_results: Dict[str, Any], selected_platforms: List[str]) -> Dict[str, Any]:
        """Compile final, ready-to-post content using the integrated compiler"""
        logger.info(" Starting final post compilation...")
        
        if not self.post_compiler:
            logger.warning(" Post compiler not available, skipping compilation")
            return {}
        
        try:
            # Convert optimization results to compiler-compatible format
            compiler_input = self._convert_results_for_compiler(optimization_results)
            logger.info(f"this is compiler input: {compiler_input}")
            
            # Compile posts for selected platforms
            compiled_results = self.post_compiler.compile_all_platforms(compiler_input, selected_platforms)
            
            logger.info(" Final post compilation completed successfully")
            return compiled_results
            
        except Exception as e:
            logger.error(f" Final post compilation failed: {e}")
            return {}

    def _convert_results_for_compiler(self, optimization_results: Dict[str, Any]) -> Dict[str, Any]:
        """Convert optimization results to format expected by compiler"""
        logger.info("Converting results for compiler...")
        
        # Extract metadata and base data
        metadata = optimization_results.get('metadata', {})
        base_data = optimization_results.get('base_data', {})
        platforms = optimization_results.get('platforms', {})
        
        # Convert to compiler expected format
        compiler_input = {
            'base_data': {
                'all_seo_keywords': base_data.get('all_seo_keywords', []),
                'all_hashtags': base_data.get('all_hashtags', []),
                'citations': base_data.get('citations', [])
            },
            'platforms': {}
        }
        
        # Convert each platform's data
        for platform_key, platform_data in platforms.items():
            compiler_platform_data = {
                'platform': {
                    'name': platform_data.get('platform', 'Unknown'),
                    'key': platform_key
                },
                'content': {
                    'optimized_text': platform_data.get('content', ''),
                    'hashtags': platform_data.get('hashtags', []),
                    'optimal_posting_time': platform_data.get('optimal_posting_time', ''),
                    'citations': platform_data.get('citations', [])
                },
                'engagement': {
                    'seo_keywords': metadata.get('seo_keywords', []),
                    'tagging_profiles': platform_data.get('tagging_profiles', {})
                },
                'metadata': {
                    'niche': metadata.get('niche', 'general'),
                    'fallback_used': platform_data.get('fallback_used', False)
                }
            }
            
            compiler_input['platforms'][platform_key] = compiler_platform_data
        
        return compiler_input

    def run_multi_platform_optimization(self, file_path: str, platforms_input: str, 
                                       image_platforms_input: str, compilation_input: str) -> Dict[str, Any]:
        """Main method to run multi-platform optimization with guaranteed results and optional compilation (production version)"""
        try:
            logger.info(f"🚀 Starting Multi-Platform Article Optimization for user {self.user_id}...")
            
            # Step 1: Get article from file
            article_content = self.get_article_from_file(file_path)
            
            # Store the article file path for profile processing
            # Create a temporary file for the profile processor
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(article_content)
                article_file_path = temp_file.name
            
            # Step 2: Parse platform selection
            selected_platforms = self.get_selected_platforms(platforms_input)
            
            # Step 3: Parse image platform selection
            image_platforms = self.get_image_platforms(image_platforms_input, selected_platforms)
            
            # Step 4: Parse compilation choice
            compile_final = self.parse_compilation_choice(compilation_input)
            
            logger.info(f"⚡ Processing article for {len(selected_platforms)} platform(s)...")
            
            # Step 5: Gather base data needed for all platforms (including profiles)
            base_data = self.gather_base_data(article_content, selected_platforms, article_file_path)
            
            # Step 6: Optimize content for each platform
            platform_results = {}
            
            logger.info(f"🔄 Optimizing content for each platform...")
            for platform_key in selected_platforms:
                platform_name = self.PLATFORMS[platform_key]['name']
                logger.info(f"📝 Optimizing for {platform_name}...")
                
                try:
                    platform_result = self.optimize_content_for_platform(
                        article_content, platform_key, base_data
                    )
                    platform_results[platform_key] = platform_result
                    logger.info(f"✅ {platform_name} optimization complete")
                except Exception as e:
                    logger.error(f"❌ Failed to optimize for {platform_name}: {e}")
                    # Create fallback result
                    platform_results[platform_key] = {
                        "platform": platform_name,
                        "content": self._manual_content_optimization(article_content, self.PLATFORMS[platform_key]),
                        "content_style": self.PLATFORMS[platform_key]['content_style'],
                        "character_count": len(article_content[:1000]),
                        "max_length": self.PLATFORMS[platform_key]['max_length'],
                        "hashtags": self._get_platform_hashtags_with_fallback(base_data, platform_key),
                        "optimal_posting_time": self.FALLBACK_POSTING_TIMES.get(platform_key, "Weekdays 10AM-2PM"),
                        "tagging_profiles": self.generate_fallback_profiles(platform_key, base_data.get('niche', 'general')),
                        "fallback_used": True,
                        "error": str(e)
                    }
                    logger.info(f"⚠️ {platform_name} using fallback optimization")
            
            # Step 7: Generate images for selected platforms
            platform_images = {}
            if image_platforms:
                logger.info(f"🖼️ Generating images for {len(image_platforms)} platform(s)...")
                try:
                    platform_images = self.generate_images_for_platforms(article_content, image_platforms)
                except Exception as e:
                    logger.error(f"❌ Image generation failed: {e}")
                    platform_images = {}
            
            # Step 8: Combine results with validation
            optimization_result = {
                "metadata": {
                    "user_id": self.user_id,
                    "processed_at": datetime.now().isoformat(),
                    "article_length": len(article_content),
                    "platforms_optimized": [self.PLATFORMS[p]['name'] for p in selected_platforms],
                    "niche": base_data.get('niche', 'general'),
                    "seo_keywords": base_data.get('seo_hashtags', {}).get('seo_keywords', [])[:10],
                    "total_citations": len(base_data.get('citations', [])),
                    "images_generated": bool(image_platforms),
                    "fallbacks_used": any(result.get('fallback_used', False) for result in platform_results.values()),
                    "compilation_requested": compile_final
                },
                "platforms": platform_results,
                "images": platform_images,
                "base_data": {
                    "citations": base_data.get('citations', []),
                    "all_hashtags": base_data.get('seo_hashtags', {}).get('hashtags', []),
                    "all_seo_keywords": base_data.get('seo_hashtags', {}).get('seo_keywords', [])
                }
            }
            
            # Step 9: Compile final posts if requested
            compiled_results = {}
            if compile_final:
                logger.info(f"📝 Compiling final, ready-to-post content...")
                compiled_results = self.compile_final_posts(optimization_result, selected_platforms)
                
                if compiled_results:
                    logger.info(f"✅ Final compilation completed for {len(compiled_results.get('compiled_posts', {}))} platforms")
                else:
                    logger.info(f"⚠️ Final compilation failed, continuing with optimization results")
            
            # Combine both optimization and compilation results
            final_result = {
                "optimization": optimization_result,
                "compilation": compiled_results
            }
            
            # Clean up temporary file
            try:
                os.unlink(article_file_path)
            except:
                pass
            
            logger.info(f"✅ Multi-platform optimization completed successfully for user {self.user_id}!")
            return final_result
            
        except Exception as e:
            logger.error(f"Multi-platform optimization failed for user {self.user_id}: {e}")
            raise

    def save_results_json(self, results: Dict[str, Any]):
        """Save separate JSON files for optimization and compilation results with user ID"""
        
        # Create output files with user ID prefix in shared directory
        saved_files = []
        
        optimization_results = results.get('optimization', {})
        compilation_results = results.get('compilation', {})
        
        try:
            # Save optimization results
            optimization_files = self._save_optimization_results(optimization_results)
            saved_files.extend(optimization_files)
            
            # Save compilation results if available
            if compilation_results and compilation_results.get('compiled_posts'):
                compilation_files = self._save_compilation_results(compilation_results)
                saved_files.extend(compilation_files)
            
            # Create comprehensive README
            self._create_comprehensive_readme(optimization_results, compilation_results)
            
            logger.info(f"💾 Results saved successfully for user {self.user_id}")
            logger.info(f"📁 Output directory: {PRODUCTION_OUTPUT_DIR}")
            logger.info(f"📄 Total files generated: {len(saved_files) + 1}")
            
        except Exception as e:
            logger.error(f"Error saving results for user {self.user_id}: {e}")
            raise

    def _save_optimization_results(self, optimization_results: Dict[str, Any]) -> List[str]:
        """Save optimization results using existing logic with user ID"""
        saved_files = []
        
        platforms = optimization_results.get('platforms', {})
        images = optimization_results.get('images', {})
        metadata = optimization_results.get('metadata', {})
        base_data = optimization_results.get('base_data', {})
        
        # Save individual platform files with user ID
        for platform_key, platform_data in platforms.items():
            platform_name = platform_data.get('platform', self.PLATFORMS[platform_key]['name'])
            
            # Validate platform data completeness
            if not platform_data.get('content'):
                logger.warning(f"⚠️ Empty content for {platform_name}, adding fallback")
                platform_data['content'] = f"Content for {platform_name} - please review and customize"
            
            if not platform_data.get('hashtags'):
                logger.warning(f"⚠️ Empty hashtags for {platform_name}, adding fallback")
                niche = metadata.get('niche', 'general')
                platform_data['hashtags'] = self.FALLBACK_HASHTAGS.get(niche, self.FALLBACK_HASHTAGS['general'])[:5]
            
            # Create comprehensive platform-specific JSON
            platform_json = {
                "user_id": self.user_id,
                "platform": {
                    "name": platform_name,
                    "key": platform_key,
                    "content_style": platform_data.get('content_style', 'unknown'),
                    "use_citations": self.PLATFORMS[platform_key]['use_citations'],
                    "max_length": self.PLATFORMS[platform_key]['max_length'],
                    "image_count": self.PLATFORMS[platform_key]['image_count']
                },
                "content": {
                    "optimized_text": platform_data.get('content', ''),
                    "character_count": platform_data.get('character_count', 0),
                    "hashtags": platform_data.get('hashtags', []),
                    "optimal_posting_time": platform_data.get('optimal_posting_time', 'N/A')
                },
                "engagement": {
                    "tagging_profiles": platform_data.get('tagging_profiles', {}),
                    "seo_keywords": metadata.get('seo_keywords', [])[:10]
                },
                "images": images.get(platform_key, []),
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "niche": metadata.get('niche', 'general'),
                    "original_article_length": metadata.get('article_length', 0),
                    "fallback_used": platform_data.get('fallback_used', False)
                }
            }
            
            # Add citations only for platforms that use them
            if self.PLATFORMS[platform_key]['use_citations']:
                platform_json["content"]["citations"] = base_data.get('citations', [])
            
            # Add platform-specific formatting instructions
            platform_json["formatting_tips"] = self._get_formatting_tips(platform_key)
            
            # Add error info if present
            if 'error' in platform_data:
                platform_json["error"] = platform_data['error']
            
            # Save individual platform file with user ID prefix
            platform_filename = f"{self.user_id}_{platform_key}_optimization_{self.timestamp}.json"
            platform_filepath = os.path.join(PRODUCTION_OUTPUT_DIR, platform_filename)
            
            with open(platform_filepath, 'w', encoding='utf-8') as f:
                json.dump(platform_json, f, indent=2, ensure_ascii=False)
            
            saved_files.append(platform_filepath)
            logger.info(f"💾 Saved {platform_name} optimization to: {platform_filename}")
        
        # Save summary file with metadata and cross-platform insights
        summary_json = {
            "user_id": self.user_id,
            "optimization_summary": {
                "timestamp": self.timestamp,
                "platforms_processed": list(platforms.keys()),
                "total_platforms": len(platforms),
                "niche": metadata.get('niche', 'general'),
                "total_images_generated": sum(len(imgs) for imgs in images.values()),
                "successful_optimizations": len([p for p in platforms.values() if not p.get('error') or p.get('fallback_used')]),
                "fallbacks_used": metadata.get('fallbacks_used', False)
            },
            "cross_platform_data": {
                "all_seo_keywords": base_data.get('all_seo_keywords', []),
                "all_hashtags": base_data.get('all_hashtags', []),
                "all_citations": base_data.get('citations', [])
            },
            "platform_comparison": {
                platform_key: {
                    "character_count": platform_data.get('character_count', 0),
                    "hashtag_count": len(platform_data.get('hashtags', [])),
                    "has_images": len(images.get(platform_key, [])) > 0,
                    "uses_citations": self.PLATFORMS[platform_key]['use_citations'],
                    "fallback_used": platform_data.get('fallback_used', False)
                }
                for platform_key, platform_data in platforms.items()
            }
        }
        
        summary_filepath = os.path.join(PRODUCTION_OUTPUT_DIR, f"{self.user_id}_optimization_summary_{self.timestamp}.json")
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary_json, f, indent=2, ensure_ascii=False)
        
        saved_files.append(summary_filepath)
        
        return saved_files

    def _save_compilation_results(self, compilation_results: Dict[str, Any]) -> List[str]:
        """Save compilation results using compiler's logic with user ID"""
        saved_files = []
        
        if not self.post_compiler:
            return saved_files
        
        try:
            # Save compiled results with user ID
            compiled_posts = compilation_results.get("compiled_posts", {})
            
            # Save individual platform compiled files
            for platform_key, post_data in compiled_posts.items():
                if not post_data.get("compilation_failed"):
                    # Save final post JSON
                    final_post_filename = f"{self.user_id}_{platform_key}_final_post_{self.timestamp}.json"
                    final_post_filepath = os.path.join(PRODUCTION_OUTPUT_DIR, final_post_filename)
                    
                    # Add user ID to the post data
                    post_data_with_user = {"user_id": self.user_id, **post_data}
                    
                    with open(final_post_filepath, 'w', encoding='utf-8') as f:
                        json.dump(post_data_with_user, f, indent=2, ensure_ascii=False)
                    
                    saved_files.append(final_post_filepath)
                    
                    # Save readable text file
                    readable_filename = f"{self.user_id}_{platform_key}_final_readable_{self.timestamp}.txt"
                    readable_filepath = os.path.join(PRODUCTION_OUTPUT_DIR, readable_filename)
                    
                    with open(readable_filepath, 'w', encoding='utf-8') as f:
                        f.write(f"User ID: {self.user_id}\n")
                        f.write(f"Platform: {post_data.get('platform', platform_key.title())}\n")
                        f.write(f"Generated: {self.timestamp}\n")
                        f.write("="*50 + "\n\n")
                        f.write("READY TO POST CONTENT:\n")
                        f.write("-"*30 + "\n\n")
                        f.write(post_data.get('content', ''))
                        f.write("\n\n" + "="*50 + "\n")
                        f.write(f"Character Count: {post_data.get('character_count', 0)}\n")
                        f.write(f"SEO Keywords Used: {len(post_data.get('seo_keywords_used', []))}\n")
                        f.write(f"Handles Used: {len(post_data.get('handles_used', []))}\n")
                        f.write(f"Ready to Post: {'Yes' if post_data.get('ready_to_post') else 'No'}\n")
                    
                    saved_files.append(readable_filepath)
            
            # Save main compiled results file with user ID
            main_compiled_filename = f"{self.user_id}_compiled_posts_{self.timestamp}.json"
            main_compiled_filepath = os.path.join(PRODUCTION_OUTPUT_DIR, main_compiled_filename)
            
            # Add user ID to compilation results
            compilation_with_user = {"user_id": self.user_id, **compilation_results}
            
            with open(main_compiled_filepath, 'w', encoding='utf-8') as f:
                json.dump(compilation_with_user, f, indent=2, ensure_ascii=False)
            
            saved_files.append(main_compiled_filepath)
            
        except Exception as e:
            logger.error(f"Error saving compilation results for user {self.user_id}: {e}")
        
        return saved_files

    def _create_comprehensive_readme(self, optimization_results: Dict[str, Any], 
                                   compilation_results: Dict[str, Any]):
        """Create comprehensive README with both optimization and compilation info"""
        
        has_compilation = bool(compilation_results and compilation_results.get('compiled_posts'))
        
        readme_content = f"""# Multi-Platform Optimization Results for User {self.user_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Timestamp: {self.timestamp}

## 🎯 User-Specific Files:

All files are prefixed with your User ID: `{self.user_id}_`

### 📝 READY-TO-POST FILES (Final Compilation):
"""
        
        if has_compilation:
            compiled_posts = compilation_results.get('compiled_posts', {})
            for platform_key, post_data in compiled_posts.items():
                if not post_data.get('compilation_failed'):
                    platform_name = post_data.get('platform', platform_key.title())
                    readme_content += f"""
- **{self.user_id}_{platform_key}_final_post_{self.timestamp}.json**: Complete final post data for {platform_name}
- **{self.user_id}_{platform_key}_final_readable_{self.timestamp}.txt**: Human-readable final post for {platform_name}"""
            
            readme_content += f"""
- **{self.user_id}_compiled_posts_{self.timestamp}.json**: All compiled posts in one file

### 📊 OPTIMIZATION DATA (Base Analysis):"""
        else:
            readme_content += f"""
*No final compilation was performed - using optimization data below*

### 📊 OPTIMIZATION DATA:"""
        
        platforms = optimization_results.get('platforms', {})
        for platform_key in platforms.keys():
            platform_name = self.PLATFORMS.get(platform_key, {}).get('name', platform_key.title())
            readme_content += f"""
- **{self.user_id}_{platform_key}_optimization_{self.timestamp}.json**: Complete optimization data for {platform_name}"""
        
        readme_content += f"""
- **{self.user_id}_optimization_summary_{self.timestamp}.json**: Cross-platform insights and metadata

## 🚀 How to use your files:

### For Immediate Publishing:
"""
        
        if has_compilation:
            readme_content += f"""
1. **Use the FINAL files** (recommended):
   - Open `{self.user_id}_[platform]_final_readable_{self.timestamp}.txt` files for easy copy-paste
   - Use `{self.user_id}_[platform]_final_post_{self.timestamp}.json` for programmatic posting
   - Content includes: optimized text + integrated SEO + placed handles + formatted hashtags

2. **What's ready to go**:
   - ✅ Platform-specific titles and hooks
   - ✅ SEO keywords naturally integrated
   - ✅ User handles strategically placed
   - ✅ Hashtags optimally positioned
   - ✅ Character limits respected
   - ✅ Citations properly formatted (where applicable)

### For Customization:"""
        else:
            readme_content += f"""
*Final compilation was not performed. Use optimization data for manual posting:*

### For Manual Posting:"""
        
        readme_content += f"""
1. Open individual platform optimization JSON files
2. Copy the "optimized_text" field for your post content
3. Add the provided hashtags and posting times
4. Tag the suggested profiles for maximum engagement
5. Download images from the Cloudinary URLs

## 📱 Platform-specific notes:

### Long-form Platforms:
- **Medium & Blogger**: Include citations for credibility, use full content with headings
- Use 2 images per platform for visual appeal

### Social Platforms:
- **LinkedIn**: Professional tone, use tagging profiles, post during business hours
- **X.com**: Keep within character limits, use trending hashtags, consider threads
- **Facebook**: Encourage engagement with call-to-actions, use storytelling
- **Instagram Threads**: Casual tone, visual-first approach, evening posting

## 🛡️ Quality Assurance Features:

### Guaranteed Results:
✅ All platforms have complete content
✅ All platforms have hashtags (fallback used if needed)
✅ All platforms have posting times
✅ All platforms have tagging profiles
✅ Fallback systems ensure no empty results

### Multi-User Support:
✅ Unique User ID: {self.user_id}
✅ Timestamped files: {self.timestamp}
✅ Shared output directory for easy management
✅ No file conflicts between users

## 🎯 Your User Information:

- **User ID**: {self.user_id}
- **Session Timestamp**: {self.timestamp}
- **Files Location**: {PRODUCTION_OUTPUT_DIR}/
- **File Naming**: {self.user_id}_[platform]_[type]_{self.timestamp}.[ext]

## 📈 Expected Results:

With proper implementation, expect:
- Higher engagement rates through optimized timing
- Better discoverability via researched hashtags
- Increased reach through strategic tagging
- Professional presentation across all platforms
- SEO-optimized content for long-term visibility

---

## 🔧 Technical Notes:

- All images uploaded to Cloudinary with direct URLs
- JSON files contain complete metadata for automation
- Fallback systems activated when primary services unavailable
- All content validated for platform-specific requirements
- User ID ensures file tracking and management

**Ready to dominate social media? Start posting! 🚀**

Your unique identifier: {self.user_id}
"""
        
        readme_filepath = os.path.join(PRODUCTION_OUTPUT_DIR, f"{self.user_id}_README_{self.timestamp}.md")
        with open(readme_filepath, 'w', encoding='utf-8') as f:
            f.write(readme_content)

    def _get_formatting_tips(self, platform_key: str) -> Dict[str, str]:
        """Get platform-specific formatting tips"""
        tips = {
            "medium": {
                "content_structure": "Use headings, subheadings, and bullet points for readability",
                "citations": "Include citations at the end or as inline links",
                "images": "Place images to break up text, use captions effectively",
                "engagement": "End with thought-provoking questions or call-to-action"
            },
            "blogger": {
                "content_structure": "Use HTML formatting for better presentation",
                "citations": "Link to sources naturally within the text",
                "images": "Optimize image sizes for fast loading",
                "seo": "Use SEO keywords naturally throughout the content"
            },
            "linkedin": {
                "post_structure": "Hook → Value → Call-to-action format works best",
                "line_breaks": "Use line breaks for easy scanning",
                "hashtags": "Place hashtags at the end, use 3-5 relevant ones",
                "tagging": "Tag relevant professionals and companies for visibility"
            },
            "x.com": {
                "character_limit": "Stay under 280 characters for single tweets",
                "threading": "Use threads for longer content (mark with 1/, 2/, etc.)",
                "hashtags": "1-2 trending hashtags maximum",
                "timing": "Tweet during peak hours for maximum engagement"
            },
            "facebook": {
                "post_length": "Keep posts under 2000 characters for better reach",
                "storytelling": "Use narrative elements to increase engagement",
                "call_to_action": "Ask questions to encourage comments",
                "visual_content": "Always include images or videos when possible"
            },
            "instagram_threads": {
                "tone": "Keep it casual and conversational",
                "length": "Under 500 characters works best",
                "hashtags": "Use 2-4 relevant hashtags",
                "engagement": "Encourage replies and shares with questions"
            }
        }
        
        return tips.get(platform_key, {
            "general": "Follow platform best practices for optimal engagement"
        })


def main():
    """Main function for multi-platform optimization with guaranteed results and compiler integration (production version)"""
    
    # Production mode - no interactive prompts, only terminal input validation
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} <article_file_path> <platforms> <image_platforms> <compile_final>")
        print("Example: python main.py article.txt 'linkedin,x.com' 'all' 'yes'")
        print("Platforms: medium,blogger,linkedin,x.com,facebook,instagram_threads or 'all'")
        print("Image platforms: platform names, 'all', or 'none'")
        print("Compile final: 'yes' or 'no'")
        sys.exit(1)
    
    file_path = sys.argv[1]
    platforms_input = sys.argv[2]
    image_platforms_input = sys.argv[3]
    compilation_input = sys.argv[4]
    
    try:
        # Generate unique user ID
        user_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Only output the user ID and timestamp to console for production tracking
        print(f"{user_id}:{timestamp}")
        
        # Initialize optimizer with user ID
        optimizer = MultiPlatformOptimizer(user_id)
        
        # Run optimization with parsed inputs
        results = optimizer.run_multi_platform_optimization(
            file_path, platforms_input, image_platforms_input, compilation_input
        )
        
        # Save results to shared directory with user ID
        optimizer.save_results_json(results)
        
        # Log completion
        logger.info(f"✅ Multi-platform optimization completed successfully for user {user_id}!")
        
    except Exception as e:
        logger.error(f"Multi-platform optimization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()