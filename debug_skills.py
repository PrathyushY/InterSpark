#!/usr/bin/env python3
"""
Debug script to test skills matching logic
"""

import json

def parse_skills(val):
    if not val:
        return []
    if isinstance(val, list):
        return val
    try:
        loaded = json.loads(val)
        if isinstance(loaded, list):
            return loaded
    except Exception:
        pass
    if "," in val:
        return [s.strip() for s in val.split(",") if s.strip()]
    return [val.strip()] if val.strip() else []

def test_skills_matching():
    # Test data from the database
    students = [
        {"name": "Hridhay Jayakumar", "skills": ['Python', 'Machine Learning', 'Java']},
        {"name": "Prathyush Yeturi", "skills": ['Java', 'Python', 'Artificial Intelligence Projects', 'C#']}
    ]
    
    # Test search for "python"
    search_skills = "python"
    selected_skills = set(parse_skills(search_skills))
    
    print(f"Search skills: {search_skills}")
    print(f"Parsed selected skills: {selected_skills}")
    
    for student in students:
        profile_skills = student.get("skills", [])
        print(f"\nStudent: {student['name']}")
        print(f"Profile skills: {profile_skills}")
        
        # Check if any selected skill matches any profile skill (case-insensitive exact match)
        profile_skills_lower = [s.lower() for s in profile_skills]
        selected_skills_lower = [s.lower() for s in selected_skills]
        
        print(f"Profile skills lower: {profile_skills_lower}")
        print(f"Selected skills lower: {selected_skills_lower}")
        
        match = any(skill in profile_skills_lower for skill in selected_skills_lower)
        print(f"Match: {match}")

if __name__ == "__main__":
    test_skills_matching()