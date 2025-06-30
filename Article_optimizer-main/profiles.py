"""
Combined Social Media Account Discovery & Username Extraction Pipeline
This standalone script integrates profiles.py output with filteruser.py username extraction.
"""

import os
import json
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CombinedSocialMediaPipeline:
    """Combined pipeline for account discovery and username extraction"""
    
    def __init__(self):
        """Initialize the pipeline with API clients"""
        self.openai_client = self._init_openai()
        self.gemini_client = self._init_gemini()
        self.supported_platforms = [
            "instagram", 
            "threads", 
            "linkedin", 
            "twitter/x.com", 
            "blogger", 
            "medium", 
            "facebook"
        ]
    
    def _init_openai(self) -> Optional[OpenAI]:
        """Initialize OpenAI client"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            
            client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return None
    
    def _init_gemini(self) -> Optional[genai.Client]:
        """Initialize Gemini client"""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            
            client = genai.Client(api_key=api_key)
            logger.info("Gemini client initialized successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            return None
    
    def read_article_file(self, file_path: str) -> str:
        """Read article content from .txt file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
            logger.info(f"Successfully read article from {file_path}")
            return content
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
    
    def choose_platform(self) -> str:
        """Interactive platform selection"""
        print("\n🌐 Select a social media platform:")
        print("=" * 50)
        
        for i, platform in enumerate(self.supported_platforms, 1):
            print(f"{i}. {platform.title()}")
        
        while True:
            try:
                choice = input(f"\nEnter your choice (1-{len(self.supported_platforms)}): ").strip()
                choice_idx = int(choice) - 1
                
                if 0 <= choice_idx < len(self.supported_platforms):
                    selected_platform = self.supported_platforms[choice_idx]
                    print(f"✅ Selected platform: {selected_platform.title()}")
                    return selected_platform
                else:
                    print("❌ Invalid choice. Please try again.")
            except ValueError:
                print("❌ Please enter a valid number.")
    
    def analyze_article_content(self, article_content: str, platform: str) -> Dict[str, Any]:
        """Use OpenAI to analyze article and create targeted search strategy"""
        
        analysis_prompt = f"""
        You are an expert social media strategist and content analyst. Analyze the following article and create a comprehensive strategy for finding relevant accounts on {platform.upper()}.

        ARTICLE CONTENT:
        {article_content[:4000]}...

        TASK: Analyze this article and provide:

        1. **CONTENT THEMES** (3-5 main topics/themes)
        2. **TARGET ACCOUNT TYPES** (specific types of accounts to find)
        3. **KEYWORDS & HASHTAGS** (for searching)
        4. **GEOGRAPHIC FOCUS** (if applicable)
        5. **INDUSTRY FOCUS** (specific sectors/industries)
        6. **SEARCH QUERIES** (5-7 specific search queries for {platform})

        Respond in JSON format:
        {{
            "content_themes": ["theme1", "theme2", "theme3"],
            "target_account_types": [
                "account_type_1_description",
                "account_type_2_description"
            ],
            "keywords": ["keyword1", "keyword2", "keyword3"],
            "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
            "geographic_focus": "geographic_region",
            "industry_focus": ["industry1", "industry2"],
            "search_queries": [
                "search query 1 for {platform}",
                "search query 2 for {platform}",
                "search query 3 for {platform}",
                "search query 4 for {platform}",
                "search query 5 for {platform}"
            ],
            "platform_specific_tips": "Tips for finding accounts on {platform}"
        }}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert social media strategist. Always respond with valid JSON."
                    },
                    {
                        "role": "user", 
                        "content": analysis_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in analysis_text:
                json_start = analysis_text.find("```json") + 7
                json_end = analysis_text.find("```", json_start)
                analysis_text = analysis_text[json_start:json_end].strip()
            
            analysis = json.loads(analysis_text)
            logger.info("Article analysis completed successfully")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in article analysis: {e}")
            # Return fallback analysis
            return {
                "content_themes": ["general topic"],
                "target_account_types": ["relevant professionals", "industry experts"],
                "keywords": ["topic", "industry"],
                "hashtags": ["#topic"],
                "geographic_focus": "global",
                "industry_focus": ["general"],
                "search_queries": [f"topic related accounts on {platform}"],
                "platform_specific_tips": f"Search for relevant accounts on {platform}"
            }
    
    def create_gemini_search_prompt(self, analysis: Dict[str, Any], platform: str) -> str:
        """Create optimized prompt for Gemini to find specific accounts"""
        
        prompt_template = f"""
        I need you to find active and relevant {platform.upper()} accounts/usernames related to the following content analysis:

        📊 CONTENT THEMES: {', '.join(analysis['content_themes'])}
        🎯 TARGET ACCOUNT TYPES: {', '.join(analysis['target_account_types'])}
        🔍 KEYWORDS: {', '.join(analysis['keywords'])}
        🏷️ HASHTAGS: {', '.join(analysis['hashtags'])}
        🌍 GEOGRAPHIC FOCUS: {analysis['geographic_focus']}
        🏭 INDUSTRY FOCUS: {', '.join(analysis['industry_focus'])}

        SPECIFIC SEARCH QUERIES FOR {platform.upper()}:
        {chr(10).join([f"• {query}" for query in analysis['search_queries']])}

        REQUIREMENTS:
        1. Find ACTIVE accounts (recently posted content)
        2. Look for accounts with good engagement (likes, comments, shares)
        3. Focus on accounts that would be interested in this content
        4. Include both individual professionals and organizations
        5. Prioritize accounts with substantial followings (1K+ followers)

        PROVIDE RESULTS IN THIS FORMAT:
        **FOUND {platform.upper()} ACCOUNTS:**

        🏢 **ORGANIZATIONS/COMPANIES:**
        • @username1 - Description (follower count if available)
        • @username2 - Description (follower count if available)

        👤 **INDIVIDUAL PROFESSIONALS:**
        • @username3 - Description (follower count if available)
        • @username4 - Description (follower count if available)

        📰 **MEDIA/NEWS ACCOUNTS:**
        • @username5 - Description (follower count if available)

        🎓 **EDUCATIONAL/ACADEMIC:**
        • @username6 - Description (follower count if available)

        PLATFORM-SPECIFIC NOTES: {analysis.get('platform_specific_tips', '')}

        Please search for these accounts and provide working usernames with the @ symbol.
        """
        
        return prompt_template
    
    def find_accounts_with_gemini(self, search_prompt: str) -> str:
        """Use Gemini with search capability to find relevant accounts"""
        
        if not self.gemini_client:
            logger.error("Gemini client not initialized")
            return "❌ Gemini client not available"
        
        try:
            google_search_tool = Tool(google_search=GoogleSearch())
            
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=search_prompt,
                config=GenerateContentConfig(
                    tools=[google_search_tool],
                    response_modalities=["TEXT"],
                    temperature=0.3
                )
            )
            
            result = ""
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    result += part.text
            
            logger.info("Successfully found accounts using Gemini")
            return result
            
        except Exception as e:
            logger.error(f"Error finding accounts with Gemini: {e}")
            return f"❌ Error occurred while searching: {str(e)}"
    
    # USERNAME EXTRACTION METHODS (from filteruser.py)
    
    def extract_usernames_from_text(self, text_data: str) -> List[str]:
        """
        Extract valid usernames from text data using OpenAI LLM
        
        Args:
            text_data (str): Input text containing potential usernames
            
        Returns:
            List[str]: List of valid usernames with @ prefix
        """
        try:
            # Create a prompt for OpenAI to extract usernames
            prompt = f"""
            Analyze the following text and extract all valid social media usernames or handles.
            Look for:
            - Existing usernames (with or without @)
            - Organization names that could be converted to valid usernames
            - Page names that could be social media handles
            - Any text that represents social media accounts
            
            Rules for username extraction:
            1. Convert organization/page names to valid username format (remove spaces, special chars except underscore)
            2. Keep usernames between 3-30 characters
            3. Use only alphanumeric characters and underscores
            4. Make them lowercase
            5. If an organization name is too long, use a reasonable abbreviation
            
            Text to analyze:
            {text_data}
            
            Return ONLY the usernames, one per line, without the @ symbol. If no valid usernames can be extracted or created, return "NO_USERNAMES_FOUND".
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",  # or "gpt-3.5-turbo" for faster/cheaper processing
                messages=[
                    {"role": "system", "content": "You are a social media username extraction expert. Extract and format usernames according to the given rules."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # Extract the response content
            extracted_text = response.choices[0].message.content.strip()
            
            if extracted_text == "NO_USERNAMES_FOUND":
                logger.warning("No valid usernames found in the text")
                return []
            
            # Split by lines and clean up
            usernames = [line.strip() for line in extracted_text.split('\n') if line.strip()]
            
            # Validate and format usernames
            valid_usernames = []
            for username in usernames:
                # Remove @ if present
                username = username.lstrip('@')
                
                # Validate username format
                if self.validate_username(username):
                    valid_usernames.append(f"@{username}")
                else:
                    logger.warning(f"Invalid username format: {username}")
            
            return valid_usernames
            
        except Exception as e:
            logger.error(f"Error extracting usernames: {e}")
            return []

    def validate_username(self, username: str) -> bool:
        """
        Validate if a username meets standard social media criteria
        
        Args:
            username (str): Username to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Check length (3-30 characters)
        if len(username) < 3 or len(username) > 30:
            return False
        
        # Check for valid characters (alphanumeric and underscore only)
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False
        
        # Username should not start or end with underscore
        if username.startswith('_') or username.endswith('_'):
            return False
        
        # Should not have consecutive underscores
        if '__' in username:
            return False
        
        return True

    def save_usernames_to_file(self, usernames: List[str], output_file: str = "extracted_usernames.txt"):
        """
        Save extracted usernames to a file
        
        Args:
            usernames (List[str]): List of usernames with @ prefix
            output_file (str): Output file path
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                for username in usernames:
                    file.write(f"{username}\n")
            logger.info(f"Usernames saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving usernames to file: {e}")
    
    def save_results(self, results: str, usernames: List[str], platform: str, article_title: str = "article") -> str:
        """Save complete results to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{article_title}_{platform}_complete_results_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Social Media Account Discovery & Username Extraction Results\n")
                f.write(f"Platform: {platform.title()}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                
                # Raw discovery results
                f.write("🔍 ACCOUNT DISCOVERY RESULTS:\n")
                f.write("=" * 40 + "\n")
                f.write(results)
                f.write("\n\n")
                
                # Extracted usernames
                f.write("📝 EXTRACTED USERNAMES:\n")
                f.write("=" * 40 + "\n")
                if usernames:
                    f.write(f"Found {len(usernames)} valid usernames:\n\n")
                    for username in usernames:
                        f.write(f"{username}\n")
                else:
                    f.write("No valid usernames could be extracted.\n")
            
            logger.info(f"Complete results saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return ""
    
    def run_complete_pipeline(self, file_path: str) -> None:
        """Run the complete combined pipeline"""
        try:
            print("🚀 Starting Combined Social Media Discovery & Username Extraction Pipeline")
            print("=" * 80)
            
            # Step 1: Read article
            print("\n📖 Reading article...")
            article_content = self.read_article_file(file_path)
            print(f"✅ Article loaded ({len(article_content)} characters)")
            
            # Step 2: Choose platform
            platform = self.choose_platform()
            
            # Step 3: Analyze content with OpenAI
            print(f"\n🤖 Analyzing article content for {platform}...")
            analysis = self.analyze_article_content(article_content, platform)
            
            print("\n📊 Analysis Results:")
            print(f"   🎯 Themes: {', '.join(analysis['content_themes'])}")
            print(f"   🔍 Target Types: {len(analysis['target_account_types'])} account types identified")
            print(f"   🌍 Geographic Focus: {analysis['geographic_focus']}")
            
            # Step 4: Create search prompt
            print(f"\n🔍 Creating search strategy for {platform}...")
            search_prompt = self.create_gemini_search_prompt(analysis, platform)
            
            # Step 5: Find accounts with Gemini
            print(f"\n🌐 Searching for {platform} accounts...")
            discovery_results = self.find_accounts_with_gemini(search_prompt)
            
            # Step 6: Extract usernames from discovery results
            print(f"\n🔤 Extracting usernames from discovery results...")
            extracted_usernames = self.extract_usernames_from_text(discovery_results)
            
            # Step 7: Display results
            print("\n" + "=" * 80)
            print("🎉 COMPLETE PIPELINE RESULTS")
            print("=" * 80)
            
            print("\n🔍 ACCOUNT DISCOVERY RESULTS:")
            print("=" * 40)
            print(discovery_results)
            
            print(f"\n📝 EXTRACTED USERNAMES ({len(extracted_usernames)} found):")
            print("=" * 40)
            if extracted_usernames:
                for username in extracted_usernames:
                    print(username)
            else:
                print("No valid usernames could be extracted from the discovery results.")
            
            # Step 8: Save complete results
            filename = self.save_results(discovery_results, extracted_usernames, platform, "article_analysis")
            if filename:
                print(f"\n💾 Complete results saved to: {filename}")
            
            # Step 9: Save usernames separately
            if extracted_usernames:
                username_file = f"extracted_usernames_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                self.save_usernames_to_file(extracted_usernames, username_file)
                print(f"📝 Usernames also saved separately to: {username_file}")
            
            print("\n✅ Complete pipeline finished successfully!")
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            print(f"❌ Pipeline failed: {e}")


def main():
    """Main function to run the combined pipeline"""
    pipeline = CombinedSocialMediaPipeline()
    
    # Get file path from user
    file_path = input("\n📁 Enter the path to your article .txt file: ").strip()
    
    if not os.path.exists(file_path):
        print("❌ File not found. Please check the path and try again.")
        return
    
    # Run the complete pipeline
    pipeline.run_complete_pipeline(file_path)


if __name__ == "__main__":
    main()