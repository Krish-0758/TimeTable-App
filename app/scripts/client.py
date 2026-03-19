#!/usr/bin/env python3
"""
API Client for Timetable Generator
Usage: python -m scripts.client [command] [options]
"""

import requests
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"

class TimetableClient:
    """Client for interacting with the Timetable Generator API"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make an HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, json=data)
            elif method == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Error: Cannot connect to API at {self.base_url}")
            print("   Make sure the server is running: python -m uvicorn app.main:app --reload")
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            if response.text:
                print(f"   Response: {response.text}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    def reset(self) -> Dict[str, Any]:
        """Reset the system"""
        return self._request("POST", "/reset")
    
    def status(self) -> Dict[str, Any]:
        """Get system status"""
        return self._request("GET", "/status")
    
    def create_structure(self, structure_file: str) -> Dict[str, Any]:
        """Create timetable structure from JSON file"""
        with open(structure_file, 'r') as f:
            data = json.load(f)
        return self._request("POST", "/structure", data)
    
    def add_constraint(self, constraint_file: str) -> Dict[str, Any]:
        """Add a constraint from JSON file"""
        with open(constraint_file, 'r') as f:
            data = json.load(f)
        return self._request("POST", "/constraints", data)
    
    def add_constraints_batch(self, constraints_file: str) -> Dict[str, Any]:
        """Add multiple constraints from a JSON file containing an array"""
        with open(constraints_file, 'r') as f:
            data = json.load(f)
        return self._request("POST", "/constraints/batch", data)
    
    def get_constraints(self) -> Dict[str, Any]:
        """Get all constraints"""
        return self._request("GET", "/constraints")
    
    def clear_constraints(self) -> Dict[str, Any]:
        """Clear all constraints"""
        return self._request("DELETE", "/constraints")
    
    def validate_constraints(self) -> Dict[str, Any]:
        """Validate all constraints"""
        return self._request("POST", "/constraints/validate")
    
    def solve(self) -> Dict[str, Any]:
        """Solve the timetable"""
        return self._request("POST", "/solve")
    
    def run_workflow(self, structure_file: str, constraint_files: list) -> Dict[str, Any]:
        """Run a complete workflow"""
        print("🔄 Resetting system...")
        print(json.dumps(self.reset(), indent=2))
        
        print(f"\n📅 Creating structure from {structure_file}...")
        print(json.dumps(self.create_structure(structure_file), indent=2))
        
        print(f"\n📊 Current status:")
        print(json.dumps(self.status(), indent=2))
        
        for cf in constraint_files:
            print(f"\n➕ Adding constraint from {cf}...")
            print(json.dumps(self.add_constraint(cf), indent=2))
        
        print(f"\n📊 Final status:")
        print(json.dumps(self.status(), indent=2))
        
        print(f"\n⚙️ Solving timetable...")
        result = self.solve()
        print(json.dumps(result, indent=2))
        
        # Save result to file
        output_file = "timetable_solution.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Solution saved to {output_file}")
        
        return result


def main():
    parser = argparse.ArgumentParser(description='Timetable Generator Client')
    parser.add_argument('--url', default=BASE_URL, help='API base URL')
    parser.add_argument('--output', '-o', help='Output file for results')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands', required=True)
    
    # Reset command
    subparsers.add_parser('reset', help='Reset the system')
    
    # Status command
    subparsers.add_parser('status', help='Get system status')
    
    # Create structure command
    struct_parser = subparsers.add_parser('create-structure', help='Create timetable structure')
    struct_parser.add_argument('file', help='JSON file with structure definition')
    
    # Add constraint command
    constraint_parser = subparsers.add_parser('add-constraint', help='Add a constraint')
    constraint_parser.add_argument('file', help='JSON file with constraint definition')
    
    # Batch add constraints
    batch_parser = subparsers.add_parser('batch-add', help='Add multiple constraints')
    batch_parser.add_argument('file', help='JSON file with array of constraints')
    
    # List constraints
    subparsers.add_parser('list-constraints', help='List all constraints')
    
    # Clear constraints
    subparsers.add_parser('clear-constraints', help='Clear all constraints')
    
    # Validate constraints
    subparsers.add_parser('validate', help='Validate all constraints')
    
    # Solve command
    subparsers.add_parser('solve', help='Solve the timetable')
    
    # Workflow command
    workflow_parser = subparsers.add_parser('workflow', help='Run complete workflow')
    workflow_parser.add_argument('structure_file', help='Structure JSON file')
    workflow_parser.add_argument('constraint_files', nargs='+', help='Constraint JSON files')
    
    args = parser.parse_args()
    
    client = TimetableClient(args.url)
    
    try:
        if args.command == 'reset':
            result = client.reset()
        elif args.command == 'status':
            result = client.status()
        elif args.command == 'create-structure':
            result = client.create_structure(args.file)
        elif args.command == 'add-constraint':
            result = client.add_constraint(args.file)
        elif args.command == 'batch-add':
            result = client.add_constraints_batch(args.file)
        elif args.command == 'list-constraints':
            result = client.get_constraints()
        elif args.command == 'clear-constraints':
            result = client.clear_constraints()
        elif args.command == 'validate':
            result = client.validate_constraints()
        elif args.command == 'solve':
            result = client.solve()
        elif args.command == 'workflow':
            result = client.run_workflow(args.structure_file, args.constraint_files)
        else:
            parser.print_help()
            return
        
        # Pretty print the result
        print(json.dumps(result, indent=2))
        
        # Save to file if output specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Result saved to {args.output}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()