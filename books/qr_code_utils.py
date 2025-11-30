"""
QR Code processing utilities using Pillow.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from io import BytesIO
import qrcode
import os


def create_enhanced_qr_code(data, size=(500, 500), error_correction='H', 
                            fill_color='black', back_color='white', 
                            add_border=True, border_color='white', border_size=20):
    """
    Create an enhanced QR code with Pillow processing.
    
    Args:
        data: Data to encode in QR code
        size: Tuple (width, height) for final image size
        error_correction: Error correction level ('L', 'M', 'Q', 'H')
        fill_color: QR code foreground color
        back_color: QR code background color
        add_border: Whether to add a border around QR code
        border_color: Border color
        border_size: Border size in pixels
    
    Returns:
        PIL Image object
    """
    # Map error correction string to constant
    error_map = {
        'L': qrcode.constants.ERROR_CORRECT_L,
        'M': qrcode.constants.ERROR_CORRECT_M,
        'Q': qrcode.constants.ERROR_CORRECT_Q,
        'H': qrcode.constants.ERROR_CORRECT_H,
    }
    error_level = error_map.get(error_correction.upper(), qrcode.constants.ERROR_CORRECT_H)
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=error_level,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Generate QR code image
    qr_img = qr.make_image(fill_color=fill_color, back_color=back_color)
    
    # Convert to RGB for better processing
    if qr_img.mode != 'RGB':
        qr_img = qr_img.convert('RGB')
    
    # Add border if requested
    if add_border:
        bordered_img = Image.new('RGB', 
                                (qr_img.size[0] + border_size * 2, 
                                 qr_img.size[1] + border_size * 2),
                                border_color)
        bordered_img.paste(qr_img, (border_size, border_size))
        qr_img = bordered_img
    
    # Resize to desired size
    if qr_img.size != size:
        qr_img = qr_img.resize(size, Image.Resampling.LANCZOS)
    
    return qr_img


def add_logo_to_qr_code(qr_image, logo_path, logo_size_ratio=0.2):
    """
    Add a logo to the center of a QR code image.
    
    Args:
        qr_image: PIL Image object of QR code
        logo_path: Path to logo image file
        logo_size_ratio: Logo size as ratio of QR code size (0.0-1.0)
    
    Returns:
        PIL Image object with logo
    """
    if not os.path.exists(logo_path):
        return qr_image
    
    try:
        logo = Image.open(logo_path)
        
        # Calculate logo size
        logo_size = (
            int(qr_image.size[0] * logo_size_ratio),
            int(qr_image.size[1] * logo_size_ratio)
        )
        
        # Resize logo
        logo = logo.resize(logo_size, Image.Resampling.LANCZOS)
        
        # Create white background for logo
        logo_bg = Image.new('RGB', logo_size, 'white')
        
        # Handle transparency
        if logo.mode == 'RGBA':
            logo_bg.paste(logo, (0, 0), logo)
        else:
            logo_bg.paste(logo, (0, 0))
        
        # Calculate center position
        logo_pos = (
            (qr_image.size[0] - logo_size[0]) // 2,
            (qr_image.size[1] - logo_size[1]) // 2
        )
        
        # Paste logo onto QR code
        qr_image.paste(logo_bg, logo_pos)
        
        return qr_image
        
    except Exception as e:
        # Return original image if logo processing fails
        return qr_image


def optimize_qr_code_image(image, format='PNG', quality=95, optimize=True):
    """
    Optimize QR code image for file size and quality.
    
    Args:
        image: PIL Image object
        format: Output format ('PNG', 'JPEG', 'WEBP')
        quality: Image quality 1-100 (for JPEG/WEBP)
        optimize: Whether to optimize the image
    
    Returns:
        BytesIO buffer with optimized image
    """
    buffer = BytesIO()
    
    # Convert to RGB if saving as JPEG
    if format.upper() == 'JPEG' and image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Save with optimization
    if format.upper() == 'PNG':
        image.save(buffer, format='PNG', optimize=optimize, compress_level=9)
    elif format.upper() == 'JPEG':
        image.save(buffer, format='JPEG', quality=quality, optimize=optimize)
    elif format.upper() == 'WEBP':
        image.save(buffer, format='WEBP', quality=quality, method=6)
    else:
        image.save(buffer, format='PNG', optimize=optimize)
    
    buffer.seek(0)
    return buffer


def resize_qr_code_image(image, size, maintain_aspect=True):
    """
    Resize QR code image with high-quality resampling.
    
    Args:
        image: PIL Image object
        size: Tuple (width, height) or single dimension (maintains aspect)
        maintain_aspect: Whether to maintain aspect ratio
    
    Returns:
        Resized PIL Image object
    """
    if isinstance(size, int):
        # Single dimension - maintain aspect ratio
        aspect_ratio = image.size[0] / image.size[1]
        if image.size[0] > image.size[1]:
            size = (size, int(size / aspect_ratio))
        else:
            size = (int(size * aspect_ratio), size)
    elif maintain_aspect:
        # Calculate size maintaining aspect ratio
        original_ratio = image.size[0] / image.size[1]
        target_ratio = size[0] / size[1]
        
        if original_ratio > target_ratio:
            # Fit to width
            new_height = int(size[0] / original_ratio)
            size = (size[0], new_height)
        else:
            # Fit to height
            new_width = int(size[1] * original_ratio)
            size = (new_width, size[1])
    
    return image.resize(size, Image.Resampling.LANCZOS)


def apply_filters_to_qr_code(image, filters=None):
    """
    Apply image filters to QR code.
    
    Args:
        image: PIL Image object
        filters: List of filter names to apply ('sharpen', 'smooth', 'edge_enhance')
    
    Returns:
        PIL Image object with filters applied
    """
    if filters is None:
        filters = []
    
    filtered_image = image.copy()
    
    for filter_name in filters:
        if filter_name == 'sharpen':
            filtered_image = filtered_image.filter(ImageFilter.SHARPEN)
        elif filter_name == 'smooth':
            filtered_image = filtered_image.filter(ImageFilter.SMOOTH)
        elif filter_name == 'edge_enhance':
            filtered_image = filtered_image.filter(ImageFilter.EDGE_ENHANCE)
        elif filter_name == 'emboss':
            filtered_image = filtered_image.filter(ImageFilter.EMBOSS)
    
    return filtered_image


def adjust_qr_code_brightness_contrast(image, brightness=1.0, contrast=1.0):
    """
    Adjust brightness and contrast of QR code image.
    
    Args:
        image: PIL Image object
        brightness: Brightness factor (1.0 = no change, >1.0 = brighter)
        contrast: Contrast factor (1.0 = no change, >1.0 = more contrast)
    
    Returns:
        PIL Image object with adjustments
    """
    # Adjust brightness
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(brightness)
    
    # Adjust contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(contrast)
    
    return image


def get_image_info(image_path):
    """
    Get detailed information about an image file.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Dictionary with image information
    """
    if not os.path.exists(image_path):
        return None
    
    try:
        img = Image.open(image_path)
        file_size = os.path.getsize(image_path)
        
        return {
            'format': img.format,
            'mode': img.mode,
            'size': img.size,
            'width': img.size[0],
            'height': img.size[1],
            'file_size_bytes': file_size,
            'file_size_kb': round(file_size / 1024, 2),
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'has_transparency': img.mode in ('RGBA', 'LA', 'P'),
            'color_count': len(img.getcolors(maxcolors=256*256*256)) if img.mode == 'P' else None
        }
    except Exception as e:
        return {'error': str(e)}

