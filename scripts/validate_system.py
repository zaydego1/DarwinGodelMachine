#!/usr/bin/env python3
"""
System Validation Script for DGM-Chess

This script validates that all components of the DGM-Chess system are
functioning correctly before starting evolution training.
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

def validate_imports() -> Tuple[bool, List[str]]:
    """Validate that all required modules can be imported"""
    
    validation_results = []
    all_passed = True
    
    try:
        # Core modules
        from llm import chat_with_model
        validation_results.append("✅ llm module imported successfully")
        
        from llm_withtools import chat_with_agent
        validation_results.append("✅ llm_withtools module imported successfully")
        
        # Chess tools
        from tools.chess_position import tool_function as chess_position_tool
        validation_results.append("✅ chess_position tool imported successfully")
        
        from tools.chess_moves import tool_function as chess_moves_tool
        validation_results.append("✅ chess_moves tool imported successfully")
        
        from tools.lichess_puzzle import tool_function as lichess_puzzle_tool
        validation_results.append("✅ lichess_puzzle tool imported successfully")
        
        # Core tools
        from tools.bash import tool_function as bash_tool
        validation_results.append("✅ bash tool imported successfully")
        
        from tools.edit import tool_function as edit_tool
        validation_results.append("✅ edit tool imported successfully")
        
        # Evolution components
        from chess_agent import ChessAgent
        validation_results.append("✅ ChessAgent imported successfully")
        
        from chess_self_improve import self_improve_agent
        validation_results.append("✅ chess_self_improve imported successfully")
        
        # Monitoring components
        from monitoring.dashboard import DGMChessMonitor
        validation_results.append("✅ DGMChessMonitor imported successfully")
        
        from monitoring.metrics_collector import MetricsCollector
        validation_results.append("✅ MetricsCollector imported successfully")
        
        # External libraries
        import chess
        import chess.engine
        validation_results.append("✅ python-chess library imported successfully")
        
        import psutil
        validation_results.append("✅ psutil library imported successfully")
        
    except Exception as e:
        validation_results.append(f"❌ Import error: {str(e)}")
        all_passed = False
    
    return all_passed, validation_results

def validate_tools() -> Tuple[bool, List[str]]:
    """Validate that all tools are functioning correctly"""
    
    validation_results = []
    all_passed = True
    
    try:
        # Test chess_position tool
        from tools.chess_position import tool_function as chess_position_tool
        result = chess_position_tool("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "basic")
        if isinstance(result, dict) and 'material_balance' in result:
            validation_results.append("✅ chess_position tool working correctly")
        else:
            validation_results.append("❌ chess_position tool returned unexpected result")
            all_passed = False
            
    except Exception as e:
        validation_results.append(f"❌ chess_position tool error: {str(e)}")
        all_passed = False
    
    try:
        # Test chess_moves tool
        from tools.chess_moves import tool_function as chess_moves_tool
        result = chess_moves_tool("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "e2e4", "validate")
        if isinstance(result, dict) and 'is_legal' in result:
            validation_results.append("✅ chess_moves tool working correctly")
        else:
            validation_results.append("❌ chess_moves tool returned unexpected result")
            all_passed = False
            
    except Exception as e:
        validation_results.append(f"❌ chess_moves tool error: {str(e)}")
        all_passed = False
    
    try:
        # Test bash tool (simple command)
        from tools.bash import tool_function as bash_tool
        result = bash_tool("echo 'test'")
        if isinstance(result, dict) and result.get('exit_code') == 0:
            validation_results.append("✅ bash tool working correctly")
        else:
            validation_results.append("❌ bash tool returned unexpected result")
            all_passed = False
            
    except Exception as e:
        validation_results.append(f"❌ bash tool error: {str(e)}")
        all_passed = False
    
    return all_passed, validation_results

def validate_model_access() -> Tuple[bool, List[str]]:
    """Validate that DeepSeek R1 model is accessible"""
    
    validation_results = []
    all_passed = True
    
    try:
        from llm import chat_with_model
        
        # Test basic model access
        response = chat_with_model(
            msg="Say 'Hello from DeepSeek R1' and nothing else.",
            model="deepseek-r1:14b",
            msg_history=[],
            system_message="You are a test assistant. Follow instructions exactly."
        )
        
        if response and "deepseek" in response.lower():
            validation_results.append("✅ DeepSeek R1 model accessible and responding")
        else:
            validation_results.append("🟡 DeepSeek R1 accessible but response unclear")
            
    except Exception as e:
        validation_results.append(f"❌ DeepSeek R1 model access error: {str(e)}")
        all_passed = False
    
    return all_passed, validation_results

def validate_enhanced_tool_system() -> Tuple[bool, List[str]]:
    """Validate that the enhanced tool integration system is working"""
    
    validation_results = []
    all_passed = True
    
    try:
        from llm_withtools import chat_with_agent
        
        # Test tool usage tracking
        tool_calls_made = []
        
        def tool_logging(message):
            if "TOOL_CALL:" in message:
                tool_calls_made.append(message)
        
        # Test with a simple chess analysis
        msg_history = chat_with_agent(
            msg="Analyze this chess position using the chess_position tool: rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
            model="deepseek-r1:14b",
            msg_history=[],
            logging=tool_logging
        )
        
        if tool_calls_made:
            validation_results.append("✅ Enhanced tool system working - tools were called")
        else:
            validation_results.append("🟡 Enhanced tool system accessible but no tools were used")
        
        if msg_history:
            validation_results.append("✅ Enhanced tool system returning conversation history")
        else:
            validation_results.append("❌ Enhanced tool system not returning conversation history")
            all_passed = False
            
    except Exception as e:
        validation_results.append(f"❌ Enhanced tool system error: {str(e)}")
        all_passed = False
    
    return all_passed, validation_results

def validate_directories() -> Tuple[bool, List[str]]:
    """Validate that required directories exist or can be created"""
    
    validation_results = []
    all_passed = True
    
    required_dirs = [
        "archive",
        "baselines", 
        "metrics",
        "monitoring",
        "scripts",
        "tools",
        "evaluation",
        "utils",
        "prompts"
    ]
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        try:
            dir_path.mkdir(exist_ok=True)
            if dir_path.exists():
                validation_results.append(f"✅ Directory '{dir_name}' exists/created successfully")
            else:
                validation_results.append(f"❌ Directory '{dir_name}' could not be created")
                all_passed = False
        except Exception as e:
            validation_results.append(f"❌ Directory '{dir_name}' error: {str(e)}")
            all_passed = False
    
    return all_passed, validation_results

def validate_system_resources() -> Tuple[bool, List[str]]:
    """Validate system has sufficient resources for evolution training"""
    
    validation_results = []
    all_passed = True
    
    try:
        import psutil
        
        # Check available memory
        memory = psutil.virtual_memory()
        total_gb = memory.total / (1024**3)
        available_gb = memory.available / (1024**3)
        
        validation_results.append(f"📊 Total RAM: {total_gb:.1f}GB")
        validation_results.append(f"📊 Available RAM: {available_gb:.1f}GB")
        
        if total_gb >= 40:
            validation_results.append("✅ Sufficient RAM for 2-3 parallel agents")
        elif total_gb >= 24:
            validation_results.append("🟡 RAM suitable for 1-2 parallel agents")
        else:
            validation_results.append("❌ Insufficient RAM for evolution training")
            all_passed = False
        
        # Check available disk space
        disk = psutil.disk_usage('.')
        free_gb = disk.free / (1024**3)
        
        validation_results.append(f"📊 Available disk space: {free_gb:.1f}GB")
        
        if free_gb >= 50:
            validation_results.append("✅ Sufficient disk space for evolution data")
        elif free_gb >= 20:
            validation_results.append("🟡 Adequate disk space for evolution data")
        else:
            validation_results.append("❌ Insufficient disk space for evolution training")
            all_passed = False
        
        # Check CPU cores
        cpu_count = psutil.cpu_count()
        validation_results.append(f"📊 CPU cores: {cpu_count}")
        
        if cpu_count >= 8:
            validation_results.append("✅ Excellent CPU capacity for parallel processing")
        elif cpu_count >= 4:
            validation_results.append("🟡 Good CPU capacity for parallel processing")
        else:
            validation_results.append("❌ Limited CPU capacity - may affect performance")
            # Don't fail on this, just warn
        
    except Exception as e:
        validation_results.append(f"❌ System resource check error: {str(e)}")
        all_passed = False
    
    return all_passed, validation_results

def validate_quick_chess_analysis() -> Tuple[bool, List[str]]:
    """Validate that the system can perform basic chess analysis"""
    
    validation_results = []
    all_passed = True
    
    try:
        from llm_withtools import chat_with_agent
        
        # Test with a simple chess puzzle
        test_fen = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4"
        
        msg_history = chat_with_agent(
            msg=f"Analyze this chess position and suggest the best move: {test_fen}. Use the chess_position tool to help with your analysis.",
            model="deepseek-r1:14b",
            msg_history=[],
            logging=lambda x: None  # Suppress logging for validation
        )
        
        if msg_history and len(msg_history) > 0:
            response = msg_history[-1].get('content', '')
            
            # Check if response contains chess analysis
            chess_keywords = ['move', 'position', 'chess', 'piece', 'attack', 'defense']
            if any(keyword in response.lower() for keyword in chess_keywords):
                validation_results.append("✅ System can perform chess analysis")
            else:
                validation_results.append("🟡 System responds but chess analysis unclear")
        else:
            validation_results.append("❌ System did not provide chess analysis")
            all_passed = False
            
    except Exception as e:
        validation_results.append(f"❌ Chess analysis validation error: {str(e)}")
        all_passed = False
    
    return all_passed, validation_results

def run_full_validation() -> Dict:
    """Run complete system validation"""
    
    print("🔍 DGM-Chess System Validation")
    print("="*80)
    
    start_time = datetime.now()
    validation_report = {
        'validation_start': start_time.isoformat(),
        'tests_run': {},
        'overall_status': 'UNKNOWN',
        'ready_for_training': False
    }
    
    # Run all validation tests
    tests = [
        ("Import Validation", validate_imports),
        ("Tool Validation", validate_tools),
        ("Model Access", validate_model_access),
        ("Enhanced Tool System", validate_enhanced_tool_system),
        ("Directory Structure", validate_directories),
        ("System Resources", validate_system_resources),
        ("Chess Analysis", validate_quick_chess_analysis)
    ]
    
    all_tests_passed = True
    
    for test_name, test_function in tests:
        print(f"\n🧪 Running {test_name}...")
        
        try:
            passed, results = test_function()
            
            validation_report['tests_run'][test_name] = {
                'passed': passed,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
            # Print results
            for result in results:
                print(f"  {result}")
            
            if not passed:
                all_tests_passed = False
                print(f"  ❌ {test_name} FAILED")
            else:
                print(f"  ✅ {test_name} PASSED")
                
        except Exception as e:
            print(f"  ❌ {test_name} ERROR: {str(e)}")
            validation_report['tests_run'][test_name] = {
                'passed': False,
                'results': [f"Test error: {str(e)}"],
                'timestamp': datetime.now().isoformat()
            }
            all_tests_passed = False
    
    # Final status
    end_time = datetime.now()
    validation_report['validation_end'] = end_time.isoformat()
    validation_report['duration_seconds'] = (end_time - start_time).total_seconds()
    
    if all_tests_passed:
        validation_report['overall_status'] = 'PASSED'
        validation_report['ready_for_training'] = True
        print("\n" + "="*80)
        print("🎉 SYSTEM VALIDATION PASSED")
        print("✅ All components are functioning correctly")
        print("🚀 System is ready for evolution training!")
    else:
        validation_report['overall_status'] = 'FAILED'
        validation_report['ready_for_training'] = False
        print("\n" + "="*80)
        print("❌ SYSTEM VALIDATION FAILED")
        print("🔧 Please address the issues above before starting training")
    
    print("="*80)
    
    # Save validation report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = Path("baselines") / f"system_validation_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(validation_report, f, indent=2, default=str)
    
    print(f"📄 Validation report saved to: {report_file}")
    
    return validation_report

def main():
    """Main function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate DGM-Chess System")
    parser.add_argument('--quick', action='store_true', help='Run quick validation (skip detailed tests)')
    
    args = parser.parse_args()
    
    if args.quick:
        print("⚡ Running quick validation...")
        # Just run import and directory validation for speed
        tests = [validate_imports, validate_directories]
        all_passed = True
        
        for test_func in tests:
            passed, results = test_func()
            for result in results:
                print(result)
            if not passed:
                all_passed = False
        
        if all_passed:
            print("✅ Quick validation passed")
        else:
            print("❌ Quick validation failed")
    else:
        # Run full validation
        validation_report = run_full_validation()
        
        if validation_report['ready_for_training']:
            print("\n🎯 NEXT STEPS:")
            print("1. Run baseline collection: python scripts/collect_baseline_base.py")
            print("2. Run enhanced tools baseline: python scripts/collect_baseline_tools.py")
            print("3. Start evolution training: python chess_dgm_outer.py")
        else:
            print("\n🔧 REQUIRED ACTIONS:")
            print("Fix the validation issues above before proceeding.")

if __name__ == "__main__":
    main()
