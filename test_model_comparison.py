#!/usr/bin/env python3
"""
OpenAI Model Comparison Test for Image Analysis
Tests different models for speed vs accuracy trade-offs
"""

import os
import time
import json
import base64
from openai import OpenAI
from datetime import datetime
import google.generativeai as genai
from PIL import Image
import io

def encode_image_to_base64(image_path):
    """Convert image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def load_image_for_gemini(image_path):
    """Load image for Gemini API"""
    return Image.open(image_path)

def test_openai_model(client, model_name, base64_image, prompt, max_completion_tokens=500):
    """Test a specific model and return timing + response data"""
    
    print(f"\n{'='*60}")
    print(f"🧪 TESTING MODEL: {model_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_completion_tokens=max_completion_tokens,
            response_format={"type": "json_object"}
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Extract response content
        print(response)
        content = response.choices[0].message.content
        
        # Try to parse JSON to validate format
        try:
            parsed_json = json.loads(content)
            json_valid = True
        except json.JSONDecodeError as e:
            parsed_json = {"error": f"Invalid JSON: {str(e)}"}
            json_valid = False
        
        # Calculate tokens used
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else "N/A"
        completion_tokens = usage.completion_tokens if usage else "N/A"
        total_tokens = usage.total_tokens if usage else "N/A"
        
        print(f"⏱️  **TIMING**: {duration:.3f} seconds")
        print(f"🔢 **TOKENS**: Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
        print(f"✅ **JSON VALID**: {json_valid}")
        print(f"📝 **RESPONSE LENGTH**: {len(content)} characters")
        
        if json_valid:
            items_count = len(parsed_json.get('items', []))
            print(f"📦 **ITEMS DETECTED**: {items_count}")
        
        print(f"\n📄 **FULL RESPONSE**:")
        print("-" * 40)
        
        if json_valid:
            # Pretty print the JSON
            print(json.dumps(parsed_json, indent=2))
        else:
            # Print raw response if JSON is invalid
            print(content)
        
        return {
            "model": model_name,
            "duration": duration,
            "json_valid": json_valid,
            "response": content,
            "parsed_response": parsed_json,
            "tokens": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": total_tokens
            },
            "success": True
        }
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"❌ **ERROR**: {str(e)}")
        print(f"⏱️  **TIME BEFORE ERROR**: {duration:.3f} seconds")
        
        return {
            "model": model_name,
            "duration": duration,
            "error": str(e),
            "success": False
        }

def test_gemini_model(model_name, image, prompt, max_tokens=500):
    """Test a Gemini model and return timing + response data"""

    print(f"\n{'='*60}")
    print(f"🧪 TESTING GEMINI MODEL: {model_name}")
    print(f"{'='*60}")

    start_time = time.time()

    try:
        # Initialize Gemini model
        model = genai.GenerativeModel(model_name)

        # Define the expected JSON schema
        response_schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "item_name": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["item_name", "description"]
                    }
                },
                "total_items": {"type": "integer"},
                "analysis_notes": {"type": "string"}
            },
            "required": ["items", "total_items", "analysis_notes"]
        }

        # Generate response with JSON format enforcement
        response = model.generate_content(
            [prompt, image],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                max_output_tokens=max_tokens
            )
        )

        end_time = time.time()
        duration = end_time - start_time

        # Extract response content
        content = response.text.strip()

        # Try to parse JSON to validate format
        try:
            parsed_json = json.loads(content)
            json_valid = True
        except json.JSONDecodeError as e:
            parsed_json = {"error": f"Invalid JSON: {str(e)}"}
            json_valid = False

        # Gemini doesn't provide token usage in the same way
        prompt_tokens = "N/A"
        completion_tokens = "N/A"
        total_tokens = "N/A"

        print(f"⏱️  **TIMING**: {duration:.3f} seconds")
        print(f"🔢 **TOKENS**: Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
        print(f"✅ **JSON VALID**: {json_valid}")
        print(f"📝 **RESPONSE LENGTH**: {len(content)} characters")

        if json_valid:
            items_count = len(parsed_json.get('items', []))
            print(f"📦 **ITEMS DETECTED**: {items_count}")

        print(f"\n📄 **FULL RESPONSE**:")
        print("-" * 40)

        if json_valid:
            # Pretty print the JSON
            print(json.dumps(parsed_json, indent=2))
        else:
            # Print raw response if JSON is invalid
            print(content)

        return {
            "model": model_name,
            "duration": duration,
            "json_valid": json_valid,
            "response": content,
            "parsed_response": parsed_json,
            "tokens": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": total_tokens
            },
            "success": True
        }

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time

        print(f"❌ **ERROR**: {str(e)}")
        print(f"⏱️  **TIME BEFORE ERROR**: {duration:.3f} seconds")

        return {
            "model": model_name,
            "duration": duration,
            "error": str(e),
            "success": False
        }

def main():
    """Main function to run model comparison tests"""
    
    print("🔬 OPENAI MODEL COMPARISON TEST")
    print("=" * 80)
    print("Testing different OpenAI models for image analysis speed vs accuracy")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check for API keys
    openai_api_key = os.getenv('OPENAI_API_KEY')
    gemini_api_key = os.getenv('GEMINI_API_KEY')

    if not openai_api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        return

    if not gemini_api_key:
        print("⚠️  Warning: GEMINI_API_KEY not set, skipping Gemini models")
        test_gemini = False
    else:
        test_gemini = True
        genai.configure(api_key=gemini_api_key)

    # Initialize OpenAI client
    client = OpenAI(api_key=openai_api_key)
    
    # Test image path
    image_path = 'test/coaster_pen_mouse.jpg'
    if not os.path.exists(image_path):
        print(f"❌ Error: Test image not found at {image_path}")
        return
    
    print(f"📸 Using test image: {image_path}")
    
    # Encode image for OpenAI and load for Gemini
    try:
        base64_image = encode_image_to_base64(image_path)
        image_size_kb = len(base64_image) * 3 / 4 / 1024  # Approximate KB
        print(f"📏 Image size: ~{image_size_kb:.1f} KB (base64 encoded)")

        if test_gemini:
            gemini_image = load_image_for_gemini(image_path)
    except Exception as e:
        print(f"❌ Error loading image: {e}")
        return
    
    # Test prompt (simplified since schema handles structure)
    prompt = """Analyze this image and identify ALL distinct items shown. For each item, provide a specific name and detailed description of observable features including colors, materials, brand markings, unique characteristics, condition, wear patterns, text/logos, and size. Focus on what you can actually see rather than generic explanations. Also provide overall observations about the image."""
    
    # Models to test
    openai_models = [
        #"gpt-5",      
        #"gpt-5-mini",      
        "gpt-5-nano",      
    ]

    gemini_models = [
        # "gemini-2.5-flash",     
        "gemini-2.5-flash-lite",       
        # "gemini-2.5-pro"
    ] if test_gemini else []

    all_models = openai_models + gemini_models

    print(f"🎯 Testing {len(all_models)} models:")
    for i, model in enumerate(all_models, 1):
        model_type = "OpenAI" if model.startswith("gpt") else "Gemini"
        print(f"   {i}. {model} ({model_type})")
    print()

    # Run tests
    results = []

    for i, model in enumerate(all_models):
        if model.startswith("gpt"):
            # OpenAI model
            result = test_openai_model(client, model, base64_image, prompt, max_completion_tokens=3000)
        else:
            # Gemini model
            result = test_gemini_model(model, gemini_image, prompt, max_tokens=500)

        results.append(result)

        # Add a small delay between tests
        if i < len(all_models) - 1:  # Not the last model
            print(f"\n⏳ Waiting 2 seconds before next test...")
            time.sleep(2)
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 SUMMARY COMPARISON")
    print(f"{'='*80}")
    
    print(f"{'Model':<15} {'Time (s)':<10} {'JSON Valid':<12} {'Items Found':<12} {'Status':<10}")
    print("-" * 70)
    
    for result in results:
        if result['success']:
            items_count = len(result['parsed_response'].get('items', [])) if result.get('json_valid') else 'N/A'
            status = "✅ Success"
        else:
            items_count = 'N/A'
            status = "❌ Error"
        
        json_status = "✅ Yes" if result.get('json_valid') else "❌ No"
        
        print(f"{result['model']:<15} {result['duration']:<10.3f} {json_status:<12} {str(items_count):<12} {status:<10}")
    
    # Speed ranking
    successful_results = [r for r in results if r['success']]
    if successful_results:
        print(f"\n🏆 SPEED RANKING (fastest to slowest):")
        sorted_by_speed = sorted(successful_results, key=lambda x: x['duration'])
        for i, result in enumerate(sorted_by_speed, 1):
            print(f"   {i}. {result['model']}: {result['duration']:.3f}s")
    
    print(f"\n🎉 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
