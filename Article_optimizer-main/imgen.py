
"""
Image Generation Module for Article Optimization Pipeline
This module provides image generation functionality using OpenAI's DALL-E API with gpt-image-1 model.
"""

import os
import base64
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    client = OpenAI(api_key=api_key)
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    client = None

class ImageGenerator:
    """Class for generating AI images using OpenAI's DALL-E with gpt-image-1 model"""
    
    def __init__(self, openai_client=None):
        """Initialize the image generator"""
        self.client = openai_client or client
        if not self.client:
            raise ValueError("OpenAI client not available")
    
    def create_realistic_entity_prompt(self, entity_type: str, entity_name: str, 
                                     context: str, visual_description: str = "") -> str:
        """
        Create a realistic image generation prompt for specific entities
        
        Args:
            entity_type: Type of entity (person, event, place, situation, thing)
            entity_name: Name or description of the entity
            context: Context from the article
            visual_description: Additional visual description
            
        Returns:
            Detailed realistic prompt for image generation
        """
        
        # Base realistic photography style
        base_style = "Professional high-quality photograph, realistic lighting, sharp focus, detailed, photojournalistic style"
        
        entity_type = entity_type.lower()
        
        if entity_type == "person":
            prompt = f"""Professional portrait photograph of {entity_name}. {visual_description}. 
            
            Setting: Professional environment appropriate for their role/context: {context}
            
            Style: {base_style}, professional headshot or environmental portrait
            Lighting: Natural professional lighting, well-lit face, soft shadows
            Composition: Professional business portrait style, rule of thirds
            Details: Professional attire, confident pose, clear facial features, appropriate background
            Camera: Shot with professional camera, shallow depth of field
            Quality: High-resolution professional photography, crisp details
            
            Avoid: Cartoonish features, unrealistic lighting, amateur photography, overly dramatic poses"""
            
        elif entity_type == "event":
            prompt = f"""Professional event photography of {entity_name}. {visual_description}.
            
            Context: {context}
            
            Style: {base_style}, documentary event photography
            Setting: Appropriate venue for the event type, realistic crowd and setup
            Elements: People engaged in the event, professional atmosphere, authentic interactions
            Lighting: Professional event lighting, well-balanced exposure
            Composition: Wide or medium shot showing event in progress, dynamic composition
            Details: Professional setup, realistic crowd/participants, authentic staging
            Camera: Professional event photography equipment, good depth of field
            Quality: High-resolution event photography, journalistic quality
            
            Avoid: Staged or artificial looking scenes, poor lighting, empty unrealistic venues"""
            
        elif entity_type == "place":
            prompt = f"""Professional architectural/location photograph of {entity_name}. {visual_description}.
            
            Context: {context}
            
            Style: {base_style}, architectural or landscape photography
            Composition: Well-framed exterior or interior view, professional angles
            Lighting: Natural daylight or appropriate ambient lighting, golden hour if exterior
            Details: Clear architectural features, realistic perspective, authentic atmosphere
            Elements: May include people for scale, realistic weather conditions
            Camera: Professional architectural photography, wide-angle lens, straight lines
            Quality: High-resolution architectural photography, excellent detail
            
            Avoid: Overly stylized or fantasy elements, unrealistic colors, distorted perspective"""
            
        elif entity_type == "situation":
            prompt = f"""Professional documentary photograph showing {entity_name}. {visual_description}.
            
            Context: {context}
            
            Style: {base_style}, documentary or lifestyle photography
            Setting: Realistic environment where this situation occurs, authentic props
            Elements: People engaged in the situation, authentic atmosphere, natural interactions
            Lighting: Natural realistic lighting appropriate for setting, available light
            Composition: Candid documentary style, capturing real moment, storytelling angle
            Details: Authentic props, clothing, and environment, realistic human behavior
            Camera: Documentary photography style, natural perspective
            Quality: High-resolution documentary photography, journalistic authenticity
            
            Avoid: Obviously staged or artificial scenarios, perfect studio lighting"""
            
        elif entity_type == "thing":
            prompt = f"""Professional product/object photograph of {entity_name}. {visual_description}.
            
            Context: {context}
            
            Style: {base_style}, product or technical photography
            Setting: Clean professional background or relevant environment
            Lighting: Professional product lighting, even illumination, no harsh shadows
            Composition: Clear view of the object/product, detailed close-up or contextual shot
            Elements: May include context or people using it appropriately, realistic scale
            Details: Sharp focus on key features, realistic materials and textures
            Camera: Professional product photography, macro lens if needed
            Quality: High-resolution product photography, commercial quality
            
            Avoid: Unrealistic materials, impossible designs, overly perfect CGI look"""
            
        else:
            # Default fallback for any other entity type
            prompt = f"""Professional photograph of {entity_name}. {visual_description}.
            
            Context: {context}
            
            Style: {base_style}, professional photography
            Setting: Appropriate realistic environment for the subject
            Lighting: Professional natural lighting, well-balanced exposure
            Composition: Well-framed professional shot, good visual balance
            Details: Realistic details, authentic atmosphere, professional quality
            Camera: Professional photography equipment, appropriate focal length
            Quality: High-resolution photography, commercial standard
            
            Avoid: Unrealistic or fantasy elements, poor lighting, amateur quality"""
        
        return prompt
    
    def generate_realistic_image(self, entity_type: str, entity_name: str, 
                               context: str, visual_description: str = "", 
                               size: str = "1024x1024", quality: str = "high") -> Optional[str]:
        """
        Generate a realistic image using OpenAI's gpt-image-1 model
        
        Args:
            entity_type: Type of entity to visualize
            entity_name: Name or description of the entity
            context: Context from the article
            visual_description: Additional visual description
            size: Image size (1024x1024, 1792x1024, 1024x1792)
            quality: Image quality (standard, high)
            
        Returns:
            Base64 encoded image data or None if failed
        """
        if not self.client:
            logger.error("OpenAI client not available for image generation")
            return None
        
        try:
            # Create realistic prompt
            prompt = self.create_realistic_entity_prompt(entity_type, entity_name, context, visual_description)
            
            logger.info(f"Generating realistic image for {entity_type}: {entity_name[:50]}...")
            
            response = self.client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size=size,
                quality=quality
            )
            
            if response.data and len(response.data) > 0:
                image_base64 = response.data[0].b64_json
                logger.info(f"✅ Realistic image generated successfully for {entity_name}")
                return image_base64
            else:
                logger.error("No image data received from OpenAI")
                return None
                
        except Exception as e:
            logger.error(f"Error generating realistic image for {entity_name}: {e}")
            return None
    
    def generate_image(self, prompt: str, size: str = "1024x1024", quality: str = "high") -> Optional[str]:
        """
        Generate an image using OpenAI's gpt-image-1 model with custom prompt
        
        Args:
            prompt: Custom image generation prompt
            size: Image size (1024x1024, 1792x1024, 1024x1792)
            quality: Image quality (standard, high)
            
        Returns:
            Base64 encoded image data or None if failed
        """
        if not self.client:
            logger.error("OpenAI client not available for image generation")
            return None
        
        try:
            logger.info(f"Generating image with custom prompt: {prompt[:100]}...")
            
            response = self.client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size=size,
                quality=quality
            )
            
            if response.data and len(response.data) > 0:
                image_base64 = response.data[0].b64_json
                logger.info("✅ Image generated successfully")
                return image_base64
            else:
                logger.error("No image data received from OpenAI")
                return None
                
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None
    
    def save_image_from_base64(self, base64_data: str, filename: str) -> bool:
        """
        Save base64 image data to file
        
        Args:
            base64_data: Base64 encoded image data
            filename: Output filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            image_bytes = base64.b64decode(base64_data)
            with open(filename, "wb") as f:
                f.write(image_bytes)
            logger.info(f"Image saved to: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving image to {filename}: {e}")
            return False
    
    def generate_article_entity_images(self, entities: list, article_content: str) -> list:
        """
        Generate realistic images for article entities
        
        Args:
            entities: List of entity dictionaries with type, name, context, visual_description
            article_content: Full article content for additional context
            
        Returns:
            List of dictionaries containing image info
        """
        results = []
        
        for i, entity in enumerate(entities):
            entity_type = entity.get("type", "thing")
            entity_name = entity.get("name", f"Entity {i+1}")
            context = entity.get("context", "")
            visual_desc = entity.get("visual_description", "")
            
            logger.info(f"Generating realistic image {i+1}/{len(entities)} for {entity_type}: {entity_name[:50]}...")
            
            try:
                # Generate realistic image
                image_base64 = self.generate_realistic_image(
                    entity_type, entity_name, context, visual_desc
                )
                
                if image_base64:
                    # Create temporary filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    temp_filename = f"entity_{entity_type}_{i+1}_{timestamp}.png"
                    
                    result = {
                        "entity_type": entity_type,
                        "entity_name": entity_name,
                        "context": context,
                        "base64_data": image_base64,
                        "temp_filename": temp_filename,
                        "success": True
                    }
                else:
                    result = {
                        "entity_type": entity_type,
                        "entity_name": entity_name,
                        "context": context,
                        "base64_data": None,
                        "temp_filename": None,
                        "success": False,
                        "error": "Image generation failed"
                    }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing entity {i+1}: {e}")
                results.append({
                    "entity_type": entity_type,
                    "entity_name": entity_name,
                    "context": context,
                    "base64_data": None,
                    "temp_filename": None,
                    "success": False,
                    "error": str(e)
                })
        
        return results

# Global instance for backward compatibility
image_generator = ImageGenerator() if client else None

# Functions for direct use (backward compatibility)
def generate_realistic_entity_image(entity_type: str, entity_name: str, 
                                  context: str, visual_description: str = "") -> Optional[str]:
    """
    Generate a realistic image for a specific entity
    
    Args:
        entity_type: Type of entity (person, event, place, situation, thing)
        entity_name: Name or description of the entity
        context: Context from article
        visual_description: Additional visual description
        
    Returns:
        Base64 image data or None
    """
    if not image_generator:
        logger.error("Image generator not available")
        return None
    
    return image_generator.generate_realistic_image(entity_type, entity_name, context, visual_description)

def generate_image_for_article(visualization_point: str, article_content: str = "") -> Optional[str]:
    """
    Generate a single image for article content (legacy function)
    
    Args:
        visualization_point: Point to visualize
        article_content: Article context
        
    Returns:
        Base64 image data or None
    """
    if not image_generator:
        logger.error("Image generator not available")
        return None
    
    # Create a basic prompt for backward compatibility
    prompt = f"""Professional photograph illustrating: {visualization_point}
    
    Context: {article_content[:300]}...
    
    Style: Professional high-quality photograph, realistic lighting, sharp focus, detailed
    Composition: Well-framed professional shot appropriate for blog content
    Quality: High-resolution photography, commercial standard
    
    Avoid: Cartoonish or unrealistic elements, poor lighting"""
    
    return image_generator.generate_image(prompt)

def save_base64_image(base64_data: str, filename: str) -> bool:
    """
    Save base64 image to file
    
    Args:
        base64_data: Base64 encoded image
        filename: Output filename
        
    Returns:
        Success status
    """
    if not image_generator:
        logger.error("Image generator not available")
        return False
    
    return image_generator.save_image_from_base64(base64_data, filename)

def test_image_generation():
    """Test function to verify image generation works with gpt-image-1"""
    if not client:
        print("❌ OpenAI client not available")
        return False
    
    try:
        test_prompt = """Professional photograph of a modern office building exterior during daytime.
        
        Style: Professional architectural photography, realistic lighting, sharp focus
        Lighting: Natural daylight, well-balanced exposure
        Composition: Wide-angle view showing full building facade
        Details: Clear architectural features, realistic perspective
        Quality: High-resolution architectural photography
        
        Avoid: Overly stylized or fantasy elements, unrealistic colors"""
        
        print("🧪 Testing image generation with gpt-image-1...")
        result = client.images.generate(
            model="gpt-image-1",
            prompt=test_prompt,
            size="1024x1024",
            quality="high"
        )
        
        if result.data and len(result.data) > 0:
            print("✅ Image generation test successful")
            return True
        else:
            print("❌ Image generation test failed - no data")
            return False
            
    except Exception as e:
        print(f"❌ Image generation test failed: {e}")
        return False

# Main execution guard - prevents automatic execution on import
if __name__ == "__main__":
    # This code only runs when the script is executed directly
    print("🖼️ Enhanced Image Generation Module Test")
    print("=" * 50)
    
    if test_image_generation():
        print("✅ Module is ready for use")
    else:
        print("❌ Module has configuration issues")
        
    # Example usage when run directly
    sample_entities = [
        {
            "type": "person",
            "name": "CEO John Smith",
            "context": "Tech industry leader announcing new AI initiative",
            "visual_description": "Professional business executive in modern office setting"
        },
        {
            "type": "event",
            "name": "AI Conference 2024",
            "context": "Major technology conference with industry leaders",
            "visual_description": "Large conference hall with speakers and audience"
        }
    ]
    
    if image_generator:
        print(f"\n📝 Testing realistic entity image generation...")
        for entity in sample_entities:
            print(f"Entity: {entity['name']} ({entity['type']})")
            prompt = image_generator.create_realistic_entity_prompt(
                entity['type'], entity['name'], entity['context'], entity['visual_description']
            )
            print(f"Generated prompt: {prompt[:200]}...")
            print()
    else:
        print("\n❌ Cannot demonstrate - image generator not available")

