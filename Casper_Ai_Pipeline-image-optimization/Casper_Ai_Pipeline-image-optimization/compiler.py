
"""
Social Media Caption Compiler - Updated Version
Transforms JSON optimization results into platform-specific, ready-to-post captions
with consistent UUID naming and streamlined output for content creators.
"""

import os
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import uuid
import re
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialMediaCaptionCompiler:
    """
    Updated caption compiler with consistent UUID naming and creator-focused output
    """
    
    # Platform-specific optimization parameters
    PLATFORM_SPECS = {
        "instagram": {
            "optimal_caption_length": (138, 150),
            "max_caption_length": 2200,
            "optimal_hashtags": (3, 5),
            "max_hashtags": 30,
            "hashtag_placement": "first_comment",
            "line_breaks": True,
            "emojis": True,
            "cta_style": "casual_engaging"
        },
        "facebook": {
            "optimal_caption_length": (40, 80),
            "max_caption_length": 63206,
            "optimal_hashtags": (1, 3),
            "max_hashtags": None,
            "hashtag_placement": "inline",
            "line_breaks": False,
            "emojis": True,
            "cta_style": "question_based"
        },
        "linkedin": {
            "optimal_caption_length": (140, 180),  # Short form
            "long_form_length": (300, 500),
            "max_caption_length": 3000,
            "optimal_hashtags": (3, 5),
            "max_hashtags": None,
            "hashtag_placement": "end",
            "line_breaks": True,
            "emojis": False,
            "cta_style": "professional"
        },
        "pinterest": {
            "optimal_caption_length": (100, 200),
            "max_caption_length": 500,
            "optimal_hashtags": (2, 5),
            "max_hashtags": None,
            "hashtag_placement": "inline",
            "line_breaks": False,
            "emojis": True,
            "cta_style": "seo_focused"
        },
        "x.com": {
            "optimal_caption_length": (71, 100),
            "max_caption_length": 280,
            "optimal_hashtags": (1, 2),
            "max_hashtags": None,
            "hashtag_placement": "inline",
            "line_breaks": False,
            "emojis": True,
            "cta_style": "punchy"
        },
        "twitter": {  # Alias for x.com
            "optimal_caption_length": (71, 100),
            "max_caption_length": 280,
            "optimal_hashtags": (1, 2),
            "max_hashtags": None,
            "hashtag_placement": "inline",
            "line_breaks": False,
            "emojis": True,
            "cta_style": "punchy"
        }
    }
    
    # CTA templates by style
    CTA_TEMPLATES = {
        "casual_engaging": [
            "What do you think? 👇",
            "Drop your thoughts below! 💭",
            "Let me know in the comments! ✨",
            "Your turn - share your experience! 🙌",
            "Tag someone who needs to see this! 👀"
        ],
        "question_based": [
            "What's your take on this?",
            "Have you experienced something similar?",
            "What would you do in this situation?",
            "How do you handle situations like this?",
            "What are your thoughts?"
        ],
        "professional": [
            "What are your insights on this?",
            "I'd love to hear your perspective.",
            "Share your experience in the comments.",
            "What strategies have worked for you?",
            "Let's discuss this further."
        ],
        "seo_focused": [
            "Save this for later!",
            "Pin this for reference!",
            "Click to learn more!",
            "Get inspired today!",
            "Try this yourself!"
        ],
        "punchy": [
            "Thoughts? 💭",
            "Your take? 👇",
            "Agree? 🤔",
            "RT if you agree! 🔄",
            "What's next? 🚀"
        ]
    }
    
    # Optimal posting times by platform
    OPTIMAL_POSTING_TIMES = {
        "instagram": {
            "weekdays": ["Monday", "Tuesday", "Thursday", "Friday"],
            "best_times": ["6:00 AM", "12:00 PM", "6:00 PM", "8:00 PM"],
            "peak_engagement": "Tuesday-Thursday, 11 AM - 1 PM"
        },
        "facebook": {
            "weekdays": ["Tuesday", "Wednesday", "Thursday"],
            "best_times": ["9:00 AM", "1:00 PM", "3:00 PM"],
            "peak_engagement": "Wednesday 11 AM - 1 PM"
        },
        "linkedin": {
            "weekdays": ["Tuesday", "Wednesday", "Thursday"],
            "best_times": ["8:00 AM", "12:00 PM", "5:00 PM"],
            "peak_engagement": "Tuesday-Thursday, 10 AM - 12 PM"
        },
        "pinterest": {
            "weekdays": ["Saturday", "Sunday", "Tuesday", "Thursday"],
            "best_times": ["8:00 PM", "9:00 PM", "10:00 PM", "11:00 PM"],
            "peak_engagement": "Weekends 8-11 PM"
        },
        "x.com": {
            "weekdays": ["Tuesday", "Wednesday", "Thursday"],
            "best_times": ["9:00 AM", "12:00 PM", "3:00 PM", "6:00 PM"],
            "peak_engagement": "Wednesday 9 AM - 10 AM"
        },
        "twitter": {  # Same as x.com
            "weekdays": ["Tuesday", "Wednesday", "Thursday"],
            "best_times": ["9:00 AM", "12:00 PM", "3:00 PM", "6:00 PM"],
            "peak_engagement": "Wednesday 9 AM - 10 AM"
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the compiler with OpenAI API for content generation"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            logger.warning("No OpenAI API key provided. Caption generation will use templates only.")
            self.client = None
    
    def load_json_results(self, json_path: str) -> Dict[str, Any]:
        """Load optimization results from JSON file"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Successfully loaded JSON data from {json_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading JSON file: {e}")
            raise
    
    def extract_platform_data(self, json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract individual platform data from JSON results"""
        platforms_data = []
        
        # Check if it's a combined result file or individual platform file
        if "platforms" in json_data:
            # Combined results file
            for platform, platform_info in json_data["platforms"].items():
                if platform_info.get("status") == "success":
                    platforms_data.append({
                        "platform": platform,
                        "data": {**platform_info, "timestamp": json_data.get("timestamp")},  # Add timestamp from root
                        "session_info": json_data.get("optimization_metadata", {}),
                        "content_description": json_data.get("content_description", ""),
                        "product_photography": json_data.get("product_photography_session", {}),
                        "source_image": json_data.get("source_image", ""),
                        "user_uuid": json_data.get("user_uuid", None)  # Extract user UUID from combined file
                    })
        else:
            # Individual platform file
            platforms_data.append({
                "platform": json_data.get("platform", "unknown"),
                "data": json_data,  # Individual files already have timestamp in root
                "session_info": json_data.get("optimization_metadata", {}),
                "content_description": json_data.get("content_description", ""),
                "product_photography": json_data.get("product_photography_data", {}),
                "source_image": json_data.get("source_image", ""),
                "user_uuid": json_data.get("user_uuid", None)  # Extract user UUID from individual file
            })
        
        logger.info(f"Extracted data for {len(platforms_data)} platform(s)")
        return platforms_data
    
    def optimize_hashtags(self, hashtags: str, platform: str) -> Tuple[str, str]:
        """
        Optimize hashtags for platform-specific requirements
        Returns: (caption_hashtags, comment_hashtags)
        """
        if not hashtags:
            return "", ""
        
        specs = self.PLATFORM_SPECS.get(platform, self.PLATFORM_SPECS["instagram"])
        
        # Clean and parse hashtags
        hashtag_list = []
        if hashtags.startswith('#'):
            # Already formatted hashtags
            hashtag_list = [tag.strip() for tag in hashtags.split() if tag.strip().startswith('#')]
        else:
            # Comma-separated hashtag names
            hashtag_names = [name.strip() for name in hashtags.split(',') if name.strip()]
            hashtag_list = [f"#{name}" for name in hashtag_names]
        
        # Limit to optimal range
        optimal_min, optimal_max = specs["optimal_hashtags"]
        if len(hashtag_list) > optimal_max:
            hashtag_list = hashtag_list[:optimal_max]
        elif len(hashtag_list) < optimal_min:
            # Add generic hashtags if needed
            generic_tags = ["#content", "#social", "#engagement", "#trending", "#viral"]
            while len(hashtag_list) < optimal_min and generic_tags:
                hashtag_list.append(generic_tags.pop(0))
        
        hashtag_string = " ".join(hashtag_list)
        
        # Determine placement
        if specs["hashtag_placement"] == "first_comment":
            return "", hashtag_string
        else:
            return hashtag_string, ""
    
    def generate_cta(self, platform: str, content_context: str = "") -> str:
        """Generate platform-appropriate CTA"""
        specs = self.PLATFORM_SPECS.get(platform, self.PLATFORM_SPECS["instagram"])
        cta_style = specs["cta_style"]
        
        templates = self.CTA_TEMPLATES.get(cta_style, self.CTA_TEMPLATES["casual_engaging"])
        
        # Use AI to generate contextual CTA if client available
        if self.client and content_context:
            try:
                prompt = f"""
                Generate a short, engaging call-to-action for {platform} that fits this content context:
                {content_context[:200]}
                
                Style: {cta_style}
                Keep it under 20 words and match the platform's tone.
                """
                
                response = self.client.chat.completions.create(
                    model="gpt-4.1-nano",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=50,
                    temperature=0.7
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                logger.warning(f"AI CTA generation failed, using template: {e}")
        
        # Fallback to template
        import random
        return random.choice(templates)
    
    def generate_platform_caption(self, platform_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimized caption for a specific platform"""
        platform = platform_data["platform"]
        data = platform_data["data"]
        content_description = platform_data["content_description"]
        user_uuid = platform_data.get("user_uuid")  # Get user UUID (same for all platforms)
        
        # Extract timestamp from JSON data to ensure filename consistency
        json_timestamp = None
        if isinstance(data, dict):
            json_timestamp = data.get("timestamp")
        
        specs = self.PLATFORM_SPECS.get(platform, self.PLATFORM_SPECS["instagram"])
        
        # Extract key information
        hashtags = data.get("hashtags", "")
        niches = data.get("niches", [])
        profile_results = data.get("profile_results", {})
        
        # Generate base caption using AI if available
        base_caption = self.generate_ai_caption(
            content_description, platform, niches, specs
        )
        
        # Optimize hashtags
        caption_hashtags, comment_hashtags = self.optimize_hashtags(hashtags, platform)
        
        # Generate CTA
        cta = self.generate_cta(platform, content_description)
        
        # Assemble final caption
        caption_parts = []
        
        # Add hook (first line is crucial)
        if base_caption:
            lines = base_caption.split('\n')
            hook = lines[0] if lines else base_caption[:50]
            caption_parts.append(hook)
            
            # Add body if there are more lines
            if len(lines) > 1:
                body = '\n'.join(lines[1:])
                if specs["line_breaks"]:
                    caption_parts.append(body)
                else:
                    caption_parts.append(body.replace('\n', ' '))
        
        # Add CTA
        if cta:
            caption_parts.append(cta)
        
        # Join caption
        separator = '\n\n' if specs["line_breaks"] else ' '
        full_caption = separator.join(caption_parts)
        
        # Add inline hashtags if needed
        if caption_hashtags:
            hashtag_sep = '\n\n' if specs["line_breaks"] else ' '
            full_caption += hashtag_sep + caption_hashtags
        
        # Ensure caption length is optimal
        optimal_min, optimal_max = specs["optimal_caption_length"]
        if len(full_caption) > specs["max_caption_length"]:
            # Truncate to max length
            full_caption = full_caption[:specs["max_caption_length"]-3] + "..."
        
        # Get optimal posting info
        posting_info = self.OPTIMAL_POSTING_TIMES.get(platform, {})
        
        return {
            "platform": platform,
            "user_uuid": user_uuid,  # Include user UUID (same for all platforms)
            "json_timestamp": json_timestamp,  # Include timestamp from JSON
            "caption": full_caption,
            "comment_hashtags": comment_hashtags,
            "caption_length": len(full_caption),
            "optimal_length_range": f"{optimal_min}-{optimal_max} chars",
            "hashtag_count": len(caption_hashtags.split()) if caption_hashtags else 0,
            "comment_hashtag_count": len(comment_hashtags.split()) if comment_hashtags else 0,
            "posting_recommendations": posting_info,
            "profile_suggestions": profile_results.get("extracted_usernames", [])
        }
    
    def generate_ai_caption(self, content_description: str, platform: str, 
                           niches: List[str], specs: Dict[str, Any]) -> str:
        """Generate AI-powered caption optimized for platform"""
        if not self.client:
            # Fallback template-based caption
            return self.generate_template_caption(content_description, platform, niches)
        
        try:
            optimal_min, optimal_max = specs["optimal_caption_length"]
            
            prompt = f"""
            Create an engaging {platform} caption for this content:
            
            Content: {content_description[:1000]}
            Niches: {', '.join(niches)}
            
            Requirements:
            - Length: {optimal_min}-{optimal_max} characters (this is CRITICAL)
            - Style: {specs['cta_style']}
            - Use emojis: {specs['emojis']}
            - Line breaks allowed: {specs['line_breaks']}
            - Platform: {platform.upper()}
            
            Make it hook readers from the first line, be authentic and engaging.
            DO NOT include hashtags in the caption (they'll be added separately).
            Focus on storytelling and value for the audience.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {
                        "role": "system", 
                        "content": f"You are an expert {platform} content creator who writes viral, engaging captions that drive maximum engagement."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"AI caption generation failed: {e}, using template")
            return self.generate_template_caption(content_description, platform, niches)
    
    def generate_template_caption(self, content_description: str, platform: str, niches: List[str]) -> str:
        """Generate template-based caption as fallback"""
        # Extract key themes from content description
        words = content_description.lower().split()
        key_themes = niches[:2] if niches else ["content", "social"]
        
        # Platform-specific templates
        templates = {
            "instagram": "✨ {theme} vibes incoming! {content_snippet} What's your take on this?",
            "facebook": "Interesting thoughts on {theme}! {content_snippet} What do you think?",
            "linkedin": "Key insights on {theme}: {content_snippet} I'd love to hear your perspective.",
            "pinterest": "Amazing {theme} inspiration! {content_snippet} Save this for later!",
            "x.com": "🚀 {theme} update: {content_snippet} Thoughts?",
            "twitter": "🚀 {theme} update: {content_snippet} Thoughts?"
        }
        
        template = templates.get(platform, templates["instagram"])
        content_snippet = content_description[:100] + "..." if len(content_description) > 100 else content_description
        theme = key_themes[0] if key_themes else "content"
        
        return template.format(theme=theme, content_snippet=content_snippet)
    
    def save_compiled_caption(self, caption_data: Dict[str, Any], output_dir: str = "compiled_captions") -> str:
        """Save compiled caption to a formatted text file with EXACT same timestamp as JSON file"""
        Path(output_dir).mkdir(exist_ok=True)
        
        platform = caption_data["platform"]
        user_uuid = caption_data.get("user_uuid")
        json_timestamp = caption_data.get("json_timestamp")  # Use SAME timestamp from JSON
        
        # Use user UUID if available, otherwise generate new one
        if user_uuid:
            file_uuid = user_uuid
        else:
            file_uuid = str(uuid.uuid4())[:8]
        
        # Use the EXACT same timestamp from JSON file if available
        if json_timestamp:
            timestamp = json_timestamp
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # EXACT SAME naming pattern as JSON: {uuid}_{platform}_final_readable_{timestamp}.txt
        filename = f"{file_uuid}_{platform}_final_readable_{timestamp}.txt"
        filepath = Path(output_dir) / filename
        
        # Format content - STREAMLINED for content creators (NO OPTIMIZATION TIPS)
        content_lines = [
            "READY TO POST CONTENT:",
            "-" * 30,
            "",
            caption_data["caption"]
        ]
        
        # Add comment hashtags for Instagram
        if caption_data["comment_hashtags"] and platform == "instagram":
            content_lines.extend([
                "",
                "FIRST COMMENT (hashtags):",
                "-" * 30,
                caption_data["comment_hashtags"]
            ])
        
        # Add essential posting info only (NO OPTIMIZATION SECTION)
        content_lines.extend([
            "",
            "POSTING INFO:",
            "-" * 30,
            f"Platform: {platform.upper()}",
            f"Caption Length: {caption_data['caption_length']} characters"
        ])
        
        # Add posting recommendations
        if caption_data["posting_recommendations"]:
            posting = caption_data["posting_recommendations"]
            content_lines.extend([
                "",
                "BEST POSTING TIMES:",
                "-" * 30,
                f"Best Days: {', '.join(posting.get('weekdays', []))}",
                f"Best Times: {', '.join(posting.get('best_times', []))}",
                f"Peak Engagement: {posting.get('peak_engagement', 'N/A')}"
            ])
        
        # Add profile suggestions
        if caption_data["profile_suggestions"]:
            content_lines.extend([
                "",
                "SUGGESTED ACCOUNTS TO TAG:",
                "-" * 30,
            ])
            for username in caption_data["profile_suggestions"][:5]:  # Top 5
                content_lines.append(f"• {username}")
        
        # REMOVED: optimization_notes section - not needed for content creators
        
        # Save file
        full_content = "\r\n".join(content_lines)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            logger.info(f"Caption saved to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving caption file: {e}")
            raise
    
    def compile_from_json(self, json_path: str, output_dir: str = "compiled_captions") -> List[str]:
        """
        Main compilation function: process JSON and generate ready-to-post captions
        Returns list of generated file paths
        """
        logger.info(f"Starting caption compilation from {json_path}")
        
        # Load JSON data
        json_data = self.load_json_results(json_path)
        
        # Extract platform data
        platforms_data = self.extract_platform_data(json_data)
        
        generated_files = []
        
        # Process each platform
        for platform_info in platforms_data:
            try:
                logger.info(f"Compiling caption for {platform_info['platform']}")
                
                # Generate optimized caption
                caption_data = self.generate_platform_caption(platform_info)
                
                # Save to file
                filepath = self.save_compiled_caption(caption_data, output_dir)
                generated_files.append(filepath)
                
                # Print summary
                platform = caption_data["platform"]
                length = caption_data["caption_length"]
                hashtags = caption_data["hashtag_count"] + caption_data["comment_hashtag_count"]
                
                print(f"✅ {platform.upper()}: {length} chars, {hashtags} hashtags → {filepath}")
                
            except Exception as e:
                logger.error(f"Error compiling caption for {platform_info['platform']}: {e}")
                continue
        
        logger.info(f"Compilation complete! Generated {len(generated_files)} caption files")
        return generated_files


def main():
    """Main entry point for the compiler"""
    parser = argparse.ArgumentParser(
        description="Social Media Caption Compiler - Transform JSON optimization results into ready-to-post content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python compiler.py results.json
  python compiler.py combined_results.json --output-dir final_captions
  python compiler.py individual_platform.json --api-key your-openai-key
        """
    )
    
    parser.add_argument(
        "json_file",
        help="Path to JSON optimization results file"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        default="compiled_captions",
        help="Output directory for compiled captions (default: compiled_captions)"
    )
    
    parser.add_argument(
        "--api-key",
        help="OpenAI API key for AI-powered caption generation"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.json_file):
        print(f"❌ Error: JSON file '{args.json_file}' not found")
        return 1
    
    try:
        # Initialize compiler
        compiler = SocialMediaCaptionCompiler(api_key=args.api_key)
        
        print("🚀 Starting Social Media Caption Compilation...")
        print("=" * 60)
        
        # Compile captions
        generated_files = compiler.compile_from_json(args.json_file, args.output_dir)
        
        if generated_files:
            print("\n🎉 Compilation Complete!")
            print("=" * 60)
            print(f"📁 Output directory: {args.output_dir}")
            print(f"📝 Generated files: {len(generated_files)}")
            print("\n📋 Files created:")
            for i, filepath in enumerate(generated_files, 1):
                print(f"   {i}. {os.path.basename(filepath)}")
            
            print("\n✨ Your content is ready to post!")
            print("   • Clean, optimized captions")
            print("   • Platform-specific hashtags")
            print("   • Best posting times")
            print("   • Account tagging suggestions")
        else:
            print("❌ No captions were generated. Check the JSON file format.")
            return 1
            
    except Exception as e:
        logger.error(f"Compilation failed: {e}")
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())