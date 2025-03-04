# Cocktail Advisor - AI-Powered Cocktail Assistant 🍸

An intelligent cocktail recommendation system that helps users discover and create perfect drink combinations using advanced AI technology and natural language processing.

## Project Structure 📁

```
cocktail-advisor/
├── app/
│   ├── api/                # API endpoints and dependencies
│   ├── database/          # Database and vector store operations
│   ├── models/            # Data models and schemas
│   ├── services/          # Business logic and AI services
│   └── utils/             # Helper functions and utilities
├── static/                # Static assets (CSS, JS, images)
├── templates/             # HTML templates
├── tests/                # Unit and integration tests
├── data/                 # Dataset and processed data
├── docs/                 # Documentation
└── scripts/              # Data processing scripts
```

## Features 🌟

- 🤖 Advanced AI-powered cocktail recommendations
- 🔍 Natural language processing for user queries
- 📊 Vector-based similarity search
- 🗃️ Extensive cocktail database
- 💬 Interactive chat interface
- 🎯 Personalized suggestions

## Installation 🚀

### Prerequisites

```bash
- Python 3.9+
- Anaconda/Miniconda
- Docker (optional)
```

### Environment Setup

```bash
# Create and activate Conda environment
conda create -n name python=3.12
conda activate name

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create `.env` file:
```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxx

ENVIRONMENT=development
DEBUG=1
CURRENT_TIME=2025-03-04 21:59:38
CURRENT_USER=ramalMr

DATABASE_URL=sqlite:///./cocktails.db
USE_REDIS=false 

APP_NAME=Cocktail Advisor
APP_VERSION=1.0.0
DEFAULT_LANGUAGE=en

CACHE_TYPE=sqlite
CACHE_DATABASE=cache.db

LOG_LEVEL=DEBUG
LOG_FORMAT=detailed

JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Database Setup

```bash
# Initialize database and vector store
python scripts/preprocess_data.py
python scripts/generate_embeddings.py
```

## Running the Application 🚀

### Development Mode

```bash
# Start the application
uvicorn app.main:app --reload
```

### Docker Mode

```bash
# Build and run with Docker
docker-compose up --build
```

## API Endpoints 🔗

```plaintext
POST /api/chat
- Interactive chat endpoint for cocktail recommendations

GET /api/cocktails
- List available cocktails with filtering options

POST /api/cocktails/search
- Vector similarity search for cocktails
```

## Development 💻

### Installing Dev Dependencies

```bash
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Project Components 🔧

### Core Services

- `chat_service.py`: Handles chat interactions
- `cocktail_service.py`: Manages cocktail recommendations
- `llm_service.py`: Integrates with OpenAI's GPT
- `vector_store.py`: Manages vector embeddings

### Data Processing

- `data_processor.py`: Preprocesses cocktail data
- `embeddings.py`: Generates vector embeddings
- `logger.py`: Handles logging

### Frontend

- `templates/`: Jinja2 templates
- `static/`: CSS, JavaScript, and images
- Components for chat interface and cocktail display

## Documentation 📚

Detailed documentation available in `docs/`:
- `API.md`: API documentation
- `SETUP.md`: Detailed setup guide

## Testing 🧪

```bash
# Run specific test file
pytest tests/test_chat_service.py

# Run with verbose output
pytest -v

# Run with specific marker
pytest -m "integration"
```

## Deployment 🌐

### Docker Deployment

```bash
# Build the image
docker build -t cocktail-advisor .

# Run the container
docker run -p 8000:8000 cocktail-advisor
```

## Monitoring & Logging 📊

- Application logs in `logs/`
- Vector store metrics in `data/processed/vector_store/`
- Embedding data in `data/processed/embeddings/`

## Project Maintenance 🔧

Current maintainer: ramalMr
Last updated: 2025-03-04 22:42:01

## Contributing 🤝

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License 📄

MIT License - See LICENSE file for details

## Contact 📧

Project Maintainer: ramalMr