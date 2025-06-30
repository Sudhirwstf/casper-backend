#!/usr/bin/env python3
"""
Platform Post Compiler
Takes JSON optimization results and creates final, ready-to-post content for each platform
with integrated SEO keywords, hashtags, user handles, and platform-specific formatting.
"""

import os
import sys
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('platform_compiler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('platform_compiler')

class PlatformPostCompiler:
    """Compile optimized content into final, ready-to-post format for each platform"""
    
    # Platform specifications and limits
    PLATFORM_SPECS = {
        "instagram_threads": {
            "name": "Instagram Threads",
            "max_limit": 500,
            "engagement_best": "138-150 chars",
            "optimal_length": 150,
            "supports_citations": False,
            "supports_markdown": False,
            "hashtag_placement": "end",
            "handle_placement": "middle",
            "title_style": "casual_hook"
        },
        "linkedin": {
            "name": "LinkedIn",
            "max_limit": 3000,
            "engagement_best": "150-300 chars overall",
            "optimal_length": 250,
            "supports_citations": True,
            "supports_markdown": True,
            "hashtag_placement": "end",
            "handle_placement": "middle",
            "title_style": "professional_insight"
        },
        "x.com": {
            "name": "X.com (Twitter)",
            "max_limit": 280,
            "engagement_best": "70-100 chars",
            "optimal_length": 100,
            "supports_citations": False,
            "supports_markdown": False,
            "hashtag_placement": "end",
            "handle_placement": "middle",
            "title_style": "attention_grabbing"
        },
        "blogger": {
            "name": "Blogger",
            "max_limit": 20000,
            "engagement_best": "readability matters",
            "optimal_length": 2000,
            "supports_citations": True,
            "supports_markdown": True,
            "hashtag_placement": "end",
            "handle_placement": "throughout",
            "title_style": "seo_optimized"
        },
        "medium": {
            "name": "Medium",
            "max_limit": None,
            "engagement_best": "1400-2100 words",
            "optimal_length": 1800,
            "supports_citations": True,
            "supports_markdown": True,
            "hashtag_placement": "end",
            "handle_placement": "throughout",
            "title_style": "compelling_story"
        },
        "facebook": {
            "name": "Facebook",
            "max_limit": 63000,
            "engagement_best": "40-80 chars",
            "optimal_length": 80,
            "supports_citations": False,
            "supports_markdown": False,
            "hashtag_placement": "end",
            "handle_placement": "middle",
            "title_style": "engaging_hook"
        }
    }
    
    def __init__(self):
        """Initialize the compiler with OpenAI client"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            
            self.client = OpenAI(api_key=api_key)
            logger.info("✅ Platform Post Compiler initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize compiler: {e}")
            self.client = None

    def load_optimization_results(self, file_path: str = None) -> Dict[str, Any]:
        """Load optimization results from JSON file or directory"""
        print("\n" + "="*60)
        print("📁 LOADING OPTIMIZATION RESULTS")
        print("="*60)
        
        if not file_path:
            file_path = input("Enter path to optimization results (file or directory): ").strip()
            
            # Handle quoted paths
            if file_path.startswith('"') and file_path.endswith('"'):
                file_path = file_path[1:-1]
            elif file_path.startswith("'") and file_path.endswith("'"):
                file_path = file_path[1:-1]
        
        try:
            path = Path(file_path)
            
            if path.is_file() and file_path.endswith('.json'):
                # Single JSON file
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ Loaded single JSON file: {path.name}")
                return data
                
            elif path.is_dir():
                # Directory with multiple platform files
                results = {"platforms": {}, "base_data": {}, "metadata": {}}
                
                # Look for individual platform files
                platform_files = list(path.glob("*_optimization.json"))
                summary_files = list(path.glob("optimization_summary.json"))
                
                if not platform_files:
                    raise FileNotFoundError("No platform optimization files found in directory")
                
                # Load individual platform files
                for platform_file in platform_files:
                    platform_key = platform_file.stem.replace('_optimization', '')
                    with open(platform_file, 'r', encoding='utf-8') as f:
                        platform_data = json.load(f)
                    results["platforms"][platform_key] = platform_data
                
                # Load summary file if available
                if summary_files:
                    with open(summary_files[0], 'r', encoding='utf-8') as f:
                        summary_data = json.load(f)
                    results["metadata"] = summary_data.get("optimization_summary", {})
                    results["base_data"] = summary_data.get("cross_platform_data", {})
                
                print(f"✅ Loaded {len(platform_files)} platform files from directory")
                return results
            else:
                raise FileNotFoundError("Invalid file path or unsupported file type")
                
        except Exception as e:
            logger.error(f"Error loading optimization results: {e}")
            print(f"❌ Error loading results: {e}")
            return {}

    def select_platforms_to_compile(self, available_platforms: List[str]) -> List[str]:
        """Allow user to select which platforms to compile"""
        print("\n" + "="*60)
        print("🎯 PLATFORM COMPILATION SELECTION")
        print("="*60)
        
        print("Available platforms for compilation:")
        for i, platform_key in enumerate(available_platforms, 1):
            platform_name = self.PLATFORM_SPECS.get(platform_key, {}).get('name', platform_key.title())
            print(f"  {i}. {platform_name}")
        
        print(f"  {len(available_platforms) + 1}. All Platforms")
        
        while True:
            try:
                selection = input(f"\nEnter your choice (1-{len(available_platforms) + 1}): ").strip()
                
                # Handle "All Platforms" selection
                if selection == str(len(available_platforms) + 1):
                    print("✅ Selected: All Platforms")
                    return available_platforms
                
                # Parse multiple selections
                if ',' in selection:
                    selected_indices = [int(x.strip()) for x in selection.split(',')]
                    selected_platforms = []
                    
                    for index in selected_indices:
                        if 1 <= index <= len(available_platforms):
                            platform_key = available_platforms[index - 1]
                            selected_platforms.append(platform_key)
                        else:
                            raise ValueError(f"Invalid platform number: {index}")
                    
                    if selected_platforms:
                        platform_names = [self.PLATFORM_SPECS.get(p, {}).get('name', p.title()) for p in selected_platforms]
                        print(f"✅ Selected platforms: {', '.join(platform_names)}")
                        return selected_platforms
                else:
                    # Single selection
                    choice_idx = int(selection) - 1
                    if 0 <= choice_idx < len(available_platforms):
                        selected_platform = available_platforms[choice_idx]
                        platform_name = self.PLATFORM_SPECS.get(selected_platform, {}).get('name', selected_platform.title())
                        print(f"✅ Selected platform: {platform_name}")
                        return [selected_platform]
                    else:
                        print("❌ Invalid choice. Please try again.")
                        
            except ValueError as e:
                print(f"❌ Invalid input: {e}. Please try again.")
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled by user")
                sys.exit(0)

    def generate_platform_title(self, platform_key: str, content: str, seo_keywords: List[str], niche: str) -> str:
        """Generate an engaging title for the specific platform"""
        platform_spec = self.PLATFORM_SPECS.get(platform_key, {})
        title_style = platform_spec.get('title_style', 'generic')
        platform_name = platform_spec.get('name', platform_key.title())
        
        # Prepare SEO keywords context
        seo_context = ', '.join(seo_keywords[:5]) if seo_keywords else niche
        
        title_prompts = {
            "casual_hook": f"""Create a casual, relatable title for {platform_name} that hooks readers immediately.
Style: Conversational, authentic, uses "you" language
Length: 8-15 words max
Keywords to include: {seo_context}
Make it sound like something a friend would say to grab attention.""",

            "professional_insight": f"""Create a professional, thought-leadership title for {platform_name}.
Style: Authoritative, insightful, industry-focused
Length: 10-20 words
Keywords to include: {seo_context}
Make it sound like valuable business insight or professional advice.""",

            "attention_grabbing": f"""Create a punchy, viral-worthy title for {platform_name}.
Style: Bold, controversial, or surprising
Length: 5-12 words max
Keywords to include: {seo_context}
Make people want to click/engage immediately.""",

            "seo_optimized": f"""Create an SEO-optimized title for {platform_name} blog post.
Style: Search-friendly, keyword-rich, informative
Length: 50-60 characters
Keywords to include: {seo_context}
Balance SEO with readability and engagement.""",

            "compelling_story": f"""Create a compelling, story-driven title for {platform_name}.
Style: Narrative, emotional, thought-provoking
Length: 40-60 characters
Keywords to include: {seo_context}
Make it feel like the beginning of an important story.""",

            "engaging_hook": f"""Create an engaging hook title for {platform_name}.
Style: Conversational, relatable, engaging
Length: 8-15 words
Keywords to include: {seo_context}
Make people want to read more and engage."""
        }
        
        prompt = title_prompts.get(title_style, title_prompts["engaging_hook"])
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert copywriter specializing in {platform_name} content. Create titles that maximize engagement."
                    },
                    {
                        "role": "user", 
                        "content": f"""{prompt}

Article content sample:
{content[:500]}...

Return only the title, no explanations."""
                    }
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            title = response.choices[0].message.content.strip()
            # Remove quotes if present
            title = title.strip('"').strip("'")
            return title
            
        except Exception as e:
            logger.warning(f"⚠️ AI title generation failed for {platform_name}: {e}")
            # Fallback title
            return f"{niche.title()} Insights: {content.split('.')[0][:50]}..."

    def integrate_seo_keywords(self, content: str, seo_keywords: List[str], platform_key: str) -> str:
        """Intelligently integrate SEO keywords into content"""
        if not seo_keywords:
            return content
        
        platform_spec = self.PLATFORM_SPECS.get(platform_key, {})
        max_length = platform_spec.get('max_limit', 1000)
        
        try:
            prompt = f"""Enhance this content by naturally integrating SEO keywords while maintaining readability and flow.

Original content:
{content}

SEO Keywords to integrate: {', '.join(seo_keywords[:10])}

Instructions:
1. Integrate keywords naturally - don't force them
2. Maintain the original meaning and tone
3. Keep content under {max_length} characters if limit exists
4. Use keywords in context, not just stuffed in
5. Prioritize readability over keyword density

Return the enhanced content with keywords naturally integrated."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert SEO content writer. Integrate keywords naturally while maintaining quality and readability."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            enhanced_content = response.choices[0].message.content.strip()
            
            # Ensure we don't exceed platform limits
            if max_length and len(enhanced_content) > max_length:
                enhanced_content = enhanced_content[:max_length-50] + "..."
            
            return enhanced_content
            
        except Exception as e:
            logger.warning(f"⚠️ SEO integration failed: {e}")
            return content

    def format_platform_post(self, platform_key: str, platform_data: Dict[str, Any], 
                           base_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create final formatted post for specific platform"""
        platform_spec = self.PLATFORM_SPECS.get(platform_key, {})
        platform_name = platform_spec.get('name', platform_key.title())
        
        logger.info(f"🎯 Compiling post for {platform_name}")
        
        # Extract data
        original_content = platform_data.get('content', {}).get('optimized_text', '')
        seo_keywords = platform_data.get('engagement', {}).get('seo_keywords', [])
        hashtags = platform_data.get('content', {}).get('hashtags', [])
        tagging_accounts = platform_data.get('engagement', {}).get('tagging_profiles', {}).get('tagging_accounts', [])
        citations = platform_data.get('content', {}).get('citations', [])
        niche = platform_data.get('metadata', {}).get('niche', 'general')
        
        # Generate engaging title
        title = self.generate_platform_title(platform_key, original_content, seo_keywords, niche)
        
        # Integrate SEO keywords into content
        enhanced_content = self.integrate_seo_keywords(original_content, seo_keywords, platform_key)
        
        # Format content based on platform specifications
        formatted_content = self._apply_platform_formatting(
            platform_key, enhanced_content, title, hashtags, tagging_accounts, citations, platform_spec
        )
        
        # Prepare final post data
        final_post = {
            "platform": platform_name,
            "platform_key": platform_key,
            "title": title,
            "content": formatted_content,
            "character_count": len(formatted_content),
            "max_limit": platform_spec.get('max_limit'),
            "engagement_best": platform_spec.get('engagement_best'),
            "seo_keywords_used": seo_keywords[:10],
            "hashtags_used": hashtags,
            "handles_used": [acc.get('handle', '') for acc in tagging_accounts[:5]],
            "citations_included": citations if platform_spec.get('supports_citations') else [],
            "platform_optimized": True,
            "ready_to_post": True,
            "compilation_timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ {platform_name} post compiled ({len(formatted_content)} chars)")
        return final_post

    def _apply_platform_formatting(self, platform_key: str, content: str, title: str, 
                                 hashtags: List[str], handles: List[Dict], citations: List[str], 
                                 platform_spec: Dict) -> str:
        """Apply platform-specific formatting rules"""
        
        platform_name = platform_spec.get('name', platform_key.title())
        max_limit = platform_spec.get('max_limit')
        supports_markdown = platform_spec.get('supports_markdown', False)
        supports_citations = platform_spec.get('supports_citations', False)
        hashtag_placement = platform_spec.get('hashtag_placement', 'end')
        handle_placement = platform_spec.get('handle_placement', 'middle')
        
        # Start building the formatted post
        formatted_parts = []
        
        # Add title based on platform
        if platform_key in ['medium', 'blogger']:
            # Long-form platforms - title as heading
            if supports_markdown:
                formatted_parts.append(f"# {title}\n")
            else:
                formatted_parts.append(f"{title}\n{'='*len(title)}\n")
        elif platform_key == 'linkedin':
            # LinkedIn - title as hook
            formatted_parts.append(f"💡 {title}\n")
        elif platform_key in ['x.com', 'facebook', 'instagram_threads']:
            # Social platforms - title integrated into content
            if len(title) + len(content) + 50 < (max_limit or 1000):
                formatted_parts.append(f"{title}\n")
        
        # Process content with handle integration
        processed_content = self._integrate_handles(content, handles, handle_placement, platform_key)
        formatted_parts.append(processed_content)
        
        # Add citations for platforms that support them
        if supports_citations and citations:
            citations_text = self._format_citations(citations, supports_markdown)
            formatted_parts.append(f"\n{citations_text}")
        
        # Add hashtags based on placement
        if hashtags and hashtag_placement == 'end':
            hashtag_text = ' '.join(hashtags[:8])  # Limit hashtags
            formatted_parts.append(f"\n\n{hashtag_text}")
        
        # Join all parts
        final_content = '\n'.join(formatted_parts).strip()
        
        # Ensure we don't exceed platform limits
        if max_limit and len(final_content) > max_limit:
            # Trim content intelligently
            final_content = self._trim_content_intelligently(final_content, max_limit, hashtags)
        
        return final_content

    def _integrate_handles(self, content: str, handles: List[Dict], placement: str, platform_key: str) -> str:
        """Integrate user handles into content based on platform strategy"""
        if not handles:
            return content
        
        # Get clean handles
        clean_handles = [handle.get('handle', '').strip() for handle in handles[:3] if handle.get('handle')]
        if not clean_handles:
            return content
        
        try:
            if placement == 'middle':
                # Integrate handles naturally into content
                prompt = f"""Integrate these user handles naturally into the content where they make sense contextually.

Content:
{content}

Handles to integrate: {', '.join(clean_handles)}

Rules:
1. Only add handles where they make contextual sense
2. Don't force all handles if they don't fit naturally
3. Use handles to tag relevant people/organizations mentioned
4. Keep the content flow natural and readable
5. Platform: {platform_key}

Return the content with handles naturally integrated."""

                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert social media content creator. Integrate user handles naturally without disrupting content flow."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=800
                )
                
                return response.choices[0].message.content.strip()
                
            elif placement == 'throughout':
                # For long-form content, add handles at strategic points
                sentences = content.split('. ')
                if len(sentences) > 3:
                    # Add handle after first paragraph
                    insertion_point = len(sentences) // 3
                    sentences[insertion_point] += f" {clean_handles[0]}"
                    if len(clean_handles) > 1 and len(sentences) > 6:
                        insertion_point_2 = (len(sentences) * 2) // 3
                        sentences[insertion_point_2] += f" {clean_handles[1]}"
                
                return '. '.join(sentences)
            
            else:  # 'end' or default
                # Add handles at the end
                return f"{content}\n\nCC: {' '.join(clean_handles[:3])}"
                
        except Exception as e:
            logger.warning(f"⚠️ Handle integration failed: {e}")
            # Fallback - add at end
            return f"{content}\n\n{' '.join(clean_handles[:2])}"

    def _format_citations(self, citations: List[str], supports_markdown: bool) -> str:
        """Format citations based on platform capabilities"""
        if not citations:
            return ""
        
        if supports_markdown:
            citation_text = "## Sources\n"
            for i, citation in enumerate(citations[:5], 1):
                citation_text += f"{i}. [{citation}]({citation})\n"
        else:
            citation_text = "Sources:\n"
            for i, citation in enumerate(citations[:5], 1):
                citation_text += f"{i}. {citation}\n"
        
        return citation_text.strip()

    def _trim_content_intelligently(self, content: str, max_limit: int, hashtags: List[str]) -> str:
        """Intelligently trim content to fit platform limits while preserving key elements"""
        if len(content) <= max_limit:
            return content
        
        # Reserve space for hashtags
        hashtag_space = len(' '.join(hashtags[:5])) + 10 if hashtags else 0
        target_length = max_limit - hashtag_space
        
        # Try to trim at sentence boundaries
        sentences = content.split('. ')
        trimmed_content = ""
        
        for sentence in sentences:
            if len(trimmed_content + sentence + '. ') <= target_length:
                trimmed_content += sentence + '. '
            else:
                break
        
        # If we couldn't fit even one sentence, trim at word boundaries
        if not trimmed_content:
            words = content.split()
            trimmed_content = ""
            for word in words:
                if len(trimmed_content + word + ' ') <= target_length - 3:
                    trimmed_content += word + ' '
                else:
                    break
            trimmed_content += "..."
        
        # Add hashtags back if space
        if hashtags and len(trimmed_content) + hashtag_space <= max_limit:
            hashtag_text = ' '.join(hashtags[:5])
            trimmed_content += f"\n\n{hashtag_text}"
        
        return trimmed_content.strip()

    def compile_all_platforms(self, optimization_results: Dict[str, Any], 
                            selected_platforms: List[str]) -> Dict[str, Any]:
        """Compile posts for all selected platforms"""
        compiled_results = {
            "compilation_metadata": {
                "timestamp": datetime.now().isoformat(),
                "platforms_compiled": len(selected_platforms),
                "compiler_version": "1.0"
            },
            "compiled_posts": {}
        }
        
        base_data = optimization_results.get('base_data', {})
        platforms_data = optimization_results.get('platforms', {})
        
        print(f"\nCompiling posts for {len(selected_platforms)} platform(s)...")
        
        for platform_key in selected_platforms:
            platform_data = platforms_data.get(platform_key, {})
            if not platform_data:
                logger.warning(f" No data found for platform: {platform_key}")
                continue
            
            platform_name = self.PLATFORM_SPECS.get(platform_key, {}).get('name', platform_key.title())
            print(f"   Compiling {platform_name}...")
            
            try:
                compiled_post = self.format_platform_post(platform_key, platform_data, base_data)
                compiled_results["compiled_posts"][platform_key] = compiled_post
                print(f"   {platform_name} compiled successfully")
            except Exception as e:
                logger.error(f" Failed to compile {platform_name}: {e}")
                compiled_results["compiled_posts"][platform_key] = {
                    "platform": platform_name,
                    "error": str(e),
                    "compilation_failed": True
                }
                print(f"  {platform_name} compilation failed")
        
        return compiled_results

    def save_compiled_results(self, compiled_results: Dict[str, Any], output_dir: str = None) -> str:
        """Save compiled results to JSON file"""
        if not output_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"compiled_posts_{timestamp}"
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save main compiled results
        main_file = os.path.join(output_dir, "compiled_posts.json")
        with open(main_file, 'w', encoding='utf-8') as f:
            json.dump(compiled_results, f, indent=2, ensure_ascii=False)
        
        # Save individual platform files
        compiled_posts = compiled_results.get("compiled_posts", {})
        for platform_key, post_data in compiled_posts.items():
            if post_data.get("compilation_failed"):
                continue
                
            platform_file = os.path.join(output_dir, f"{platform_key}_final_post.json")
            with open(platform_file, 'w', encoding='utf-8') as f:
                json.dump(post_data, f, indent=2, ensure_ascii=False)
        
        # Create readable text versions
        self._create_readable_versions(compiled_posts, output_dir)
        
        logger.info(f"Compiled results saved to: {output_dir}")
        return output_dir

    def _create_readable_versions(self, compiled_posts: Dict[str, Any], output_dir: str):
        """Create human-readable text versions of compiled posts"""
        for platform_key, post_data in compiled_posts.items():
            if post_data.get("compilation_failed"):
                continue
            
            platform_name = post_data.get("platform", platform_key.title())
            content = post_data.get("content", "")
            title = post_data.get("title", "")
            
            readable_content = f"""
# {platform_name} - Final Post
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Title
{title}

## Content
{content}

## Stats
- Character Count: {post_data.get('character_count', 0)}
- Platform Limit: {post_data.get('max_limit', 'No limit')}
- SEO Keywords Used: {len(post_data.get('seo_keywords_used', []))}
- Hashtags Used: {len(post_data.get('hashtags_used', []))}
- Handles Used: {len(post_data.get('handles_used', []))}

## SEO Keywords
{', '.join(post_data.get('seo_keywords_used', []))}

## Hashtags
{' '.join(post_data.get('hashtags_used', []))}

## Tagged Handles
{', '.join(post_data.get('handles_used', []))}

## Ready to Post: {' YES' if post_data.get('ready_to_post') else '❌ NO'}
            """.strip()
            
            readable_file = os.path.join(output_dir, f"{platform_key}_readable.txt")
            with open(readable_file, 'w', encoding='utf-8') as f:
                f.write(readable_content)

    def display_compiled_results(self, compiled_results: Dict[str, Any]):
        """Display comprehensive compilation results"""
        print("\n" + "="*80)
        print(" PLATFORM POST COMPILATION COMPLETE!")
        print("="*80)
        
        metadata = compiled_results.get("compilation_metadata", {})
        compiled_posts = compiled_results.get("compiled_posts", {})
        
        print(f"\nCOMPILATION SUMMARY:")
        print(f"Platforms Compiled: {metadata.get('platforms_compiled', 0)}")
        print(f"Successful Compilations: {len([p for p in compiled_posts.values() if not p.get('compilation_failed')])}")
        print(f"Failed Compilations: {len([p for p in compiled_posts.values() if p.get('compilation_failed')])}")
        
        # Display each compiled post
        for platform_key, post_data in compiled_posts.items():
            print(f"\n{'='*60}")
            print(f" {post_data.get('platform', platform_key.title()).upper()}")
            print(f"{'='*60}")
            
            if post_data.get("compilation_failed"):
                print(f"Compilation Failed: {post_data.get('error', 'Unknown error')}")
                continue
            
            # Post stats
            print(f"Status: Ready to Post")
            print(f"📝 Title: {post_data.get('title', 'N/A')}")
            print(f"📊 Character Count: {post_data.get('character_count', 0)}")
            if post_data.get('max_limit'):
                print(f"🎯 Platform Limit: {post_data['max_limit']} chars")
            print(f"🔍 SEO Keywords: {len(post_data.get('seo_keywords_used', []))}")
            print(f"🏷️ Hashtags: {len(post_data.get('hashtags_used', []))}")
            print(f"👥 Tagged Handles: {len(post_data.get('handles_used', []))}")
            
            # Show content preview
            content = post_data.get('content', '')
            print(f"\n📝 FINAL CONTENT PREVIEW:")
            print("-" * 40)
            if len(content) > 300:
                print(content[:300] + "...")
                print(f"\n[Content truncated - full content in output files]")
            else:
                print(content)
            
            # Show SEO keywords used
            seo_keywords = post_data.get('seo_keywords_used', [])
            if seo_keywords:
                print(f"\n🔍 SEO KEYWORDS INTEGRATED:")
                print(", ".join(seo_keywords[:8]))
            
            # Show hashtags
            hashtags = post_data.get('hashtags_used', [])
            if hashtags:
                print(f"\n🏷️ HASHTAGS:")
                print(" ".join(hashtags[:8]))
            
            # Show handles
            handles = post_data.get('handles_used', [])
            if handles:
                print(f"\n👥 TAGGED HANDLES:")
                print(", ".join([h for h in handles if h]))
        
        print(f"\n{'='*80}")
        print("✨ All posts compiled and ready for publishing!")
        print(f"{'='*80}")

    def run_compilation_pipeline(self) -> bool:
        """Run the complete compilation pipeline"""
        try:
            print("🚀 Platform Post Compiler")
            print("Transform optimization results into ready-to-post content")
            print("="*70)
            
            # Step 1: Load optimization results
            optimization_results = self.load_optimization_results()
            if not optimization_results:
                print("❌ No optimization results loaded. Exiting.")
                return False
            
            # Step 2: Get available platforms
            if 'platforms' in optimization_results:
                # Directory format
                available_platforms = list(optimization_results['platforms'].keys())
            else:
                # Single file format - extract platform keys from results
                available_platforms = []
                for key in optimization_results.keys():
                    if key.endswith('_optimization') or key in self.PLATFORM_SPECS:
                        platform_key = key.replace('_optimization', '')
                        if platform_key in self.PLATFORM_SPECS:
                            available_platforms.append(platform_key)
            
            if not available_platforms:
                print("❌ No valid platforms found in optimization results.")
                return False
            
            print(f"✅ Found {len(available_platforms)} optimized platform(s)")
            
            # Step 3: Select platforms to compile
            selected_platforms = self.select_platforms_to_compile(available_platforms)
            
            # Step 4: Compile posts for selected platforms
            compiled_results = self.compile_all_platforms(optimization_results, selected_platforms)
            
            # Step 5: Save compiled results
            output_dir = self.save_compiled_results(compiled_results)
            
            # Step 6: Display results
            self.display_compiled_results(compiled_results)
            
            # Step 7: Show file locations
            print(f"\n💾 FILES SAVED:")
            print(f"📁 Output Directory: {output_dir}")
            print(f"📄 Main Results: compiled_posts.json")
            print(f"📱 Individual Posts: {len(selected_platforms)} platform files")
            print(f"📖 Readable Versions: {len(selected_platforms)} .txt files")
            
            print(f"\n🎯 NEXT STEPS:")
            print(f"1. Review compiled posts in the output directory")
            print(f"2. Copy content from .txt files for easy posting")
            print(f"3. Use JSON files for programmatic posting")
            print(f"4. Post at optimal times specified in original optimization")
            
            return True
            
        except KeyboardInterrupt:
            print("\n👋 Compilation cancelled by user")
            return False
        except Exception as e:
            logger.error(f"Compilation pipeline failed: {e}")
            print(f"\n❌ Compilation failed: {e}")
            return False


def integrate_with_app():
    """Integration function to be called from app.py"""
    print("\n" + "="*60)
    print("🔗 LAUNCHING POST COMPILER")
    print("="*60)
    
    compiler = PlatformPostCompiler()
    success = compiler.run_compilation_pipeline()
    
    if success:
        print("\n✅ Post compilation completed successfully!")
        print("Your optimized content is ready for publishing across all platforms.")
    else:
        print("\n❌ Post compilation failed.")
        print("Please check the logs and try again.")
    
    return success


def main():
    """Main function for standalone execution"""
    try:
        compiler = PlatformPostCompiler()
        compiler.run_compilation_pipeline()
        
    except KeyboardInterrupt:
        print("\n👋 Process cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Platform compiler failed: {e}")
        print(f"\n❌ Compiler failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

    