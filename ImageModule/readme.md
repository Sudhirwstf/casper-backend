# AI Social Media Optimization Pipeline

## 🚀 Overview

This is a comprehensive AI-powered social media optimization pipeline that processes images and content to generate platform-specific optimizations including image processing, hashtag generation, profile suggestions, product photography, and ready-to-post captions.

The pipeline consists of 9 interconnected modules that work together to provide a complete social media content optimization solution.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Module Breakdown](#module-breakdown)
- [API Keys & Environment Setup](#api-keys--environment-setup)
- [Installation & Dependencies](#installation--dependencies)
- [Usage Examples](#usage-examples)
- [Pipeline Flow](#pipeline-flow)
- [Input/Output Specifications](#inputoutput-specifications)
- [Error Handling](#error-handling)
- [Performance Considerations](#performance-considerations)
- [Backend Integration Guide](#backend-integration-guide)
- [API Endpoint Suggestions](#api-endpoint-suggestions)
- [Database Schema Recommendations](#database-schema-recommendations)
- [Monitoring & Logging](#monitoring--logging)

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Image Input   │────│ Product Detection│────│ Photography Gen │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Image Processing│    │  AI Analysis    │    │  Logo Addition  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Hashtag Analysis│    │Profile Discovery│    │Caption Compiler │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────┐
                    │ Final Output    │
                    │ - Optimized Images
                    │ - JSON Results
                    │ - Ready Captions
                    └─────────────────┘
```

## 📦 Module Breakdown

### 1. **main.py** - Pipeline Orchestrator
**Primary Function**: Coordinates the entire pipeline execution
- Manages multi-threading for parallel platform processing
- Handles user interactions and command-line arguments
- Orchestrates all modules in proper sequence
- Generates unique session IDs and user UUIDs for tracking

**Key Methods**:
```python
run_optimization(image_path, platforms, description, use_ai, output_format, max_workers)
process_single_platform(image_path, platform, content_description, output_format)
detect_product_in_image(image_path)  # Product detection logic
```

### 2. **vision.py** - AI Image Analysis
**Primary Function**: Analyzes images using OpenAI Vision API
- Extracts detailed descriptions from images
- Supports both local files and URLs
- Provides multi-image comparison capabilities

**Key Methods**:
```python
analyze_image_from_file(file_path, prompt, model="gpt-4.1-nano")
analyze_image_from_url(image_url, prompt, model="gpt-4.1-nano")
analyze_multiple_images(image_urls, prompt)
```

### 3. **imgprocess.py** - Image Optimization
**Primary Function**: Processes images for different social media platforms
- Auto-detects optimal aspect ratios (landscape, square, portrait)
- Resizes and optimizes for platform requirements
- Maintains quality while reducing file sizes

**Platform Specifications**:
```python
PLATFORM_SPECS = {
    "instagram": {"optimal_size": (1080, 1080), "aspect_ratio": (1, 1)},
    "facebook": {"optimal_size": (1200, 627), "aspect_ratio": (1.91, 1)},
    "linkedin": {"optimal_size": (1200, 627), "aspect_ratio": (1.91, 1)},
    "pinterest": {"optimal_size": (1000, 1500), "aspect_ratio": (2, 3)},
    "x.com": {"optimal_size": (1200, 675), "aspect_ratio": (16, 9)}
}
```

### 4. **hashkey.py** - Hashtag Generation
**Primary Function**: Generates platform-specific hashtags using AI
- Extracts content niches using GPT
- Scrapes hashtag data from multiple sources
- Optimizes hashtag selection per platform requirements

**Platform Hashtag Limits**:
```python
SUPPORTED_PLATFORMS = {
    "instagram": (15, 30),  # min, max hashtags
    "tiktok": (3, 6),
    "linkedin": (3, 5),
    "twitter": (1, 2),
    "facebook": (0, 2),
    "pinterest": (2, 5)
}
```

### 5. **profiles.py** - Account Discovery
**Primary Function**: Finds relevant social media accounts for engagement
- Uses Gemini API with search capabilities
- Extracts usernames from discovery results
- Provides platform-specific account recommendations

**Key Methods**:
```python
analyze_article_content(article_content, platform)
create_gemini_search_prompt(analysis, platform)
find_accounts_with_gemini(search_prompt)
extract_usernames_from_text(text_data)
```

### 6. **photography.py** - Product Photography Generation
**Primary Function**: Creates professional product photos using AI
- Generates 7 different photography styles
- Supports multi-platform optimization
- Integrates with Cloudinary for cloud storage

**Photography Styles**:
- FLOATING PHOTOGRAPHY
- FLAT LAY PHOTOGRAPHY  
- LIFESTYLE PHOTOGRAPHY
- PRODUCT ART PHOTOGRAPHY
- MACRO PHOTOGRAPHY
- DARK AND MOODY
- SOLID BACKGROUND

### 7. **logo.py** - Logo Integration
**Primary Function**: Adds logos to generated images
- Supports multiple positioning options
- Maintains aspect ratios and quality
- Works with various image formats

### 8. **compiler.py** - Caption Compilation
**Primary Function**: Converts JSON results into ready-to-post captions
- Generates platform-optimized captions using AI
- Includes posting time recommendations
- Provides clean, creator-focused output files

### 9. **Environment Configuration**
Required environment variables in `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
```

## 🔧 Installation & Dependencies

### Python Requirements
```bash
pip install -r requirements.txt
```

**Core Dependencies**:
```
openai>=1.0.0
google-genai>=0.3.0
pillow>=9.0.0
rembg>=2.0.0
requests>=2.28.0
python-dotenv>=0.19.0
cloudinary>=1.30.0
beautifulsoup4>=4.11.0
concurrent-futures>=3.1.1
pathlib>=1.0.1
```

### System Requirements
- Python 3.8+
- 4GB+ RAM (for image processing)
- 1GB+ storage (for temporary files)
- Internet connection (for API calls)

## 🔄 Pipeline Flow

### Complete Processing Sequence

```mermaid
graph TD
    A[Image Input] --> B[Product Detection]
    B --> C{Product Suitable?}
    C -->|Yes| D[Product Photography]
    C -->|No| E[Standard Processing]
    D --> F[Logo Addition]
    E --> G[Image Optimization]
    F --> G
    G --> H[AI Content Analysis]
    H --> I[Hashtag Generation]
    H --> J[Profile Discovery]
    I --> K[JSON Results]
    J --> K
    K --> L[Caption Compilation]
    L --> M[Final Output]
```

### Processing Time Estimates
- **Single Platform**: 30-60 seconds
- **Multiple Platforms (3-5)**: 2-4 minutes
- **With Product Photography**: +60-120 seconds
- **With Logo Addition**: +10-20 seconds

## 📊 Input/Output Specifications

### Input Requirements

#### Image Input
```python
{
    "image_path": "string",  # Local file path or URL
    "supported_formats": ["jpg", "jpeg", "png", "bmp", "tiff", "webp"],
    "max_file_size": "50MB",
    "min_resolution": "300x300"
}
```

#### Platform Selection
```python
{
    "platforms": ["instagram", "facebook", "linkedin", "x.com", "pinterest"],
    "all_platforms": True,  # Optional shortcut
}
```

#### Content Description
```python
{
    "user_description": "string",  # Optional user-provided description
    "use_ai_analysis": True,       # Enable AI image analysis
    "combine_descriptions": True   # Combine user + AI descriptions
}
```

### Output Structure

#### JSON Results Format
```json
{
    "session_id": "uuid",
    "user_uuid": "uuid",
    "timestamp": "YYYYMMDD_HHMMSS",
    "source_image": "path/to/image.jpg",
    "platforms": {
        "instagram": {
            "status": "success",
            "processed_image": "path/to/processed/image.jpg",
            "niches": ["lifestyle", "technology"],
            "hashtags": "#lifestyle #tech #innovation",
            "profile_results": {
                "extracted_usernames": ["@techblogger", "@lifestyle_guru"],
                "total_usernames": 2
            },
            "processing_time": 45.2,
            "product_photography_used": false
        }
    },
    "optimization_metadata": {
        "generated_at": "2025-01-15T10:30:00Z",
        "total_platforms": 1,
        "successful_platforms": 1
    }
}
```

#### Caption Output Format
```txt
READY TO POST CONTENT:
------------------------------

[Generated caption optimized for platform]

FIRST COMMENT (hashtags):
------------------------------
#hashtag1 #hashtag2 #hashtag3

POSTING INFO:
------------------------------
Platform: INSTAGRAM
Caption Length: 142 characters

BEST POSTING TIMES:
------------------------------
Best Days: Tuesday, Wednesday, Thursday
Best Times: 11:00 AM, 1:00 PM, 6:00 PM
Peak Engagement: Tuesday-Thursday, 11 AM - 1 PM

SUGGESTED ACCOUNTS TO TAG:
------------------------------
• @relevantaccount1
• @relevantaccount2
```

## 🎯 Backend Integration Guide

### RESTful API Structure Recommendations

#### 1. Image Upload & Processing Endpoint
```python
POST /api/v1/optimize/image
Content-Type: multipart/form-data

Request:
{
    "image": file,
    "platforms": ["instagram", "facebook"],
    "description": "Optional user description",
    "use_ai_analysis": true,
    "user_id": "uuid",
    "options": {
        "output_format": "PNG",
        "enable_product_photography": true,
        "logo_path": "optional/path/to/logo.png"
    }
}

Response:
{
    "status": "success",
    "session_id": "uuid",
    "processing_status": "started",
    "estimated_completion": "2025-01-15T10:35:00Z",
    "webhook_url": "/api/v1/webhooks/processing/{session_id}"
}
```

#### 2. Status Monitoring Endpoint
```python
GET /api/v1/optimize/status/{session_id}

Response:
{
    "session_id": "uuid",
    "status": "processing|completed|failed",
    "progress": {
        "current_platform": "instagram",
        "completed_platforms": 2,
        "total_platforms": 5,
        "percentage": 40
    },
    "estimated_remaining": "120 seconds"
}
```

#### 3. Results Retrieval Endpoint
```python
GET /api/v1/optimize/results/{session_id}

Response:
{
    "status": "success",
    "session_id": "uuid",
    "results": {
        "platforms": {...},
        "files": {
            "json_results": ["url1", "url2"],
            "compiled_captions": ["url1", "url2"],
            "optimized_images": ["url1", "url2"],
            "product_photography": ["url1", "url2"]
        }
    }
}
```

### Database Schema Recommendations

#### Processing Sessions Table
```sql
CREATE TABLE processing_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_uuid VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    source_image_path TEXT,
    platforms TEXT[], -- JSON array of selected platforms
    user_description TEXT,
    use_ai_analysis BOOLEAN DEFAULT false,
    processing_options JSONB,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT,
    results JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Platform Results Table
```sql
CREATE TABLE platform_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES processing_sessions(id),
    platform VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    processed_image_url TEXT,
    niches TEXT[],
    hashtags TEXT,
    profile_suggestions JSONB,
    processing_time_seconds DECIMAL,
    product_photography_used BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Generated Files Table
```sql
CREATE TABLE generated_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES processing_sessions(id),
    file_type VARCHAR(50) NOT NULL, -- 'json', 'caption', 'image', 'product_photo'
    platform VARCHAR(50),
    file_path TEXT NOT NULL,
    file_url TEXT,
    file_size BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Queue System Integration

#### Using Celery for Async Processing
```python
# tasks.py
from celery import Celery
from main import EnhancedMultiPlatformSocialMediaOrchestrator

app = Celery('social_media_optimizer')

@app.task(bind=True)
def process_social_media_optimization(self, session_data):
    """
    Celery task for async processing
    """
    try:
        # Update status to processing
        update_session_status(session_data['session_id'], 'processing')
        
        # Initialize orchestrator
        orchestrator = EnhancedMultiPlatformSocialMediaOrchestrator(
            api_key=session_data['api_key']
        )
        
        # Process optimization
        results = orchestrator.run_optimization(
            image_path=session_data['image_path'],
            platforms=session_data['platforms'],
            user_description=session_data.get('description'),
            use_ai_analysis=session_data.get('use_ai_analysis', False),
            output_format=session_data.get('output_format', 'PNG'),
            max_workers=3
        )
        
        # Store results
        store_session_results(session_data['session_id'], results)
        update_session_status(session_data['session_id'], 'completed')
        
        # Send webhook notification
        send_completion_webhook(session_data['session_id'])
        
        return results
        
    except Exception as e:
        update_session_status(session_data['session_id'], 'failed', str(e))
        raise
```

## 🔍 Error Handling

### Common Error Scenarios

#### 1. API Rate Limits
```python
{
    "error": "rate_limit_exceeded",
    "message": "OpenAI API rate limit exceeded",
    "retry_after": 60,
    "error_code": "OPENAI_RATE_LIMIT"
}
```

#### 2. Invalid Image Format
```python
{
    "error": "invalid_image",
    "message": "Unsupported image format. Supported: jpg, png, bmp, tiff, webp",
    "error_code": "INVALID_IMAGE_FORMAT"
}
```

#### 3. Processing Timeout
```python
{
    "error": "processing_timeout",
    "message": "Processing exceeded maximum time limit (10 minutes)",
    "error_code": "PROCESSING_TIMEOUT"
}
```

#### 4. Insufficient API Credits
```python
{
    "error": "insufficient_credits",
    "message": "OpenAI API credits exhausted",
    "error_code": "API_CREDITS_EXHAUSTED"
}
```

### Error Recovery Strategies

#### Retry Logic
```python
import backoff

@backoff.on_exception(backoff.expo,
                     (OpenAIError, RateLimitError),
                     max_tries=3,
                     max_time=300)
def call_openai_api(prompt, image_data):
    # API call logic
    pass
```

#### Graceful Degradation
```python
def process_with_fallback(image_path, platforms):
    """
    Process with fallback options when AI services fail
    """
    try:
        # Try full AI processing
        return full_ai_processing(image_path, platforms)
    except OpenAIError:
        # Fallback to template-based processing
        return template_based_processing(image_path, platforms)
    except Exception:
        # Minimal processing with basic optimization
        return basic_processing(image_path, platforms)
```

## 📈 Performance Considerations

### Optimization Strategies

#### 1. Image Preprocessing
- Resize large images before sending to APIs
- Compress images to reduce API payload size
- Cache processed images to avoid re-processing

#### 2. Parallel Processing
- Process multiple platforms simultaneously
- Use ThreadPoolExecutor for I/O-bound operations
- Implement request queuing for API calls

#### 3. Caching Strategy
```python
# Redis caching for API responses
import redis
import json
import hashlib

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_result(cache_key):
    cached = redis_client.get(cache_key)
    return json.loads(cached) if cached else None

def cache_result(cache_key, result, expiry=3600):
    redis_client.setex(cache_key, expiry, json.dumps(result))

def generate_cache_key(image_hash, platform, description):
    return f"opt:{image_hash}:{platform}:{hashlib.md5(description.encode()).hexdigest()}"
```

#### 4. Resource Management
```python
# Memory management for large image processing
import gc
import psutil

def monitor_memory_usage():
    memory_percent = psutil.virtual_memory().percent
    if memory_percent > 80:
        gc.collect()  # Force garbage collection
        return True
    return False

def process_with_memory_check(image_path):
    if monitor_memory_usage():
        # Reduce image quality or size
        return process_reduced_quality(image_path)
    return process_full_quality(image_path)
```

## 📊 Monitoring & Logging

### Key Metrics to Track

#### 1. Performance Metrics
- Average processing time per platform
- API response times
- Memory usage patterns
- File generation success rates

#### 2. Business Metrics
- Daily/monthly processing volumes
- Platform distribution (which platforms used most)
- User engagement with generated content
- Cost per processing session

#### 3. Error Tracking
```python
import structlog

logger = structlog.get_logger()

def log_processing_event(session_id, event_type, platform=None, **kwargs):
    logger.info(
        "processing_event",
        session_id=session_id,
        event_type=event_type,
        platform=platform,
        **kwargs
    )

# Usage examples:
log_processing_event(session_id, "processing_started", platforms=platforms)
log_processing_event(session_id, "platform_completed", platform="instagram", duration=45.2)
log_processing_event(session_id, "processing_failed", error="rate_limit_exceeded")
```

### Health Check Endpoints
```python
GET /api/v1/health

Response:
{
    "status": "healthy",
    "timestamp": "2025-01-15T10:30:00Z",
    "services": {
        "openai_api": {"status": "healthy", "response_time": "245ms"},
        "gemini_api": {"status": "healthy", "response_time": "189ms"},
        "cloudinary": {"status": "healthy", "response_time": "156ms"},
        "redis_cache": {"status": "healthy", "response_time": "12ms"},
        "database": {"status": "healthy", "response_time": "23ms"}
    },
    "system": {
        "memory_usage": "45%",
        "cpu_usage": "23%",
        "disk_usage": "67%"
    }
}
```

## 🔐 Security Considerations

### API Key Management
- Store API keys in secure environment variables
- Implement key rotation strategies
- Monitor API usage for anomalies
- Use different keys for different environments

### File Upload Security
```python
import magic
from pathlib import Path

ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/bmp', 
    'image/tiff', 'image/webp'
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def validate_uploaded_file(file_path):
    # Check file size
    if Path(file_path).stat().st_size > MAX_FILE_SIZE:
        raise ValueError("File too large")
    
    # Check MIME type
    mime_type = magic.from_file(file_path, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError("Invalid file type")
    
    return True
```

### Rate Limiting
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour", "10 per minute"]
)

@app.route('/api/v1/optimize/image', methods=['POST'])
@limiter.limit("5 per minute")  # Stricter limit for heavy processing
def optimize_image():
    # Processing logic
    pass
```

## 🚀 Deployment Recommendations

### Docker Configuration
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for output files
RUN mkdir -p social_media_output compiled_captions product_photography_output

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "600", "app:app"]
```

### Environment Variables for Production
```env
# API Keys
OPENAI_API_KEY=your_production_openai_key
GEMINI_API_KEY=your_production_gemini_key
CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud
CLOUDINARY_API_KEY=your_cloudinary_key
CLOUDINARY_API_SECRET=your_cloudinary_secret

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis Cache
REDIS_URL=redis://redis:6379/0

# Application Settings
FLASK_ENV=production
DEBUG=False
MAX_WORKERS=8
PROCESSING_TIMEOUT=600
MAX_FILE_SIZE=52428800

# Monitoring
SENTRY_DSN=your_sentry_dsn
LOG_LEVEL=INFO
```

## 📚 Additional Resources

### Testing the Pipeline
```bash
# Test single platform optimization
python main.py test_image.jpg --platforms instagram --description "Test image" --use-ai

# Test multiple platforms
python main.py test_image.jpg --platforms all --use-ai

# Test with product photography
python main.py product.jpg --platforms instagram facebook --description "Product photo" --use-ai

# Test compilation only
python main.py --compilation-only path/to/json/results/
```

### Troubleshooting Common Issues

1. **OpenAI API Errors**: Check API key validity and usage limits
2. **Memory Issues**: Reduce image size or enable memory monitoring
3. **Timeout Errors**: Increase processing timeout limits
4. **File Permission Errors**: Ensure write permissions for output directories
5. **Module Import Errors**: Verify all required dependencies are installed

### Performance Benchmarks
- **Single Instagram Post**: ~45 seconds
- **5 Platform Optimization**: ~3.5 minutes
- **With Product Photography**: ~5-7 minutes
- **Memory Usage**: 2-4GB peak during processing
- **API Calls per Session**: 15-25 calls average

---

## 📞 Support & Maintenance

For backend integration support or custom modifications, ensure you have:
- Python 3.8+ environment
- All required API keys configured
- Sufficient system resources (4GB+ RAM recommended)
- Understanding of the pipeline flow and error handling

The pipeline is designed to be modular and extensible. Each component can be replaced or enhanced based on specific backend requirements.
