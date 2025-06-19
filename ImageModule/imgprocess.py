import os
import sys
from PIL import Image, ImageEnhance
import argparse
from pathlib import Path
import math

class SocialMediaImageOptimizer:
    """Advanced image optimizer for social media platforms"""
    
    def __init__(self):
        self.aspect_ratios = {
            'landscape': (1.91, 1),     # 1.91:1 for Facebook/Instagram landscape
            'square': (1, 1),           # 1:1 for Instagram square
            'portrait': (4, 5)          # 4:5 for Instagram portrait
        }
        
        self.min_dimensions = {
            'landscape': (1200, 627),   # Facebook recommended
            'square': (1080, 1080),     # Instagram square
            'portrait': (1080, 1350)    # Instagram portrait
        }
        
        self.target_dpi = 72  # Web standard
        
    def get_crop_box_smart(self, img_width, img_height, target_ratio):
        """Calculate optimal crop box with minimal loss using smart cropping"""
        current_ratio = img_width / img_height
        target_ratio_val = target_ratio[0] / target_ratio[1]
        
        if abs(current_ratio - target_ratio_val) < 0.01:
            return (0, 0, img_width, img_height)
        
        if current_ratio > target_ratio_val:
            # Image is wider than target - crop width
            new_width = int(img_height * target_ratio_val)
            left = (img_width - new_width) // 2
            return (left, 0, left + new_width, img_height)
        else:
            # Image is taller than target - crop height
            new_height = int(img_width / target_ratio_val)
            top = (img_height - new_height) // 2
            return (0, top, img_width, top + new_height)
    
    def enhance_image_quality(self, image):
        """Enhance image quality for better social media appearance"""
        # Slightly enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.1)
        
        # Slightly enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.05)
        
        return image
    
    def resize_with_quality(self, image, target_size):
        """Resize image maintaining quality using Lanczos resampling"""
        return image.resize(target_size, Image.Resampling.LANCZOS)
    
    def detect_best_aspect_ratio(self, img_width, img_height):
        """
        Automatically detect which aspect ratio the image is closest to
        
        Args:
            img_width: Image width
            img_height: Image height
            
        Returns:
            str: 'landscape', 'square', or 'portrait'
        """
        current_ratio = img_width / img_height
        
        # Calculate target ratios correctly
        landscape_ratio = self.aspect_ratios['landscape'][0] / self.aspect_ratios['landscape'][1]  # 1.91
        square_ratio = self.aspect_ratios['square'][0] / self.aspect_ratios['square'][1]  # 1.0
        portrait_ratio = self.aspect_ratios['portrait'][0] / self.aspect_ratios['portrait'][1]  # 0.8
        
        # Calculate absolute distances to each target ratio
        distances = {
            'landscape': abs(current_ratio - landscape_ratio),
            'square': abs(current_ratio - square_ratio),
            'portrait': abs(current_ratio - portrait_ratio)
        }
        
        # Find the format with minimum distance
        best_format = min(distances, key=distances.get)
        
        # Debug information
        print(f"Image dimensions: {img_width}x{img_height}")
        print(f"Current ratio: {current_ratio:.3f}")
        print(f"Target ratios - Landscape: {landscape_ratio:.3f}, Square: {square_ratio:.3f}, Portrait: {portrait_ratio:.3f}")
        print(f"Distances - Landscape: {distances['landscape']:.3f}, Square: {distances['square']:.3f}, Portrait: {distances['portrait']:.3f}")
        print(f"Best match: {best_format} (closest distance: {distances[best_format]:.3f})")
        
        # Add additional logic for edge cases
        if current_ratio > 1.5:
            # Clearly landscape
            return 'landscape'
        elif current_ratio < 0.9:
            # Clearly portrait
            return 'portrait'
        elif 0.9 <= current_ratio <= 1.1:
            # Very close to square
            return 'square'
        else:
            # Use the calculated best match
            return best_format
    
    def process_image(self, input_path, output_dir, target_format='auto', 
                     output_format='PNG', enhance_quality=True):
        """
        Process a single image for social media optimization
        
        Args:
            input_path: Path to input image
            output_dir: Directory to save processed image  
            target_format: 'auto', 'landscape', 'square', or 'portrait'
            output_format: 'PNG' or 'JPG'
            enhance_quality: Whether to apply quality enhancements
        """
        try:
            # Open and validate image
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    if output_format.upper() == 'JPG':
                        # Create white background for JPG
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                        img = background
                    else:
                        img = img.convert('RGBA')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                original_size = img.size
                print(f"Original size: {original_size[0]}x{original_size[1]}")
                
                # Auto-detect best format if requested
                if target_format == 'auto':
                    target_format = self.detect_best_aspect_ratio(img.width, img.height)
                    print(f"Auto-detected format: {target_format}")
                
                # Get target aspect ratio and minimum dimensions
                target_ratio = self.aspect_ratios[target_format]
                min_dims = self.min_dimensions[target_format]
                
                # Smart crop to target aspect ratio
                crop_box = self.get_crop_box_smart(img.width, img.height, target_ratio)
                cropped_img = img.crop(crop_box)
                
                crop_loss = (1 - (crop_box[2] - crop_box[0]) * (crop_box[3] - crop_box[1]) / 
                           (original_size[0] * original_size[1])) * 100
                print(f"Cropping loss: {crop_loss:.1f}%")
                
                # Calculate final dimensions
                current_width, current_height = cropped_img.size
                
                # Ensure minimum dimensions are met
                scale_factor = max(min_dims[0] / current_width, min_dims[1] / current_height)
                
                if scale_factor > 1:
                    final_width = int(current_width * scale_factor)
                    final_height = int(current_height * scale_factor)
                    print(f"Upscaling by factor: {scale_factor:.2f}")
                else:
                    final_width, final_height = current_width, current_height
                
                # Resize image
                final_img = self.resize_with_quality(cropped_img, (final_width, final_height))
                
                # Enhance quality if requested
                if enhance_quality:
                    final_img = self.enhance_image_quality(final_img)
                
                # Prepare output filename
                input_name = Path(input_path).stem
                output_filename = f"{input_name}_{target_format}.{output_format.lower()}"
                output_path = Path(output_dir) / output_filename
                
                # Save with appropriate quality settings
                save_kwargs = {'dpi': (self.target_dpi, self.target_dpi)}
                
                if output_format.upper() == 'JPG':
                    save_kwargs.update({
                        'quality': 95,
                        'optimize': True,
                        'progressive': True
                    })
                elif output_format.upper() == 'PNG':
                    save_kwargs.update({
                        'optimize': True,
                        'compress_level': 6
                    })
                
                final_img.save(output_path, **save_kwargs)
                
                print(f"✓ Processed: {output_filename}")
                print(f"  Final size: {final_width}x{final_height}")
                print(f"  Format: {output_format}")
                print(f"  Aspect ratio: {target_ratio[0]}:{target_ratio[1]}")
                print(f"  File saved: {output_path}")
                
                return str(output_path)
                
        except Exception as e:
            print(f"✗ Error processing {input_path}: {str(e)}")
            return None
    
    def batch_process(self, input_dir, output_dir, formats=None, output_format='PNG', auto_detect=True):
        """
        Batch process multiple images
        
        Args:
            input_dir: Directory containing input images
            output_dir: Directory to save processed images
            formats: List of formats to generate or None for auto-detection
            output_format: 'PNG' or 'JPG'
            auto_detect: Whether to auto-detect best format for each image
        """
        if auto_detect:
            formats = ['auto']  # Use auto-detection for each image
        elif formats is None:
            formats = ['landscape', 'square', 'portrait']
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Supported image extensions
        supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        
        # Find all image files
        input_path = Path(input_dir)
        image_files = []
        
        for ext in supported_extensions:
            image_files.extend(input_path.glob(f"*{ext}"))
            image_files.extend(input_path.glob(f"*{ext.upper()}"))
        
        if not image_files:
            print(f"No supported image files found in {input_dir}")
            return
        
        print(f"Found {len(image_files)} image(s) to process")
        if auto_detect:
            print("Mode: Auto-detect best aspect ratio for each image")
        else:
            print(f"Output formats: {', '.join(formats)}")
        print(f"File format: {output_format}")
        print("-" * 50)
        
        processed_count = 0
        format_summary = {'landscape': 0, 'square': 0, 'portrait': 0}
        
        for img_file in image_files:
            print(f"\nProcessing: {img_file.name}")
            
            for format_type in formats:
                result = self.process_image(
                    str(img_file), 
                    output_dir, 
                    format_type, 
                    output_format
                )
                if result:
                    processed_count += 1
                    # Track which format was used (for auto-detection)
                    if format_type == 'auto':
                        # Detect the format that was actually used
                        with Image.open(img_file) as temp_img:
                            detected_format = self.detect_best_aspect_ratio(temp_img.width, temp_img.height)
                            format_summary[detected_format] += 1
                    else:
                        format_summary[format_type] += 1
        
        print(f"\n{'='*50}")
        print(f"Batch processing complete!")
        print(f"Successfully processed: {processed_count} images")
        if auto_detect:
            print(f"Format distribution:")
            for fmt, count in format_summary.items():
                if count > 0:
                    print(f"  {fmt.capitalize()}: {count} images")
        print(f"Output directory: {output_dir}")

def main():
    parser = argparse.ArgumentParser(
        description="Advanced Social Media Image Optimizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect best format for each image (recommended)
  python optimizer.py -i photo.jpg -o output/
  
  # Auto-detect for all images in a folder
  python optimizer.py -i input_folder/ -o output_folder/
  
  # Force specific format (manual mode)  
  python optimizer.py -i photo.jpg -o output/ -f square --manual
  
  # Generate multiple formats manually
  python optimizer.py -i photo.jpg -o output/ -f landscape square portrait --manual
  
  # Auto-detect with JPG output format
  python optimizer.py -i photo.jpg -o output/ --format JPG
        """
    )
    
    parser.add_argument('-i', '--input', required=True,
                       help='Input image file or directory')
    parser.add_argument('-o', '--output', required=True,
                       help='Output directory')
    parser.add_argument('-f', '--formats', nargs='+',
                       choices=['auto', 'landscape', 'square', 'portrait'],
                       default=['auto'],
                       help='Target format(s). Use "auto" for intelligent detection (default: auto)')
    parser.add_argument('--manual', action='store_true',
                       help='Disable auto-detection and use specified formats')
    parser.add_argument('--format', choices=['PNG', 'JPG'],
                       default='PNG',
                       help='Output file format (default: PNG)')
    parser.add_argument('--no-enhance', action='store_true',
                       help='Skip quality enhancement')
    
    args = parser.parse_args()
    
    # Initialize optimizer
    optimizer = SocialMediaImageOptimizer()
    
    # Check if input is file or directory
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Error: Input path '{args.input}' does not exist")
        sys.exit(1)
    
    # Create output directory
    Path(args.output).mkdir(parents=True, exist_ok=True)
    
    if input_path.is_file():
        # Process single file
        print("Processing single image...")
        print("-" * 30)
        
        # Use auto-detection unless manual mode is specified
        formats_to_use = args.formats if args.manual else ['auto']
        
        for format_type in formats_to_use:
            result = optimizer.process_image(
                str(input_path),
                args.output,
                format_type,
                args.format,
                not args.no_enhance
            )
            if result:
                print()
    
    elif input_path.is_dir():
        # Batch process directory
        print("Starting batch processing...")
        optimizer.batch_process(
            str(input_path),
            args.output,
            args.formats if args.manual else None,
            args.format,
            not args.manual  # auto_detect=True unless manual mode
        )
    
    else:
        print(f"Error: '{args.input}' is neither a file nor a directory")
        sys.exit(1)

if __name__ == "__main__":
    main()


    