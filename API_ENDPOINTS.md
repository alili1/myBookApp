# API Endpoints Documentation

This document lists all available endpoints in the Book API application.

**Base URL:** `http://localhost:8000` (or your server URL)

---

## Table of Contents

1. [Book Management Endpoints](#book-management-endpoints)
2. [QR Code Endpoints](#qr-code-endpoints)
3. [Google Books API Integration Endpoints](#google-books-api-integration-endpoints)
4. [Admin Interface](#admin-interface)

---

## Book Management Endpoints

All book management endpoints are under `/api/books/`

### 1. List All Books
**GET** `/api/books/`

Retrieve a paginated list of all books in the database.

**Query Parameters:**
- `page` (optional): Page number for pagination (default: 1)
- `page_size` (optional): Number of items per page (default: 10)

**Response:** `200 OK`
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/books/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Book Title",
      "author": "Author Name",
      "isbn": "1234567890",
      "description": "Book description",
      "publication_date": "2023-01-01",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "qrcode": {
        "id": 1,
        "qr_code": "/media/qrcodes/qrcode_1.png",
        "qr_code_url": "http://localhost:8000/media/qrcodes/qrcode_1.png",
        "created_at": "2024-01-01T00:00:00Z"
      }
    }
  ]
}
```

---

### 2. Create a New Book
**POST** `/api/books/`

Create a new book in the database. A QR code is automatically generated.

**Request Body:**
```json
{
  "title": "Book Title",
  "author": "Author Name",
  "isbn": "1234567890",
  "description": "Book description (optional)",
  "publication_date": "2023-01-01"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "title": "Book Title",
  "author": "Author Name",
  "isbn": "1234567890",
  "description": "Book description",
  "publication_date": "2023-01-01",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "qrcode": {
    "id": 1,
    "qr_code": "/media/qrcodes/qrcode_1.png",
    "qr_code_url": "http://localhost:8000/media/qrcodes/qrcode_1.png",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

### 3. Retrieve a Specific Book
**GET** `/api/books/{id}/`

Get detailed information about a specific book by its ID.

**Path Parameters:**
- `id`: Book ID (integer)

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "Book Title",
  "author": "Author Name",
  "isbn": "1234567890",
  "description": "Book description",
  "publication_date": "2023-01-01",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "qrcode": {
    "id": 1,
    "qr_code": "/media/qrcodes/qrcode_1.png",
    "qr_code_url": "http://localhost:8000/media/qrcodes/qrcode_1.png",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Response:** `404 Not Found`
```json
{
  "detail": "Not found."
}
```

---

### 4. Update a Book (Full Update)
**PUT** `/api/books/{id}/`

Update all fields of a book.

**Path Parameters:**
- `id`: Book ID (integer)

**Request Body:**
```json
{
  "title": "Updated Book Title",
  "author": "Updated Author Name",
  "isbn": "0987654321",
  "description": "Updated description",
  "publication_date": "2024-01-01"
}
```

**Response:** `200 OK` (returns updated book object)

---

### 5. Partial Update a Book
**PATCH** `/api/books/{id}/`

Update specific fields of a book without requiring all fields.

**Path Parameters:**
- `id`: Book ID (integer)

**Request Body:**
```json
{
  "title": "Updated Title Only"
}
```

**Response:** `200 OK` (returns updated book object)

---

### 6. Delete a Book
**DELETE** `/api/books/{id}/`

Delete a book from the database. The associated QR code is also deleted.

**Path Parameters:**
- `id`: Book ID (integer)

**Response:** `204 No Content`

**Error Response:** `404 Not Found`
```json
{
  "detail": "Not found."
}
```

---

## QR Code Endpoints

### 7. Get QR Code for a Book
**GET** `/api/books/{id}/qrcode/`

Retrieve the QR code information for a specific book. If no QR code exists, one will be created automatically.

**Path Parameters:**
- `id`: Book ID (integer)

**Response:** `200 OK`
```json
{
  "id": 1,
  "qr_code": "/media/qrcodes/qrcode_1.png",
  "qr_code_url": "http://localhost:8000/media/qrcodes/qrcode_1.png",
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### 8. Scan QR Code
**POST** `/api/books/scan_qrcode/`

Scan a QR code and retrieve the associated book information.

**Request Body:**
```json
{
  "qr_data": "book:1"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "Book Title",
  "author": "Author Name",
  "isbn": "1234567890",
  "description": "Book description",
  "publication_date": "2023-01-01",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "qrcode": {
    "id": 1,
    "qr_code": "/media/qrcodes/qrcode_1.png",
    "qr_code_url": "http://localhost:8000/media/qrcodes/qrcode_1.png",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid QR code format
- `404 Not Found` - Book not found

---

## Google Books API Integration Endpoints

### 9. Search Google Books (GET)
**GET** `/api/books/search_google_books/`

Search for books using the Google Books API by title or author.

**Query Parameters:**
- `query` (required): Search query (title or author)
- `max_results` (optional): Maximum number of results (default: 10, max: 40)

**Example:**
```
GET /api/books/search_google_books/?query=python programming&max_results=5
```

**Response:** `200 OK`
```json
{
  "query": "python programming",
  "total_results": 1000,
  "count": 5,
  "books": [
    {
      "title": "Python Programming",
      "authors": ["John Doe"],
      "publishedDate": "2023-01-01",
      "publisher": "Publisher Name",
      "description": "Book description...",
      "pageCount": 300,
      "categories": ["Programming"],
      "averageRating": 4.5,
      "ratingsCount": 100,
      "language": "en",
      "previewLink": "https://books.google.com/...",
      "infoLink": "https://books.google.com/...",
      "thumbnail": "http://books.google.com/...",
      "isbn10": "1234567890",
      "isbn13": "9781234567890",
      "googleBooksId": "volume_id"
    }
  ]
}
```

**Error Response:** `400 Bad Request`
```json
{
  "error": "Query parameter is required"
}
```

---

### 10. Search Google Books (POST)
**POST** `/api/books/search_google_books/`

Search for books using the Google Books API (POST method).

**Request Body:**
```json
{
  "query": "python programming",
  "max_results": 10
}
```

**Response:** Same as GET method above.

---

### 11. Get Google Book Details
**GET** `/api/books/google_book_detail/`

Get detailed information about a specific book from Google Books API by its Google Books ID.

**Query Parameters:**
- `book_id` (required): Google Books volume ID

**Example:**
```
GET /api/books/google_book_detail/?book_id=volume_id_here
```

**Response:** `200 OK`
```json
{
  "title": "Book Title",
  "authors": ["Author Name"],
  "publishedDate": "2023-01-01",
  "publisher": "Publisher Name",
  "description": "Book description...",
  "pageCount": 300,
  "categories": ["Category"],
  "averageRating": 4.5,
  "ratingsCount": 100,
  "language": "en",
  "previewLink": "https://books.google.com/...",
  "infoLink": "https://books.google.com/...",
  "thumbnail": "http://books.google.com/...",
  "isbn10": "1234567890",
  "isbn13": "9781234567890",
  "googleBooksId": "volume_id"
}
```

**Error Responses:**
- `400 Bad Request` - Missing book_id parameter
- `404 Not Found` - Book not found
- `500 Internal Server Error` - API error

---

### 12. Import Book from Google Books
**POST** `/api/books/import_from_google_books/`

Import a book from Google Books API into the local database. The book will be created or updated if it already exists (matched by ISBN or title+author).

**Request Body (Option 1 - By Google Books ID):**
```json
{
  "google_books_id": "volume_id_here"
}
```

**Request Body (Option 2 - By Search Query):**
```json
{
  "query": "python programming",
  "index": 0
}
```

**Parameters:**
- `google_books_id`: Google Books volume ID (use this OR query)
- `query`: Search query (use this OR google_books_id)
- `index`: Index of the search result to import (default: 0, only used with query)

**Response:** `201 Created` (new book) or `200 OK` (updated book)
```json
{
  "id": 1,
  "title": "Book Title",
  "author": "Author Name",
  "isbn": "9781234567890",
  "description": "Book description",
  "publication_date": "2023-01-01",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "qrcode": {
    "id": 1,
    "qr_code": "/media/qrcodes/qrcode_1.png",
    "qr_code_url": "http://localhost:8000/media/qrcodes/qrcode_1.png",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Missing required parameters or invalid index
- `404 Not Found` - Book not found in Google Books
- `500 Internal Server Error` - API error

---

## Admin Interface

### 13. Django Admin
**GET** `/admin/`

Access the Django admin interface for managing books, QR codes, and other models.

**Note:** Requires admin user authentication.

---

## Configuration

### Google Books API Key

The Google Books API can work without an API key for basic searches, but using a key increases rate limits. You can configure the API key in two ways:

1. **Environment Variable:**
   ```bash
   export GOOGLE_BOOKS_API_KEY=your_api_key_here
   ```

2. **Django Settings** (`bookapi/settings.py`):
   ```python
   GOOGLE_BOOKS_API_KEY = "your_api_key_here"
   ```

---

## Response Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `204 No Content` - Resource deleted successfully
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Notes

- All endpoints return JSON responses
- Pagination is enabled for list endpoints (default: 10 items per page)
- QR codes are automatically generated when books are created
- The import endpoint will update existing books if they match by ISBN or title+author
- All dates are in ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)
- All ID fields are integers (BigAutoField) instead of UUIDs

