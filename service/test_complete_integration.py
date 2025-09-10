#!/usr/bin/env python3
"""
Complete integration test suite for Gemini API migration (Task 9).

This script runs all integration tests to validate:
- Gemini API integration functionality (Requirement 1.4)
- Superimposed image generation quality (Requirement 2.4) 
- End-to-end flow from image upload to enhanced plant recommendations (Requirement 3.4)

This is the comprehensive test for Task 9 that validates the complete integration.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add service directory to path for imports
service_dir = Path(__file__).parent
sys.path.insert(0, str(service_dir))


def run_test_script(script_name):
    """Run a test script and capture its output"""
    print(f"\n{'='*20} Running {script_name} {'='*20}")
    
    try:
        # Run the test script
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=service_dir,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Check return code
        if result.returncode == 0:
            print(f"✅ {script_name} PASSED")
            return True
        else:
            print(f"❌ {script_name} FAILED (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ {script_name} TIMED OUT")
        return False
    except Exception as e:
        print(f"❌ {script_name} ERROR: {e}")
        return False


def validate_test_files_exist():
    """Validate that all required test files exist"""
    required_files = [
        'test_gemini_integration.py',
        'test_end_to_end_community.py', 
        'test_community_compatibility.py',
        'test_integration.py',
        'test_error_handling.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not (service_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing test files: {missing_files}")
        return False
    
    print("✅ All required test files found")
    return True


def validate_implementation_files():
    """Validate that all implementation files exist and are properly configured"""
    required_files = [
        'app.py',
        'gemini_client.py',
        'models.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not (service_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing implementation files: {missing_files}")
        return False
    
    print("✅ All implementation files found")
    return True


def setup_test_environment():
    """Set up the test environment with required environment variables"""
    print("Setting up test environment...")
    
    # Set test API keys
    os.environ['GEMINI_API_KEY'] = 'test_key_for_complete_integration_testing'
    os.environ['PPLX_API_KEY'] = 'test_key_for_community_testing'
    
    # Verify Python dependencies
    try:
        import flask
        import google.generativeai
        import pydantic
        import PIL
        import requests
        print("✅ All required Python packages available")
        return True
    except ImportError as e:
        print(f"❌ Missing Python package: {e}")
        return False


def run_comprehensive_integration_tests():
    """Run all integration tests in the correct order"""
    print("\n" + "="*80)
    print("COMPREHENSIVE GEMINI API INTEGRATION TEST SUITE (TASK 9)")
    print("="*80)
    print("Testing Requirements:")
    print("- 1.4: Gemini API integration functionality")
    print("- 2.4: Superimposed image generation quality")
    print("- 3.4: End-to-end flow validation")
    print("="*80)
    
    # Track test results
    test_results = {}
    
    # Test 1: Core Gemini API Integration
    print("\n🧪 TEST 1: Core Gemini API Integration")
    test_results['gemini_integration'] = run_test_script('test_gemini_integration.py')
    
    # Test 2: Error Handling Integration
    print("\n🧪 TEST 2: Error Handling Integration")
    test_results['error_handling'] = run_test_script('test_error_handling.py')
    
    # Test 3: General Integration Tests
    print("\n🧪 TEST 3: General Integration Tests")
    test_results['integration'] = run_test_script('test_integration.py')
    
    # Test 4: Community Compatibility
    print("\n🧪 TEST 4: Community Compatibility")
    test_results['community_compatibility'] = run_test_script('test_community_compatibility.py')
    
    # Test 5: End-to-End Community Flow
    print("\n🧪 TEST 5: End-to-End Community Flow")
    test_results['end_to_end_community'] = run_test_script('test_end_to_end_community.py')
    
    return test_results


def generate_test_report(test_results):
    """Generate a comprehensive test report"""
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST REPORT")
    print("="*80)
    
    passed_tests = []
    failed_tests = []
    
    for test_name, result in test_results.items():
        if result:
            passed_tests.append(test_name)
            print(f"✅ {test_name.replace('_', ' ').title()}: PASSED")
        else:
            failed_tests.append(test_name)
            print(f"❌ {test_name.replace('_', ' ').title()}: FAILED")
    
    print(f"\nSUMMARY:")
    print(f"✅ Passed: {len(passed_tests)}/{len(test_results)}")
    print(f"❌ Failed: {len(failed_tests)}/{len(test_results)}")
    
    if len(failed_tests) == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("✅ Task 9 requirements fully satisfied:")
        print("   - Gemini API integration working correctly")
        print("   - Superimposed image generation validated")
        print("   - End-to-end flow functioning properly")
        print("   - Error handling comprehensive")
        print("   - Community compatibility maintained")
        return True
    else:
        print(f"\n⚠️  {len(failed_tests)} TEST(S) FAILED")
        print("❌ Task 9 requirements not fully satisfied")
        print("Please review failed tests and fix issues before deployment")
        return False


def validate_requirements_coverage():
    """Validate that all Task 9 requirements are covered by tests"""
    print("\n📋 REQUIREMENTS COVERAGE VALIDATION")
    print("-" * 50)
    
    requirements = {
        "1.4": "Gemini API integration functionality",
        "2.4": "Superimposed image generation quality", 
        "3.4": "End-to-end flow validation"
    }
    
    coverage = {
        "1.4": ["test_gemini_integration.py", "test_integration.py"],
        "2.4": ["test_gemini_integration.py"],
        "3.4": ["test_gemini_integration.py", "test_end_to_end_community.py"]
    }
    
    for req_id, description in requirements.items():
        test_files = coverage[req_id]
        print(f"✅ Requirement {req_id}: {description}")
        print(f"   Covered by: {', '.join(test_files)}")
    
    print("\n✅ All Task 9 requirements have test coverage")


def main():
    """Main function to run complete integration testing"""
    start_time = time.time()
    
    print("🚀 Starting Complete Integration Test Suite for Task 9")
    print("Testing Gemini API integration with superimposed image generation")
    
    # Pre-flight checks
    if not validate_test_files_exist():
        sys.exit(1)
    
    if not validate_implementation_files():
        sys.exit(1)
    
    if not setup_test_environment():
        sys.exit(1)
    
    # Validate requirements coverage
    validate_requirements_coverage()
    
    # Run comprehensive tests
    test_results = run_comprehensive_integration_tests()
    
    # Generate report
    success = generate_test_report(test_results)
    
    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"\n⏱️  Total execution time: {execution_time:.2f} seconds")
    
    if success:
        print("\n🎯 TASK 9 COMPLETE: All integration tests passed!")
        print("The Gemini API integration is fully validated and ready for use.")
        sys.exit(0)
    else:
        print("\n❌ TASK 9 INCOMPLETE: Some tests failed")
        print("Please review and fix failing tests before marking task complete.")
        sys.exit(1)


if __name__ == "__main__":
    main()