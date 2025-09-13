#!/usr/bin/env python3
import os
import xml.etree.ElementTree as ET
import json
from pathlib import Path

def parse_csproj_dependencies(csproj_path):
    """Parse a .csproj file to extract dependencies"""
    try:
        tree = ET.parse(csproj_path)
        root = tree.getroot()
        
        project_refs = []
        package_refs = []
        
        # Find all ProjectReference elements
        for proj_ref in root.findall('.//ProjectReference'):
            include = proj_ref.get('Include')
            if include:
                # Convert relative path to project name, handle Windows paths
                # Convert backslashes to forward slashes for cross-platform compatibility
                normalized_path = include.replace('\\', '/')
                project_name = Path(normalized_path).stem
                project_refs.append(project_name)
        
        # Find all PackageReference elements
        for pkg_ref in root.findall('.//PackageReference'):
            include = pkg_ref.get('Include')
            if include:
                package_refs.append(include)
        
        return project_refs, package_refs
    except Exception as e:
        print(f"Error parsing {csproj_path}: {e}")
        return [], []

def analyze_projects():
    """Analyze all projects and their dependencies"""
    solution_dir = Path('./CSharpToCppTranslatorTestSolution')
    projects = {}
    
    # Find all .csproj files
    for csproj_path in solution_dir.glob('**/*.csproj'):
        project_name = csproj_path.stem
        project_refs, package_refs = parse_csproj_dependencies(csproj_path)
        
        projects[project_name] = {
            'path': str(csproj_path),
            'project_dependencies': project_refs,
            'package_dependencies': package_refs
        }
    
    return projects

def find_parallel_translatable_groups(projects):
    """Find groups of projects that can be translated in parallel"""
    # Build dependency graph
    dependency_graph = {}
    all_projects = set(projects.keys())
    
    for project, info in projects.items():
        deps = [dep for dep in info['project_dependencies'] if dep in all_projects]
        dependency_graph[project] = deps
    
    # Find projects with no dependencies (can be translated first)
    no_deps = [p for p, deps in dependency_graph.items() if not deps]
    
    # Find levels of dependency
    levels = []
    remaining = set(all_projects)
    
    while remaining:
        # Find projects whose dependencies are all satisfied
        current_level = []
        satisfied = set(all_projects) - remaining
        
        for project in remaining:
            if all(dep in satisfied for dep in dependency_graph[project]):
                current_level.append(project)
        
        if not current_level:
            # Handle circular dependencies or missing deps
            print(f"Warning: Circular dependency or missing dependency detected for remaining projects: {remaining}")
            current_level = list(remaining)
        
        levels.append(current_level)
        remaining -= set(current_level)
    
    return levels, dependency_graph

def main():
    projects = analyze_projects()
    
    print("=== PROJECT ANALYSIS ===")
    print(f"Found {len(projects)} projects:")
    for project, info in projects.items():
        print(f"\n{project}:")
        if info['project_dependencies']:
            print(f"  Project Dependencies: {info['project_dependencies']}")
        if info['package_dependencies']:
            print(f"  Package Dependencies: {info['package_dependencies']}")
    
    levels, dep_graph = find_parallel_translatable_groups(projects)
    
    print("\n=== TRANSLATION PARALLELIZATION ANALYSIS ===")
    for i, level in enumerate(levels):
        print(f"\nLevel {i + 1} (can be translated in parallel):")
        for project in level:
            deps = dep_graph.get(project, [])
            if deps:
                print(f"  - {project} (depends on: {', '.join(deps)})")
            else:
                print(f"  - {project} (no project dependencies)")
    
    # Save results
    result = {
        'projects': projects,
        'dependency_graph': dep_graph,
        'parallel_groups': levels
    }
    
    with open('./experiments/dependency_analysis.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n=== SUMMARY ===")
    print(f"Total projects: {len(projects)}")
    print(f"Translation levels needed: {len(levels)}")
    print(f"Maximum parallel projects in one level: {max(len(level) for level in levels)}")

if __name__ == "__main__":
    main()