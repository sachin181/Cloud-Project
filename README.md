# Movie Review Backend API

A FastAPI backend for movie reviews with Firebase Authentication and Firestore database.

## Features

- **Firebase Authentication**: Secure user authentication using Firebase Auth
- **Firestore Database**: NoSQL database for storing reviews and user data
- **Movie Catalog**: Integration with Studio Ghibli API for movie data
- **Sentiment Analysis**: AI-powered sentiment analysis for reviews (OpenAI or mock)
- **RESTful API**: Full CRUD operations for reviews

## Setup

### Prerequisites

- Python 3.8+
- Firebase project with:
  - Authentication enabled
  - Firestore database enabled
  - Service account key

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Firebase credentials:

   **Option 1: Service Account File**
   - Download your Firebase service account JSON file from Firebase Console
   - Set the path in your `.env` file:
   ```
   FIREBASE_CREDENTIALS_PATH=/path/to/serviceAccountKey.json
   ```

   **Option 2: JSON String (for deployment)**
   - Set the credentials as a JSON string in your `.env` file:
   ```
   FIREBASE_CREDENTIALS_JSON='{"type":"service_account",...}'
   ```

   **Option 3: Application Default Credentials (local development)**
   - If using `gcloud` CLI, you can use application default credentials
   - No environment variables needed

3. Configure other environment variables (optional):
```env
ENV=dev
GHIBLI_FILMS_URL=https://ghibliapi.vercel.app/films
SENTIMENT_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
```

### Running the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## API Endpoints

### Authentication

- `GET /auth/me` - Get current user info (requires Firebase ID token)

**Note**: User registration and login are handled by Firebase Auth on the client side. The backend verifies Firebase ID tokens sent in the `Authorization: Bearer <token>` header.

### Movies

- `GET /movies` - List movies with filtering and pagination
- `GET /movies/{movie_id}` - Get movie details
- `GET /movies/{movie_id}/sentiment` - Get overall sentiment for a movie

### Reviews

- `POST /reviews` - Create a review (requires authentication)
- `GET /reviews` - List reviews (optional `movie_id` query parameter)
- `GET /reviews/{review_id}` - Get a specific review
- `PATCH /reviews/{review_id}` - Update a review (requires authentication, owner only)
- `DELETE /reviews/{review_id}` - Delete a review (requires authentication, owner only)

### Health

- `GET /healthz` - Health check endpoint

## Authentication

This API uses Firebase Authentication. Clients must:

1. Use Firebase Auth SDK to register/login users
2. Obtain Firebase ID tokens from the client
3. Send tokens in the `Authorization: Bearer <token>` header for protected endpoints

Example client code (JavaScript):
```javascript
import { getAuth, signInWithEmailAndPassword } from 'firebase/auth';

const auth = getAuth();
const userCredential = await signInWithEmailAndPassword(auth, email, password);
const token = await userCredential.user.getIdToken();

// Use token in API requests
fetch('/api/reviews', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

## Database Structure

### Firestore Collections

**users**
- Document ID: Firebase user UID
- Fields: `uid`, `email`, `created_at`

**reviews**
- Document ID: Auto-generated
- Fields: `movie_id`, `user_id`, `rating`, `body`, `sentiment_label`, `sentiment_score`, `created_at`, `updated_at`

## Migration from SQLite

This codebase has been migrated from SQLite/SQLModel to Firebase/Firestore. Key changes:

- Removed SQLModel dependencies
- Replaced SQL database with Firestore
- Replaced JWT authentication with Firebase Auth
- Updated all models to Pydantic (removed SQLModel table definitions)
- Updated all database operations to use Firestore queries

