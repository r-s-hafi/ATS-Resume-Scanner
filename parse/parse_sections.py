
import json
from dotenv import load_dotenv
import os
from openai import AsyncOpenAI

load_dotenv()
key = os.getenv('OPEN_AI_KEY')
client = AsyncOpenAI(api_key=key)


async def parse_education(context: str) -> list:
    
    """
    Parse education entries from resume text and return structured data.
    
    Expected input format examples:
    - "University of Michigan  Ann Arbor, MI\nB.S.E. Chemical Engineering & B.S. Chemistry Aug 2021 – May 2025\nGPA: 3.90 / 4.00 | Capstone: Production of Light Olefins from Methanol"
    - "Stanford University, Stanford, CA\nMaster of Science in Computer Science\nSeptember 2018 - June 2020\nGPA: 3.8/4.0"
    - "Bachelor of Arts in English Literature\nHarvard University\nCambridge, MA\n2016 - 2020"
    """

    prompt = f'''You are analyzing a resume's education section to extract structured education entries. 
    RESUME EDUCATION TEXT:
    {context}

    Extract each education entry and return a JSON array where each entry follows this exact structure:
    {{
        "degree": "Full degree name (e.g., 'Bachelor of Science in Computer Science', 'M.S. in Engineering', 'Ph.D. in Physics')",
        "school": "School/University name (e.g., 'University of Michigan', 'Stanford University')",
        "location": "City, State format (e.g., 'Ann Arbor, MI', 'Stanford, CA') or 'Remote' if specified",
        "duration": "Start date - End date format (e.g., 'Aug 2021 – May 2025', '2016 - 2020', 'Expected 2024')",
        "content": "Additional details about the education entry (e.g., 'GPA: 3.90 / 4.00 | Capstone: Production of Light Olefins from Methanol', 'Honors: Dean's List, Summa Cum Laude')"
    }}

    PARSING RULES:
    1. Extract ALL education entries from the text, including:
    - Bachelor's degrees, Master's degrees, PhDs
    - Associate degrees, certificates, diplomas
    - Any academic achievements or honors

    2. For DEGREE field:
    - Include the full degree name with major/concentration
    - Examples: "Bachelor of Science in Chemical Engineering", "Master of Arts in Literature"
    - If multiple degrees are listed together, separate them into individual entries
    - Handle abbreviated forms: "B.S.E." → "Bachelor of Science in Engineering"

    3. For SCHOOL field:
    - Extract the complete university/institution name
    - Remove any location information that might be attached to the school name
    - Standardize common abbreviations (e.g., "MIT" → "Massachusetts Institute of Technology" if full name appears)

    4. For LOCATION field:
    - Format as "City, State" (e.g., "Ann Arbor, MI", "Stanford, CA")
    - If no location specified, set to null
    - Handle various formats: "Ann Arbor, MI", "Cambridge, MA", "Remote"

    5. For DURATION field:
    - Preserve the exact date format as shown in the resume
    - Examples: "Aug 2021 – May 2025", "2016 - 2020", "Expected 2024", "Fall 2020 - Spring 2022"
    - If no dates provided, set to null

    6. For CONTENT field:
    - Extract ALL additional information about the education entry that doesn't fit into the other fields
    - Include GPA (e.g., "GPA: 3.90 / 4.00", "3.8/4.0")
    - Include capstone projects (e.g., "Capstone: Production of Light Olefins from Methanol")
    - Include honors and awards (e.g., "Summa Cum Laude", "Dean's List", "Honors Program")
    - Include relevant coursework (e.g., "Relevant Coursework: Data Structures, Algorithms")
    - Include thesis titles (e.g., "Thesis: Machine Learning Applications in Healthcare")
    - Include minors or concentrations not in degree name (e.g., "Minor in Mathematics")
    - Include scholarships (e.g., "Presidential Scholarship")
    - Include academic achievements (e.g., "Published research in Nature")
    - Combine multiple details with " | " separator for clean formatting
    - IMPORTANT: If content has multiple distinct items or bullet points, separate each item with a newline character (\\n)
    - If no additional content, set to null or empty string

    7. COMBINING vs SEPARATING ENTRIES - CRITICAL RULE:
    - ALWAYS check if degrees share the SAME time period/duration before creating separate entries
    - If multiple degrees have the EXACT SAME or OVERLAPPING dates (earned simultaneously), you MUST combine them into ONE single entry
    - When combining: put all degree names in the "degree" field, use the shared school/location/duration, and combine all content
    
    EXAMPLES OF COMBINING (same dates = ONE entry):
    - Input: "B.S.E. Chemical Engineering & B.S. Chemistry, University of Michigan, Aug 2021 – May 2025"
      Output: ONE entry with degree="B.S.E. Chemical Engineering & B.S. Chemistry"
    - Input: "B.A. Economics" and "B.S. Mathematics" both from "Harvard University, 2020-2024"
      Output: ONE entry with degree="B.A. Economics & B.S. Mathematics"
    - Even if formatted as separate lines/sections, if the dates match, merge into ONE entry
    
    EXAMPLES OF SEPARATING (different dates = SEPARATE entries):
    - Input: "M.S. Computer Science, Stanford, 2018-2020" and "Ph.D. Computer Science, Stanford, 2020-2024"
      Output: TWO separate entries (different time periods, even though same school)
    - Input: "B.S. Biology, 2016-2020" and "M.S. Biology, 2020-2022"
      Output: TWO separate entries (sequential degrees with different durations)
    
    CRITICAL: The ONLY factor that determines combining vs separating is whether the time periods are the same or different.
    - Same/overlapping time period = COMBINE into one entry
    - Different time periods = SEPARATE entries
    - Ignore degree level differences (Bachelor's, Master's, PhD) - only look at the dates!

    Return ONLY the JSON array, no other text. If no education entries are found, return an empty array [].

    Example output format (notice how dual degrees with same dates are ONE entry):
    [
        {{
            "degree": "High School Diploma",
            "school": "Brighton High School",
            "location": "Brighton, MI",
            "duration": "Aug 2017 - June 2021",
            "content": "GPA: 4.0 | National Honor Society"
        }},
        {{
            "degree": "B.S.E. Chemical Engineering & B.S. Chemistry",
            "school": "University of Michigan", 
            "location": "Ann Arbor, MI",
            "duration": "Aug 2021 – May 2025",
            "content": "GPA: 3.90 / 4.00 | Capstone: Production of Light Olefins from Methanol | Dean's List"
        }}
    ]
    
    IMPORTANT REMINDER: If you see "B.S.E. Chemical Engineering & B.S. Chemistry Aug 2021 – May 2025" this is ONE entry, not two!
    The "&" symbol and shared dates indicate simultaneous degrees that must be combined.'''

    try:
        completion = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt}
            ]
        )
        
        response = completion.choices[0].message.content

        # Parse JSON response and return as Python dictionary
        education_entries = json.loads(response)

        for entry in education_entries:
            entry['content'] = entry['content'].replace('\n','<br>')
            
        return education_entries if education_entries else []

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return []
    except Exception as e:
        print(f"Error parsing education: {e}")
        return []


async def parse_experience(context: str) -> list:
    """
    Parse work experience entries from resume text and return structured data.
    
    Expected input format examples:
    - "Process Engineer\nMarathon Petroleum Company\nSt. Paul, MN\nMay 2018 - Present\n• Led process optimization initiatives\n• Managed production operations"
    - "Software Engineer Intern\nGoogle Inc.\nMountain View, CA\nJune 2020 - August 2020\n• Developed web applications\n• Collaborated with cross-functional teams"
    - "Research Assistant\nUniversity of Michigan\nAnn Arbor, MI\nJan 2021 - Dec 2021\n• Conducted laboratory experiments\n• Analyzed data and prepared reports"
    """

    prompt = f'''You are analyzing a resume's work experience section to extract structured experience entries. 

    RESUME EXPERIENCE TEXT:
    {context}

    Extract each work experience entry and return a JSON array where each entry follows this exact structure:
    {{
        "title": "Job title/position (e.g., 'Process Engineer', 'Software Engineer Intern', 'Research Assistant')",
        "company": "Company/Organization name (e.g., 'Marathon Petroleum Company', 'Google Inc.', 'University of Michigan')",
        "location": "City, State format (e.g., 'St. Paul, MN', 'Mountain View, CA', 'Ann Arbor, MI') or 'Remote' if specified",
        "duration": "Start date - End date format (e.g., 'May 2018 - Present', 'June 2020 - August 2020', 'Jan 2021 - Dec 2021')",
        "content": "All additional details about the position (e.g., responsibilities, achievements, technologies used, metrics, bullet points)"
    }}

    PARSING RULES:
    1. Extract ALL work experience entries from the text, including:
    - Full-time positions, part-time jobs
    - Internships, co-ops, summer positions
    - Research positions, teaching assistantships
    - Volunteer work, freelance projects
    - Any professional experience

    2. For TITLE field:
    - Extract the exact job title/position as written
    - Examples: "Process Engineer", "Software Engineer Intern", "Research Assistant"
    - Preserve any specific titles or levels (e.g., "Senior", "Lead", "Principal")
    - Handle abbreviated forms appropriately

    3. For COMPANY field:
    - Extract the complete company/organization name
    - Include full company names (e.g., "Marathon Petroleum Company" not just "Marathon")
    - For universities, use full name (e.g., "University of Michigan")
    - Remove any location information that might be attached to the company name

    4. For LOCATION field:
    - Format as "City, State" (e.g., "St. Paul, MN", "Mountain View, CA")
    - If no location specified, set to null
    - Handle various formats: "St. Paul, MN", "Mountain View, CA", "Remote"
    - For remote positions, use "Remote"

    5. For DURATION field:
    - Preserve the exact date format as shown in the resume
    - Examples: "May 2018 - Present", "June 2020 - August 2020", "Jan 2021 - Dec 2021"
    - Handle various formats: "May 2018 - Present", "Summer 2020", "2021 - 2022"
    - If no dates provided, set to null

    6. For CONTENT field:
    - Extract ALL additional information about the work experience that doesn't fit into the other fields
    - Include job responsibilities and duties (preserve bullet points with • or - if present)
    - Include achievements and accomplishments with metrics (e.g., "Reduced costs by 30%", "Increased efficiency by 50%")
    - Include technologies, tools, and software used (e.g., "Python, React, AWS")
    - Include specific projects worked on
    - Include team information (e.g., "Led team of 5 engineers")
    - Include methodologies used (e.g., "Agile", "Scrum")
    - Preserve the original formatting and bullet points structure
    - IMPORTANT: Each bullet point MUST be on a new line - separate each bullet point with a newline character (\\n)
    - Example: "• First bullet\\n• Second bullet\\n• Third bullet"
    - If no additional content, set to null or empty string

    7. SEPARATE ENTRIES:
    - Each job/position should be a separate entry
    - If multiple positions at the same company are listed, create separate entries
    - Example: "Software Engineer (2020-2022) and Senior Software Engineer (2022-Present)" should become two entries

    Return ONLY the JSON array, no other text. If no experience entries are found, return an empty array [].

    Example output:
    [
        {{
            "title": "Process Engineer",
            "company": "Marathon Petroleum Company",
            "location": "St. Paul, MN",
            "duration": "May 2018 - Present",
            "content": "• Led process optimization initiatives resulting in 15% cost reduction\\n• Managed production operations for 3 major units\\n• Collaborated with cross-functional teams to improve safety protocols"
        }},
        {{
            "title": "Software Engineer Intern",
            "company": "Google Inc.",
            "location": "Mountain View, CA",
            "duration": "June 2020 - August 2020",
            "content": "• Developed web applications using React and Node.js\\n• Collaborated with team of 8 engineers on search optimization\\n• Implemented features used by 10M+ users"
        }},
        {{
            "title": "Research Assistant",
            "company": "University of Michigan",
            "location": "Ann Arbor, MI",
            "duration": "Jan 2021 - Dec 2021",
            "content": "• Conducted laboratory experiments on polymer synthesis\\n• Analyzed data using Python and MATLAB\\n• Co-authored 2 peer-reviewed publications"
        }}
    ]'''

    try:
        completion = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt}
            ]
        )
        
        response = completion.choices[0].message.content

        # Parse JSON response and return as Python dictionary
        experience_entries = json.loads(response)

        for entry in experience_entries:
            entry['content'] = entry['content'].replace('\n','<br>')

        return experience_entries if experience_entries else []

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return []
    except Exception as e:
        print(f"Error parsing experience: {e}")
        return []


async def parse_projects(context: str) -> list:

    """
    Parse projects, research, publications, presentations, and other academic/professional work from resume text and return structured data.
    
    Expected input format examples:
    - "Stock Dashboard Application\nWheaton, IL\nPersonal Project\nAug 2025 - Oct 2025\n• Built using React and Python\n• Real-time stock data integration"
    - "Production of Light Olefins from Methanol\nUniversity of Michigan\nAnn Arbor, MI\nJan 2025 - Apr 2025\n• Capstone research project\n• Process optimization and analysis"
    - "Machine Learning in Healthcare\nIEEE Conference 2024\nSan Francisco, CA\nMarch 2024\n• Presented research findings\n• Published in conference proceedings"
    """

    prompt = f'''You are analyzing a resume's projects/research section to extract structured project entries. 

    RESUME PROJECTS/RESEARCH TEXT:
    {context}

    Extract each project/research entry and return a JSON array where each entry follows this exact structure:
    {{
        "project": "Project/Research/Publication name (e.g., 'Stock Dashboard Application', 'Production of Light Olefins from Methanol', 'Machine Learning in Healthcare')",
        "location": "City, State format (e.g., 'Wheaton, IL', 'Ann Arbor, MI', 'San Francisco, CA') or 'Remote' if specified",
        "affiliation": "University/Organization/Project type (e.g., 'Personal Project', 'University of Michigan', 'IEEE Conference 2024', 'Capstone Project')",
        "duration": "Start date - End date format (e.g., 'Aug 2025 - Oct 2025', 'Jan 2025 - Apr 2025', 'March 2024')",
        "content": "All additional details about the project (e.g., descriptions, technologies used, outcomes, achievements, technical details, bullet points)"
    }}

    PARSING RULES:
    1. Extract ALL project/research entries from the text, including:
    - Personal projects, side projects, portfolio projects
    - Research projects, capstone projects, thesis work
    - Publications, papers, journal articles
    - Conference presentations, talks, workshops
    - Patents, inventions, innovations
    - Academic projects, coursework projects
    - Open source contributions, GitHub projects
    - Hackathons, competitions, contests

    2. For PROJECT field:
    - Extract the exact project/research/publication name as written
    - Examples: "Stock Dashboard Application", "Production of Light Olefins from Methanol", "Machine Learning in Healthcare"
    - For publications, use the paper title
    - For presentations, use the presentation title
    - For patents, use the patent title or invention name

    3. For LOCATION field:
    - Format as "City, State" (e.g., "Wheaton, IL", "Ann Arbor, MI", "San Francisco, CA")
    - If no location specified, set to null
    - Handle various formats: "Wheaton, IL", "Ann Arbor, MI", "Remote"
    - For virtual/online projects, use "Remote" or null

    4. For AFFILIATION field:
    - Extract the university, organization, or project type
    - Examples: "Personal Project", "University of Michigan", "IEEE Conference 2024", "Capstone Project"
    - For personal projects, use "Personal Project" or the closest relevant text that is in the context
    - For academic work, use the university name
    - For conferences, use the conference name
    - For company projects, use the company name
    - For open source, use "Open Source" or the organization name

    5. For DURATION field:
    - Preserve the exact date format as shown in the resume
    - Examples: "Aug 2025 - Oct 2025", "Jan 2025 - Apr 2025", "March 2024"
    - Handle various formats: "Aug 2025 - Oct 2025", "Summer 2024", "2024", "Ongoing"
    - Duration can also be a single date, like "Aug 2025"
    - If no dates provided, set to null

    6. For CONTENT field:
    - Extract ALL additional information about the project that doesn't fit into the other fields
    - Include project descriptions and objectives
    - Include technologies, programming languages, tools, and frameworks used (e.g., "Built with React, Node.js, MongoDB")
    - Include technical details and methodologies (e.g., "Implemented machine learning algorithms", "Used Agile methodology")
    - Include project outcomes, results, and metrics (e.g., "Achieved 95% accuracy", "Reduced processing time by 40%")
    - Include features and functionality implemented
    - Include team information if mentioned (e.g., "Collaborated with 3 team members")
    - Include awards or recognition (e.g., "Won Best Project Award")
    - Preserve bullet points with • or - if present
    - IMPORTANT: Each bullet point MUST be on a new line - separate each bullet point with a newline character (\\n)
    - Example: "• Built application with React\\n• Integrated API for data\\n• Deployed on AWS"
    - If no additional content, set to null or empty string

    7. SEPARATE ENTRIES:
    - Each project/research/publication should be a separate entry
    - If multiple related works are listed together, create separate entries
    - Example: "Paper A (2023) and Paper B (2024)" should become two entries

    Return ONLY the JSON array, no other text. If no project entries are found, return an empty array [].

    Example output:
    [
        {{
            "project": "Stock Dashboard Application",
            "location": "Wheaton, IL",
            "affiliation": "Personal Project",
            "duration": "Aug 2025 - Oct 2025",
            "content": "• Built using React and Python with real-time stock data integration\\n• Implemented interactive charts and portfolio tracking features\\n• Integrated yfinance API for live market data\\n• Deployed on AWS with CI/CD pipeline"
        }},
        {{
            "project": "Production of Light Olefins from Methanol",
            "location": "Ann Arbor, MI",
            "affiliation": "University of Michigan",
            "duration": "Jan 2025 - Apr 2025",
            "content": "• Capstone research project on chemical process optimization\\n• Designed and simulated production process using Aspen Plus\\n• Achieved 85% conversion efficiency in laboratory trials\\n• Presented findings to faculty panel and industry experts"
        }},
        {{
            "project": "Machine Learning in Healthcare",
            "location": "San Francisco, CA",
            "affiliation": "IEEE Conference 2024",
            "duration": "March 2024",
            "content": "• Presented research on predictive diagnostics using neural networks\\n• Published in IEEE conference proceedings\\n• Achieved 94% accuracy in disease prediction model\\n• Collaborated with medical professionals from 3 hospitals"
        }}
    ]'''

    try:
        completion = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt}
            ]
        )
        
        response = completion.choices[0].message.content

        # Parse JSON response and return as Python dictionary
        project_entries = json.loads(response)

        for entry in project_entries:
            entry['content'] = entry['content'].replace('\n','<br>')
        
        return project_entries if project_entries else []

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return []
    except Exception as e:
        print(f"Error parsing projects: {e}")
        return []
        
async def parse_skills(context: str) -> str:
    bullets = ['*', '•', '•', '·', '◦', '▪', '▫', '', '', '']
    for word in context:
        if word in bullets:
            context = context.replace(word, '•')
    context = context.replace('\n', '<br>')
    return context