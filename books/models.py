from django.db import models
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image, ImageDraw, ImageFont
import os


class Book(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=20, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    publication_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.author}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Automatically create QR code when book is saved
        if not hasattr(self, 'qrcode'):
            QRCode.objects.create(book=self)


class QRCode(models.Model):
    id = models.BigAutoField(primary_key=True)
    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name='qrcode')
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"QR Code for {self.book.title}"

    def generate_qr_code(self, size=(500, 500), quality=95, add_logo=False, logo_path=None):
        """
        Generate QR code with enhanced Pillow processing.
        
        Args:
            size: Tuple (width, height) for final image size (default: 500x500)
            quality: Image quality 1-100 (default: 95)
            add_logo: Whether to add a logo in the center (default: False)
            logo_path: Path to logo image file (optional)
        """
        # Generate QR code data
        qr_data = f"book:{self.book.id}"
        
        # Create QR code with better error correction
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Generate base QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to RGB if needed (for logo overlay)
        if add_logo or qr_img.mode != 'RGB':
            qr_img = qr_img.convert('RGB')
        
        # Add logo in center if requested
        if add_logo and logo_path and os.path.exists(logo_path):
            try:
                logo = Image.open(logo_path)
                # Resize logo to 20% of QR code size
                logo_size = (qr_img.size[0] // 5, qr_img.size[1] // 5)
                logo = logo.resize(logo_size, Image.Resampling.LANCZOS)
                
                # Create a white background for logo
                logo_bg = Image.new('RGB', logo_size, 'white')
                if logo.mode == 'RGBA':
                    logo_bg.paste(logo, (0, 0), logo)
                else:
                    logo_bg.paste(logo, (0, 0))
                
                # Calculate position to center logo
                logo_pos = (
                    (qr_img.size[0] - logo_size[0]) // 2,
                    (qr_img.size[1] - logo_size[1]) // 2
                )
                
                # Paste logo onto QR code
                qr_img.paste(logo_bg, logo_pos)
            except Exception as e:
                # If logo processing fails, continue without logo
                pass
        
        # Resize image to desired size using high-quality resampling
        if qr_img.size != size:
            qr_img = qr_img.resize(size, Image.Resampling.LANCZOS)
        
        # Optimize image quality
        buffer = BytesIO()
        
        # Save as PNG with optimization
        qr_img.save(
            buffer, 
            format='PNG',
            optimize=True,
            compress_level=9
        )
        buffer.seek(0)

        filename = f'qrcode_{self.book.id}.png'
        self.qr_code.save(filename, File(buffer), save=False)

    def process_qr_code_image(self, resize=None, format='PNG', quality=95):
        """
        Process existing QR code image using Pillow.
        
        Args:
            resize: Tuple (width, height) or None to keep original size
            format: Output format ('PNG', 'JPEG', 'WEBP')
            quality: Image quality 1-100 (for JPEG/WEBP)
        
        Returns:
            BytesIO buffer with processed image
        """
        if not self.qr_code:
            return None
        
        try:
            # Open existing QR code image
            img = Image.open(self.qr_code.path)
            
            # Convert to RGB if saving as JPEG
            if format.upper() == 'JPEG' and img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if requested
            if resize:
                img = img.resize(resize, Image.Resampling.LANCZOS)
            
            # Process image
            buffer = BytesIO()
            
            if format.upper() == 'PNG':
                img.save(buffer, format='PNG', optimize=True, compress_level=9)
            elif format.upper() == 'JPEG':
                img.save(buffer, format='JPEG', quality=quality, optimize=True)
            elif format.upper() == 'WEBP':
                img.save(buffer, format='WEBP', quality=quality, method=6)
            else:
                img.save(buffer, format='PNG', optimize=True)
            
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            return None

    def get_qr_code_info(self):
        """
        Get information about the QR code image using Pillow.
        
        Returns:
            Dictionary with image information
        """
        if not self.qr_code:
            return None
        
        try:
            img = Image.open(self.qr_code.path)
            file_size = os.path.getsize(self.qr_code.path)
            
            return {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.size[0],
                'height': img.size[1],
                'file_size_bytes': file_size,
                'file_size_kb': round(file_size / 1024, 2),
                'has_transparency': img.mode in ('RGBA', 'LA', 'P')
            }
        except Exception as e:
            return None

    def validate_qr_code(self):
        """
        Validate that the QR code can be read and contains correct data.
        
        Returns:
            Dictionary with validation results
        """
        if not self.qr_code:
            return {
                'valid': False,
                'error': 'QR code image not found'
            }
        
        try:
            from pyzbar import pyzbar
            import numpy as np
            
            img = Image.open(self.qr_code.path)
            
            # Convert to grayscale for better decoding
            if img.mode != 'L':
                img = img.convert('L')
            
            # Try to decode QR code
            decoded_objects = pyzbar.decode(img)
            
            if not decoded_objects:
                return {
                    'valid': False,
                    'error': 'Could not decode QR code'
                }
            
            # Check if decoded data matches expected format
            decoded_data = decoded_objects[0].data.decode('utf-8')
            expected_data = f"book:{self.book.id}"
            
            return {
                'valid': decoded_data == expected_data,
                'decoded_data': decoded_data,
                'expected_data': expected_data,
                'matches': decoded_data == expected_data
            }
            
        except ImportError:
            # pyzbar not installed, skip validation
            return {
                'valid': None,
                'error': 'QR code validation library (pyzbar) not installed'
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }

    def save(self, *args, **kwargs):
        if not self.qr_code:
            self.generate_qr_code()
        super().save(*args, **kwargs)
