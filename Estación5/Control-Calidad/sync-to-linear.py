#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenSymphony -> Linear Sync Script
Syncs task-package.yaml to Linear workspace
"""

import json
import requests
from datetime import datetime, timedelta
import yaml
import sys
import io

# Fix encoding on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
LINEAR_API_KEY = "REDACTED"
LINEAR_ENDPOINT = "https://api.linear.app/graphql"
TEAM_ID = "223ad377-615a-4e92-af70-32613c94cea1"  # Valentina Succar team UUID
PROJECT_NAME = "Control de Calidad"

# Headers (Linear API requires just the key, no Bearer prefix)
HEADERS = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json",
}

def graphql_query(query, variables=None):
    """Execute GraphQL query against Linear API"""
    payload = {
        "query": query,
        "variables": variables or {}
    }

    try:
        response = requests.post(LINEAR_ENDPOINT, json=payload, headers=HEADERS, timeout=10)
        data = response.json()

        if "errors" in data:
            print(f"GraphQL Error: {data['errors']}")
            if response.status_code >= 400:
                print(f"Status: {response.status_code}")
                print(f"Response: {data}")
            return None

        if response.status_code >= 400:
            print(f"API Error (Status {response.status_code}): {data}")
            return None

        return data.get("data", {})
    except Exception as e:
        print(f"API Error: {e}")
        return None

def get_or_create_project():
    """Get or create Control de Calidad project"""
    print(f"\n1️⃣ Creating/Getting project '{PROJECT_NAME}'...")

    # Check if project exists
    query = """
    query {
        projects(first: 10, filter: { name: { eq: "%s" } }) {
            nodes {
                id
                name
            }
        }
    }
    """ % PROJECT_NAME

    result = graphql_query(query)
    if result and result.get("projects", {}).get("nodes"):
        project_id = result["projects"]["nodes"][0]["id"]
        print(f"   ✓ Found existing project: {project_id}")
        return project_id

    # Create project
    mutation = """
    mutation CreateProject($input: ProjectCreateInput!) {
        projectCreate(input: $input) {
            project {
                id
                name
            }
        }
    }
    """

    variables = {
        "input": {
            "name": PROJECT_NAME,
            "teamIds": [TEAM_ID]
        }
    }

    result = graphql_query(mutation, variables)
    if result and "projectCreate" in result:
        project_id = result["projectCreate"]["project"]["id"]
        print(f"   ✓ Created project: {project_id}")
        return project_id

    print("   ✗ Failed to create project")
    return None

def get_or_create_cycle(project_id, cycle_name, start_date, end_date):
    """Get or create a cycle (wave)"""
    print(f"\n2️⃣ Creating/Getting cycle '{cycle_name}'...")

    # Check if cycle exists
    query = """
    query {
        cycles(first: 10, filter: { name: { eq: "%s" } }) {
            nodes {
                id
                name
            }
        }
    }
    """ % cycle_name

    result = graphql_query(query)
    if result and result.get("cycles", {}).get("nodes"):
        cycle_id = result["cycles"]["nodes"][0]["id"]
        print(f"   ✓ Found cycle: {cycle_id}")
        return cycle_id

    # Create cycle
    mutation = """
    mutation CreateCycle($input: CycleCreateInput!) {
        cycleCreate(input: $input) {
            cycle {
                id
                name
            }
        }
    }
    """

    variables = {
        "input": {
            "name": cycle_name,
            "teamId": TEAM_ID,
            "startsAt": start_date.isoformat(),
            "endsAt": end_date.isoformat()
        }
    }

    result = graphql_query(mutation, variables)
    if result and "cycleCreate" in result:
        cycle_id = result["cycleCreate"]["cycle"]["id"]
        print(f"   ✓ Created cycle: {cycle_id}")
        return cycle_id

    print("   ✗ Failed to create cycle")
    return None

def create_issue(project_id, cycle_id, title, description, estimate, phase_data):
    """Create an issue in Linear"""
    mutation = """
    mutation CreateIssue($input: IssueCreateInput!) {
        issueCreate(input: $input) {
            issue {
                id
                identifier
                title
            }
        }
    }
    """

    variables = {
        "input": {
            "teamId": TEAM_ID,
            "projectId": project_id,
            "cycleId": cycle_id,
            "title": title,
            "description": description,
            "estimate": estimate,
            "priority": 2  # Medium priority
        }
    }

    result = graphql_query(mutation, variables)
    if result and "issueCreate" in result:
        issue = result["issueCreate"]["issue"]
        return issue["id"]

    return None

def load_task_package():
    """Load task-package.yaml"""
    print("\n📦 Loading task-package.yaml...")
    try:
        # Try multiple paths
        paths = [
            "task-package.yaml",
            "docs/tasks/task-package.yaml",
            "./docs/tasks/task-package.yaml"
        ]

        for path in paths:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                print(f"   ✓ Loaded from {path}")
                return data
            except FileNotFoundError:
                continue

        print("   ✗ Error: task-package.yaml not found")
        return None
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None

def get_teams():
    """Get available teams"""
    print("\n Getting teams from Linear...")

    query = """
    query {
        teams(first: 10) {
            nodes {
                id
                name
                key
            }
        }
    }
    """

    result = graphql_query(query)
    if result and "teams" in result:
        teams = result["teams"]["nodes"]
        print("\nAvailable teams:")
        for team in teams:
            print(f"  - {team['name']} (ID: {team['id']}, Key: {team['key']})")
        return teams
    return []

def main():
    """Main sync function"""
    print("=" * 60)
    print("🎼 OpenSymphony -> Linear Sync")
    print("=" * 60)

    # Get teams first to verify connection
    teams = get_teams()
    if not teams:
        print("\nError: Could not fetch teams. Check API key.")
        return False

    # Load task package
    task_package = load_task_package()
    if not task_package:
        return False

    # Create project
    project_id = get_or_create_project()
    if not project_id:
        return False

    # Create cycles
    print("\n📅 Setting up cycles (Waves)...")

    waves = task_package.get("waves", {})
    cycle_ids = {}

    for wave_key, wave_data in waves.items():
        start_date = datetime.fromisoformat(wave_data["start_date"])
        end_date = datetime.fromisoformat(wave_data["end_date"])

        cycle_id = get_or_create_cycle(
            project_id,
            wave_data["name"],
            start_date,
            end_date
        )
        if cycle_id:
            cycle_ids[wave_key] = cycle_id

    # Create issues for each phase
    print("\n📝 Creating issues...")

    phases = task_package.get("phases", {})
    issue_ids = {}

    for phase_key, phase_data in phases.items():
        unit_key = phase_data.get("unit", "unknown")
        units = task_package.get("units", {})
        unit_data = units.get(unit_key, {})
        wave_key = unit_data.get("wave", "wave_1")

        cycle_id = cycle_ids.get(wave_key)
        if not cycle_id:
            print(f"   ⚠️  Skipping {phase_key} (no cycle)")
            continue

        title = f"{unit_key} → {phase_data['name']}"
        description = f"""
**Phase**: {phase_data['name']}
**Unit**: {unit_key}
**Duration**: {phase_data['duration_days']} days
**Status**: {phase_data['status']}

{phase_data.get('description', '')}
        """

        estimate = 5  # Default estimate

        issue_id = create_issue(
            project_id,
            cycle_id,
            title,
            description,
            estimate,
            phase_data
        )

        if issue_id:
            issue_ids[phase_key] = issue_id
            print(f"   ✓ Created: {title}")
        else:
            print(f"   ✗ Failed: {title}")

    print("\n" + "=" * 60)
    print(f"✅ Sync Complete!")
    print(f"   • Project ID: {project_id}")
    print(f"   • Cycles created: {len(cycle_ids)}")
    print(f"   • Issues created: {len(issue_ids)}")
    print("=" * 60)

    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Sync cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        exit(1)
