#!/usr/bin/env python3
"""
Corrected Outlook Account Connection Test - Using Query Parameters
Testing /api/outlook/connect-account endpoint with proper parameter format
"""

import requests
import json
import sys
from datetime import datetime

class OutlookConnectionCorrectedTester:
    def __init__(self, base_url="https://outlook-fix.preview.emergentagent.com/api"):
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

    def test_outlook_connect_with_query_params_valid(self):
        """Test /api/outlook/connect-account with valid-looking query parameters"""
        print("🔗 Testing Outlook connect-account with valid query parameters...")
        
        try:
            # Use query parameters instead of JSON body
            params = {
                "code": "M.C507_BAY.2.U.12345678-1234-1234-1234-123456789abc.1234567890abcdef1234567890abcdef12345678",
                "state": "test-state-12345-67890-abcdef"
            }
            
            url = f"{self.base_url}/outlook/connect-account"
            headers = {'Authorization': f'Bearer {self.token}'}
            
            response = requests.post(url, params=params, headers=headers)
            
            # Analyze response structure
            response_analysis = {
                "status_code": response.status_code,
                "content_type": response.headers.get('Content-Type', 'unknown'),
                "response_length": len(response.text),
                "request_method": "POST with query params"
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
            
            return self.log_test(
                "Outlook Connect Valid Query Params",
                True,  # Always pass since we're analyzing format
                json.dumps(response_analysis, indent=2, default=str)
            )
            
        except Exception as e:
            return self.log_test(
                "Outlook Connect Valid Query Params",
                False,
                f"Connect test exception: {str(e)}"
            )

    def test_outlook_connect_with_query_params_invalid(self):
        """Test /api/outlook/connect-account with invalid query parameters"""
        print("❌ Testing Outlook connect-account with invalid query parameters...")
        
        try:
            # Use invalid query parameters
            params = {
                "code": "invalid-code-123",
                "state": "invalid-state-456"
            }
            
            url = f"{self.base_url}/outlook/connect-account"
            headers = {'Authorization': f'Bearer {self.token}'}
            
            response = requests.post(url, params=params, headers=headers)
            
            # Analyze error response structure
            error_analysis = {
                "status_code": response.status_code,
                "content_type": response.headers.get('Content-Type', 'unknown'),
                "response_length": len(response.text),
                "request_method": "POST with invalid query params"
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
                "Outlook Connect Invalid Query Params",
                True,  # Always pass since we're analyzing error format
                json.dumps(error_analysis, indent=2, default=str)
            )
            
        except Exception as e:
            return self.log_test(
                "Outlook Connect Invalid Query Params",
                False,
                f"Error test exception: {str(e)}"
            )

    def test_outlook_connect_missing_query_params(self):
        """Test /api/outlook/connect-account with missing query parameters"""
        print("🚫 Testing Outlook connect-account with missing query parameters...")
        
        test_cases = [
            {"name": "Missing Code", "params": {"state": "test-state"}},
            {"name": "Missing State", "params": {"code": "test-code"}},
            {"name": "Empty Code", "params": {"code": "", "state": "test-state"}},
            {"name": "Empty State", "params": {"code": "test-code", "state": ""}},
            {"name": "No Parameters", "params": {}}
        ]
        
        results = []
        
        for test_case in test_cases:
            try:
                url = f"{self.base_url}/outlook/connect-account"
                headers = {'Authorization': f'Bearer {self.token}'}
                
                response = requests.post(url, params=test_case["params"], headers=headers)
                
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
            "Outlook Connect Missing Query Parameters",
            True,  # Always pass since we're analyzing response formats
            json.dumps(results, indent=2, default=str)
        )

    def test_real_oauth_flow_simulation(self):
        """Test simulating a more realistic OAuth flow"""
        print("🔄 Testing realistic OAuth flow simulation...")
        
        try:
            # First, let's try to get the auth URL to understand the flow
            auth_url_endpoint = f"{self.base_url}/outlook/auth-url"
            headers = {'Authorization': f'Bearer {self.token}'}
            
            auth_response = requests.get(auth_url_endpoint, headers=headers)
            
            flow_analysis = {
                "auth_url_status": auth_response.status_code,
                "auth_url_available": auth_response.status_code == 200
            }
            
            if auth_response.status_code == 200:
                try:
                    auth_data = auth_response.json()
                    flow_analysis["auth_url_response"] = auth_data
                    
                    # Extract state from auth URL if available
                    auth_url = auth_data.get("auth_url", "")
                    if "state=" in auth_url:
                        state_param = auth_url.split("state=")[1].split("&")[0]
                        flow_analysis["extracted_state"] = state_param
                        
                        # Now test with the extracted state
                        params = {
                            "code": "realistic-oauth-code-from-microsoft",
                            "state": state_param
                        }
                        
                        connect_response = requests.post(
                            f"{self.base_url}/outlook/connect-account",
                            params=params,
                            headers=headers
                        )
                        
                        flow_analysis["connect_with_real_state"] = {
                            "status_code": connect_response.status_code,
                            "content_type": connect_response.headers.get('Content-Type', 'unknown')
                        }
                        
                        try:
                            connect_data = connect_response.json()
                            flow_analysis["connect_with_real_state"]["response_data"] = connect_data
                            
                            if "detail" in connect_data:
                                detail_value = connect_data["detail"]
                                flow_analysis["connect_with_real_state"]["detail_field"] = {
                                    "type": type(detail_value).__name__,
                                    "is_string": isinstance(detail_value, str),
                                    "value": detail_value
                                }
                        except json.JSONDecodeError:
                            flow_analysis["connect_with_real_state"]["response_data"] = "invalid_json"
                            
                except json.JSONDecodeError:
                    flow_analysis["auth_url_response"] = "invalid_json"
            
            return self.log_test(
                "Realistic OAuth Flow Simulation",
                True,  # Always pass since we're analyzing
                json.dumps(flow_analysis, indent=2, default=str)
            )
            
        except Exception as e:
            return self.log_test(
                "Realistic OAuth Flow Simulation",
                False,
                f"OAuth flow test exception: {str(e)}"
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
        """Run all corrected Outlook connection tests"""
        print("🚀 Starting Corrected Outlook Connection Test")
        print("=" * 60)
        print(f"Target User: tyrzmusak@gmail.com")
        print(f"Target Endpoint: /api/outlook/connect-account")
        print(f"Focus: Proper query parameter usage and response format analysis")
        print("=" * 60)
        
        # Step 1: Login
        if not self.login_tyrz_user():
            print("❌ Cannot proceed without successful login")
            return False
        
        # Step 2: Test various connection scenarios with proper query params
        self.test_outlook_connect_with_query_params_valid()
        self.test_outlook_connect_with_query_params_invalid()
        self.test_outlook_connect_missing_query_params()
        self.test_real_oauth_flow_simulation()
        
        # Step 3: Analyze for React issues
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
    tester = OutlookConnectionCorrectedTester()
    success = tester.run_comprehensive_test()
    
    # Save detailed results to file
    with open('/app/outlook_connection_corrected_test_results.json', 'w') as f:
        json.dump(tester.test_results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: /app/outlook_connection_corrected_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())