from django.db import models
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image


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

    def generate_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        # Generate URL that can be used to retrieve book info
        qr_data = f"book:{self.book.id}"
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        filename = f'qrcode_{self.book.id}.png'
        self.qr_code.save(filename, File(buffer), save=False)

    def save(self, *args, **kwargs):
        if not self.qr_code:
            self.generate_qr_code()
        super().save(*args, **kwargs)
