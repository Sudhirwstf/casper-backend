import os
import base64
import requests
from openai import OpenAI
from typing import Optional, Union
import json
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')

class ImageAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the ImageAnalyzer with OpenAI API key.
        
        Args:
            api_key: OpenAI API key. If not provided, will look for OPENAI_API_KEY environment variable.
        """
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            # Will use OPENAI_API_KEY environment variable
            self.client = OpenAI()
    
    def analyze_image_from_url(self, 
                              image_url: str, 
                              prompt: str = "Describe this image in detail. Include objects, colors, composition, mood, and any text you can see in such way that this picture is going to be uploaded on the social media.",
                              model: str = "gpt-4.1-nano",
                              detail_level: str = "high") -> str:
        """
        Analyze an image from a URL and return a detailed description.
        
        Args:
            image_url: URL of the image to analyze
            prompt: Custom prompt for image analysis
            model: OpenAI model to use (gpt-4o, gpt-4o-mini, etc.)
            detail_level: "high", "low", or "auto"
        
        Returns:
            Detailed description of the image
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                    "detail": detail_level
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error analyzing image: {str(e)}"
    
    def analyze_image_from_file(self, 
                               file_path: str, 
                               prompt: str = "Describe what is happening in the image and what the person is doing and if there is no person then tell me waht is ther in teh image and oevrall things.",
                               model: str = "gpt-4.1-nano",
                               detail_level: str = "high") -> str:
        """
        Analyze a local image file and return a detailed description.
        
        Args:
            file_path: Path to the local image file
            prompt: Custom prompt for image analysis
            model: OpenAI model to use
            detail_level: "high", "low", or "auto"
        
        Returns:
            Detailed description of the image
        """
        try:
            # Read and encode the image
            with open(file_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Determine the image format
            file_extension = file_path.lower().split('.')[-1]
            if file_extension == 'jpg':
                file_extension = 'jpeg'
            
            data_url = f"data:image/{file_extension};base64,{base64_image}"
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_url,
                                    "detail": detail_level
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error analyzing image: {str(e)}"
    
    def analyze_multiple_images(self, 
                               image_urls: list, 
                               prompt: str = "Compare and describe these images in detail.",
                               model: str = "gpt-4.1-nano",
                               detail_level: str = "high") -> str:
        """
        Analyze multiple images at once.
        
        Args:
            image_urls: List of image URLs
            prompt: Custom prompt for image analysis
            model: OpenAI model to use
            detail_level: "high", "low", or "auto"
        
        Returns:
            Detailed description and comparison of the images
        """
        try:
            content = [{"type": "text", "text": prompt}]
            
            # Add each image to the content
            for url in image_urls:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": url,
                        "detail": detail_level
                    }
                })
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error analyzing images: {str(e)}"

def main():
    """
    Example usage of the ImageAnalyzer class.
    """
    # Initialize the analyzer
    # Make sure to set your OPENAI_API_KEY environment variable
    # or pass it directly: analyzer = ImageAnalyzer(api_key="your-api-key-here")
    analyzer = ImageAnalyzer()
    
    print("=== OpenAI Vision Image Analyzer ===\n")
    
    while True:
        print("\nChoose an option:")
        print("1. Analyze image from URL")
        print("2. Analyze local image file")
        print("3. Analyze multiple images from URLs")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            image_url = input("Enter image URL: ").strip()
            if image_url:
                print("\nAnalyzing image...")
                description = analyzer.analyze_image_from_url(image_url)
                print(f"\n{'='*50}")
                print("IMAGE DESCRIPTION:")
                print(f"{'='*50}")
                print(description)
                print(f"{'='*50}")
        
        elif choice == '2':
            file_path = input("Enter path to image file: ").strip()
            if file_path and os.path.exists(file_path):
                print("\nAnalyzing image...")
                description = analyzer.analyze_image_from_file(file_path)
                print(f"\n{'='*50}")
                print("IMAGE DESCRIPTION:")
                print(f"{'='*50}")
                print(description)
                print(f"{'='*50}")
            else:
                print("File not found!")
        
        elif choice == '3':
            urls_input = input("Enter image URLs separated by commas: ").strip()
            if urls_input:
                urls = [url.strip() for url in urls_input.split(',')]
                print(f"\nAnalyzing {len(urls)} images...")
                description = analyzer.analyze_multiple_images(urls)
                print(f"\n{'='*50}")
                print("IMAGES ANALYSIS:")
                print(f"{'='*50}")
                print(description)
                print(f"{'='*50}")
        
        elif choice == '4':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice! Please try again.")

# Example usage as a simple function
def analyze_image_simple(image_url: str, api_key: Optional[str] = None) -> str:
    """
    Simple function to analyze a single image from URL.
    
    Args:
        image_url: URL of the image to analyze
        api_key: OpenAI API key (optional if set as environment variable)
    
    Returns:
        Description of the image
    """
    analyzer = ImageAnalyzer(api_key)
    return analyzer.analyze_image_from_url(image_url)

if __name__ == "__main__":
    # Set up your API key before running
    print("Make sure to set your OPENAI_API_KEY environment variable!")
    print("You can do this by running: export OPENAI_API_KEY='your-api-key-here'")
    print("Or set it in your Python script directly.\n")
    
    # Example usage:

    
    main()




    


