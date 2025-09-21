# BinBot — Technical Specification

## Overview
BinBot is an AI-assisted inventory system that lets users manage storage bins via natural language and images. It integrates:

- FastAPI backend API
- Chat/LLM orchestration for function calling
- Vision/image analysis and storage
- Vector search via ChromaDB
- A simple single-page HTML UI
- Docker-based development and deployment

Key behaviors:

- Efficient, targeted API endpoints (no over-fetching)
- UI shows the contents of the last bin worked on
- Items added from images maintain association to the source image

---

## Architecture

- **Frontend**: Static HTML page with a simple split layout: left chat (with camera button) and right bin contents. Includes comprehensive camera support with live preview, photo capture, and device selection.
- **Backend API**: FastAPI app exposing REST endpoints for inventory operations, images, and chat.
- **Chat Layer**: Command parsing, function selection and dispatching (Gemini tool/function calling).
- **LLM Layer**: Text LLM client, embeddings service, and vision utilities.
- **Database**: ChromaDB for vectorized item metadata (name, description, bin_id, embeddings) and audit logs.
- **Storage**: Local image store with metadata updates and ID-based lookup.
- **Session/Conversation**: Track session state, conversation history, and current bin context.
- **Config**: Centralized settings and embeddings configuration.

---

## Key Files, Responsibilities, and Proposed Main Functions

### Application Entry
- **app.py**
  - `create_app()`: Build and configure the FastAPI app (mount routers, CORS, static).
  - `run()`: Start the app with Uvicorn (or executed via Docker/start.sh).

- **start.sh**
  - `main()`: Shell entrypoint to launch the API server in Docker/local.

- **docker-compose.yml / docker-compose.yaml**
  - Services definition (API, optional vector DB backing, volumes, networks).

- **Dockerfile**
  - Defines runtime environment for API and dependencies.

### API Layer (FastAPI Implementation)

#### Inventory Operations
- **api/inventory.py**
  - `add_items()`: **POST /api/items/add**
    - **Purpose**: Add items with embeddings to a bin; optionally link image_id
    - **Request**: `{ bin_id: string, items: [{name: string, description?: string, image_id?: string}] }`
    - **Response**: `{ success: boolean, added_items: array, failed_items: array, current_bin: string }`

  - `remove_items()`: **POST /api/items/remove**
    - **Purpose**: Remove items from a bin using item IDs
    - **Request**: `{ bin_id: string, item_ids: [string] }`
    - **Response**: `{ success: boolean, removed_items: array, not_found_items: array, current_bin: string }`

  - `move_items()`: **POST /api/items/move**
    - **Purpose**: Move items between bins using item IDs
    - **Request**: `{ target_bin_id: string, item_ids: [string] }`
    - **Response**: `{ success: boolean, moved_items: array, not_found_items: array, current_bin: string }`

  - `search_items()`: **POST /api/items/search**
    - **Purpose**: Semantic search over inventory
    - **Request**: `{ query: string, limit?: number }`
    - **Response**: `{ success: boolean, items: array }`

#### Image Operations

- **api/images.py** - `upload_image()`: **POST /api/images**
  - **Purpose**: Upload image, auto-analyze, return structured items
  - **Request**: Form: multipart file
  - **Response**: `{ success: boolean, image_id: string, analyzed_items: [{name: string, description: string}] }`

- **api/images.py** - `analyze_image()`: **POST /api/images/{image_id}/analyze**
  - **Purpose**: Re-analyze image
  - **Request**: `{}`
  - **Response**: `{ success: boolean, items: [{name: string, description: string}] }`

- **api/images.py** - `get_image()`: **GET /images/{image_id}**
  - **Purpose**: Serve stored image asset
  - **Response**: Image file (JPEG/PNG)

#### Session Operations


- **api/session.py** - `start_session()`: **POST /api/session**
  - **Purpose**: Create session with UUID, set secure cookie, initialize state
  - **Response**: `{ success: boolean, session_id: string }`
  - **Cookie**: Sets `session_id` cookie (httponly, secure, 30min TTL)

- **api/session.py** - `get_session()`: **GET /api/session/{id}**
  - **Purpose**: Retrieve session state (current bin, conversation length, etc.)
  - **Response**: `{ success: boolean, session: { session_id: string, created_at: string, last_accessed: string, current_bin: string, conversation: [{ role: string, content: string }] } }`

- **api/session.py** - `end_session()`: **DELETE /api/session/{id}**
  - **Purpose**: End session, clear from memory, delete cookie
  - **Response**: `{ success: boolean }`
  - **Cookie**: Deletes `session_id` cookie

#### Chat operations

- **api/chat.py** - `chat()`: **POST /api/chat/command**
  - **Purpose**: Create session-bound functions, send to Gemini with automatic execution
  - **Request**: `{ message: string }` (session from cookie)
  - **Response**: `{ success: boolean, response: string }`
  - **Process**: Creates `SessionBoundFunctionWrapper` → Maps to Gemini functions → Auto-execution.

- **api/chat.py** - `chat_image()`: **POST /api/chat/image**
  - **Purpose**: Upload image, analyze contents, and add to session context
  - **Request**: Form: multipart file (session from cookie)
  - **Response**: `{ success: boolean, image_id: string, analyzed_items: [{name: string, description: string}] }`
  - **Process**: Uploads image → Vision analysis → Stores in session context for LLM
  
#### System Operations

- **api/health.py** - `health_check()`: **GET /health**
  - **Purpose**: Liveness/readiness probe
  - **Response**: `{ status: "ok" }`

#### Data Models

- **api_schemas.py**
  - Pydantic models for request/response DTOs (e.g., ItemAddRequest, SearchRequest, ChatRequest)

#### Session Architecture

**In-Memory Session Store with TTL Management:**

```python
# Session structure
{
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "created_at": datetime,
  "last_accessed": datetime,
  "current_bin": "A3",
  "conversation": [
    {"role": "user", "content": "Add screwdriver to bin A3"},
    {"role": "assistant", "content": "Added Phillips screwdriver to bin A3"}
  ],
}
```

**Key Features:**
- **UUID Session IDs**: Cryptographically secure using `uuid.uuid4()`
- **HTTP-Only Cookies**: Secure session ID storage, prevents XSS
- **30-minute TTL**: Automatic expiration with lazy cleanup
- **In-Memory Storage**: Fast access, no external dependencies
- **Background Cleanup**: Periodic removal of expired sessions

### Chat Orchestration

- **chat/function_wrappers.py**
  - `InventoryFunctionWrappers`: Simple class containing business logic for inventory operations.
  - Session-bound wrapper methods: `add_items()`, `search_items()`, `get_bin_contents()`, `move_items()`, `remove_items()`.
  - Handles embeddings generation, database operations, and session state updates.
  - Returns simple string responses for LLM consumption.

- **chat/function_definitions.py**
  - `get_inventory_functions()`: Returns Gemini function declarations for inventory operations.
  - `get_all_functions()`: Returns all available function definitions for LLM tool schema.
  - `get_gemini_inventory_functions()`: Complete Gemini function schemas.
  - `get_function_by_name(function_name)`: Get specific function schema by name.

- **session/session_manager.py** (handles conversation management)
  - `get_conversation(session_id)`: Retrieve conversation history and system messages.
  - `add_message(session_id, role, content)`: Add to conversation context.
  - `set_current_bin(session_id, bin_id)`: Maintain current/last bin context.

### LLM & Vision
- **llm/client.py**
  - `chat_completion(messages, tools)`: Call Gemini LLM with automatic function execution enabled.
  - `GeminiClient`: Uses new `google-genai` SDK (v1.38.0+) with improved function calling.
  - `tool_config`: Configured for `FunctionCallingConfig.Mode.AUTO` - functions execute automatically.

- **llm/embeddings.py**
  - `generate_embedding(text)`: Create vector embedding used across inventory operations.
  - `batch_generate_embedding(texts)`: Efficient batched embeddings.

- **llm/vision.py**
  - `analyze_image(image_path)`: Gemini Vision API to identify items and return structured JSON.
  - Single production method with predefined schema for inventory item identification.

### Database / Vector Store
- **database/chromadb_client.py**
  - `add_documents_bulk(items)`: Insert multiple items (name, description, bin_id, embedding, timestamps).
  - `search_documents(query, limit, max_distance)`: Vector search with distance filtering.
  - `remove_document(item_id)`: Delete item by UUID identifier.
  - `update_item_bin(item_id, new_bin_id)`: Update item's bin location by UUID.
  - `get_bin_contents(bin_id)`: Get all items in a specific bin.
  - `add_image_to_item(item_id, image_id)`: Link image to item metadata.
  - `add_audit_log_entry(entry)`: Append structured audit events (placeholder).
  - `inventory_collection`: Property exposing underlying ChromaDB collection for updates.

### Image Storage
- **storage/image_storage.py**
  - `save_image(file_path, filename)`: Persist uploaded image and return image_id.
  - `get_image_path(image_id)`: Resolve file path by image ID.
  - `get_image_data(image_id)`: Get image bytes (for in-memory mode).
  - `get_image_metadata(image_id)`: Get image metadata and associations.
  - `update_image_metadata(image_id, metadata)`: Maintain associations (item_id, bin_id).

### Session Management
- **session/session_manager.py**
  - `SessionManager`: In-memory session store with TTL and cleanup
  - `new_session()`: Generate UUID session ID, create initial session state
  - `get_session(session_id)`: Get session data if it exists and hasn't expired
  - `get_conversation(session_id)`: Retrieve conversation history from session
  - `add_message(session_id, role, content)`: Add message to conversation history
  - `set_current_bin(session_id, bin_id)`: Track the last/active bin for UI context
  - `cleanup_expired_sessions()`: Remove sessions past TTL (30 minutes default)
  - `end_session(session_id)`: Explicit cleanup and finalize
  - `_is_expired(session)`: Check if session has exceeded TTL

### Config
- **config/settings.py**
  - Simple environment variable based configuration with sensible defaults.
  - Constants: `GEMINI_API_KEY`, `DATABASE_PATH`, `IMAGES_PATH`, `API_HOST`, `API_PORT`
  - Session configuration: `SESSION_TTL_MINUTES` (default 30 minutes)
  - Storage mode: `STORAGE_MODE` ('memory' for testing, 'persistent' for production)

- **config/embeddings.py**
  - Embedding dimension constant: `EMBEDDING_DIMENSION = 768`
  - `get_embedding_service()`: Get global embedding service instance.

### Frontend
- **frontend/index.html** - Single-page web application
  - Split layout: left chat panel with camera button; right panel for current bin contents
  - Responsive design with mobile support and touch-friendly interface

- **frontend/app.js** - JavaScript application with comprehensive camera and voice support
  - **CameraManager Class**: getUserMedia API integration with permission handling
  - **Live Camera Preview**: Full-screen camera modal with video feed and controls
  - **Photo Capture**: Canvas-based capture with high-quality JPEG output
  - **Camera Selection**: Device switching for front/back cameras on mobile devices
  - **VoiceManager Class**: Web Speech API integration with microphone permissions
  - **Conversational Speech**: Real-time speech recognition with automatic message sending
  - **Voice UI Integration**: Simple microphone toggle button with visual listening feedback
  - **Chat Integration**: Seamless integration with existing message handling workflow
  - **Error Handling**: Comprehensive error handling for all camera and voice failures

- **frontend/style.css** - Modern responsive styling
  - Dark theme camera interface with gradient buttons
  - Mobile-optimized camera controls and responsive modal design
  - Consistent styling across all UI components

### Utilities
- **utils/** (minimal utilities as needed)
  - Image resizing handled directly in vision service (llm/vision.py)

### Data
- **data/images**
  - Stored images managed by ImageStorage.

- **data/chromadb**
  - Vector DB files for ChromaDB.

### Tests (selected)
- **test/test_ui_workflow_scenario.py**: UI workflow happy path
- **test/test_chat_simple.py**: Chat basic commands
- **test/test_image_context.py**: Image associations and context
- **test/test_image_upload.py**: Upload flow
- **test/test_complete_flow.py**: End-to-end integration
- Additional tests cover performance, optimization, and LLM/vision behavior.



## LLM Function Schemas

The system uses Gemini's automatic function calling (AUTO mode) to enable seamless execution of inventory operations. Gemini automatically decides when to call functions and can chain multiple function calls without manual intervention. Image analysis is handled automatically on upload, not as LLM functions. These schemas are defined in `chat/function_definitions.py` and passed to the LLM during chat completion.

### LLM Inventory Functions

The LLM has access to these 5 core inventory management functions:

#### add_items_to_bin
```python
genai.protos.FunctionDeclaration(
    name="add_items_to_bin",
    description="Add one or more items to a specific bin in the inventory system",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "items": genai.protos.Schema(
                type=genai.protos.Type.ARRAY,
                items=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "name": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="The name of the item"
                        ),
                        "description": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="Optional detailed description of the item"
                        ),
                        "image_id": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="Optional image ID to associate with this specific item"
                        )
                    },
                    required=["name"]
                ),
                description="List of items to add to the bin. Each item can have a name, optional description, and optional image_id"
            ),
            "bin_id": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="The ID/number of the bin to add items to (e.g., 'A3', 'B5', 'TOOLS12')"
            )
        },
        required=["items", "bin_id"]
    )
)
```

#### remove_items_from_bin
```python
genai.protos.FunctionDeclaration(
    name="remove_items_from_bin",
    description="Remove one or more items from a specific bin in the inventory system using item IDs",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "item_ids": genai.protos.Schema(
                type=genai.protos.Type.ARRAY,
                items=genai.protos.Schema(type=genai.protos.Type.STRING),
                description="List of item IDs (UUIDs) to remove from the bin"
            ),
            "bin_id": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="The ID/number of the bin to remove items from (e.g., 'A3', 'B5', 'TOOLS12')"
            )
        },
        required=["item_ids", "bin_id"]
    )
)
```

#### move_items_between_bins
```python
genai.protos.FunctionDeclaration(
    name="move_items_between_bins",
    description="Move one or more items from one bin to another bin using item IDs",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "item_ids": genai.protos.Schema(
                type=genai.protos.Type.ARRAY,
                items=genai.protos.Schema(type=genai.protos.Type.STRING),
                description="List of item IDs (UUIDs) to move between bins"
            ),
            "source_bin_id": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="The ID/number of the bin to move items from (e.g., 'A3', 'B5', 'TOOLS12')"
            ),
            "target_bin_id": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="The ID/number of the bin to move items to (e.g., 'A3', 'B5', 'TOOLS12')"
            )
        },
        required=["item_ids", "source_bin_id", "target_bin_id"]
    )
)
```

#### search_for_items
```python
genai.protos.FunctionDeclaration(
    name="search_for_items",
    description="Search for items in the inventory system using semantic search. Returns items with their names, descriptions, bin locations, and associated images.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "query": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Search query to find items (e.g., 'electronics', 'screws', 'tools')"
            ),
            "max_results": genai.protos.Schema(
                type=genai.protos.Type.INTEGER,
                description="Maximum number of results to return (default: 10)"
            )
        },
        required=["query"]
    )
)
```

#### list_bin_contents
```python
genai.protos.FunctionDeclaration(
    name="list_bin_contents",
    description="List all items in a specific bin. Returns items with their names, descriptions, and associated images.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "bin_id": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="The ID/number of the bin to list contents for (e.g., 'A3', 'B5', 'TOOLS12')"
            )
        },
        required=["bin_id"]
    )
)
```



### Function Schema Access
- **`get_gemini_inventory_functions()`**: Returns all function schemas in Gemini format
- **`get_function_by_name(function_name)`**: Get specific function schema by name
- **`get_all_function_names()`**: Get list of all available function names

### Automatic Function Execution Architecture

**Gemini AUTO Mode Configuration:**
```python
tool_config = genai.protos.ToolConfig(
    function_calling_config=genai.protos.FunctionCallingConfig(
        mode=genai.protos.FunctionCallingConfig.Mode.AUTO
    )
)
```

**Execution Flow:**
1. **User Message** → Sent to Gemini with function schemas and AUTO mode
2. **Gemini Analysis** → Automatically decides which functions to call (if any)
3. **Function Execution** → Gemini calls functions directly, receives results
4. **Multi-Step Operations** → Gemini can chain multiple function calls automatically
5. **Final Response** → User receives complete answer with all operations completed

**Example Multi-Step Operation:**
- **User**: "Move all electronics from bin A3 to bin B5"
- **Gemini automatically**:
  1. Calls `list_bin_contents(bin_id="A3")`
  2. Analyzes results to identify electronics
  3. Calls `move_items_between_bins(item_ids=[...], source_bin_id="A3", target_bin_id="B5")`
  4. Returns final success message to user

**Benefits:**
- **Seamless UX**: No manual function approval needed
- **Complex Workflows**: Multi-step operations handled automatically
- **Intelligent Decisions**: Gemini determines optimal function sequence
- **Error Recovery**: Can retry or adjust approach if functions fail

### Session-Bound Function Architecture

**Problem**: Gemini function schemas cannot include `session_id`, but our functions need session context.

**Solution**: Session-bound wrapper that injects session_id automatically.

#### Component Architecture
```mermaid
graph LR
    A[FastAPI] --> B[SessionBoundWrapper]
    B --> C[InventoryWrappers]
    C --> D[Database]
    C --> E[SessionManager]

    F[Gemini] --> B
    B -.->|session_id injected| C

    subgraph "Clean Function Signatures"
        G[add_items_to_bin<br/>bin_id, items]
        H[move_items_between_bins<br/>source, target, item_ids]
        I[search_for_items<br/>query, max_results]
    end

    subgraph "chat/function_wrappers.py"
        B
        C
    end

    F --> G
    F --> H
    F --> I

    style B fill:#f3e5f5
    style C fill:#fff3e0
```

#### Execution Flow
```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI /chat
    participant SW as SessionBoundWrapper
    participant IW as InventoryWrappers
    participant G as Gemini
    participant DB as Database
    participant SM as SessionManager

    U->>API: POST /api/chat<br/>{message, session_id}

    API->>IW: new InventoryFunctionWrappers()
    API->>SW: new SessionBoundWrapper(session_id, IW)

    Note over API,IW: Both classes in chat/function_wrappers.py
    API->>SW: create function mapping

    Note over API,SW: Functions bound to session:<br/>add_items_to_bin(bin_id, items)<br/>move_items_between_bins(...)<br/>search_for_items(query)

    API->>G: chat_with_functions(message, tools, functions)

    Note over G: Gemini analyzes message<br/>and decides to call functions

    G->>SW: add_items_to_bin("A3", [items])
    SW->>IW: add_items_to_bin_wrapper(session_id, "A3", [items])

    IW->>DB: add_documents_bulk(processed_items)
    DB-->>IW: {success: true, added_items: [...]}

    IW->>SM: set_current_bin(session_id, "A3")
    SM-->>IW: updated

    IW-->>SW: {success: true, current_bin: "A3", ...}
    SW-->>G: {success: true, current_bin: "A3", ...}

    Note over G: Gemini may call more functions<br/>or continue with response

    G->>SW: search_for_items("screwdriver")
    SW->>IW: search_for_items_wrapper(session_id, "screwdriver")

    IW->>DB: search_documents("screwdriver")
    DB-->>IW: {success: true, items: [...]}

    IW->>SM: set_last_search_results(session_id, items)
    SM-->>IW: updated

    IW-->>SW: {success: true, items: [...]}
    SW-->>G: {success: true, items: [...]}

    G-->>API: "I added 3 items to bin A3 and found 2 screwdrivers"
    API-->>U: {success: true, response: "I added 3 items..."}

    Note over U,SM: Session state updated:<br/>current_bin: "A3"<br/>search_results: [...]<br/>conversation: [...]
```

**Function Side Effects:**
- **Add/Remove/List**: Updates current_bin, **Move**: Updates to target_bin, **Search**: No current_bin change

### Key Schema Features
- **Rich Item Structure**: Items support both names and optional descriptions
- **Individual Image Associations**: Each item can have its own image_id when adding
- **Flexible Bin IDs**: Support alphanumeric bin identifiers (e.g., 'A3', 'TOOLS12')
- **Unambiguous Operations**: Move and remove operations use item UUIDs to eliminate ambiguity
- **Automatic Image Analysis**: Images are analyzed on upload, returning structured item data for LLM context
- **Automatic Function Execution**: Gemini executes functions automatically in AUTO mode, enabling seamless multi-step operations
- **Session-Bound Functions**: Functions automatically include session context without exposing session_id to Gemini
- **Smart Side Effects**: Each function type has tailored side effects (current_bin updates, logging, etc.)
- **Comprehensive Retrieval**: Search and list functions return full item details including descriptions and images

---

## Item Schema

### Base Item Structure

The core item entity used throughout the system:

```json
{
  "id": "string (UUID)",
  "name": "string (required)",
  "description": "string (optional)",
  "bin_id": "string (required, alphanumeric)",
  "embedding": "vector (generated from name + description)",
  "created_at": "string (ISO datetime)",
  "updated_at": "string (ISO datetime)",
  "embedding_model": "string (e.g., 'openai')",
  "images": [
    {
      "image_id": "string",
      "is_primary": "boolean",
      "created_at": "string (ISO datetime)"
    }
  ]
}
```

### Item Input Schema (for adding items)

When adding items via function calls or API:

```json
{
  "name": "string (required, min length 1)",
  "description": "string (optional)",
  "image_id": "string (optional)"
}
```

### Item Response Schema (from search/list operations)

When retrieving items from search or list operations:

```json
{
  "id": "string (UUID)",
  "name": "string",
  "description": "string (may be empty)",
  "bin_id": "string",
  "created_at": "string (ISO datetime)",
  "updated_at": "string (ISO datetime)",
  "images": ["string (image_id)"],
  "primary_image": "string (image_id, optional)",
  "confidence_score": "number (for search results, 0.0-1.0)"
}
```

### Field Descriptions

- **id**: Unique identifier (UUID) generated by the system
- **name**: Human-readable item name (required, used for search and display)
- **description**: Optional detailed description (enhances search accuracy via embeddings)
- **bin_id**: Alphanumeric identifier for the storage bin (e.g., 'A3', 'TOOLS12', 'BIN-ELECTRONICS')
- **embedding**: Vector representation generated from name + description for semantic search
- **images**: Array of associated image IDs, supporting multiple images per item
- **primary_image**: The main/featured image for the item (optional)
- **confidence_score**: Relevance score for search results (0.0 = no match, 1.0 = perfect match)

---

## Data Model (Conceptual)

- **Item**
  - id (UUID), name, description (optional), bin_id, embedding (vector), created_at, embedding_model
  - images: [image_id] (multiple images supported, each item can have individual image associations)

- **Image**
  - image_id, path, metadata { item_id?, bin_id? }, created_at

- **Audit Log**
  - operation_id, type (add|remove|move), item_ids (array), bin_id(s), description, timestamp, metadata

---

## Implementation Notes

### Configuration Simplification
- **Eliminated config.yaml**: Replaced complex YAML configuration with simple environment variables
- **Direct imports**: Use `from config.settings import GEMINI_API_KEY` instead of complex configuration objects
- **Sensible defaults**: All configuration has reasonable defaults for local development
- **89% reduction**: Configuration system reduced from ~232 lines to ~26 lines

### API Schema Improvements
- **Optional image_id**: Item.image_id is optional since not all items have images
- **Simplified move operation**: Removed redundant source_bin_id from MoveItemsRequest (lookup from item_ids)
- **Minimal required fields**: Only require essential data, make everything else optional with defaults

### Chat Function System
- **Simplified function calling**: Direct Gemini function declarations without complex wrapper hierarchies
- **Session-bound operations**: Function wrappers automatically update session state (current_bin)
- **String responses**: Functions return simple string messages for natural LLM conversation flow
- **Minimal error handling**: Basic try/catch with user-friendly error messages
- **5 core functions**: add_items, search_items, get_bin_contents, move_items, remove_items

### Storage Mode Configuration
- **Dual storage modes**: `STORAGE_MODE=memory` for testing, `STORAGE_MODE=persistent` for production
- **In-memory database**: ChromaDB uses `chromadb.Client()` for clean test isolation
- **In-memory images**: Images stored as byte arrays in memory dictionary
- **Clean test state**: Each test run starts with empty database and image storage
- **No cleanup required**: Memory storage automatically cleared between test runs

### Embedding Consistency Fix
- **Single dimension source**: `EMBEDDING_DIMENSION=768` constant in config/embeddings.py
- **Consistent embedding service**: Search uses same Gemini embedding service as storage
- **ChromaDB collection metadata**: Specifies dimension to prevent mismatches
- **Fixed search method**: Uses `query_embeddings` instead of `query_texts` for consistency

### Semantic Search Quality Control
- **Distance-based filtering**: `max_distance` parameter filters results by similarity threshold
- **Optimal thresholds**: Strict (0.5), Balanced (0.7), Loose (1.0) based on empirical testing
- **Quality metrics**: Distance 0.28-0.49 for relevant items, 0.40-0.79 for irrelevant items
- **Confidence scoring**: `confidence_score = 1.0 - distance` for user-friendly relevance indication

### Test Organization
- **Simple structure**: `test/unit/`, `test/integration/`, `test/analysis/` directories
- **Unit tests**: Individual component testing (config, database, session, etc.)
- **Integration tests**: Multi-component workflow testing with in-memory storage
- **Analysis tests**: Research scripts for parameter tuning and system analysis
- **Test runner**: `python test/run_tests.py [quick|unit|integration|analysis|all]`

### Image Analysis Testing
- **Complete workflow test**: `test/integration/test_image_analysis.py` - Full pipeline from upload to inventory
- **Basic vision test**: `test/integration/test_vision_basic.py` - Core image analysis functionality
- **Real image testing**: Uses `test/coaster_pen_mouse.jpg` for consistent validation
- **Vision service methods**: `analyze_image()` for general analysis, `analyze_image_for_items()` for structured extraction

### Camera Support Testing
- **Complete camera workflow**: `test_camera_complete_workflow.html` - Comprehensive camera functionality validation
- **Camera permissions**: `test_camera_permissions.html` - getUserMedia API and permission handling
- **Live camera preview**: `test_camera_preview.html` - Video feed and capture controls
- **Camera-first behavior**: `test_camera_first_behavior.html` - Direct camera access validation
- **PNG upload fix**: `test_png_upload_complete.html` - RGBA to RGB conversion testing
- **Browser compatibility**: Tests across Chrome, Firefox, Safari, and mobile browsers
- **Mobile responsiveness**: Touch interface and front/back camera switching validation

### Structured Vision Output
- **JSON Schema Support**: Uses Gemini's `response_mime_type="application/json"` with defined schemas
- **Reliable Parsing**: Direct JSON response from API - no text parsing needed
- **Simple Implementation**: No fallback mechanisms - structured output only
- **Item Schema**: Predefined schema for inventory items with name/description fields
- **Simplified Interface**: Context parameter removed for cleaner, more focused analysis

### Chat Function Integration
- **Session-bound functions**: Function wrappers automatically bound to user sessions
- **Automatic execution**: Gemini AUTO mode for seamless function calling
- **5 core functions**: add_items, search_items, get_bin_contents, move_items, remove_items
- **Function mapping**: Direct mapping between LLM function names and wrapper methods
- **Conversation management**: Session-based conversation history with automatic message tracking

### API Endpoints Implementation
- **Health endpoint**: `api/health.py` - Simple health check returning `{"status": "ok"}`
- **Session endpoints**: `api/session.py` - Create, retrieve, and end sessions with secure cookie handling
- **Inventory endpoints**: `api/inventory.py` - Add, remove, move, search, and list items with session binding
- **Image endpoints**: `api/images.py` - Upload, analyze, and serve images with vision integration
- **Chat endpoints**: `api/chat.py` - LLM chat with function calling and image analysis
- **FastAPI app**: `app.py` - Application setup with CORS, router mounting, and static file serving
- **Cookie security**: HTTP-only, secure, SameSite=strict cookies with 30-minute TTL
- **Session validation**: Automatic expiration checking and cleanup
- **Comprehensive testing**: Unit tests for all API endpoints with direct function testing

### Implementation Status
**✅ Completed (Tasks 1-13):**
- Core backend infrastructure (config, database, session management)
- LLM integration with Gemini (client, embeddings, vision)
- Image storage and processing system
- Complete API layer (health, session, inventory, images, chat)
- Function calling system with session binding
- Comprehensive test suite (unit and integration tests)
- FastAPI application with CORS and static file serving
- CLI Frontend interface with session management and image upload support

**✅ Task 14 Complete:**
- **CLI Frontend**: `frontend/cli.py` - Text-based command-line interface
  - Session management with automatic setup/teardown
  - Text commands via `/api/chat/command` endpoint
  - Image upload via `/api/chat/image` endpoint with `/upload <path>` command
  - CLI commands use "/" prefix (`/help`, `/upload`, `/quit`)
  - Natural language commands pass through to BinBot
  - Interactive help system and error handling
  - Configurable API server URL

**✅ Task 15 Complete:**
- **Web Frontend with Camera Support**: `frontend/` - Complete web application
  - **Camera Support Implementation**: Full camera functionality with live preview and capture
    - Camera permissions handling with getUserMedia API
    - Live camera preview with full-screen modal interface
    - Canvas-based photo capture with high-quality JPEG output
    - Camera device selection and switching (front/back cameras)
    - Seamless integration with existing chat and upload workflow
  - **PNG Upload Fix**: RGBA to RGB conversion for PNG files with transparency
  - **Camera-First UX**: Direct camera access with file upload as secondary option
  - **Mobile Responsive**: Touch-friendly interface optimized for mobile devices
  - **Comprehensive Testing**: Complete test suite with browser compatibility validation

  - **Voice Input Support Implementation**: Complete conversational voice input functionality
    - VoiceManager class with Web Speech API integration and microphone permissions
    - Conversational speech recognition with real-time transcript updates
    - Automatic message sending when user pauses speaking (interim/final results)
    - Simple toggle UI with microphone button and visual listening feedback
    - Browser compatibility detection and basic error handling
    - Comprehensive test suite for voice functionality validation

## 🧪 Voice Input Testing Instructions

### Testing the Voice Input Feature:

1. **Start the BinBot server**: `uvicorn main:app --reload --host 0.0.0.0 --port 8001`

2. **Open the main application**: Navigate to `http://localhost:8001`

3. **Test voice input in the main app**:
   - Click the 🎤 microphone button next to the camera button
   - Allow microphone permissions when prompted
   - Speak naturally - your words will appear in the input field in real-time
   - When you pause, your message will automatically be sent to the chat
   - Click the microphone button again to stop voice input

4. **Use the dedicated test page**: Open `test_voice_input.html` in your browser
   - Tests browser support detection
   - Tests microphone permission handling
   - Tests speech recognition with live transcript display
   - Tests final result processing and error handling

### Browser Compatibility:
- **Chrome/Edge**: Full support (recommended)
- **Firefox**: Limited support (may require manual configuration)
- **Safari**: Partial support (iOS Safari has restrictions)
- **Mobile browsers**: Variable support depending on device and OS

### Expected Behavior:
- **Conversational flow**: Speak naturally, pause, and your message is sent automatically
- **Real-time feedback**: See your words appear in the input field as you speak
- **Visual indicators**: Microphone button changes color when listening
- **Error handling**: Clear error messages for permission denied or unsupported browsers

**🚧 Remaining (Task 16):**
- Voice Output Support (text-to-speech and audio feedback)
- UX Improvements (animations, keyboard shortcuts, settings panel)

## Non-Functional Requirements

- **Performance**: Use bulk adds and batched embeddings; avoid fetching all items where not needed.
- **Reliability**: Audit logged mutations; clear error messaging in NLP formatting for the UI.
- **UX**: Single-page UI; always show last active/current bin; camera-first interface with live preview and capture.
- **Deployability**: Dockerized; compose file for local dev; environment-based config. 

---

## Open Proposals / Enhancements

- Enhanced Gemini function validation: Leverage Gemini's native schema validation for stricter parameter checking.
- `api/session`: Consider endpoint to set/get current_bin directly for UI affordance.
- Pagination/limits: Apply to search and list_bin for large inventories.
- Gemini multimodal: Current architecture uses Gemini Vision for automatic image analysis on upload.
- Context-aware analysis: Enhance image analysis with bin location context for better item identification.
- Image cleanup: Consider automatic cleanup of unused images (images not associated with any items).
- Session persistence: Consider Redis backend for session store if horizontal scaling needed.
- Session security: Implement session rotation for sensitive operations.
- Memory management: Add LRU eviction if session memory usage becomes an issue.

If you'd like, I can extend this spec with exact endpoint signatures (Pydantic models) from api_schemas.py and verify real function names in each api/*.py module.
