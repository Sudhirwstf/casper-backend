#!/usr/bin/env python3
"""
Enhanced Multi-Platform Social Media Optimizer - Command Line Orchestration with Compiler Integration
A comprehensive tool for optimizing images and content across multiple social media platforms,
now with integrated product photography generation and automatic caption compilation.
"""


from dotenv import load_dotenv
load_dotenv()

import os
import sys
import argparse
import logging
import json
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
from PIL import Image
from dotenv import load_dotenv

# Import custom modules (ensure these are in the same directory)
try:
    from imgprocess import SocialMediaImageOptimizer
    from profiles import CombinedSocialMediaPipeline
    from hashkey import ArticleNicheHashtagAnalyzer
    from vision import ImageAnalyzer
    from photography import ProductPhotoGenerator
    from logo import add_logo_to_image
    from compiler import SocialMediaCaptionCompiler  
except ImportError:
    print("❌ Error: compiler.py not found. Please ensure compiler.py is in the same directory.")
    # Create a dummy class to prevent crashes
    class SocialMediaCaptionCompiler:
        def __init__(self, api_key=None):
            pass
        def compile_from_json(self, json_path, output_dir):
            print("⚠️ Compiler not available - skipping caption compilation")
            return []
except ImportError as e:
    print(f"❌ Error importing custom modules: {e}")
    print("Make sure all required modules are in the same directory as this script.")
    sys.exit(1)

# Load environment variables
load_dotenv()

class EnhancedMultiPlatformSocialMediaOrchestrator:
    """Enhanced command-line orchestrator for multi-platform social media optimization with product photography and compiler integration"""
    
    SUPPORTED_PLATFORMS = {
        "instagram": {"name": "Instagram", "hashtag_range": (15, 30), "emoji": "📷"},
        "facebook": {"name": "Facebook", "hashtag_range": (2, 5), "emoji": "👥"},
        "x.com": {"name": "X.com (Twitter)", "hashtag_range": (1, 3), "emoji": "🐦"},
        "linkedin": {"name": "LinkedIn", "hashtag_range": (3, 5), "emoji": "💼"},
        "pinterest": {"name": "Pinterest", "hashtag_range": (5, 15), "emoji": "📌"},
    }
    
    PLATFORM_IMAGE_FORMATS = {
        "instagram": "auto",
        "facebook": "landscape",
        "x.com": "landscape",
        "linkedin": "landscape",
        "pinterest": "portrait",
    }
    
    def __init__(self, api_key: Optional[str] = None, log_level: str = "INFO"):
        """Initialize the enhanced orchestrator with compiler"""
        self.session_id = str(uuid.uuid4())
        self.user_uuid = str(uuid.uuid4())[:8]  # Generate user UUID once at initialization
        self.setup_logging(log_level)
        self.setup_api_key(api_key)
        
        # Setup directories first
        self.results_dir = Path("social_media_output")
        self.results_dir.mkdir(exist_ok=True)
        
        # Product photography specific
        self.product_images_dir = Path("product_photography_output")
        self.product_images_dir.mkdir(exist_ok=True)
        self.logo_path = None
        self.perform_product_photography = False
        
        # Initialize components after directories are set up
        self.setup_components()
        
        # Track generated JSON files for compilation
        self.generated_json_files = []
    
    def setup_logging(self, log_level: str):
        """Setup logging configuration"""
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {log_level}')
        
        logging.basicConfig(
            level=numeric_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(f'social_media_optimizer_{self.session_id}.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_api_key(self, api_key: Optional[str] = None):
        """Setup OpenAI API key"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            self.logger.error("❌ OpenAI API key not found. Set OPENAI_API_KEY environment variable or use --api-key flag")
            sys.exit(1)
        
        self.logger.info("✅ API Key configured successfully")
    
    def setup_components(self):
        """Initialize all optimizer components including compiler"""
        try:
            self.image_optimizer = SocialMediaImageOptimizer()
            self.image_analyzer = ImageAnalyzer(api_key=self.api_key)
            self.profile_pipeline = CombinedSocialMediaPipeline()
            self.hashtag_analyzer = ArticleNicheHashtagAnalyzer(api_key=self.api_key)
            self.product_photo_generator = ProductPhotoGenerator(api_key=self.api_key, output_dir=str(self.product_images_dir))
            
            # Initialize compiler
            self.caption_compiler = SocialMediaCaptionCompiler(api_key=self.api_key)
            
            self.logger.info("✅ All components initialized successfully (including compiler)")
        except Exception as e:
            self.logger.error(f"❌ Error initializing components: {e}")
            sys.exit(1)
    
    def detect_product_in_image(self, image_path: str) -> Dict[str, any]:
        """
        Detect if the image contains a product that covers 70% of the image
        or has a plain background with no humans
        """
        self.logger.info(f"🔍 Analyzing image for product detection: {image_path}")
        
        detection_prompt = (
            "Analyze this image carefully and provide the following information:\n"
            "1. Is there a clear product or object that covers approximately 70% or more of the image?\n"
            "2. If not 70%, does it have a plain/solid background with no humans visible?\n"
            "3. What is the main product/object in the image?\n"
            "4. Estimate the percentage of the image covered by the main product/object\n"
            "5. Are there any people/humans visible in the image?\n"
            "6. Describe the background (plain, cluttered, natural, etc.)\n"
            "7. Would this image be suitable for product photography enhancement?\n\n"
            "Please format your response as JSON with the following structure:\n"
            "{\n"
            "  \"product_detected\": true/false,\n"
            "  \"product_name\": \"name of the product\",\n"
            "  \"coverage_percentage\": number,\n"
            "  \"has_plain_background\": true/false,\n"
            "  \"humans_present\": true/false,\n"
            "  \"background_description\": \"description\",\n"
            "  \"suitable_for_product_photography\": true/false,\n"
            "  \"recommendation\": \"explanation of why it's suitable or not\"\n"
            "}"
        )
        
        try:
            analysis_result = self.image_analyzer.analyze_image_from_file(
                image_path, 
                prompt=detection_prompt
            )
            
            # Try to parse JSON from the response
            try:
                # Extract JSON from response if it's wrapped in text
                if "```json" in analysis_result:
                    start = analysis_result.find("```json") + 7
                    end = analysis_result.find("```", start)
                    json_str = analysis_result[start:end].strip()
                else:
                    # Try to find JSON-like content
                    start = analysis_result.find("{")
                    end = analysis_result.rfind("}") + 1
                    json_str = analysis_result[start:end]
                
                detection_data = json.loads(json_str)
                
                # Determine if product photography should be offered
                product_suitable = (
                    detection_data.get("product_detected", False) and
                    (detection_data.get("coverage_percentage", 0) >= 70 or
                     (detection_data.get("has_plain_background", False) and 
                      not detection_data.get("humans_present", True)))
                )
                
                detection_data["suitable_for_product_photography"] = product_suitable
                
                self.logger.info(f"🎯 Product detection complete: {detection_data.get('product_name', 'Unknown')}")
                return detection_data
                
            except json.JSONDecodeError:
                self.logger.warning("⚠️ Could not parse JSON from analysis, creating fallback response")
                return {
                    "product_detected": False,
                    "product_name": "Unknown",
                    "coverage_percentage": 0,
                    "has_plain_background": False,
                    "humans_present": True,
                    "background_description": "Could not analyze",
                    "suitable_for_product_photography": False,
                    "recommendation": "Analysis failed, proceeding with normal optimization"
                }
            
        except Exception as e:
            self.logger.error(f"❌ Error during product detection: {e}")
            return {
                "product_detected": False,
                "product_name": "Error in detection",
                "coverage_percentage": 0,
                "has_plain_background": False,
                "humans_present": True,
                "background_description": "Error occurred",
                "suitable_for_product_photography": False,
                "recommendation": f"Error occurred: {e}"
            }
    
    def ask_user_for_product_photography(self, detection_data: Dict[str, any]) -> bool:
        """Ask user if they want to perform product photography"""
        print(f"\n🎯 Product Detection Results:")
        print(f"{'='*50}")
        print(f"📦 Product Detected: {detection_data.get('product_name', 'Unknown')}")
        print(f"📊 Coverage: {detection_data.get('coverage_percentage', 0)}%")
        print(f"🖼️ Background: {detection_data.get('background_description', 'Unknown')}")
        print(f"👥 Humans Present: {'Yes' if detection_data.get('humans_present', False) else 'No'}")
        print(f"💡 Recommendation: {detection_data.get('recommendation', 'No recommendation')}")
        print(f"{'='*50}")
        
        if detection_data.get("suitable_for_product_photography", False):
            while True:
                response = input("\n🎨 Would you like to perform product photography enhancement? (y/n): ").strip().lower()
                if response in ['y', 'yes']:
                    return True
                elif response in ['n', 'no']:
                    return False
                else:
                    print("❌ Please enter 'y' for yes or 'n' for no.")
        else:
            print("\n⚠️ Image not suitable for product photography enhancement.")
            print("Proceeding with standard optimization...")
            return False
    
    def get_logo_from_user(self) -> Optional[str]:
        """Ask user for logo image path"""
        while True:
            logo_path = input("\n📁 Enter the path to your logo image (or press Enter to skip): ").strip()
            
            if not logo_path:
                return None
            
            if os.path.exists(logo_path):
                try:
                    # Validate it's an image
                    with Image.open(logo_path) as img:
                        img.verify()
                    self.logger.info(f"✅ Logo image validated: {logo_path}")
                    return logo_path
                except Exception as e:
                    print(f"❌ Invalid image file: {e}")
                    continue
            else:
                print("❌ File not found. Please check the path and try again.")
    
    def get_product_photography_settings(self, product_name: str) -> Dict[str, any]:
        """Get product photography settings from user"""
        print(f"\n🎨 Product Photography Settings for: {product_name}")
        print("="*60)
        
        # Get photography types
        photography_types = self.product_photo_generator.get_photography_types()
        print("\n📸 Choose a photography style:")
        for i, ptype in enumerate(photography_types, 1):
            print(f"   {i}. {ptype}")
        
        while True:
            try:
                choice = int(input(f"Enter your choice (1-{len(photography_types)}): "))
                if 1 <= choice <= len(photography_types):
                    photography_type = photography_types[choice - 1]
                    break
            except ValueError:
                pass
            print("❌ Invalid choice. Please try again.")
        
        # Get background color if needed
        background_color = None
        if photography_type == "SOLID BACKGROUND":
            colors = self.product_photo_generator.get_background_colors()
            print("\n🎨 Choose a background color:")
            for i, color in enumerate(colors, 1):
                print(f"   {i}. {color}")
            
            while True:
                try:
                    choice = int(input(f"Enter your color choice (1-{len(colors)}): "))
                    if 1 <= choice <= len(colors):
                        background_color = colors[choice - 1]
                        break
                except ValueError:
                    pass
                print("❌ Invalid choice. Please try again.")
        
        return {
            "photography_type": photography_type,
            "background_color": background_color
        }
    
    def generate_product_photography(self, image_path: str, product_name: str, platforms: List[str], settings: Dict[str, any]) -> Dict[str, str]:
        """Generate product photography for all platforms and return Cloudinary URLs"""
        self.logger.info(f"🎨 Generating product photography for {len(platforms)} platforms")
        
        try:
            # Generate product photography with Cloudinary upload enabled
            results = self.product_photo_generator.generate_photos_for_platforms(
                product_name=product_name,
                photography_type=settings["photography_type"],
                platforms=platforms,
                image_path=image_path,
                background_color=settings.get("background_color"),
                upload_to_cloudinary=True,  # Enable Cloudinary upload
                delay_between_requests=1.0
            )
            
            # Process results to get Cloudinary URLs or local paths
            product_images = {}
            for platform, (success, result_url) in results.items():
                if success and result_url:
                    # If we have a logo, we need to download, add logo, and re-upload
                    if self.logo_path and result_url.startswith('http'):
                        try:
                            import requests
                            import tempfile
                            
                            # Download the image from Cloudinary
                            response = requests.get(result_url)
                            if response.status_code == 200:
                                # Create temporary file for the downloaded image
                                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                                    temp_file.write(response.content)
                                    temp_path = temp_file.name
                                
                                # Add logo to the downloaded image
                                logo_enhanced_path = str(Path(temp_path).parent / f"logo_{platform}_{Path(temp_path).name}")
                                final_image = add_logo_to_image(
                                    image_data=temp_path,
                                    logo_data=self.logo_path,
                                    logo_size_percent=12,
                                    output_path=logo_enhanced_path,
                                    position="bottom-right"
                                )
                                
                                # Upload the logo-enhanced image back to Cloudinary
                                cloudinary_url = self.product_photo_generator.cloudinary.upload_image(
                                    logo_enhanced_path,
                                    public_id=f"{product_name.lower().replace(' ', '_')}_{platform}_with_logo"
                                )
                                
                                if cloudinary_url:
                                    product_images[platform] = cloudinary_url
                                    self.logger.info(f"✅ Logo added and uploaded to Cloudinary for {platform}")
                                else:
                                    product_images[platform] = result_url  # Fallback to original
                                    self.logger.warning(f"⚠️ Failed to upload logo version, using original for {platform}")
                                
                                # Cleanup temporary files
                                try:
                                    os.unlink(temp_path)
                                    os.unlink(logo_enhanced_path)
                                except:
                                    pass
                            else:
                                product_images[platform] = result_url
                                self.logger.warning(f"⚠️ Failed to download image for logo addition: {platform}")
                        except Exception as e:
                            self.logger.warning(f"⚠️ Failed to add logo to {platform}: {e}")
                            product_images[platform] = result_url  # Use original without logo
                    else:
                        # No logo or result is local path
                        product_images[platform] = result_url
                        if result_url.startswith('http'):
                            self.logger.info(f"✅ Product photo uploaded to Cloudinary for {platform}")
                        else:
                            self.logger.info(f"✅ Product photo saved locally for {platform}")
                else:
                    self.logger.error(f"❌ Failed to generate product photography for {platform}")
            
            return product_images
            
        except Exception as e:
            self.logger.error(f"❌ Error generating product photography: {e}")
            return {}
    
    def validate_image_file(self, image_path: str) -> bool:
        """Validate that the image file exists and is readable"""
        path = Path(image_path)
        
        if not path.exists():
            self.logger.error(f"❌ Image file not found: {image_path}")
            return False
        
        if not path.is_file():
            self.logger.error(f"❌ Path is not a file: {image_path}")
            return False
        
        # Check if it's a valid image
        try:
            with Image.open(path) as img:
                img.verify()
            self.logger.info(f"✅ Valid image file: {image_path}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Invalid image file {image_path}: {e}")
            return False
    
    def get_image_description(self, image_path: str, user_description: Optional[str] = None, 
                            use_ai_analysis: bool = False) -> str:
        """Get image description based on user preference"""
        
        if user_description and user_description.strip():
            self.logger.info("👤 Using user-provided description")
            if use_ai_analysis:
                self.logger.info("🔄 Combining user description with AI analysis")
                ai_description = self.analyze_image_with_ai(image_path)
                if "Error analyzing image" not in ai_description:
                    combined_description = f"""
                    USER DESCRIPTION:
                    {user_description}
                    
                    AI ANALYSIS:
                    {ai_description}
                    
                    COMBINED CONTEXT:
                    The user describes this image as: {user_description}. 
                    AI analysis reveals: {ai_description[:200]}...
                    """
                    return combined_description
                else:
                    self.logger.warning("AI analysis failed, using only user description")
                    return user_description
            else:
                return user_description
        
        elif use_ai_analysis:
            self.logger.info("🤖 Using AI-powered image analysis")
            return self.analyze_image_with_ai(image_path)
        
        else:
            self.logger.warning("No image description provided and AI analysis disabled")
            return f"Image content from {Path(image_path).name}. Please provide a description for better optimization."
    
    def analyze_image_with_ai(self, image_path: str) -> str:
        """Analyze image content using AI vision"""
        self.logger.info(f"🖼️ Analyzing image content: {image_path}")
        
        analysis_prompt = (
            "Analyze this image for social media optimization. Describe:\n"
            "1. Main subjects, objects, and people in the image\n"
            "2. Colors, lighting, and visual composition\n"
            "3. Mood, atmosphere, and emotions conveyed\n"
            "4. Any text, brands, logos, or products visible\n"
            "5. Setting, location, or environment\n"
            "6. Potential target audience and use cases\n"
            "7. Overall vibe and story the image tells\n"
            "Provide a comprehensive description for hashtag and content optimization."
        )
        
        try:
            image_description = self.image_analyzer.analyze_image_from_file(
                image_path, 
                prompt=analysis_prompt
            )
            
            if "Error analyzing image" in image_description:
                self.logger.error(f"❌ Image analysis failed: {image_description}")
                return image_description
            
            return image_description
            
        except Exception as e:
            error_msg = f"Error analyzing image: {e}"
            self.logger.error(f"❌ {error_msg}")
            return error_msg
    
    def create_content_article(self, image_description: str, platform: str) -> str:
        """Create a content article from image description"""
        self.logger.info(f"📝 Creating content article for {platform}")
        
        article_content = f"""
        Social Media Content Analysis for {platform.title()}
        
        Content Description:
        {image_description}
        
        This content is being optimized for {platform} to maximize engagement and reach.
        The image contains elements that would appeal to audiences interested in the themes
        and subjects described above.
        
        Target Platform: {platform}
        Content Type: Visual Social Media Post
        Optimization Goal: Maximum engagement and discoverability
        """
        
        return article_content
    
    def get_hashtags(self, content_article: str, platform: str) -> tuple:
        """Get hashtags for a specific platform"""
        self.logger.info(f"🔍 Analyzing hashtags for {platform}")
        
        try:
            # Create temporary file for the article
            temp_file = Path(tempfile.gettempdir()) / f"temp_article_{platform}_{self.session_id}.txt"
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content_article)
            
            # Get niches
            niches = self.hashtag_analyzer.get_niches(content_article)
            self.logger.info(f"🎯 Extracted niches for {platform}: {niches}")
            
            # Get hashtag data for each niche using the correct method name
            all_hashtag_text = ""
            
            for niche in niches:
                hashtag_text = self.hashtag_analyzer.scrape_hashtags_from_multiple_sources(niche)
                all_hashtag_text += hashtag_text + "\n"
            
            # Generate hashtags
            hashtags = self.hashtag_analyzer.analyze_hashtags(all_hashtag_text, platform)
            
            # Format hashtags properly
            if hashtags and not hashtags.startswith('#'):
                hashtag_list = [f"#{tag.strip()}" for tag in hashtags.split(',') if tag.strip()]
                hashtags = ' '.join(hashtag_list)
            
            # Clean up temp file
            temp_file.unlink(missing_ok=True)
            
            return hashtags, niches
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing hashtags for {platform}: {e}")
            return "", []
    
    def get_profile_suggestions(self, content_description: str, platform: str) -> dict:
        """Get profile suggestions and usernames for a platform"""
        self.logger.info(f"👥 Finding profile suggestions for {platform}")
        
        try:
            # Analyze article content
            analysis = self.profile_pipeline.analyze_article_content(content_description, platform)
            
            # Create search prompt
            search_prompt = self.profile_pipeline.create_gemini_search_prompt(analysis, platform)
            
            # Find accounts with Gemini
            discovery_results = self.profile_pipeline.find_accounts_with_gemini(search_prompt)
            
            # Extract usernames
            extracted_usernames = self.profile_pipeline.extract_usernames_from_text(discovery_results)
            
            return {
                "platform": platform,
                "content_analysis": analysis,
                "discovery_results": discovery_results,
                "extracted_usernames": extracted_usernames,
                "total_usernames": len(extracted_usernames)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting profile suggestions for {platform}: {e}")
            return {
                "platform": platform,
                "content_analysis": {},
                "discovery_results": f"Error occurred: {str(e)}",
                "extracted_usernames": [],
                "total_usernames": 0,
                "error": str(e)
            }
    
    def process_single_platform(self, image_path: str, platform: str, content_description: str, 
                               output_format: str, product_images: Dict[str, str] = None) -> dict:
        """Process optimization for a single platform"""
        start_time = time.time()
        platform_emoji = self.SUPPORTED_PLATFORMS[platform]["emoji"]
        self.logger.info(f"🔄 Processing {platform} {platform_emoji}...")
        
        try:
            # Use product photography image if available, otherwise process original
            if product_images and platform in product_images:
                processed_image_path = product_images[platform]
                self.logger.info(f"🎨 Using product photography image for {platform}")
            else:
                # Process image for platform
                target_format = self.PLATFORM_IMAGE_FORMATS.get(platform, "auto")
                platform_output_dir = self.results_dir / platform.lower()
                platform_output_dir.mkdir(parents=True, exist_ok=True)
                
                processed_image_path = self.image_optimizer.process_image(
                    image_path, 
                    str(platform_output_dir), 
                    target_format, 
                    output_format, 
                    enhance_quality=True
                )
            
            # Create content article
            content_article = self.create_content_article(content_description, platform)
            
            # Get hashtags
            hashtags, niches = self.get_hashtags(content_article, platform)
            
            # Get profile suggestions
            profile_results = self.get_profile_suggestions(content_article, platform)
            
            processing_time = time.time() - start_time
            self.logger.info(f"✅ {platform} {platform_emoji} completed in {processing_time:.2f}s")
            
            return {
                "platform": platform,
                "processed_image": processed_image_path,
                "niches": niches,
                "hashtags": hashtags,
                "profile_results": profile_results,
                "processing_time": processing_time,
                "status": "success",
                "product_photography_used": platform in (product_images or {})
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"❌ Error processing {platform}: {e}")
            return {
                "platform": platform,
                "processed_image": None,
                "niches": [],
                "hashtags": "",
                "profile_results": {},
                "processing_time": processing_time,
                "status": "error",
                "error": str(e),
                "product_photography_used": False
            }
    
    def run_optimization(self, image_path: str, platforms: List[str], user_description: Optional[str] = None, 
                        use_ai_analysis: bool = False, output_format: str = "PNG", max_workers: int = 3) -> Dict[str, dict]:
        """Run optimization for multiple platforms with product photography integration"""
        total_start_time = time.time()
        
        self.logger.info(f"🚀 Starting enhanced multi-platform optimization for {len(platforms)} platform(s)")
        self.logger.info(f"📸 Image: {image_path}")
        self.logger.info(f"🎯 Platforms: {', '.join(platforms)}")
        self.logger.info(f"🆔 Session ID: {self.session_id}")
        
        # Step 1: Product Detection
        self.logger.info("🔍 Performing product detection...")
        detection_data = self.detect_product_in_image(image_path)
        
        # Step 2: Ask for product photography if suitable
        product_images = {}
        if detection_data.get("suitable_for_product_photography", False):
            self.perform_product_photography = self.ask_user_for_product_photography(detection_data)
            
            if self.perform_product_photography:
                # Get logo if user wants it
                self.logo_path = self.get_logo_from_user()
                
                # Get product photography settings
                product_name = detection_data.get("product_name", "Product")
                settings = self.get_product_photography_settings(product_name)
                
                # Generate product photography for all platforms
                self.logger.info("🎨 Generating product photography...")
                product_images = self.generate_product_photography(
                    image_path, product_name, platforms, settings
                )
        
        # Step 3: Get image description based on user preference
        self.logger.info("📸 Getting image description...")
        content_description = self.get_image_description(image_path, user_description, use_ai_analysis)
        
        if "Error analyzing image" in content_description and not user_description:
            self.logger.error(f"❌ Image description failed: {content_description}")
            return {}
        
        # Step 4: Process platforms in parallel
        self.logger.info(f"🔄 Processing {len(platforms)} platform(s) in parallel...")
        
        results = {}
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=min(len(platforms), max_workers)) as executor:
            # Submit tasks
            futures = {
                executor.submit(
                    self.process_single_platform,
                    image_path,
                    platform,
                    content_description,
                    output_format,
                    product_images
                ): platform 
                for platform in platforms
            }
            
            # Collect results
            completed = 0
            for future in as_completed(futures):
                platform = futures[future]
                try:
                    result = future.result()
                    results[platform] = result
                    completed += 1
                    
                    status = "✅" if result["status"] == "success" else "❌"
                    photo_status = "🎨" if result.get("product_photography_used", False) else "📷"
                    self.logger.info(f"{status} {photo_status} {platform} completed ({completed}/{len(platforms)})")
                    
                except Exception as e:
                    self.logger.error(f"❌ Error processing {platform}: {e}")
                    results[platform] = {
                        "platform": platform,
                        "status": "error",
                        "error": str(e),
                        "product_photography_used": False
                    }
        
        total_time = time.time() - total_start_time
        successful_platforms = len([r for r in results.values() if r.get("status") == "success"])
        
        self.logger.info(f"🎉 Enhanced multi-platform optimization complete!")
        self.logger.info(f"⏱️ Total time: {total_time:.2f}s")
        self.logger.info(f"✅ Successful: {successful_platforms}/{len(platforms)} platforms")
        if self.perform_product_photography:
            self.logger.info(f"🎨 Product photography: Generated for {len(product_images)} platforms")
        
        # Save results with product photography info
        json_files = self.save_enhanced_results(results, content_description, user_description, image_path, detection_data, product_images)
        
        # Step 5: NEW - Automatically compile captions from JSON files
        self.compile_captions_from_results(json_files)
        
        return results
    
    def save_enhanced_results(self, results: Dict[str, dict], content_description: str, 
                            user_description: Optional[str], image_path: str, 
                            detection_data: Dict[str, any], product_images: Dict[str, str]) -> List[str]:
        """Save enhanced optimization results to JSON files with product photography info and return list of JSON file paths"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create JSON output directory
        json_output_dir = self.results_dir / "json_results"
        json_output_dir.mkdir(parents=True, exist_ok=True)
        
        json_files = []
        
        # Use the consistent user UUID from initialization (NOT generating new one)
        user_uuid = self.user_uuid
        
        # Save individual platform results with SAME UUID for all platforms
        for platform, result in results.items():
            if result.get("status") == "success":
                platform_data = {
                    "session_id": self.session_id,
                    "user_uuid": user_uuid,  # SAME UUID for all platforms
                    "timestamp": timestamp,
                    "source_image": str(image_path),
                    "platform": platform,
                    "content_description": content_description,
                    "user_description": user_description,
                    "niches": result.get("niches", []),
                    "hashtags": result.get("hashtags", ""),
                    "profile_results": result.get("profile_results", {}),
                    "processed_image": result.get("processed_image", ""),
                    "processing_time": result.get("processing_time", 0),
                    "product_photography_data": {
                        "detection_results": detection_data,
                        "product_photography_performed": self.perform_product_photography,
                        "product_photography_used": result.get("product_photography_used", False),
                        "logo_used": self.logo_path is not None,
                        "logo_path": self.logo_path
                    },
                    "optimization_metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "platform_format": self.PLATFORM_IMAGE_FORMATS.get(platform, "auto"),
                        "hashtag_range": self.SUPPORTED_PLATFORMS[platform]["hashtag_range"]
                    }
                }
                
                # Save individual platform JSON with SAME user UUID
                platform_file = json_output_dir / f"{user_uuid}_{platform}_final_data_{timestamp}.json"
                with open(platform_file, 'w', encoding='utf-8') as f:
                    json.dump(platform_data, f, indent=2, ensure_ascii=False)
                
                json_files.append(str(platform_file))
                self.logger.info(f"💾 Saved {platform} results: {platform_file}")
        
        # Save combined results with SAME UUID
        combined_data = {
            "session_id": self.session_id,
            "user_uuid": user_uuid,  # SAME UUID for consistency
            "timestamp": timestamp,
            "source_image": str(image_path),
            "content_description": content_description,
            "user_description": user_description,
            "platforms": results,
            "product_photography_session": {
                "detection_results": detection_data,
                "product_photography_performed": self.perform_product_photography,
                "product_images_generated": product_images,
                "logo_used": self.logo_path is not None,
                "logo_path": self.logo_path
            },
            "optimization_metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_platforms": len(results),
                "successful_platforms": len([r for r in results.values() if r.get("status") == "success"]),
                "total_processing_time": sum([r.get("processing_time", 0) for r in results.values()]),
                "enhanced_features_used": {
                    "product_detection": True,
                    "product_photography": self.perform_product_photography,
                    "logo_integration": self.logo_path is not None
                }
            }
        }
        
        # Combined file also uses same UUID
        combined_file = json_output_dir / f"{user_uuid}_combined_final_data_{timestamp}.json"
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        
        json_files.append(str(combined_file))
        self.logger.info(f"💾 Saved combined results: {combined_file}")
        
        # Store timestamp for compiler to use same timestamp
        self.current_timestamp = timestamp
        
        return json_files
    
    def compile_captions_from_results(self, json_files: List[str]) -> List[str]:
        """Compile captions from JSON files using the compiler module"""
        self.logger.info("📝 Starting automatic caption compilation...")
        
        compiled_files = []
        
        # Create compiled captions directory
        compiled_output_dir = self.results_dir / "compiled_captions"
        compiled_output_dir.mkdir(parents=True, exist_ok=True)
        
        for json_file in json_files:
            try:
                # Skip combined files, process only individual platform files
                if "_combined_" in os.path.basename(json_file):
                    continue
                
                self.logger.info(f"📋 Compiling caption for: {os.path.basename(json_file)}")
                
                # Use the compiler to process the JSON file
                generated_files = self.caption_compiler.compile_from_json(json_file, str(compiled_output_dir))
                
                if generated_files:
                    compiled_files.extend(generated_files)
                    for file_path in generated_files:
                        self.logger.info(f"✅ Caption compiled: {os.path.basename(file_path)}")
                else:
                    self.logger.warning(f"⚠️ No captions generated for: {os.path.basename(json_file)}")
                    
            except Exception as e:
                self.logger.error(f"❌ Error compiling captions for {json_file}: {e}")
                continue
        
        # Print compilation summary
        if compiled_files:
            self.logger.info(f"🎉 Caption compilation complete! Generated {len(compiled_files)} files")
            print(f"\n📝 CAPTION COMPILATION SUMMARY:")
            print(f"{'='*60}")
            print(f"✅ Generated {len(compiled_files)} ready-to-post caption files")
            print(f"📁 Location: {compiled_output_dir}")
            print(f"\n📋 Compiled files:")
            for i, file_path in enumerate(compiled_files, 1):
                print(f"   {i}. {os.path.basename(file_path)}")
            print(f"{'='*60}")
        else:
            self.logger.warning("⚠️ No caption files were generated")
        
        return compiled_files
    
    def print_results_summary(self, results: Dict[str, dict]):
        """Print a comprehensive summary of optimization results with product photography and compilation info"""
        print("\n" + "="*80)
        print("🎉 ENHANCED MULTI-PLATFORM OPTIMIZATION RESULTS")
        print("="*80)
        
        successful = [p for p, r in results.items() if r.get("status") == "success"]
        failed = [p for p, r in results.items() if r.get("status") == "error"]
        product_photo_used = [p for p, r in results.items() if r.get("product_photography_used", False)]
        
        print(f"📊 Summary:")
        print(f"   ✅ Successful: {len(successful)} platforms")
        print(f"   ❌ Failed: {len(failed)} platforms")
        print(f"   🎨 Product Photography: {len(product_photo_used)} platforms")
        print(f"   🆔 Session ID: {self.session_id}")
        
        if self.perform_product_photography:
            print(f"\n🎨 Product Photography Details:")
            print(f"   📦 Logo Integration: {'Yes' if self.logo_path else 'No'}")
            print(f"   📁 Product Images Directory: {self.product_images_dir}")
        
        if successful:
            print(f"\n✅ Successfully optimized platforms:")
            for platform in successful:
                result = results[platform]
                emoji = self.SUPPORTED_PLATFORMS[platform]["emoji"]
                hashtag_count = len(result.get("hashtags", "").split()) if result.get("hashtags") else 0
                username_count = len(result.get("profile_results", {}).get("extracted_usernames", []))
                photo_type = "🎨 Product Photo" if result.get("product_photography_used", False) else "📷 Standard"
                print(f"   {emoji} {platform.title()}: {hashtag_count} hashtags, {username_count} usernames ({photo_type})")
        
        if failed:
            print(f"\n❌ Failed platforms:")
            for platform in failed:
                emoji = self.SUPPORTED_PLATFORMS[platform]["emoji"]
                error = results[platform].get("error", "Unknown error")
                print(f"   {emoji} {platform.title()}: {error}")
        
        print(f"\n📁 Results saved to:")
        print(f"   📊 Standard Images: {self.results_dir}")
        print(f"   📋 JSON Results: {self.results_dir / 'json_results'}")
        print(f"   📝 Compiled Captions: {self.results_dir / 'compiled_captions'}")
        if self.perform_product_photography:
            print(f"   🎨 Product Photos: {self.product_images_dir}")
        
        print(f"\n🎯 Ready-to-Use Content:")
        print(f"   📝 Check 'compiled_captions' folder for ready-to-post content")
        print(f"   📋 Each platform has optimized captions with posting tips")
        print(f"   🕐 Best posting times included in caption files")
        print("="*80)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Enhanced Multi-Platform Social Media Optimizer with Product Photography and Auto-Compilation - Optimize images and content for multiple social platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s image.jpg --platforms instagram facebook --description "Beautiful sunset at the beach"
  %(prog)s photo.png --platforms all --use-ai
  %(prog)s image.jpg --platforms linkedin x.com --description "Professional photo" --use-ai
  %(prog)s photo.jpg --platforms instagram --description "My description" --use-ai --format JPG
  %(prog)s batch.txt --batch --platforms instagram pinterest --description "Batch photos"
        """
    )
    
    # Required arguments
    parser.add_argument(
        "input",
        help="Input image file path or batch file (with --batch flag)"
    )
    
    # Platform selection
    platforms_group = parser.add_mutually_exclusive_group(required=True)
    platforms_group.add_argument(
        "--platforms",
        nargs="+",
        choices=list(EnhancedMultiPlatformSocialMediaOrchestrator.SUPPORTED_PLATFORMS.keys()) + ["all"],
        help="Target platforms for optimization"
    )
    
    # Image description options
    description_group = parser.add_argument_group('Image Description Options')
    description_group.add_argument(
        "--description",
        "-d",
        help="User-provided description of the image content"
    )
    
    description_group.add_argument(
        "--use-ai",
        action="store_true",
        help="Use AI-powered image analysis (can be combined with --description)"
    )
    
    # Product photography options
    product_group = parser.add_argument_group('Product Photography Options')
    product_group.add_argument(
        "--skip-product-detection",
        action="store_true",
        help="Skip product detection and proceed with standard optimization"
    )
    
    product_group.add_argument(
        "--force-product-photography",
        action="store_true",
        help="Force product photography generation without detection"
    )
    
    product_group.add_argument(
        "--logo-path",
        help="Path to logo image file for product photography"
    )
    
    # Compilation options
    compilation_group = parser.add_argument_group('Caption Compilation Options')
    compilation_group.add_argument(
        "--skip-compilation",
        action="store_true",
        help="Skip automatic caption compilation after optimization"
    )
    
    compilation_group.add_argument(
        "--compilation-only",
        help="Run compilation only on existing JSON files (provide path to JSON file or directory)"
    )
    
    # Optional arguments
    parser.add_argument(
        "--format",
        choices=["PNG", "JPG"],
        default="PNG",
        help="Output image format (default: PNG)"
    )
    
    parser.add_argument(
        "--api-key",
        help="OpenAI API key (can also use OPENAI_API_KEY env var)"
    )
    
    parser.add_argument(
        "--max-workers",
        type=int,
        default=3,
        help="Maximum number of parallel workers (default: 3)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process multiple images from a text file (one image path per line)"
    )
    
    parser.add_argument(
        "--output-dir",
        help="Custom output directory (default: social_media_output)"
    )
    
    return parser


def process_batch_file(batch_file: str, orchestrator: EnhancedMultiPlatformSocialMediaOrchestrator, 
                      platforms: List[str], description: str, use_ai: bool, output_format: str, max_workers: int):
    """Process multiple images from a batch file"""
    try:
        with open(batch_file, 'r') as f:
            image_paths = [line.strip() for line in f if line.strip()]
        
        orchestrator.logger.info(f"📁 Processing batch file with {len(image_paths)} images")
        
        total_results = {}
        all_compiled_files = []
        
        for i, image_path in enumerate(image_paths, 1):
            orchestrator.logger.info(f"🔄 Processing image {i}/{len(image_paths)}: {image_path}")
            
            if not orchestrator.validate_image_file(image_path):
                orchestrator.logger.warning(f"⚠️ Skipping invalid image: {image_path}")
                continue
            
            # Create new session and UUID for each image
            orchestrator.session_id = str(uuid.uuid4())
            orchestrator.user_uuid = str(uuid.uuid4())[:8]  # New UUID for each image
            
            results = orchestrator.run_optimization(
                image_path, platforms, description, use_ai, output_format, max_workers
            )
            
            total_results[image_path] = results
            
            orchestrator.logger.info(f"✅ Completed image {i}/{len(image_paths)}")
        
        orchestrator.logger.info(f"🎉 Batch processing complete! Processed {len(total_results)} images")
        return total_results
        
    except Exception as e:
        orchestrator.logger.error(f"❌ Error processing batch file: {e}")
        return {}


def run_compilation_only(orchestrator: EnhancedMultiPlatformSocialMediaOrchestrator, target_path: str):
    """Run compilation only on existing JSON files"""
    print("📝 Running compilation-only mode...")
    
    target = Path(target_path)
    json_files = []
    
    if target.is_file() and target.suffix == '.json':
        # Single JSON file
        json_files = [str(target)]
        print(f"📄 Processing single JSON file: {target.name}")
    elif target.is_dir():
        # Directory of JSON files
        json_files = list(target.glob("*.json"))
        json_files = [str(f) for f in json_files if not ("_combined_" in f.name)]
        print(f"📁 Found {len(json_files)} JSON files in directory")
    else:
        print(f"❌ Invalid path: {target_path}")
        return
    
    if not json_files:
        print("❌ No JSON files found to compile")
        return
    
    # Compile captions
    compiled_files = orchestrator.compile_captions_from_results(json_files)
    
    if compiled_files:
        print(f"\n✅ Compilation complete! Generated {len(compiled_files)} caption files")
        print("📁 Check the 'compiled_captions' directory for ready-to-post content")
    else:
        print("❌ No caption files were generated")


def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Handle compilation-only mode
    if args.compilation_only:
        try:
            orchestrator = EnhancedMultiPlatformSocialMediaOrchestrator(
                api_key=args.api_key,
                log_level=args.log_level
            )
            run_compilation_only(orchestrator, args.compilation_only)
            return
        except Exception as e:
            print(f"❌ Compilation failed: {e}")
            sys.exit(1)
    
    # Validate input arguments for normal operation
    if not args.description and not args.use_ai:
        print("❌ Error: You must provide either --description, --use-ai, or both")
        print("\nExamples:")
        print("  python main.py image.jpg --platforms instagram --description 'A beautiful sunset'")
        print("  python main.py image.jpg --platforms instagram --use-ai")
        print("  python main.py image.jpg --platforms instagram --description 'My photo' --use-ai")
        sys.exit(1)
    
    # Handle platform selection
    if "all" in args.platforms:
        platforms = list(EnhancedMultiPlatformSocialMediaOrchestrator.SUPPORTED_PLATFORMS.keys())
    else:
        platforms = args.platforms
    
    try:
        # Initialize enhanced orchestrator
        orchestrator = EnhancedMultiPlatformSocialMediaOrchestrator(
            api_key=args.api_key,
            log_level=args.log_level
        )
        
        # Set custom output directory if specified
        if args.output_dir:
            orchestrator.results_dir = Path(args.output_dir)
            orchestrator.results_dir.mkdir(exist_ok=True)
        
        # Handle product photography options
        if args.skip_product_detection:
            orchestrator.perform_product_photography = False
            print("⚠️ Product detection disabled - proceeding with standard optimization")
        
        if args.force_product_photography:
            orchestrator.perform_product_photography = True
            print("🎨 Product photography forced - will generate product photos")
        
        if args.logo_path:
            if os.path.exists(args.logo_path):
                orchestrator.logo_path = args.logo_path
                print(f"📱 Logo provided: {args.logo_path}")
            else:
                print(f"⚠️ Logo file not found: {args.logo_path}")
        
        # Handle compilation options
        if args.skip_compilation:
            # Monkey patch the compilation method to do nothing
            orchestrator.compile_captions_from_results = lambda x: []
            print("⚠️ Caption compilation disabled")
        
        # Process batch or single image
        if args.batch:
            results = process_batch_file(
                args.input, orchestrator, platforms, args.description, 
                args.use_ai, args.format, args.max_workers
            )
            print(f"\n✅ Batch processing complete! Processed {len(results)} images")
            
        else:
            # Validate single image
            if not orchestrator.validate_image_file(args.input):
                sys.exit(1)
            
            # Run enhanced optimization with compilation
            results = orchestrator.run_optimization(
                args.input, platforms, args.description, args.use_ai, args.format, args.max_workers
            )
            
            # Print results summary
            orchestrator.print_results_summary(results)
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


