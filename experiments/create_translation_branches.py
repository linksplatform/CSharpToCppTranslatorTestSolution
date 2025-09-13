#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

def run_git_command(cmd):
    """Run a git command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command '{cmd}': {e.stderr}")
        return None

def create_branches_for_parallel_groups():
    """Create git branches for projects that can be translated in parallel"""
    
    # Load dependency analysis
    with open('./experiments/dependency_analysis.json', 'r') as f:
        data = json.load(f)
    
    parallel_groups = data['parallel_groups']
    dependency_graph = data['dependency_graph']
    
    print("=== CREATING TRANSLATION BRANCHES ===")
    
    branches_created = []
    
    for level_num, level_projects in enumerate(parallel_groups, 1):
        print(f"\nLevel {level_num} - Projects that can be translated in parallel:")
        
        # Create a branch for the entire level (for coordinating the level)
        level_branch_name = f"translation-level-{level_num}"
        
        print(f"Creating level branch: {level_branch_name}")
        result = run_git_command(f"git checkout -b {level_branch_name}")
        if result is not None:
            branches_created.append(level_branch_name)
            print(f"  ✓ Created branch: {level_branch_name}")
        else:
            print(f"  ✗ Failed to create branch: {level_branch_name}")
        
        # Create individual branches for each project in this level
        for project in level_projects:
            project_branch_name = f"translate-{project.lower().replace('.', '-')}"
            
            # Switch back to main branch before creating new branch
            run_git_command("git checkout main")
            
            print(f"Creating project branch: {project_branch_name}")
            result = run_git_command(f"git checkout -b {project_branch_name}")
            if result is not None:
                branches_created.append(project_branch_name)
                deps = dependency_graph.get(project, [])
                if deps:
                    print(f"  ✓ Created branch: {project_branch_name} (depends on: {', '.join(deps)})")
                else:
                    print(f"  ✓ Created branch: {project_branch_name} (no dependencies)")
            else:
                print(f"  ✗ Failed to create branch: {project_branch_name}")
    
    # Return to main branch
    run_git_command("git checkout main")
    
    print(f"\n=== SUMMARY ===")
    print(f"Created {len(branches_created)} branches total:")
    for branch in branches_created:
        print(f"  - {branch}")
    
    # Create a markdown file documenting the translation strategy
    create_translation_strategy_doc(parallel_groups, dependency_graph)
    
    return branches_created

def create_translation_strategy_doc(parallel_groups, dependency_graph):
    """Create a markdown file documenting the translation strategy"""
    
    doc_content = """# C# to C++ Translation Strategy

This document outlines the parallel translation strategy for the CSharpToCppTranslatorTestSolution projects.

## Overview

The projects have been analyzed for dependencies and grouped into levels that can be translated in parallel. Projects in the same level have no dependencies on each other within the solution.

"""
    
    for level_num, level_projects in enumerate(parallel_groups, 1):
        doc_content += f"## Level {level_num} - Parallel Translation Group\n\n"
        doc_content += f"These {len(level_projects)} projects can be translated in parallel:\n\n"
        
        for project in level_projects:
            deps = dependency_graph.get(project, [])
            if deps:
                doc_content += f"- **{project}** (depends on: {', '.join(deps)})\n"
            else:
                doc_content += f"- **{project}** (no project dependencies)\n"
        
        doc_content += f"\n### Git Branches Created:\n\n"
        doc_content += f"- `translation-level-{level_num}` - Coordination branch for this level\n"
        
        for project in level_projects:
            project_branch = f"translate-{project.lower().replace('.', '-')}"
            doc_content += f"- `{project_branch}` - Translation branch for {project}\n"
        
        doc_content += "\n"
    
    doc_content += """## Translation Workflow

1. **Level 1**: Start with all Level 1 projects simultaneously since they have no internal dependencies
2. **Level 2**: Begin Level 2 translations only after their Level 1 dependencies are completed
3. **Level 3**: Begin Level 3 translations only after their Level 2 dependencies are completed

## Benefits

- **Parallel Execution**: Multiple projects can be translated simultaneously within each level
- **Dependency Safety**: No project will be translated before its dependencies are ready
- **Progress Tracking**: Each project has its own branch for isolated development
- **Coordination**: Level branches allow for coordinating work within each parallel group

## Branch Usage

- Use individual project branches (`translate-*`) for the actual translation work
- Use level branches (`translation-level-*`) for coordinating and merging completed translations
- All branches are based off the main branch to ensure consistency
"""
    
    strategy_file = Path('./experiments/translation_strategy.md')
    strategy_file.write_text(doc_content)
    print(f"Created translation strategy document: {strategy_file}")

def main():
    if not Path('./experiments/dependency_analysis.json').exists():
        print("Error: dependency_analysis.json not found. Please run analyze_dependencies.py first.")
        sys.exit(1)
    
    create_branches_for_parallel_groups()

if __name__ == "__main__":
    main()