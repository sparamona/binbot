"""
Simple function definitions for Gemini LLM function calling
"""

import google.generativeai as genai


def get_inventory_functions():
    """Get function definitions for inventory operations"""
    
    add_items_function = genai.protos.FunctionDeclaration(
        name="add_items",
        description="Add items to a specific bin",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "bin_id": genai.protos.Schema(type=genai.protos.Type.STRING, description="Bin identifier (e.g., A3, B1)"),
                "items": genai.protos.Schema(
                    type=genai.protos.Type.ARRAY,
                    items=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            "name": genai.protos.Schema(type=genai.protos.Type.STRING, description="Item name"),
                            "description": genai.protos.Schema(type=genai.protos.Type.STRING, description="Item description")
                        },
                        required=["name"]
                    )
                )
            },
            required=["bin_id", "items"]
        )
    )
    
    search_items_function = genai.protos.FunctionDeclaration(
        name="search_items",
        description="Search for items in the inventory",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "query": genai.protos.Schema(type=genai.protos.Type.STRING, description="Search query"),
                "limit": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="Maximum number of results")
            },
            required=["query"]
        )
    )
    
    get_bin_contents_function = genai.protos.FunctionDeclaration(
        name="get_bin_contents",
        description="Get all items in a specific bin",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "bin_id": genai.protos.Schema(type=genai.protos.Type.STRING, description="Bin identifier")
            },
            required=["bin_id"]
        )
    )
    
    move_items_function = genai.protos.FunctionDeclaration(
        name="move_items",
        description="Move items to a different bin",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "target_bin_id": genai.protos.Schema(type=genai.protos.Type.STRING, description="Target bin identifier"),
                "item_ids": genai.protos.Schema(
                    type=genai.protos.Type.ARRAY,
                    items=genai.protos.Schema(type=genai.protos.Type.STRING),
                    description="List of item IDs to move"
                )
            },
            required=["target_bin_id", "item_ids"]
        )
    )
    
    remove_items_function = genai.protos.FunctionDeclaration(
        name="remove_items",
        description="Remove items from inventory",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "item_ids": genai.protos.Schema(
                    type=genai.protos.Type.ARRAY,
                    items=genai.protos.Schema(type=genai.protos.Type.STRING),
                    description="List of item IDs to remove"
                )
            },
            required=["item_ids"]
        )
    )
    
    return [
        add_items_function,
        search_items_function,
        get_bin_contents_function,
        move_items_function,
        remove_items_function
    ]


def get_all_functions():
    """Get all function definitions for the LLM"""
    return get_inventory_functions()
