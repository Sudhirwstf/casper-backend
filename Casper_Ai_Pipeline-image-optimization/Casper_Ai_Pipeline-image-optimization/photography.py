
#!/usr/bin/env python3
"""
Standalone Product Photography Generator with Multi-Platform Support and Cloudinary Integration
A comprehensive script for generating professional product photography for different social media platforms using AI.
Can be used as a standalone tool or integrated into other pipelines.

Requirements:
- OpenAI API key (set as OPENAI_API_KEY environment variable or pass directly)
- Cloudinary credentials (set in .env file or pass directly)
- PIL (Pillow)
- rembg
- openai
- python-dotenv
- cloudinary
- requests

Usage:
    python product_photo_generator.py --help
    python product_photo_generator.py --product-name "Smartphone" --photography-type "LIFESTYLE PHOTOGRAPHY" --platforms "instagram,facebook" --image-path "/path/to/image.jpg"
    
Integration:
    from product_photo_generator import ProductPhotoGenerator
    generator = ProductPhotoGenerator(api_key="your-key")
    results = generator.generate_photos_for_platforms("Product Name", "LIFESTYLE PHOTOGRAPHY", ["instagram", "facebook"], "/path/to/image.jpg")
"""

import os
import sys
import logging
import base64
import argparse
from typing import Optional, Dict, Tuple, List
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path
import time

# Third-party imports
try:
    import PIL.Image
    from rembg import remove
    from openai import OpenAI
    from dotenv import load_dotenv
    import requests  # For downloading images from URLs
    import cloudinary
    import cloudinary.uploader
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install pillow rembg openai python-dotenv requests cloudinary")
    sys.exit(1)

# Configure logging
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Setup logging configuration"""
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, mode='a', encoding='utf-8'))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

logger = logging.getLogger(__name__)

class CloudinaryUploader:
    """Handle Cloudinary upload operations"""
    
    def __init__(self, cloud_name: Optional[str] = None, api_key: Optional[str] = None, 
                 api_secret: Optional[str] = None):
        """
        Initialize Cloudinary configuration
        
        Args:
            cloud_name: Cloudinary cloud name
            api_key: Cloudinary API key  
            api_secret: Cloudinary API secret
        """
        # Load environment variables
        load_dotenv()
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=cloud_name or os.getenv("CLOUDINARY_CLOUD_NAME", "dmz4lknv4"),
            api_key=api_key or os.getenv("CLOUDINARY_API_KEY", "666561538621679"),
            api_secret=api_secret or os.getenv("CLOUDINARY_API_SECRET", "nGMt1pNjjiAtVVYzK2Sp2FVvcqA")
        )
        
        logger.info("Cloudinary configured successfully")
    
    def upload_image(self, file_path: str, public_id: Optional[str] = None) -> Optional[str]:
        """
        Upload an image to Cloudinary and return the secure URL
        
        Args:
            file_path: Path to the image file
            public_id: Optional custom public ID for the image
            
        Returns:
            Secure Cloudinary URL if successful, None otherwise
        """
        try:
            upload_options = {
                "resource_type": "image",
                "folder": "product_photography",
                "quality": "auto:good",
                "format": "webp"  # Optimize for web
            }
            
            if public_id:
                upload_options["public_id"] = public_id
            
            logger.info(f"Uploading image to Cloudinary: {file_path}")
            response = cloudinary.uploader.upload(file_path, **upload_options)
            
            url = response.get("secure_url")
            if url:
                logger.info(f"✅ Cloudinary upload successful: {url}")
                return url
            else:
                logger.error("❌ No URL returned from Cloudinary")
                return None
                
        except Exception as e:
            logger.error(f"❌ Cloudinary upload failed: {e}")
            return None

class ProductPhotoGenerator:
    """
    Multi-Platform Product Photography Generator with Cloudinary Integration
    
    This class handles the complete workflow of generating professional product
    photography for different social media platforms using AI and uploading to Cloudinary.
    """
    
    # Supported social media platforms
    SUPPORTED_PLATFORMS = {
        "instagram": "Instagram",
        "facebook": "Facebook", 
        "x.com": "X (Twitter)",
        "linkedin": "LinkedIn", 
        "pinterest": "Pinterest"
    }
    
    # Photography style templates with platform-specific variations
    PHOTOGRAPHY_TEMPLATES = {
        "FLOATING PHOTOGRAPHY": {
            "base": "Product {product_name} floating in mid-air against soft gradient background. Dynamic shot with subtle movement, elegant composition highlighting form and features. Low angle emphasizing floating effect, no visible supports.",
            "variations": {
                "instagram": "Add warm, vibrant lighting with subtle shadows for Instagram's aesthetic",
                "facebook": "Include soft bokeh background effects for Facebook's engaging visual style", 
                "x.com": "Sharp, clean edges with minimalist composition perfect for Twitter's clean feed",
                "linkedin": "Professional lighting with corporate-friendly gradient backdrop",
                "pinterest": "Dreamy, inspirational floating effect with artistic composition"
            }
        },
        
        "FLAT LAY PHOTOGRAPHY": {
            "base": "Flat lay {product_name} on textured surface, camera directly above. Clean aesthetic composition with relevant props, balanced lighting, minimal shadows, professional look.",
            "variations": {
                "instagram": "Add trendy lifestyle props and warm natural lighting for Instagram stories",
                "facebook": "Include complementary items and cozy, relatable setting for Facebook community",
                "x.com": "Minimalist composition with clean lines and modern aesthetic for Twitter",
                "linkedin": "Professional workspace elements with business-appropriate styling",
                "pinterest": "Styled with seasonal elements and inspiring, pin-worthy composition"
            }
        },
        
        "LIFESTYLE PHOTOGRAPHY": {
            "base": "Lifestyle photo of {product_name} in natural setting. Real-life context with natural lighting, complementary props, genuine interaction moment. Avoid showing faces, elements relate to product context.",
            "variations": {
                "instagram": "Bright, authentic moment with lifestyle blogger aesthetic and natural poses",
                "facebook": "Warm, family-friendly setting with relatable everyday usage scenario",
                "x.com": "Quick, authentic moment captured with modern, urban lifestyle context",
                "linkedin": "Professional usage scenario in workplace or business environment",
                "pinterest": "Aspirational lifestyle moment with beautiful, curated home setting"
            }
        },
        
        "PRODUCT ART PHOTOGRAPHY": {
            "base": "Artistic {product_name} in dynamic swirl of vibrant colors. Deep rich background, high contrast, luxurious dramatic feel. Creative story and mood around product.",
            "variations": {
                "instagram": "Bold, saturated colors with trendy artistic effects for maximum engagement",
                "facebook": "Warm, approachable artistic style with inviting color palette",
                "x.com": "Sharp, contemporary art style with bold contrasts and clean composition",
                "linkedin": "Sophisticated artistic presentation with professional color schemes",
                "pinterest": "Dreamy, artistic composition with inspiring and shareable visual impact"
            }
        },
        
        "MACRO PHOTOGRAPHY": {
            "base": "Macro shot of {product_name} on natural surface. Razor-sharp focus on intricate details, shallow depth of field, blurred background. Capture tiny details invisible to naked eye.",
            "variations": {
                "instagram": "Ultra-sharp details with warm, natural bokeh perfect for Instagram close-ups",
                "facebook": "Detailed textures with inviting, accessible macro photography style",
                "x.com": "Clean, technical macro shot with precise focus and minimal distractions",
                "linkedin": "Professional macro photography showcasing quality and craftsmanship",
                "pinterest": "Beautiful detailed shot with artistic bokeh and inspiring composition"
            }
        },
        
        "DARK AND MOODY": {
            "base": "Dramatic {product_name} lit by sharp light beam with long dark shadows. Blurred deep contrast background, moody atmosphere. More shadows than highlights, mystery and elegance.",
            "variations": {
                "instagram": "Moody aesthetic with dramatic shadows perfect for Instagram's dark theme lovers",
                "facebook": "Approachable drama with softer shadows for broader Facebook audience appeal",
                "x.com": "Sharp, high-contrast drama with clean composition for Twitter's fast scroll",
                "linkedin": "Professional dramatic lighting conveying quality and sophistication",
                "pinterest": "Artistic moody composition with inspiring dramatic visual storytelling"
            }
        },
        
        "SOLID BACKGROUND": {
            "base": "Clean {product_name} on solid {background_color} background. Plain uniform backdrop, centered and focused, preserve all product details, textures, logos, and text.",
            "variations": {
                "instagram": "Perfect product shot with Instagram-optimized lighting and subtle shadow",
                "facebook": "Clean, trustworthy product presentation ideal for Facebook marketplace",
                "x.com": "Minimal, professional product shot perfect for Twitter's clean aesthetic",
                "linkedin": "Corporate-quality product photography with professional presentation",
                "pinterest": "Clean, pin-worthy product shot with perfect lighting and composition"
            }
        }
    }
    
    # Available background colors for solid background photography
    BACKGROUND_COLORS = [
        "Sage Green", "Sea Blue", "White", "Cream", "Blush Pink", 
        "Mint Green", "Sky Blue", "Lavender", "Soft Gray", "Peach", 
        "Dusty Rose", "Pale Yellow", "Light Coral", "Powder Blue", 
        "Seafoam Green"
    ]
    
    def __init__(self, api_key: Optional[str] = None, output_dir: str = "output",
                 cloudinary_config: Optional[Dict[str, str]] = None, cleanup_temp_files: bool = True):
        """
        Initialize the Product Photo Generator with Cloudinary integration
        
        Args:
            api_key: OpenAI API key (optional, will load from environment if not provided)
            output_dir: Directory to save generated images locally
            cloudinary_config: Dict with 'cloud_name', 'api_key', 'api_secret' for Cloudinary
            cleanup_temp_files: Whether to cleanup temporary mask files after generation
        """
        # Load environment variables
        load_dotenv()
        
        # Setup API key
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # Setup output directory
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup cleanup option
        self.cleanup_temp_files = cleanup_temp_files
        self.temp_files = []  # Track temporary files for cleanup
        
        # Initialize Cloudinary uploader
        if cloudinary_config:
            self.cloudinary = CloudinaryUploader(**cloudinary_config)
        else:
            self.cloudinary = CloudinaryUploader()
        
        logger.info(f"ProductPhotoGenerator initialized with output directory: {self.output_dir}")
        logger.info(f"Cleanup temporary files: {self.cleanup_temp_files}")
    
    @lru_cache(maxsize=128)
    def _generate_prompt_with_ai(self, base_prompt: str) -> str:
        """
        Enhance the base prompt using AI with length constraints
        
        Args:
            base_prompt: Base photography prompt template
            
        Returns:
            Enhanced prompt from AI (max 900 characters to be safe)
        """
        try:
            system_prompt = (
                "You are an expert in generating concise, creative photography prompts for social media. "
                "Enhance the given prompt to be more detailed and professional, but keep it "
                "under 900 characters. Focus on the most important visual elements that work well for the specified platform."
            )
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": base_prompt}
                ],
                max_tokens=300,  # Reduced to ensure shorter response
                temperature=0.7
            )
            
            enhanced_prompt = response.choices[0].message.content.strip()
            
            # Ensure prompt is within OpenAI's 1000 character limit (we use 900 to be safe)
            if len(enhanced_prompt) > 900:
                enhanced_prompt = enhanced_prompt[:897] + "..."
                logger.warning(f"Prompt truncated to 900 characters")
            
            logger.info(f"Enhanced prompt generated: {len(enhanced_prompt)} characters")
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error enhancing prompt with AI: {e}")
            # Fallback to base prompt, also check length
            fallback_prompt = base_prompt
            if len(fallback_prompt) > 900:
                fallback_prompt = fallback_prompt[:897] + "..."
                logger.warning(f"Base prompt truncated to 900 characters")
            return fallback_prompt
    
    def _create_mask(self, image_path: str, output_path: str) -> None:
        """
        Create a mask for the image using background removal
        
        Args:
            image_path: Path to input image
            output_path: Path to save the mask
        """
        try:
            with open(image_path, "rb") as inp_file:
                input_image = PIL.Image.open(inp_file).convert("RGBA")
                mask_image = remove(input_image)
            
            mask_image.save(output_path, format="PNG")
            self.temp_files.append(output_path)  # Track for cleanup
            logger.info(f"Mask created and saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error creating mask: {e}")
            raise
    
    def cleanup_temporary_files(self) -> None:
        """Clean up temporary mask files"""
        if not self.cleanup_temp_files:
            return
            
        cleaned_count = 0
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    cleaned_count += 1
                    logger.debug(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned up {cleaned_count} temporary files")
        
        self.temp_files.clear()
    
    @staticmethod
    def _validate_inputs(product_name: str, photography_type: str, platforms: List[str], 
                        image_path: str, background_color: Optional[str] = None) -> None:
        """
        Validate input parameters
        
        Args:
            product_name: Name of the product
            photography_type: Type of photography
            platforms: List of platforms to generate for
            image_path: Path to input image
            background_color: Background color (for solid background type)
        """
        if not product_name or len(product_name.strip()) < 2:
            raise ValueError("Product name must be at least 2 characters long")
        
        if photography_type not in ProductPhotoGenerator.PHOTOGRAPHY_TEMPLATES:
            valid_types = list(ProductPhotoGenerator.PHOTOGRAPHY_TEMPLATES.keys())
            raise ValueError(f"Invalid photography type. Must be one of: {valid_types}")
        
        if not platforms:
            raise ValueError("At least one platform must be selected")
        
        invalid_platforms = [p for p in platforms if p not in ProductPhotoGenerator.SUPPORTED_PLATFORMS]
        if invalid_platforms:
            valid_platforms = list(ProductPhotoGenerator.SUPPORTED_PLATFORMS.keys())
            raise ValueError(f"Invalid platforms: {invalid_platforms}. Must be from: {valid_platforms}")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        if photography_type == "SOLID BACKGROUND":
            if not background_color:
                raise ValueError("Background color is required for SOLID BACKGROUND photography type")
            if background_color not in ProductPhotoGenerator.BACKGROUND_COLORS:
                raise ValueError(f"Invalid background color. Must be one of: {ProductPhotoGenerator.BACKGROUND_COLORS}")
    
    def generate_prompt_for_platform(self, product_name: str, photography_type: str, 
                                   platform: str, background_color: Optional[str] = None) -> str:
        """
        Generate photography prompt for the given parameters and platform with variations
        
        Args:
            product_name: Name of the product
            photography_type: Type of photography
            platform: Target platform
            background_color: Background color (for solid background type)
            
        Returns:
            Generated photography prompt with platform-specific variations
        """
        try:
            # Get template
            template_data = self.PHOTOGRAPHY_TEMPLATES[photography_type]
            base_template = template_data["base"]
            platform_variation = template_data["variations"][platform]
            
            # Format base template
            if photography_type == "SOLID BACKGROUND" and background_color:
                base_prompt = base_template.format(
                    product_name=product_name, 
                    background_color=background_color
                )
            else:
                base_prompt = base_template.format(product_name=product_name)
            
            # Combine base prompt with platform variation
            combined_prompt = f"{base_prompt} {platform_variation}"
            
            # Enhance with AI
            enhanced_prompt = self._generate_prompt_with_ai(combined_prompt)
            
            platform_name = self.SUPPORTED_PLATFORMS[platform]
            logger.info(f"Generated platform-specific prompt for {product_name} - {photography_type} - {platform_name}")
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            raise
    
    def generate_single_photo(self, product_name: str, photography_type: str, platform: str,
                            image_path: str, background_color: Optional[str] = None, 
                            output_filename: Optional[str] = None,
                            upload_to_cloudinary: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Generate a single product photography for a specific platform
        
        Args:
            product_name: Name of the product
            photography_type: Type of photography
            platform: Target platform
            image_path: Path to input image
            background_color: Background color (for solid background type)
            output_filename: Custom output filename (without extension)
            upload_to_cloudinary: Whether to upload the result to Cloudinary
            
        Returns:
            Tuple of (success_status, cloudinary_url_or_local_path)
        """
        try:
            platform_name = self.SUPPORTED_PLATFORMS[platform]
            logger.info(f"🎨 Generating photo for {product_name} - {platform_name}")
            
            # Generate prompt for this platform
            prompt = self.generate_prompt_for_platform(
                product_name, photography_type, platform, background_color
            )
            logger.info(f"📝 Using prompt: {prompt[:100]}...")
            
            # Generate output filename
            if output_filename is None:
                safe_product_name = product_name.replace(' ', '_').lower()
                safe_photo_type = photography_type.replace(' ', '_').lower()
                output_filename = f"{safe_product_name}_{safe_photo_type}_{platform}"
            
            # Create mask (only once per session - reuse if exists)
            safe_product_name = product_name.replace(' ', '_').lower()
            mask_path = self.output_dir / f"{safe_product_name}_mask.png"
            if not mask_path.exists():
                self._create_mask(image_path, str(mask_path))
            
            # Generate image using OpenAI
            logger.info(f"🤖 Sending request to OpenAI API for {platform_name}...")
            response = self.client.images.edit(
                model="gpt-image-1",
                image=open(image_path, "rb"),
                mask=open(mask_path, "rb"),
                prompt=prompt,
                n=1,
                size="1024x1024",
                # response_format="b64_json"  # Explicitly request base64 format
            )
            
            # Handle different response formats
            image_data = None
            if hasattr(response.data[0], 'b64_json') and response.data[0].b64_json:
                # Base64 format
                image_base64 = response.data[0].b64_json
                image_data = base64.b64decode(image_base64)
                logger.info(f"📥 Received image data in base64 format for {platform_name}")
            elif hasattr(response.data[0], 'url') and response.data[0].url:
                # URL format - download the image
                image_url = response.data[0].url
                logger.info(f"📥 Downloading image from URL for {platform_name}: {image_url}")
                img_response = requests.get(image_url)
                if img_response.status_code == 200:
                    image_data = img_response.content
                else:
                    raise Exception(f"Failed to download image from URL: {img_response.status_code}")
            else:
                raise Exception("No valid image data found in API response")
            
            if image_data is None:
                raise Exception("Failed to extract image data from API response")
            
            # Save final image locally
            final_image_path = self.output_dir / f"{output_filename}.png"
            with open(final_image_path, "wb") as f:
                f.write(image_data)
            
            logger.info(f"💾 Image saved locally for {platform_name}: {final_image_path}")
            
            # Upload to Cloudinary if requested
            if upload_to_cloudinary:
                logger.info(f"☁️ Uploading to Cloudinary for {platform_name}...")
                cloudinary_url = self.cloudinary.upload_image(
                    str(final_image_path), 
                    public_id=f"{output_filename}_{platform}"
                )
                
                if cloudinary_url:
                    logger.info(f"🌐 Cloudinary URL for {platform_name}: {cloudinary_url}")
                    return True, cloudinary_url
                else:
                    logger.warning(f"⚠️ Cloudinary upload failed for {platform_name}, returning local path")
                    return True, str(final_image_path)
            else:
                return True, str(final_image_path)
            
        except Exception as e:
            logger.error(f"❌ Error during photo generation for {platform}: {e}")
            return False, None
    
    def generate_photos_for_platforms(self, product_name: str, photography_type: str, 
                                    platforms: List[str], image_path: str,
                                    background_color: Optional[str] = None, 
                                    upload_to_cloudinary: bool = True,
                                    delay_between_requests: float = 2.0) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        Generate product photography for multiple platforms
        
        Args:
            product_name: Name of the product
            photography_type: Type of photography
            platforms: List of platforms to generate for
            image_path: Path to input image
            background_color: Background color (for solid background type)
            upload_to_cloudinary: Whether to upload the results to Cloudinary
            delay_between_requests: Delay between API requests to avoid rate limits
            
        Returns:
            Dictionary mapping platform to (success_status, cloudinary_url_or_local_path)
        """
        try:
            logger.info(f"🎨 Starting multi-platform photo generation for {product_name}")
            
            # Validate inputs
            self._validate_inputs(product_name, photography_type, platforms, image_path, background_color)
            
            results = {}
            total_platforms = len(platforms)
            
            for i, platform in enumerate(platforms, 1):
                platform_name = self.SUPPORTED_PLATFORMS[platform]
                print(f"\n📱 Generating for {platform_name} ({i}/{total_platforms})...")
                
                success, result_url = self.generate_single_photo(
                    product_name=product_name,
                    photography_type=photography_type,
                    platform=platform,
                    image_path=image_path,
                    background_color=background_color,
                    upload_to_cloudinary=upload_to_cloudinary
                )
                
                results[platform] = (success, result_url)
                
                if success:
                    print(f"   ✅ {platform_name}: Generated successfully")
                    if result_url and result_url.startswith('http'):
                        print(f"   🌐 URL: {result_url}")
                else:
                    print(f"   ❌ {platform_name}: Generation failed")
                
                # Add delay between requests to avoid rate limiting
                if i < total_platforms:
                    logger.info(f"⏳ Waiting {delay_between_requests}s before next request...")
                    time.sleep(delay_between_requests)
            
            # Cleanup temporary files after all generations
            self.cleanup_temporary_files()
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error during multi-platform photo generation: {e}")
            return {}
    
    @classmethod
    def get_photography_types(cls) -> list:
        """Get list of available photography types"""
        return list(cls.PHOTOGRAPHY_TEMPLATES.keys())
    
    @classmethod
    def get_supported_platforms(cls) -> Dict[str, str]:
        """Get dictionary of supported platforms"""
        return cls.SUPPORTED_PLATFORMS.copy()
    
    @classmethod
    def get_background_colors(cls) -> list:
        """Get list of available background colors"""
        return cls.BACKGROUND_COLORS.copy()
    
    def interactive_mode(self):
        """Run in interactive mode for user input"""
        try:
            print("\n" + "="*70)
            print("🎨 MULTI-PLATFORM PRODUCT PHOTOGRAPHY GENERATOR")
            print("="*70)
            
            # Get product name
            while True:
                product_name = input("📦 Enter the product name: ").strip()
                if len(product_name) >= 2:
                    break
                print("❌ Product name must be at least 2 characters long!")
            
            # Get platforms
            print("\n📱 Choose target platforms:")
            platforms = list(self.get_supported_platforms().keys())
            platform_names = list(self.get_supported_platforms().values())
            
            for i, (platform_key, platform_name) in enumerate(self.get_supported_platforms().items(), 1):
                print(f"   {i}. {platform_name}")
            print(f"   {len(platforms) + 1}. All platforms")
            
            while True:
                try:
                    choices_input = input(f"Enter your choices (1-{len(platforms) + 1}, comma-separated or single): ").strip()
                    
                    if choices_input == str(len(platforms) + 1):
                        # All platforms selected
                        selected_platforms = platforms
                        break
                    else:
                        # Parse individual selections
                        choices = [int(x.strip()) for x in choices_input.split(',')]
                        if all(1 <= choice <= len(platforms) for choice in choices):
                            selected_platforms = [platforms[choice - 1] for choice in choices]
                            break
                        else:
                            raise ValueError()
                except (ValueError, IndexError):
                    print(f"❌ Invalid choice. Enter numbers 1-{len(platforms) + 1}, comma-separated.")
            
            selected_platform_names = [self.SUPPORTED_PLATFORMS[p] for p in selected_platforms]
            print(f"✅ Selected platforms: {', '.join(selected_platform_names)}")
            
            # Get photography type
            print("\n🎭 Choose a photography type:")
            types = self.get_photography_types()
            for i, ptype in enumerate(types, 1):
                print(f"   {i}. {ptype}")
            
            while True:
                try:
                    choice = int(input(f"Enter your choice (1-{len(types)}): "))
                    if 1 <= choice <= len(types):
                        photography_type = types[choice - 1]
                        break
                except ValueError:
                    pass
                print("❌ Invalid choice. Please try again.")
            
            # Get background color if needed
            background_color = None
            if photography_type == "SOLID BACKGROUND":
                print("\n🎨 Choose a background color:")
                colors = self.get_background_colors()
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
            
            # Get image path
            while True:
                image_path = input("\n📁 Enter the full path to the image: ").strip()
                if os.path.exists(image_path):
                    break
                print("❌ File not found. Please check the path and try again.")
            
            # Ask about Cloudinary upload
            while True:
                upload_choice = input("\n☁️ Upload to Cloudinary? (y/n): ").strip().lower()
                if upload_choice in ['y', 'yes', 'n', 'no']:
                    upload_to_cloudinary = upload_choice in ['y', 'yes']
                    break
                print("❌ Please enter 'y' for yes or 'n' for no.")
            
            # Generate photos
            print(f"\n{'='*70}")
            print("🔄 GENERATING MULTI-PLATFORM PRODUCT PHOTOGRAPHY...")
            print(f"📦 Product: {product_name}")
            print(f"🎭 Style: {photography_type}")
            if background_color:
                print(f"🎨 Background: {background_color}")
            print(f"📱 Platforms: {', '.join(selected_platform_names)}")
            print(f"📁 Input: {image_path}")
            print(f"☁️ Cloudinary: {'Yes' if upload_to_cloudinary else 'No'}")
            print(f"{'='*70}")
            
            results = self.generate_photos_for_platforms(
                product_name=product_name,
                photography_type=photography_type,
                platforms=selected_platforms,
                image_path=image_path,
                background_color=background_color,
                upload_to_cloudinary=upload_to_cloudinary
            )
            
            # Display results summary
            print(f"\n{'='*70}")
            print("📊 GENERATION SUMMARY")
            print(f"{'='*70}")
            
            successful_platforms = []
            failed_platforms = []
            
            for platform, (success, result_url) in results.items():
                platform_name = self.SUPPORTED_PLATFORMS[platform]
                if success and result_url:
                    successful_platforms.append((platform_name, result_url))
                    print(f"✅ {platform_name}: SUCCESS")
                    if result_url.startswith('http'):
                        print(f"   🌐 Cloudinary: {result_url}")
                    else:
                        print(f"   💾 Local: {result_url}")
                else:
                    failed_platforms.append(platform_name)
                    print(f"❌ {platform_name}: FAILED")
            
            print(f"\n📈 Success Rate: {len(successful_platforms)}/{len(selected_platforms)} platforms")
            if successful_platforms:
                print(f"📂 Local output directory: {self.output_dir}")
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Operation cancelled by user.")
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}")
            print(f"❌ An error occurred: {e}")

def create_argument_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Multi-Platform Product Photography Generator with Cloudinary Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --interactive
  %(prog)s --product-name "Smartphone" --photography-type "LIFESTYLE PHOTOGRAPHY" --platforms "instagram,facebook" --image-path "/path/to/image.jpg"
  %(prog)s --product-name "Watch" --photography-type "SOLID BACKGROUND" --background-color "White" --platforms "all" --image-path "/path/to/image.jpg"
        """
    )
    
    # Mode selection
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    # Required arguments for non-interactive mode
    parser.add_argument(
        "--product-name",
        help="Name of the product"
    )
    
    parser.add_argument(
        "--photography-type",
        choices=ProductPhotoGenerator.get_photography_types(),
        help="Type of photography style"
    )
    
    parser.add_argument(
        "--platforms",
        help="Target platforms (comma-separated: instagram,facebook,x.com,linkedin,pinterest or 'all')"
    )
    
    parser.add_argument(
        "--image-path",
        help="Path to the input image file"
    )
    
    # Optional arguments
    parser.add_argument(
        "--background-color",
        choices=ProductPhotoGenerator.get_background_colors(),
        help="Background color (required for SOLID BACKGROUND type)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory for generated images (default: output)"
    )
    
    parser.add_argument(
        "--api-key",
        help="OpenAI API key (can also be set via OPENAI_API_KEY environment variable)"
    )
    
    parser.add_argument(
        "--no-cloudinary",
        action="store_true",
        help="Skip Cloudinary upload and save only locally"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay between API requests in seconds (default: 2.0)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        help="Log file path (optional)"
    )
    
    return parser

def parse_platforms(platforms_input: str) -> List[str]:
    """
    Parse platform input string into list of platforms
    
    Args:
        platforms_input: Comma-separated platform names or 'all'
        
    Returns:
        List of platform keys
    """
    if platforms_input.lower().strip() == 'all':
        return list(ProductPhotoGenerator.get_supported_platforms().keys())
    
    platforms = [p.strip().lower() for p in platforms_input.split(',')]
    valid_platforms = list(ProductPhotoGenerator.get_supported_platforms().keys())
    
    # Validate all platforms
    invalid_platforms = [p for p in platforms if p not in valid_platforms]
    if invalid_platforms:
        raise ValueError(f"Invalid platforms: {invalid_platforms}. Valid options: {valid_platforms}")
    
    return platforms

def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    try:
        # Initialize generator
        generator = ProductPhotoGenerator(
            api_key=args.api_key,
            output_dir=args.output_dir,
            cleanup_temp_files=True
        )
        
        # Run in appropriate mode
        if args.interactive or len(sys.argv) == 1:
            generator.interactive_mode()
        else:
            # Validate required arguments for non-interactive mode
            if not all([args.product_name, args.photography_type, args.platforms, args.image_path]):
                print("❌ Error: --product-name, --photography-type, --platforms, and --image-path are required for non-interactive mode")
                print("Use --interactive or -i for interactive mode")
                print("\nPlatform options: instagram,facebook,x.com,linkedin,pinterest or 'all'")
                sys.exit(1)
            
            # Parse platforms
            try:
                platforms = parse_platforms(args.platforms)
            except ValueError as e:
                print(f"❌ Platform error: {e}")
                sys.exit(1)
            
            # Check background color requirement
            if args.photography_type == "SOLID BACKGROUND" and not args.background_color:
                print("❌ Error: --background-color is required when using SOLID BACKGROUND photography type")
                sys.exit(1)
            
            # Display processing information
            platform_names = [ProductPhotoGenerator.get_supported_platforms()[p] for p in platforms]
            print("\n" + "="*70)
            print("🎨 MULTI-PLATFORM PRODUCT PHOTOGRAPHY GENERATOR")
            print("="*70)
            print(f"📦 Product: {args.product_name}")
            print(f"🎭 Style: {args.photography_type}")
            print(f"📱 Platforms: {', '.join(platform_names)} ({len(platforms)} total)")
            print(f"📁 Input: {args.image_path}")
            if args.background_color:
                print(f"🎨 Background: {args.background_color}")
            print(f"📂 Output: {args.output_dir}")
            print(f"☁️ Cloudinary: {'No' if args.no_cloudinary else 'Yes'}")
            print(f"⏳ Delay: {args.delay}s between requests")
            print("="*70)
            
            # Generate photos for all platforms
            results = generator.generate_photos_for_platforms(
                product_name=args.product_name,
                photography_type=args.photography_type,
                platforms=platforms,
                image_path=args.image_path,
                background_color=args.background_color,
                upload_to_cloudinary=not args.no_cloudinary,
                delay_between_requests=args.delay
            )
            
            # Display final results
            print(f"\n{'='*70}")
            print("📊 FINAL RESULTS")
            print(f"{'='*70}")
            
            successful_count = 0
            failed_count = 0
            
            for platform, (success, result_url) in results.items():
                platform_name = ProductPhotoGenerator.get_supported_platforms()[platform]
                if success and result_url:
                    successful_count += 1
                    print(f"✅ {platform_name}: SUCCESS")
                    if not args.no_cloudinary and result_url.startswith('http'):
                        print(f"   🌐 Cloudinary: {result_url}")
                    else:
                        print(f"   💾 Local: {result_url}")
                else:
                    failed_count += 1
                    print(f"❌ {platform_name}: FAILED")
            
            print(f"\n📈 Overall Success Rate: {successful_count}/{len(platforms)} platforms")
            
            if successful_count > 0:
                print(f"📂 Check output directory: {args.output_dir}")
                if not args.no_cloudinary:
                    print("🌐 Cloudinary URLs are ready for sharing!")
                sys.exit(0)
            else:
                print("❌ All platform generations failed!")
                sys.exit(1)
                
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()








