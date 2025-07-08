from datasets import load_dataset
import json


def explore_methods2test():
    """Explore the andstor/methods2test dataset structure"""

    print("🔍 Exploring andstor/methods2test dataset...")

    try:
        # Load the dataset with the specific configuration
        print("📥 Loading dataset: andstor/methods2test with config 'fm+fc+c'")
        ds = load_dataset("andstor/methods2test", "fm+fc+c")

        print(f"✅ Dataset loaded successfully!")
        print(f"📊 Dataset info: {ds}")

        # Explore splits
        for split_name in ds.keys():
            split_data = ds[split_name]
            print(f"\n📋 Split: {split_name}")
            print(f"  Examples: {len(split_data)}")

            # Look at first example
            if len(split_data) > 0:
                example = split_data[0]
                print(f"  Example keys: {list(example.keys())}")

                # Print sample of each field
                for key, value in example.items():
                    if isinstance(value, str):
                        preview = value[:100] + "..." if len(value) > 100 else value
                        print(f"    {key}: {preview}")
                    else:
                        print(f"    {key}: {value}")

        return ds

    except Exception as e:
        print(f"❌ Error loading dataset: {e}")

        # Try alternative configurations
        configs_to_try = ["fm+fc", "fm", "all"]
        for config in configs_to_try:
            try:
                print(f"\n🔄 Trying config: {config}")
                ds = load_dataset("andstor/methods2test", config)
                print(f"✅ Success with config: {config}")
                return ds
            except Exception as alt_e:
                print(f"❌ Config {config} failed: {alt_e}")

        return None


def test_dataset_processing():
    """Test processing a few examples"""

    print("\n🧪 Testing dataset processing...")

    ds = explore_methods2test()
    if ds is None:
        print("❌ Could not load dataset")
        return False

    # Get a few examples from train split
    train_split = ds['train'] if 'train' in ds else list(ds.values())[0]

    # FIX: Use range to iterate by index instead of slicing
    num_examples = min(3, len(train_split))

    print(f"\n📝 Processing {num_examples} sample examples:")

    for i in range(num_examples):
        example = train_split[i]  # Get individual example by index
        print(f"\nExample {i + 1}:")
        print(f"  Example type: {type(example)}")  # Debug line

        # Extract method and test code
        method_code = (
                example.get('focal_method') or
                example.get('method') or
                example.get('source_method') or
                "NOT FOUND"
        )

        test_code = (
                example.get('test_method') or
                example.get('test') or
                example.get('target_test') or
                "NOT FOUND"
        )

        print(f"  Method code length: {len(method_code)} chars")
        print(f"  Test code length: {len(test_code)} chars")
        print(f"  Method preview: {method_code[:150]}...")
        print(f"  Test preview: {test_code[:150]}...")

        # Check for common Java patterns
        has_public = "public" in method_code
        has_test_annotation = "@Test" in test_code
        has_assert = "assert" in test_code.lower()

        print(f"  ✅ Valid Java method: {has_public}")
        print(f"  ✅ Has @Test annotation: {has_test_annotation}")
        print(f"  ✅ Has assertions: {has_assert}")

    return True


def save_sample_for_testing():
    """Save a small sample for testing DGM"""

    print("\n💾 Saving sample data for DGM testing...")

    ds = load_dataset("andstor/methods2test", "fm+fc+c")
    train_split = ds['train'] if 'train' in ds else list(ds.values())[0]

    # Take first 10 examples for testing
    sample_examples = []
    for i in range(min(10, len(train_split))):  # FIX: Use range instead of slicing
        example = train_split[i]  # Get individual example by index

        method_code = example.get('focal_method', '')
        test_code = example.get('test_method', '')

        if method_code and test_code:
            processed = {
                'id': str(i),
                'method_code': method_code,
                'test_code': test_code,
                'method_name': extract_method_name(method_code),
                'class_name': example.get('focal_class', 'UnknownClass'),
                'complexity': calculate_simple_complexity(method_code)
            }
            sample_examples.append(processed)

    # Save to file
    import os
    os.makedirs('data/methods2test', exist_ok=True)

    with open('data/methods2test/sample.json', 'w') as f:
        json.dump(sample_examples, f, indent=2)

    print(f"✅ Saved {len(sample_examples)} examples to data/methods2test/sample.json")
    return sample_examples


def extract_method_name(method_code):
    """Extract method name from Java code"""
    import re
    match = re.search(r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\(', method_code)
    return match.group(1) if match else "unknownMethod"


def calculate_simple_complexity(method_code):
    """Calculate simple complexity"""
    keywords = ['if', 'else', 'while', 'for', 'switch', 'case']
    complexity = 1 + sum(method_code.lower().count(kw) for kw in keywords)
    return min(complexity / 20.0, 1.0)


if __name__ == "__main__":
    print("🚀 Testing andstor/methods2test dataset")
    print("=" * 50)

    # Explore dataset
    if test_dataset_processing():
        # Save sample for DGM testing
        sample_examples = save_sample_for_testing()

        print(f"\n🎉 Dataset exploration complete!")
        print(f"📁 Sample saved for DGM testing")
        print(f"🚀 Ready to run full download with: python download_methods2test.py")
    else:
        print(f"\n❌ Dataset exploration failed")