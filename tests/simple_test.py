import ollama


def test_ollama_connection():
    """Simple test to verify Ollama connection"""
    print("🔌 Testing Ollama connection...")

    try:
        client = ollama.Client()
        models = client.list()
        print(f"✅ Connected to Ollama. Available models: {len(models['models'])}")

        # Check if DeepSeek model is available
        model_names = [model['model'] for model in models['models']]
        if 'deepseek-r1:14b' in model_names:
            print("✅ DeepSeek model is available")
            return True
        else:
            print(f"❌ DeepSeek model not found. Available: {model_names}")
            return False

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def test_basic_generation():
    """Test basic text generation"""
    print("\n🤖 Testing basic generation...")

    try:
        client = ollama.Client()
        response = client.chat(
            model='deepseek-r1:14b',
            messages=[
                {'role': 'user', 'content': 'Say hello and introduce yourself briefly.'}
            ]
        )

        print(f"✅ Generation successful!")
        print(f"Response: {response['message']['content'][:200]}...")
        return True

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False


if __name__ == "__main__":
    if test_ollama_connection() and test_basic_generation():
        print("\n🎉 Basic tests passed! Ready for agent testing.")
    else:
        print("\n💥 Basic tests failed. Check Ollama setup.")