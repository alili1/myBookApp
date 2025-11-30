"""
Google Books API utility functions for Django integration.
"""

import requests
import os
from typing import Optional, Dict, List
from django.conf import settings


def search_books(query: str, api_key: Optional[str] = None, max_results: int = 10) -> Dict:
    """
    Search for books using the Google Books API.
    
    Args:
        query: Search query (title or author)
        api_key: Optional Google Books API key (if not provided, uses settings or env var)
        max_results: Maximum number of results to return (default: 10)
    
    Returns:
        Dictionary with 'success' flag, 'books' list, and optional 'error' message
    """
    base_url = "https://www.googleapis.com/books/v1/volumes"
    
    # Get API key from parameter, settings, or environment variable
    if not api_key:
        api_key = getattr(settings, 'GOOGLE_BOOKS_API_KEY', None)
    if not api_key:
        api_key = os.getenv('GOOGLE_BOOKS_API_KEY')
    
    params = {
        'q': query,
        'maxResults': max_results
    }
    
    # Add API key if available
    if api_key:
        params['key'] = api_key
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        books = []
        if 'items' in data:
            for item in data['items']:
                volume_info = item.get('volumeInfo', {})
                
                # Extract ISBNs
                industry_identifiers = volume_info.get('industryIdentifiers', [])
                isbn_10 = None
                isbn_13 = None
                for identifier in industry_identifiers:
                    if identifier.get('type') == 'ISBN_10':
                        isbn_10 = identifier.get('identifier')
                    elif identifier.get('type') == 'ISBN_13':
                        isbn_13 = identifier.get('identifier')
                
                book = {
                    'title': volume_info.get('title', 'N/A'),
                    'authors': volume_info.get('authors', []),
                    'publishedDate': volume_info.get('publishedDate', None),
                    'publisher': volume_info.get('publisher', None),
                    'description': volume_info.get('description', None),
                    'pageCount': volume_info.get('pageCount', None),
                    'categories': volume_info.get('categories', []),
                    'averageRating': volume_info.get('averageRating', None),
                    'ratingsCount': volume_info.get('ratingsCount', None),
                    'language': volume_info.get('language', None),
                    'previewLink': volume_info.get('previewLink', None),
                    'infoLink': volume_info.get('infoLink', None),
                    'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail', None) if volume_info.get('imageLinks') else None,
                    'isbn10': isbn_10,
                    'isbn13': isbn_13,
                    'googleBooksId': item.get('id', None),
                }
                books.append(book)
        
        return {
            'success': True,
            'books': books,
            'total_results': data.get('totalItems', 0)
        }
    
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'books': [],
            'error': 'Request to Google Books API timed out'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'books': [],
            'error': f'Error connecting to Google Books API: {str(e)}'
        }
    except ValueError as e:
        return {
            'success': False,
            'books': [],
            'error': f'Error parsing API response: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'books': [],
            'error': f'Unexpected error: {str(e)}'
        }


def get_book_by_id(book_id: str, api_key: Optional[str] = None) -> Dict:
    """
    Get a specific book by Google Books ID.
    
    Args:
        book_id: Google Books volume ID
        api_key: Optional Google Books API key
    
    Returns:
        Dictionary with 'success' flag, 'book' data, and optional 'error' message
    """
    base_url = f"https://www.googleapis.com/books/v1/volumes/{book_id}"
    
    # Get API key from parameter, settings, or environment variable
    if not api_key:
        api_key = getattr(settings, 'GOOGLE_BOOKS_API_KEY', None)
    if not api_key:
        api_key = os.getenv('GOOGLE_BOOKS_API_KEY')
    
    params = {}
    if api_key:
        params['key'] = api_key
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        volume_info = data.get('volumeInfo', {})
        
        # Extract ISBNs
        industry_identifiers = volume_info.get('industryIdentifiers', [])
        isbn_10 = None
        isbn_13 = None
        for identifier in industry_identifiers:
            if identifier.get('type') == 'ISBN_10':
                isbn_10 = identifier.get('identifier')
            elif identifier.get('type') == 'ISBN_13':
                isbn_13 = identifier.get('identifier')
        
        book = {
            'title': volume_info.get('title', 'N/A'),
            'authors': volume_info.get('authors', []),
            'publishedDate': volume_info.get('publishedDate', None),
            'publisher': volume_info.get('publisher', None),
            'description': volume_info.get('description', None),
            'pageCount': volume_info.get('pageCount', None),
            'categories': volume_info.get('categories', []),
            'averageRating': volume_info.get('averageRating', None),
            'ratingsCount': volume_info.get('ratingsCount', None),
            'language': volume_info.get('language', None),
            'previewLink': volume_info.get('previewLink', None),
            'infoLink': volume_info.get('infoLink', None),
            'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail', None) if volume_info.get('imageLinks') else None,
            'isbn10': isbn_10,
            'isbn13': isbn_13,
            'googleBooksId': data.get('id', None),
        }
        
        return {
            'success': True,
            'book': book
        }
    
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'book': None,
            'error': 'Request to Google Books API timed out'
        }
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, 'status_code') and e.response.status_code == 404:
            return {
                'success': False,
                'book': None,
                'error': 'Book not found'
            }
        return {
            'success': False,
            'book': None,
            'error': f'Error connecting to Google Books API: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'book': None,
            'error': f'Unexpected error: {str(e)}'
        }

