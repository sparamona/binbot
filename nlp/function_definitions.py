"""
OpenAI Function Calling Definitions for BinBot Inventory System

This module defines the function schemas that OpenAI can call to perform
inventory operations instead of using explicit JSON parsing.
"""

from typing import List, Dict, Any

def get_inventory_functions() -> List[Dict[str, Any]]:
    """
    Get the list of function definitions for OpenAI function calling.
    
    Returns:
        List of function definitions in OpenAI's expected format
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "add_items_to_bin",
                "description": "Add one or more items to a specific bin in the inventory system",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of item names to add to the bin",
                            "minItems": 1
                        },
                        "bin_id": {
                            "type": "string",
                            "description": "The ID/number of the bin to add items to (e.g., '3', '5', '12')",
                            "pattern": "^[0-9]+$"
                        }
                    },
                    "required": ["items", "bin_id"],
                    "additionalProperties": False
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "remove_items_from_bin",
                "description": "Remove one or more items from a specific bin in the inventory system",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of item names to remove from the bin",
                            "minItems": 1
                        },
                        "bin_id": {
                            "type": "string",
                            "description": "The ID/number of the bin to remove items from (e.g., '3', '5', '12')",
                            "pattern": "^[0-9]+$"
                        }
                    },
                    "required": ["items", "bin_id"],
                    "additionalProperties": False
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "move_items_between_bins",
                "description": "Move one or more items from one bin to another bin",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of item names to move between bins",
                            "minItems": 1
                        },
                        "source_bin_id": {
                            "type": "string",
                            "description": "The ID/number of the bin to move items from (e.g., '3', '5', '12')",
                            "pattern": "^[0-9]+$"
                        },
                        "target_bin_id": {
                            "type": "string",
                            "description": "The ID/number of the bin to move items to (e.g., '3', '5', '12')",
                            "pattern": "^[0-9]+$"
                        }
                    },
                    "required": ["items", "source_bin_id", "target_bin_id"],
                    "additionalProperties": False
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_for_items",
                "description": "Search for items in the inventory system using semantic search",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find items (e.g., 'electronics', 'screws', 'tools')",
                            "minLength": 1
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 10)",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 10
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_bin_contents",
                "description": "List all items in a specific bin",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "bin_id": {
                            "type": "string",
                            "description": "The ID/number of the bin to list contents for (e.g., '3', '5', '12')",
                            "pattern": "^[0-9]+$"
                        }
                    },
                    "required": ["bin_id"],
                    "additionalProperties": False
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_items_from_image",
                "description": "Upload an image to a bin and automatically identify and add items from the image",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "bin_id": {
                            "type": "string",
                            "description": "The ID/number of the bin to add items to (e.g., '3', '5', '12')",
                            "pattern": "^[0-9]+$"
                        },
                        "image_description": {
                            "type": "string",
                            "description": "Description of what the user wants to add from the image (e.g., 'the screws in this image', 'these tools')"
                        }
                    },
                    "required": ["bin_id", "image_description"],
                    "additionalProperties": False
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_image",
                "description": "Analyze an image using AI vision to identify what item it shows",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_id": {
                            "type": "string",
                            "description": "The ID of the image to analyze"
                        },
                        "context": {
                            "type": "string",
                            "description": "Optional context about where the item is located (e.g., 'bin 3')"
                        }
                    },
                    "required": ["image_id"],
                    "additionalProperties": False
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_by_image",
                "description": "Generate search terms based on image content to find similar items",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_id": {
                            "type": "string",
                            "description": "The ID of the image to use for search"
                        },
                        "additional_query": {
                            "type": "string",
                            "description": "Optional additional search context or terms"
                        }
                    },
                    "required": ["image_id"],
                    "additionalProperties": False
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "describe_image",
                "description": "Get a detailed description of an image for accessibility or understanding",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_id": {
                            "type": "string",
                            "description": "The ID of the image to describe"
                        }
                    },
                    "required": ["image_id"],
                    "additionalProperties": False
                }
            }
        }
    ]

def get_function_by_name(function_name: str) -> Dict[str, Any]:
    """
    Get a specific function definition by name.
    
    Args:
        function_name: Name of the function to retrieve
        
    Returns:
        Function definition dict or None if not found
    """
    functions = get_inventory_functions()
    for func_def in functions:
        if func_def["function"]["name"] == function_name:
            return func_def
    return None

def get_all_function_names() -> List[str]:
    """
    Get a list of all available function names.
    
    Returns:
        List of function names
    """
    functions = get_inventory_functions()
    return [func_def["function"]["name"] for func_def in functions]
