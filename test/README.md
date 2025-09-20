# BinBot Test Suite

Simple, organized test structure for BinBot development and validation.

## Test Organization

### 📁 `unit/` - Unit Tests
Tests for individual components in isolation.

- `test_config.py` - Configuration system tests
- `test_schemas.py` - API schema validation tests  
- `test_session.py` - Session management tests
- `test_chromadb.py` - Database client tests
- `test_image_storage.py` - Image storage tests
- `test_llm.py` - LLM integration tests
- `test_chat_functions.py` - Chat function system tests
- `test_chromadb_simple.py` - Simple ChromaDB tests
- `test_image_simple.py` - Simple image storage tests
- `test_simple_add.py` - Simple item addition tests

### 📁 `integration/` - Integration Tests
Tests that verify multiple components working together.

- `test_end_to_end.py` - Complete workflow tests (persistent storage)
- `test_end_to_end_memory.py` - Complete workflow tests (in-memory storage)
- `test_setup.py` - System setup and initialization tests
- `test_image_analysis.py` - Complete image analysis workflow (upload → analyze → extract → inventory)
- `test_vision_basic.py` - Basic vision service functionality tests

### 📁 `analysis/` - Analysis & Research
Scripts for analyzing system behavior and tuning parameters.

- `test_semantic_search_cutoff.py` - Comprehensive semantic search analysis
- `test_search_distances.py` - Distance threshold analysis
- `test_distance_filtering.py` - Distance filtering validation
- `test_embedding_dimension.py` - Embedding dimension verification

## Running Tests

### Quick Test Commands

```bash
# Run the main end-to-end test (recommended)
python test/integration/test_end_to_end_memory.py

# Run unit tests for specific components
python test/unit/test_chromadb.py
python test/unit/test_session.py

# Run analysis scripts
python test/analysis/test_search_distances.py
python test/analysis/test_distance_filtering.py
```

### Test Categories

**🚀 Start Here**: `test/integration/test_end_to_end_memory.py`
- Complete system validation
- Uses in-memory storage for clean testing
- Tests full workflow: add items → check bins → search

**🔧 Component Testing**: `test/unit/`
- Test individual components
- Fast execution
- Good for development and debugging

**📊 System Analysis**: `test/analysis/`
- Research and tuning scripts
- Performance analysis
- Parameter optimization

## Test Principles

- **Simple**: Each test focuses on one clear objective
- **Clean**: In-memory storage prevents test contamination
- **Fast**: Most tests complete in under 30 seconds
- **Informative**: Clear output showing what's being tested

## Storage Modes

All tests use `STORAGE_MODE=memory` for clean, isolated testing:
- No cleanup required between runs
- Consistent starting state
- No file system dependencies
- Faster execution

## Adding New Tests

1. **Unit tests** → `test/unit/test_[component].py`
2. **Integration tests** → `test/integration/test_[feature].py`  
3. **Analysis scripts** → `test/analysis/test_[analysis_type].py`

Keep tests simple, focused, and well-documented with clear output messages.
