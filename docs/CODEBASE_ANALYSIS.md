# WAPOW Codebase Analysis Report

**Date**: April 2026
**Project**: WAPOW - Content Aggregation & Recommendation Platform

---

## Project Overview

**WAPOW** is a full-stack web application for content aggregation and recommendations.

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Vue 3 + Vite + TypeScript + Tailwind CSS |
| **Backend API** | FastAPI (Python) |
| **Primary Database** | MongoDB (content storage) |
| **Graph Database** | Neo4j (recommendations) |
| **Analytics** | ClickHouse |
| **Authentication** | Auth0 |
| **Deployment** | Docker Compose, Nginx, Let's Encrypt, DigitalOcean |

---

## Findings Summary

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Security | 1 | 2 | 4 | 3 |
| Code Quality | - | 2 | 4 | - |
| Performance | - | 2 | 3 | - |
| Testing | 1 | - | - | - |
| Configuration | - | - | 4 | - |
| Monitoring | - | 3 | - | - |

---

## Critical Issues

### 1. No Test Coverage

**Severity**: Critical
**Location**: Entire codebase
**Issue**: Zero unit, integration, or E2E tests found.

**Impact**:
- No deployment confidence
- High regression risk
- Unsafe refactoring

**Recommendation**:
- Add pytest for backend
- Add Vitest for frontend
- Add Cypress/Playwright for E2E

---

### 2. Credentials Logged to Console

**Severity**: Critical
**Location**: `wapow-collector/config.py:20`

```python
print(f"CLICKHOUSE_PASSWORD: {CLICKHOUSE_PASSWORD}")
```

**Impact**: Passwords visible in container/application logs

**Fix**: Remove debug print statements

---

### 3. Environment Files Committed to Repository

**Severity**: High
**Location**:
- `wapow-ui/.env`
- `wapow-ui/.env.local`

**Issue**: Auth0 credentials exposed in repository:
```
VITE_AUTH0_DOMAIN=dev-2uzbhsv08o2x2keh.us.auth0.com
VITE_AUTH0_CLIENT_ID=fsPh9rXll7iqeGgtnMxVRrohE0s6vczW
```

**Fix**:
```bash
git rm --cached wapow-ui/.env wapow-ui/.env.local
echo "wapow-ui/.env" >> .gitignore
echo "wapow-ui/.env.local" >> .gitignore
```

---

## High Severity Issues

### 4. Neo4j Driver Created Per Request

**Location**: `wapow-app/api/db/neo4j_query.py:13-24`

```python
class Neo4jQuery:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
```

**Issue**: New driver/connection created for every `/api/recommendations` request

**Impact**: Performance bottleneck, connection exhaustion

**Fix**: Cache driver instance at module level or use dependency injection with singleton scope

---

### 5. No Rate Limiting

**Location**: All API endpoints

**Issue**: FastAPI backend has no rate limiting configured

**Impact**:
- API abuse potential
- DoS vulnerability
- Resource exhaustion

**Fix**: Implement `slowapi` or nginx rate limiting

---

### 6. No Error Tracking

**Issue**: 500 errors logged locally only, no centralized monitoring

**Impact**: Production errors go undetected

**Fix**: Integrate Sentry or similar APM

---

### 7. Console.log Statements in Production

**Location**: 15+ files in `wapow-ui/src/`

**Examples**:
```typescript
console.log('[handleSave] Saving article:', articleId, 'collection:', collection)
console.log('Recommendations data:', data)
```

**Impact**: Debug information leaked to browser console

**Fix**: Remove or wrap in `if (import.meta.env.DEV)`

---

## Medium Severity Issues

### 8. No Input Validation on Query Parameters

**Location**: `wapow-app/api/routers/content.py`, `articles.py`

```python
sortBy: str = Query("created_date", alias="sortBy"),
sortOrder: str = Query("desc", alias="sortOrder"),
```

**Issue**: Parameters not validated against whitelist

**Risk**: Potential NoSQL injection or unexpected behavior

**Fix**:
```python
from enum import Enum

class SortField(str, Enum):
    created_date = "created_date"
    publish_date = "publish_date"
    title = "title"

sortBy: SortField = Query(SortField.created_date, alias="sortBy")
```

---

### 9. Duplicate Serialization Logic

**Locations**:
- `wapow-app/api/services/user.py`
- `wapow-app/api/services/content.py`
- `wapow-app/api/services/comments.py`

**Issue**: Identical `_serialize_doc()` function duplicated across files

**Fix**: Create shared utility:
```python
# api/utils/serialization.py
from bson import ObjectId
from datetime import datetime

def serialize_doc(doc: dict) -> dict:
    result = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result
```

---

### 10. Hardcoded Collection Categories

**Location**: `wapow-app/api/routers/articles.py:19-27`

```python
COLLECTION_MAP = {
    "sports": ("articles", False, False),
    "style": ("articles", False, False),
    ...
}
```

**Issue**: Adding new categories requires code changes

**Fix**: Query MongoDB for available categories dynamically or use configuration file

---

### 11. Vue DevTools Enabled in Production

**Location**: `wapow-ui/vite.config.ts:11`

```typescript
vueDevTools(),
```

**Impact**: Unnecessary bundle size (~100KB), dev tools exposed

**Fix**:
```typescript
plugins: [
  vue(),
  ...(process.env.NODE_ENV === 'development' ? [vueDevTools()] : []),
],
```

---

### 12. Vite Dev Server Binds to 0.0.0.0

**Location**: `wapow-ui/vite.config.ts:19`

```typescript
server: { host: '0.0.0.0', port: 3000, allowedHosts: true }
```

**Risk**: Dev server exposed to all network interfaces

**Fix**:
```typescript
server: {
  host: '127.0.0.1',
  port: 3000,
  allowedHosts: ['localhost', '127.0.0.1']
}
```

---

### 13. Full Document Serialization

**Location**: `wapow-app/api/services/content.py:69`

```python
return {
    "id": ...,
    "title": ...,
    **_serialize_doc(item),  # Returns ALL fields
}
```

**Impact**: Bloated responses, wasted bandwidth

**Fix**: Use MongoDB projection to return only needed fields

---

### 14. Global MongoDB Client Not Thread-Safe

**Location**: `wapow-app/api/db/mongodb.py`

```python
_client: MongoClient | None = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(...)
    return _client
```

**Issue**: Race condition on initialization

**Fix**: Use `threading.Lock()` or FastAPI's dependency injection with lifespan

---

## Performance Concerns

### 15. No Query Result Caching

**Issue**: Recommendations, categories, stats queried fresh every request

**Impact**: Unnecessary latency and database load

**Fix**: Implement Redis caching with TTL

---

### 16. Missing Database Indexes

**Issue**: No indexes on frequently filtered fields

**Impacted fields**: `category`, `created_date`, `publish_date`

**Fix**:
```python
# In MongoDB setup
db.articles.create_index([("category", 1)])
db.articles.create_index([("created_date", -1)])
db.articles.create_index([("publish_date", -1)])
```

---

### 17. Fetching Entire User Document for Save Check

**Location**: `wapow-app/api/services/user.py:116`

```python
user = coll.find_one({"user_id": user_id}, {"saved.article_id": 1})
```

**Issue**: Returns all saved article IDs for every check

**Fix**: Use `$elemMatch` or separate collection for saved articles

---

## Architecture Issues

### 18. No API Versioning

**Issue**: All endpoints on `/api/`, no version prefix

**Risk**: Breaking changes affect all clients

**Fix**: Introduce `/api/v1/` prefix

---

### 19. No Structured Logging

**Location**: `wapow-collector/config.py:22`

```python
logging.basicConfig(level=logging.INFO)
```

**Issue**: Plain text logs, no correlation IDs

**Fix**: Use structured JSON logging with correlation IDs

---

### 20. Generic Exception Handling

**Location**: `wapow-app/api/db/neo4j_query.py:78`

```python
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Recommendations error: {str(e)}")
```

**Issue**: Internal error details exposed in API responses

**Fix**: Log error server-side, return generic message to client

---

## Positive Findings

The codebase demonstrates good practices in several areas:

- **Clean architecture** - Separation of routers, services, DB layers
- **Type safety** - TypeScript frontend, Python type hints
- **Authentication** - Proper Auth0 integration with JWT validation
- **Docker setup** - Well-structured Compose files, prod/dev separation
- **Git workflow** - Proper `.gitignore`, deployment automation
- **Frontend state** - Clean Pinia store implementation
- **CORS handling** - Proper environment-based configuration
- **API design** - RESTful endpoints with proper HTTP methods
- **Frontend routing** - Auth guards, lazy loading with Vue Router

---

## Recommended Action Plan

### Week 1 (Immediate)

1. Remove `.env` files from repository
2. Delete password print statements
3. Add input validation whitelist for query parameters
4. Remove console.log statements from production code

### Week 2-3 (Short Term)

5. Implement Neo4j connection pooling
6. Create shared utility for serialization
7. Set up pytest with basic test coverage
8. Fix Vite configuration (DevTools, host binding)
9. Add structured logging

### Month 1 (Medium Term)

10. Implement rate limiting
11. Add Redis caching layer
12. Integrate Sentry for error tracking
13. Add database indexes
14. Introduce API versioning (`/api/v1/`)

### Quarter 1 (Long Term)

15. MongoDB replica set for high availability
16. Environment variable validation on startup
17. Automated secrets rotation
18. E2E testing with Cypress/Playwright
19. Comprehensive API documentation
20. Pydantic models for all endpoints

---

## Overall Assessment

**Score: 7/10**

WAPOW is a well-architected web application with a solid foundation. The codebase is production-ready for MVP but needs hardening for scale:

- **Security**: Low-to-medium risk from exposed credentials and missing validation; fixable
- **Performance**: Moderate issues with connection pooling and caching; manageable
- **Testing**: Complete gap; should be addressed before major features
- **Operations**: Monitoring/logging insufficient for production; add APM

The project demonstrates good software engineering practices and clean code organization. With the recommended fixes, it will be ready for production scale.
