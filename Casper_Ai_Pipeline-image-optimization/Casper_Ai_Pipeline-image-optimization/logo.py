


import io
from PIL import Image

def add_logo_to_image(image_data, logo_data, logo_size_percent=12, output_path=None, position="bottom-right"):
    """
    Add logo to the image with specified size and position.
    
    Args:
        image_data: PIL.Image, bytes, or path to the main image
        logo_data: PIL.Image, bytes, or path to the logo image
        logo_size_percent (int): Size of logo as percentage of image's smallest dimension
        output_path (str, optional): Path where to save the output image (if None, doesn't save)
        position (str): Position of logo - "top-left", "top-right", "bottom-left", "bottom-right"
        
    Returns:
        PIL.Image: Final image with logo
    """
    try:
        # Load images
        if isinstance(image_data, str):
            image = Image.open(image_data)
        elif isinstance(image_data, bytes):
            image = Image.open(io.BytesIO(image_data))
        elif isinstance(image_data, Image.Image):
            image = image_data
        else:
            raise ValueError("Unsupported image format")
            
        if isinstance(logo_data, str):
            logo = Image.open(logo_data)
        elif isinstance(logo_data, bytes):
            logo = Image.open(io.BytesIO(logo_data))
        elif isinstance(logo_data, Image.Image):
            logo = logo_data
        else:
            raise ValueError("Unsupported logo format")
        
        # Store original mode to convert back later if needed
        original_mode = image.mode
        image = image.convert("RGBA")
        image_width, image_height = image.size
        
        # Convert logo to RGBA
        logo = logo.convert("RGBA")
        logo_width, logo_height = logo.size
        
        # Set default logo size to 12% if input is invalid
        if logo_size_percent is None or logo_size_percent <= 0 or logo_size_percent > 40:
            logo_size_percent = 12
        
        # Calculate the new logo size based on percentage while preserving aspect ratio
        base_size = min(image_width, image_height)
        new_width = int((logo_size_percent / 100) * base_size)
        # Maintain aspect ratio
        new_height = int(new_width * (logo_height / logo_width))
        
        # Resize the logo while preserving aspect ratio
        logo = logo.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create a transparent layer for pasting
        transparent_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        
        # Define padding
        padding = 10
        
        # Calculate position to place the logo based on selected corner
        if position == "top-left":
            logo_x = padding
            logo_y = padding
        elif position == "top-right":
            logo_x = image_width - new_width - padding
            logo_y = padding
        elif position == "bottom-left":
            logo_x = padding
            logo_y = image_height - new_height - padding
        else:  # Default: bottom-right
            logo_x = image_width - new_width - padding
            logo_y = image_height - new_height - padding
        
        # Paste the logo onto the transparent layer
        transparent_layer.paste(logo, (logo_x, logo_y), logo)
        
        # Merge the transparent layer with the image
        final_image = Image.alpha_composite(image, transparent_layer)
        
        # Convert back to original mode if it doesn't support alpha
        if output_path and (output_path.lower().endswith(('.jpg', '.jpeg')) or original_mode == 'RGB'):
            final_image = final_image.convert('RGB')
        
        # Save the modified image if output path is provided
        if output_path:
            # Detect image format from file extension
            output_format = output_path.split('.')[-1].upper()
            if not output_format or output_format.lower() not in ('png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'):
                output_format = "PNG"  # Default to PNG if no extension or unsupported
                
            final_image.save(output_path, format=output_format)
            print(f"Image with logo saved successfully as {output_path}")
        
        return final_image
    except Exception as e:
        error_msg = f"Error adding logo: {e}"
        print(error_msg)
        
        # Return original image if we can
        if isinstance(image_data, Image.Image):
            return image_data
        elif isinstance(image_data, str):
            return Image.open(image_data)
        elif isinstance(image_data, bytes):
            return Image.open(io.BytesIO(image_data))
        else:
            return None
        

        