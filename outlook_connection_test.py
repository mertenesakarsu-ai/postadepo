#!/usr/bin/env python3
"""
Outlook Account Connection Test - Focused Test for tyrzmusak@gmail.com user
Testing /api/outlook/connect-account endpoint response format issues
"""

import requests
import json
import sys
from datetime import datetime

class OutlookConnectionTester:
    def __init__(self, base_url="https://auth-system-repair-3.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user = None
        self.test_results = []

    def log_test(self, test_name, success, details):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {test_name}")
        print(f"Details: {details}")
        return success

    def login_tyrz_user(self):
        """Login as tyrzmusak@gmail.com user"""
        print("🔐 Logging in as tyrzmusak@gmail.com...")
        
        try:
            url = f"{self.base_url}/auth/login"
            data = {
                "email": "tyrzmusak@gmail.com",
                "password": "deneme123"
            }
            
            response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                response_data = response.json()
                self.token = response_data.get('token')
                self.user = response_data.get('user')
                
                return self.log_test(
                    "Tyrz User Login",
                    True,
                    f"Successfully logged in as {self.user.get('email')} with user_id: {self.user.get('id')}"
                )
            else:
                return self.log_test(
                    "Tyrz User Login",
                    False,
                    f"Login failed with status {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            return self.log_test(
                "Tyrz User Login",
                False,
                f"Login exception: {str(e)}"
            )

    def test_outlook_status_endpoint(self):
        """Test /api/outlook/status endpoint"""
        print("📊 Testing Outlook status endpoint...")
        
        try:
            url = f"{self.base_url}/outlook/status"
            headers = {'Authorization': f'Bearer {self.token}'}
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Check response structure
                details = {
                    "status_code": response.status_code,
                    "response_keys": list(response_data.keys()),
                    "credentials_configured": response_data.get('credentials_configured'),
                    "message": response_data.get('message'),
                    "response_type": type(response_data).__name__
                }
                
                return self.log_test(
                    "Outlook Status Endpoint",
                    True,
                    json.dumps(details, indent=2)
                )
            else:
                return self.log_test(
                    "Outlook Status Endpoint",
                    False,
                    f"Status check failed with {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            return self.log_test(
                "Outlook Status Endpoint",
                False,
                f"Status check exception: {str(e)}"
            )

    def test_outlook_connect_with_valid_code(self):
        """Test /api/outlook/connect-account with valid-looking code and state"""
        print("🔗 Testing Outlook connect-account with valid code format...")
        
        try:
            url = f"{self.base_url}/outlook/connect-account"
            headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
            
            # Use realistic looking OAuth2 code and state
            data = {
                "code": "M.C507_BAY.2.U.12345678-1234-1234-1234-123456789abc.1234567890abcdef1234567890abcdef12345678",
                "state": "test-state-12345-67890-abcdef"
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            # Analyze response structure regardless of success/failure
            response_analysis = {
                "status_code": response.status_code,
                "content_type": response.headers.get('Content-Type', 'unknown'),
                "response_length": len(response.text)
            }
            
            try:
                response_data = response.json()
                response_analysis["response_type"] = type(response_data).__name__
                response_analysis["response_keys"] = list(response_data.keys()) if isinstance(response_data, dict) else "not_dict"
                
                # Check detail field specifically
                if "detail" in response_data:
                    detail_value = response_data["detail"]
                    response_analysis["detail_field"] = {
                        "type": type(detail_value).__name__,
                        "value": detail_value,
                        "is_string": isinstance(detail_value, str),
                        "is_object": isinstance(detail_value, dict),
                        "is_list": isinstance(detail_value, list)
                    }
                
                # Check message field
                if "message" in response_data:
                    message_value = response_data["message"]
                    response_analysis["message_field"] = {
                        "type": type(message_value).__name__,
                        "value": message_value,
                        "is_string": isinstance(message_value, str)
                    }
                
                response_analysis["full_response"] = response_data
                
            except json.JSONDecodeError:
                response_analysis["response_type"] = "invalid_json"
                response_analysis["raw_response"] = response.text[:500]
            
            # This test focuses on response format, not success
            return self.log_test(
                "Outlook Connect Valid Code Format",
                True,  # Always pass since we're analyzing format
                json.dumps(response_analysis, indent=2, default=str)
            )
            
        except Exception as e:
            return self.log_test(
                "Outlook Connect Valid Code Format",
                False,
                f"Connect test exception: {str(e)}"
            )

    def test_outlook_connect_with_invalid_code(self):
        """Test /api/outlook/connect-account with invalid code to check error response format"""
        print("❌ Testing Outlook connect-account with invalid code...")
        
        try:
            url = f"{self.base_url}/outlook/connect-account"
            headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
            
            # Use invalid code to trigger error response
            data = {
                "code": "invalid-code-123",
                "state": "invalid-state-456"
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            # Analyze error response structure
            error_analysis = {
                "status_code": response.status_code,
                "content_type": response.headers.get('Content-Type', 'unknown'),
                "response_length": len(response.text)
            }
            
            try:
                response_data = response.json()
                error_analysis["response_type"] = type(response_data).__name__
                error_analysis["response_keys"] = list(response_data.keys()) if isinstance(response_data, dict) else "not_dict"
                
                # Focus on detail field for error responses
                if "detail" in response_data:
                    detail_value = response_data["detail"]
                    error_analysis["detail_field"] = {
                        "type": type(detail_value).__name__,
                        "value": detail_value,
                        "is_string": isinstance(detail_value, str),
                        "is_object": isinstance(detail_value, dict),
                        "is_list": isinstance(detail_value, list),
                        "length": len(str(detail_value))
                    }
                    
                    # Check if detail contains nested objects that could cause React render issues
                    if isinstance(detail_value, dict):
                        error_analysis["detail_nested_analysis"] = {
                            "nested_keys": list(detail_value.keys()),
                            "nested_values_types": {k: type(v).__name__ for k, v in detail_value.items()}
                        }
                
                error_analysis["full_response"] = response_data
                
            except json.JSONDecodeError:
                error_analysis["response_type"] = "invalid_json"
                error_analysis["raw_response"] = response.text[:500]
            
            return self.log_test(
                "Outlook Connect Invalid Code Error Format",
                True,  # Always pass since we're analyzing error format
                json.dumps(error_analysis, indent=2, default=str)
            )
            
        except Exception as e:
            return self.log_test(
                "Outlook Connect Invalid Code Error Format",
                False,
                f"Error test exception: {str(e)}"
            )

    def test_outlook_connect_missing_parameters(self):
        """Test /api/outlook/connect-account with missing parameters"""
        print("🚫 Testing Outlook connect-account with missing parameters...")
        
        test_cases = [
            {"name": "Missing Code", "data": {"state": "test-state"}},
            {"name": "Missing State", "data": {"code": "test-code"}},
            {"name": "Empty Code", "data": {"code": "", "state": "test-state"}},
            {"name": "Empty State", "data": {"code": "test-code", "state": ""}},
            {"name": "No Parameters", "data": {}}
        ]
        
        results = []
        
        for test_case in test_cases:
            try:
                url = f"{self.base_url}/outlook/connect-account"
                headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
                
                response = requests.post(url, json=test_case["data"], headers=headers)
                
                case_analysis = {
                    "test_case": test_case["name"],
                    "status_code": response.status_code,
                    "content_type": response.headers.get('Content-Type', 'unknown')
                }
                
                try:
                    response_data = response.json()
                    case_analysis["response_type"] = type(response_data).__name__
                    
                    if "detail" in response_data:
                        detail_value = response_data["detail"]
                        case_analysis["detail_field"] = {
                            "type": type(detail_value).__name__,
                            "value": detail_value,
                            "is_string": isinstance(detail_value, str)
                        }
                    
                    case_analysis["full_response"] = response_data
                    
                except json.JSONDecodeError:
                    case_analysis["response_type"] = "invalid_json"
                    case_analysis["raw_response"] = response.text[:200]
                
                results.append(case_analysis)
                
            except Exception as e:
                results.append({
                    "test_case": test_case["name"],
                    "error": str(e)
                })
        
        return self.log_test(
            "Outlook Connect Missing Parameters",
            True,  # Always pass since we're analyzing response formats
            json.dumps(results, indent=2, default=str)
        )

    def test_outlook_connect_unauthorized(self):
        """Test /api/outlook/connect-account without authorization"""
        print("🔒 Testing Outlook connect-account without authorization...")
        
        try:
            url = f"{self.base_url}/outlook/connect-account"
            headers = {'Content-Type': 'application/json'}  # No Authorization header
            
            data = {
                "code": "test-code",
                "state": "test-state"
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            auth_analysis = {
                "status_code": response.status_code,
                "content_type": response.headers.get('Content-Type', 'unknown'),
                "expected_status": 401
            }
            
            try:
                response_data = response.json()
                auth_analysis["response_type"] = type(response_data).__name__
                
                if "detail" in response_data:
                    detail_value = response_data["detail"]
                    auth_analysis["detail_field"] = {
                        "type": type(detail_value).__name__,
                        "value": detail_value,
                        "is_string": isinstance(detail_value, str)
                    }
                
                auth_analysis["full_response"] = response_data
                
            except json.JSONDecodeError:
                auth_analysis["response_type"] = "invalid_json"
                auth_analysis["raw_response"] = response.text[:200]
            
            success = response.status_code == 401  # Should be unauthorized
            
            return self.log_test(
                "Outlook Connect Unauthorized Access",
                success,
                json.dumps(auth_analysis, indent=2, default=str)
            )
            
        except Exception as e:
            return self.log_test(
                "Outlook Connect Unauthorized Access",
                False,
                f"Unauthorized test exception: {str(e)}"
            )

    def analyze_response_for_react_issues(self):
        """Analyze all collected responses for potential React rendering issues"""
        print("🔍 Analyzing responses for React rendering issues...")
        
        react_issues = []
        
        for result in self.test_results:
            if "full_response" in result.get("details", ""):
                try:
                    details_data = json.loads(result["details"])
                    if "full_response" in details_data:
                        response_data = details_data["full_response"]
                        
                        # Check for object values in fields that might be rendered in React
                        problematic_fields = []
                        
                        if isinstance(response_data, dict):
                            for key, value in response_data.items():
                                if key in ["detail", "message", "error"] and isinstance(value, (dict, list)):
                                    problematic_fields.append({
                                        "field": key,
                                        "type": type(value).__name__,
                                        "value": value,
                                        "test": result["test"]
                                    })
                        
                        if problematic_fields:
                            react_issues.extend(problematic_fields)
                            
                except (json.JSONDecodeError, KeyError):
                    continue
        
        analysis_result = {
            "total_issues_found": len(react_issues),
            "issues": react_issues,
            "summary": "Found object/array values in fields that might cause 'Objects are not valid as a React child' errors" if react_issues else "No obvious React rendering issues found"
        }
        
        return self.log_test(
            "React Rendering Issues Analysis",
            len(react_issues) == 0,  # Pass if no issues found
            json.dumps(analysis_result, indent=2, default=str)
        )

    def run_comprehensive_test(self):
        """Run all Outlook connection tests"""
        print("🚀 Starting Comprehensive Outlook Connection Test")
        print("=" * 60)
        print(f"Target User: tyrzmusak@gmail.com")
        print(f"Target Endpoint: /api/outlook/connect-account")
        print(f"Focus: Response format analysis for React compatibility")
        print("=" * 60)
        
        # Step 1: Login
        if not self.login_tyrz_user():
            print("❌ Cannot proceed without successful login")
            return False
        
        # Step 2: Test Outlook status
        self.test_outlook_status_endpoint()
        
        # Step 3: Test various connection scenarios
        self.test_outlook_connect_with_valid_code()
        self.test_outlook_connect_with_invalid_code()
        self.test_outlook_connect_missing_parameters()
        self.test_outlook_connect_unauthorized()
        
        # Step 4: Analyze for React issues
        self.analyze_response_for_react_issues()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        
        # Highlight critical findings
        print("\n🎯 CRITICAL FINDINGS:")
        
        react_analysis = next((r for r in self.test_results if r["test"] == "React Rendering Issues Analysis"), None)
        if react_analysis:
            try:
                analysis_data = json.loads(react_analysis["details"])
                if analysis_data["total_issues_found"] > 0:
                    print("❌ FOUND POTENTIAL REACT RENDERING ISSUES:")
                    for issue in analysis_data["issues"]:
                        print(f"   - Field '{issue['field']}' contains {issue['type']} in test '{issue['test']}'")
                        print(f"     Value: {issue['value']}")
                else:
                    print("✅ No obvious React rendering issues detected")
            except:
                print("⚠️  Could not analyze React issues")
        
        # Show response format patterns
        print("\n📋 RESPONSE FORMAT PATTERNS:")
        for result in self.test_results:
            if "detail_field" in result.get("details", ""):
                try:
                    details_data = json.loads(result["details"])
                    if "detail_field" in details_data:
                        detail_info = details_data["detail_field"]
                        print(f"   {result['test']}: detail field is {detail_info['type']} - {'✅ String' if detail_info['is_string'] else '❌ Not String'}")
                except:
                    continue
        
        return passed_tests == total_tests

def main():
    """Main test execution"""
    tester = OutlookConnectionTester()
    success = tester.run_comprehensive_test()
    
    # Save detailed results to file
    with open('/app/outlook_connection_test_results.json', 'w') as f:
        json.dump(tester.test_results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: /app/outlook_connection_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())