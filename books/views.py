from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from django.shortcuts import get_object_or_404
from django.http import Http404
from datetime import datetime

from .models import Book, QRCode
from .serializers import (
    BookSerializer, 
    BookCreateSerializer, 
    QRCodeSerializer,
    QRCodeScanSerializer,
    GoogleBooksSearchSerializer,
    GoogleBookSerializer
)
from .google_books_api import search_books, get_book_by_id


def save_google_book_to_database(book_data):
    """
    Helper function to save or update a book from Google Books API data.
    
    Args:
        book_data: Dictionary containing book data from Google Books API
    
    Returns:
        tuple: (book_instance, created_boolean)
    """
    # Parse publication date
    publication_date = None
    if book_data.get('publishedDate'):
        try:
            date_str = book_data['publishedDate']
            # Handle different date formats: YYYY, YYYY-MM, YYYY-MM-DD
            if len(date_str) == 4:
                publication_date = datetime.strptime(date_str, '%Y').date()
            elif len(date_str) == 7:
                publication_date = datetime.strptime(date_str, '%Y-%m').date()
            elif len(date_str) >= 10:
                publication_date = datetime.strptime(date_str[:10], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass  # Keep publication_date as None if parsing fails
    
    # Get author(s) as comma-separated string
    authors = book_data.get('authors', [])
    author_str = ', '.join(authors) if authors else 'Unknown Author'
    
    # Get ISBN (prefer ISBN-13, fallback to ISBN-10)
    isbn = book_data.get('isbn13') or book_data.get('isbn10') or None
    title = book_data.get('title', 'Untitled')
    
    # Try to find existing book by ISBN first, then by title+author
    book = None
    created = False
    
    if isbn:
        try:
            book = Book.objects.get(isbn=isbn)
        except Book.DoesNotExist:
            pass
    
    if not book:
        # Try to find by title and author
        try:
            book = Book.objects.get(title=title, author=author_str)
        except Book.DoesNotExist:
            pass
        except Book.MultipleObjectsReturned:
            # If multiple found, get the first one
            book = Book.objects.filter(title=title, author=author_str).first()
    
    if book:
        # Update existing book
        book.title = title
        book.author = author_str
        if book_data.get('description'):
            book.description = book_data.get('description', book.description)
        if publication_date:
            book.publication_date = publication_date
        if isbn and not book.isbn:
            book.isbn = isbn
        book.save()
    else:
        # Create new book
        book = Book.objects.create(
            title=title,
            author=author_str,
            isbn=isbn,
            description=book_data.get('description', ''),
            publication_date=publication_date,
        )
        created = True
    
    return book, created


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Book instances.
    Provides CRUD operations for books.
    """
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return BookCreateSerializer
        return BookSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book = serializer.save()
        # QR code is automatically created in Book.save() method
        response_serializer = BookSerializer(book, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def qrcode(self, request, pk=None):
        """
        Retrieve QR code for a specific book.
        GET /api/books/{id}/qrcode/
        """
        book = self.get_object()
        try:
            qrcode = book.qrcode
        except QRCode.DoesNotExist:
            qrcode = QRCode.objects.create(book=book)
        
        serializer = QRCodeSerializer(qrcode, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def scan_qrcode(self, request):
        """
        Scan QR code and retrieve book information.
        POST /api/books/scan_qrcode/
        Body: {"qr_data": "book:id"}
        """
        serializer = QRCodeScanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        qr_data = serializer.validated_data['qr_data']
        
        # Parse QR code data (format: "book:id")
        if not qr_data.startswith('book:'):
            return Response(
                {'error': 'Invalid QR code format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            book_id_str = qr_data.split(':', 1)[1]
            book_id = int(book_id_str)
            book = get_object_or_404(Book, id=book_id)
            book_serializer = BookSerializer(book, context={'request': request})
            return Response(book_serializer.data)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid book ID in QR code. ID must be a number.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Http404:
            return Response(
                {'error': 'Book not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get', 'post'])
    def search_google_books(self, request):
        """
        Search for books using Google Books API.
        GET /api/books/search_google_books/?query=python&max_results=10
        POST /api/books/search_google_books/
        Body: {"query": "python", "max_results": 10}
        """
        if request.method == 'GET':
            query = request.query_params.get('query', '')
            max_results = int(request.query_params.get('max_results', 10))
        else:
            serializer = GoogleBooksSearchSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            query = serializer.validated_data['query']
            max_results = serializer.validated_data.get('max_results', 10)
        
        if not query:
            return Response(
                {'error': 'Query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Search Google Books API
        result = search_books(query, max_results=max_results)
        
        if not result['success']:
            return Response(
                {'error': result.get('error', 'Failed to search Google Books')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Serialize the results
        books_serializer = GoogleBookSerializer(result['books'], many=True)
        
        return Response({
            'query': query,
            'total_results': result['total_results'],
            'count': len(result['books']),
            'books': books_serializer.data
        })

    @action(detail=False, methods=['get'])
    def google_book_detail(self, request):
        """
        Get a specific book from Google Books API by Google Books ID.
        Automatically saves the book to the local database.
        GET /api/books/google_book_detail/?book_id=VOLUME_ID
        """
        book_id = request.query_params.get('book_id', '')
        
        if not book_id:
            return Response(
                {'error': 'book_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get book from Google Books API
        result = get_book_by_id(book_id)
        
        if not result['success']:
            status_code = status.HTTP_404_NOT_FOUND if 'not found' in result.get('error', '').lower() else status.HTTP_500_INTERNAL_SERVER_ERROR
            return Response(
                {'error': result.get('error', 'Failed to get book from Google Books')},
                status=status_code
            )
        
        # Automatically save book to database
        book, created = save_google_book_to_database(result['book'])
        
        # Return both Google Books data and saved book data
        google_book_serializer = GoogleBookSerializer(result['book'])
        saved_book_serializer = BookSerializer(book, context={'request': request})
        
        return Response({
            'google_books_data': google_book_serializer.data,
            'saved_book': saved_book_serializer.data,
            'created': created,
            'message': 'Book saved to database' if created else 'Book updated in database'
        })

    @action(detail=False, methods=['post'])
    def import_from_google_books(self, request):
        """
        Import a book from Google Books API into the local database.
        POST /api/books/import_from_google_books/
        Body: {"google_books_id": "VOLUME_ID"} or {"query": "book title", "index": 0}
        """
        google_books_id = request.data.get('google_books_id')
        query = request.data.get('query')
        index = request.data.get('index', 0)
        
        # Get book data from Google Books API
        if google_books_id:
            result = get_book_by_id(google_books_id)
            if not result['success']:
                status_code = status.HTTP_404_NOT_FOUND if 'not found' in result.get('error', '').lower() else status.HTTP_500_INTERNAL_SERVER_ERROR
                return Response(
                    {'error': result.get('error', 'Failed to get book from Google Books')},
                    status=status_code
                )
            book_data = result['book']
        elif query:
            search_result = search_books(query, max_results=index + 1)
            if not search_result['success'] or not search_result['books']:
                return Response(
                    {'error': 'No books found for the given query'},
                    status=status.HTTP_404_NOT_FOUND
                )
            if index >= len(search_result['books']):
                return Response(
                    {'error': f'Index {index} is out of range. Found {len(search_result["books"])} books.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            book_data = search_result['books'][index]
        else:
            return Response(
                {'error': 'Either google_books_id or query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save book to database using helper function
        book, created = save_google_book_to_database(book_data)
        
        serializer = BookSerializer(book, context={'request': request})
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
