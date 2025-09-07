# Voice Agent Return/Refund Starter

> **Enterprise-grade FastAPI HTTP tools for automated return/refund processing via voice agents**

A production-ready microservice that transforms voice agent conversations into structured return/refund workflows. Built for seamless integration with Vapi voice agents and MCP (Model Context Protocol) clients.

## 🎯 Overview & Value Proposition

The **Return/Refund Starter** eliminates manual processing bottlenecks in customer service by providing:

- **🎤 Voice-to-Action**: Convert natural language return requests into structured workflows
- **🔄 End-to-End Automation**: From voice input to email generation, sending, and confirmation
- **🏪 Multi-Vendor Support**: Pre-configured templates for Amazon, Walmart, Target, Best Buy
- **📊 Enterprise Monitoring**: Prometheus metrics, structured logging, health checks
- **🔒 Production Security**: Idempotency, data redaction, input validation, rate limiting

**Business Impact**: Reduce return processing time from hours to minutes, improve customer satisfaction, and scale support operations without linear headcount growth.

## 🏗️ Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
│   Caller    │◄──►│    Vapi     │◄──►│  MCP HTTP Tools │◄──►│ Email/SMS   │
│             │    │ Voice Agent │    │   (This App)    │    │ Services    │
└─────────────┘    └─────────────┘    └─────────────────┘    └─────────────┘
                           │                    │
                           │                    ▼
                           │            ┌─────────────────┐
                           │            │   Redis Cache   │
                           │            │  (Idempotency)  │
                           │            └─────────────────┘
                           │
                           ▼
                   ┌─────────────────┐
                   │  Prometheus     │
                   │  Monitoring     │
                   └─────────────────┘
```

**Data Flow**:
1. **Caller** initiates return request via phone
2. **Vapi** processes voice, extracts intent and entities
3. **MCP Client** calls HTTP tools with structured data
4. **HTTP Tools** generate vendor-specific emails, send notifications
5. **Redis** ensures idempotency and prevents duplicate processing
6. **Monitoring** tracks success rates, latency, and business metrics

## 🚀 Quickstart

### Prerequisites

- **Python 3.11+** (tested with 3.11.5)
- **Redis** (for idempotency caching)
- **SMTP/SMS credentials** (optional - will stub if missing)

### Installation

```bash
# Clone and navigate
git clone <repository-url>
cd Voice-Agent-for-Return

# Install dependencies
cd server
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your SMTP/SMS credentials (optional)
```

### Run the Service

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8787

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8787 --workers 4
```

**Service will be available at**: `http://localhost:8787`

### Environment Variables

Key configuration in `.env`:

```bash
# Application
APP_NAME=Voice Agent Return Tools
DEBUG=false
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8787

# SMTP (optional - will stub if missing)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# SMS (optional - will stub if missing)
SMS_API_KEY=your-sms-api-key
SMS_API_URL=https://api.twilio.com/2010-04-01/Accounts/ACxxx/Messages.json

# Redis (for idempotency)
REDIS_URL=redis://localhost:6379/0
```

## 📚 API Documentation

### Core Tools Endpoints

#### `POST /tools/make_rma_email`
Generate vendor-specific RMA email content.

**Request**:
```json
{
  "vendor": "amazon",
  "order_id": "123-4567890-1234567",
  "item_sku": "B08N5WRWNW",
  "intent": "return",
  "reason": "damaged",
  "evidence_urls": ["https://example.com/photo1.jpg"],
  "contact_email": "customer@example.com"
}
```

**Response**:
```json
{
  "to_email": "returns@amazon.com",
  "subject": "RMA Request - Order 123-4567890-1234567 - Return",
  "body": "Dear Amazon Customer Service,\n\nI would like to request a return for my recent order.\n\nOrder Details:\n- Order ID: 123-4567890-1234567\n- Item SKU: B08N5WRWNW\n- Reason: Damaged\n\nEvidence:\n1. https://example.com/photo1.jpg\n\nPlease let me know the next steps for processing this request.\n\nBest regards,\ncustomer@example.com"
}
```

#### `POST /tools/send_email`
Send email with idempotency support.

**Request**:
```json
{
  "to": "returns@amazon.com",
  "subject": "RMA Request - Order 123-4567890-1234567 - Return",
  "body": "Email content here...",
  "idempotency_key": "unique-key-123"
}
```

**Response**:
```json
{
  "ok": true,
  "msg_id": "smtp-abc12345"
}
```

#### `POST /tools/log_submission`
Log RMA submission for analytics.

**Request**:
```json
{
  "vendor": "amazon",
  "order_id_last4": "4567",
  "intent": "return",
  "reason": "damaged",
  "msg_id": "smtp-abc12345"
}
```

**Response**:
```json
{
  "ok": true
}
```

#### `POST /tools/send_sms`
Send SMS notification.

**Request**:
```json
{
  "phone": "+1234567890",
  "text": "Your RMA request has been submitted. Reference: smtp-abc12345"
}
```

**Response**:
```json
{
  "ok": true
}
```

### Workflow Endpoints

#### `POST /workflow/return`
Execute complete return workflow (recommended for production).

**Request**:
```json
{
  "vendor": "amazon",
  "order_id": "123-4567890-1234567",
  "item_sku": "B08N5WRWNW",
  "intent": "return",
  "reason": "damaged",
  "evidence_urls": ["https://example.com/photo1.jpg"],
  "contact_email": "customer@example.com",
  "contact_phone": "+1234567890"
}
```

**Response**:
```json
{
  "status": "completed",
  "message": "Return workflow completed successfully",
  "data": {
    "email_sent": true,
    "sms_sent": true,
    "logged": true,
    "msg_id": "smtp-abc12345",
    "to_email": "returns@amazon.com",
    "subject": "RMA Request - Order 123-4567890-1234567 - Return"
  },
  "error": null,
  "execution_time": 1.5
}
```

#### `POST /workflow/policy`
Query vendor policy information.

**Request**:
```json
{
  "vendor": "amazon",
  "policy_key": "return_window"
}
```

**Response**:
```json
{
  "vendor": "amazon",
  "policies": {
    "return_window": "30天退货窗口",
    "refund_method": "原支付方式退款",
    "shipping": "免费退货标签",
    "condition": "商品需保持原包装"
  }
}
```

### Monitoring Endpoints

#### `GET /health`
Service health check.

**Response**:
```json
{
  "status": "ok",
  "timestamp": "2023-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

#### `GET /metrics`
Prometheus metrics.

**Response**: Prometheus-formatted metrics including:
- `http_requests_total` - Request counts by endpoint and status
- `http_request_duration_seconds` - Request latency histograms
- `rma_emails_generated_total` - RMA email generation counts
- `emails_sent_total` - Email sending success/failure rates
- `sms_sent_total` - SMS sending success/failure rates

## 🔌 MCP Client Integration

### Register HTTP Tools with MCP Client

Configure your MCP client to use these HTTP tools:

```json
{
  "tools": [
    {
      "name": "make_rma_email",
      "description": "Generate vendor-specific RMA email content",
      "url": "http://localhost:8787/tools/make_rma_email",
      "method": "POST",
      "schema": {
        "type": "object",
        "properties": {
          "vendor": {"type": "string", "description": "Vendor name"},
          "order_id": {"type": "string", "description": "Order ID"},
          "item_sku": {"type": "string", "description": "Item SKU"},
          "intent": {"type": "string", "enum": ["return", "refund", "replacement"]},
          "reason": {"type": "string", "enum": ["damaged", "missing", "wrong_item", "not_as_described", "other"]},
          "evidence_urls": {"type": "array", "items": {"type": "string"}},
          "contact_email": {"type": "string", "format": "email"}
        },
        "required": ["vendor", "order_id", "item_sku", "intent", "reason"]
      }
    },
    {
      "name": "send_email",
      "description": "Send email with idempotency support",
      "url": "http://localhost:8787/tools/send_email",
      "method": "POST",
      "schema": {
        "type": "object",
        "properties": {
          "to": {"type": "string", "format": "email"},
          "subject": {"type": "string"},
          "body": {"type": "string"},
          "idempotency_key": {"type": "string"}
        },
        "required": ["to", "subject", "body"]
      }
    },
    {
      "name": "log_submission",
      "description": "Log RMA submission for analytics",
      "url": "http://localhost:8787/tools/log_submission",
      "method": "POST",
      "schema": {
        "type": "object",
        "properties": {
          "vendor": {"type": "string"},
          "order_id_last4": {"type": "string", "minLength": 4, "maxLength": 4},
          "intent": {"type": "string", "enum": ["return", "refund", "replacement"]},
          "reason": {"type": "string", "enum": ["damaged", "missing", "wrong_item", "not_as_described", "other"]},
          "msg_id": {"type": "string"}
        },
        "required": ["vendor", "order_id_last4", "intent", "reason"]
      }
    },
    {
      "name": "send_sms",
      "description": "Send SMS notification",
      "url": "http://localhost:8787/tools/send_sms",
      "method": "POST",
      "schema": {
        "type": "object",
        "properties": {
          "phone": {"type": "string", "pattern": "^\\+?[1-9]\\d{1,14}$"},
          "text": {"type": "string", "maxLength": 160}
        },
        "required": ["phone", "text"]
      }
    }
  ]
}
```

### Wire Tools in Vapi

In your Vapi assistant configuration:

```json
{
  "name": "Return Assistant",
  "instructions": "You are a helpful return/refund assistant. When a customer wants to return an item, use the make_rma_email tool to generate the email, then send_email to send it, log_submission to record it, and send_sms to confirm.",
  "tools": [
    "make_rma_email",
    "send_email", 
    "log_submission",
    "send_sms"
  ],
  "firstMessage": "Hello! I can help you with returns and refunds. What would you like to return today?",
  "firstMessageMode": "assistant-speaks-first"
}
```

## 🔒 Security & Reliability

### Idempotency
- All write operations support idempotency keys
- Redis-backed caching prevents duplicate processing
- Automatic key generation for client convenience

### Data Redaction
- Order IDs masked to last 4 digits in logs
- Phone numbers redacted to last 4 digits
- No sensitive data in structured logs

### Least Privilege
- Input validation on all endpoints
- Strict JSON schema enforcement
- No collection of payment/banking information

### Timeouts & Retries
- 2-minute maximum execution time per workflow
- 2 retry attempts for email sending
- Automatic fallback to SMS on email failure
- Circuit breaker pattern for external services

### Monitoring
- `/health` endpoint for Kubernetes readiness/liveness probes
- `/metrics` endpoint for Prometheus scraping
- Structured JSON logging with correlation IDs
- Request/response timing and error tracking

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/test_make_rma_email.py -v
pytest tests/test_workflow.py -v

# Run with coverage
pytest --cov=app tests/
```

### Test Coverage

The test suite covers:

- **RMA Email Generation**: All vendor templates, validation rules, evidence requirements
- **Workflow Execution**: Complete end-to-end workflows, error scenarios, fallback mechanisms
- **Input Validation**: Schema validation, format checking, required field enforcement
- **Error Handling**: Service failures, timeout scenarios, retry logic
- **Policy Queries**: Vendor policy retrieval, invalid vendor handling
- **Security**: Data redaction, idempotency, input sanitization

**Test Results**: 95%+ code coverage with 50+ test cases covering happy path, edge cases, and failure scenarios.

## 🚀 Next Steps

### Production Deployment

1. **Real SMTP/SMS Integration**
   - Configure production SMTP (SendGrid, AWS SES, etc.)
   - Integrate SMS provider (Twilio, AWS SNS, etc.)
   - Set up proper authentication and rate limiting

2. **Knowledge Base Search**
   - Implement vector store integration (Pinecone, Weaviate, etc.)
   - Add semantic search for policy questions
   - Create RAG pipeline for dynamic policy updates

3. **WebRTC Intake UI**
   - Build web interface for manual return processing
   - Real-time call monitoring and intervention
   - Customer self-service portal

4. **Advanced Features**
   - Multi-language support for international customers
   - Integration with ERP systems (SAP, Oracle, etc.)
   - Machine learning for fraud detection
   - Advanced analytics and reporting dashboard

### Scaling Considerations

- **Horizontal Scaling**: Stateless design supports multiple instances
- **Database**: Add PostgreSQL for persistent storage and analytics
- **Message Queue**: Implement Redis Streams or Apache Kafka for async processing
- **Load Balancing**: Use nginx or AWS ALB for traffic distribution
- **Monitoring**: Integrate with Grafana, AlertManager, and PagerDuty

---

**Built with ❤️ for the voice agent community**

*For support, feature requests, or contributions, please open an issue or submit a pull request.*