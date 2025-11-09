import re
import spacy
import os
import PyPDF2
import sys

from io import BytesIO
from dotenv import load_dotenv

from spacy.matcher import PhraseMatcher

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from keywords import common_words, keywords, eng_keywords, resume_headers, job_titles_keywords, education_headers, experience_headers, skills_headers, projects_headers, misc_headers
from models import Resume

from .parse_sections import parse_education, parse_experience, parse_projects, parse_skills#, parse_misc?




nlp = spacy.load("en_core_web_sm")

def get_text_from_pdf(file_bytes) -> str:

    #put binary file data into a format PyPDF2 can work with
    pdf_file = BytesIO(file_bytes)

    #PDF reader object is able to extract text from the PDF
    pdf_reader = PyPDF2.PdfReader(pdf_file)

    text = str()

    for page in pdf_reader.pages:
        text += page.extract_text()

    
    return text

def clean_text(text: str) -> str:
    
    text = text.replace('\n', ' ')
    text = text.replace(',', ' ')
    text = text.replace('•', ' ')

    #remove everything except letters, numbers, spaces, and some special characters and replace with a space
    text = re.sub(r"[^\w\s\.\+\&\#\-\/]", " ", text)
    #remove extra spaces
    text = re.sub(r"(\s+)", " ", text).strip() 

    return text

def extract_keywords_and_phrases(text: str, allowed_pos = ["NOUN", "PROPN", "ADJ", "VERB"], snippet_length = 40) -> dict:
    
    #use spacy to process the text
    doc = nlp(text)
    #dictionary to hold important words while preserving order
    important_words = dict()

#----Initialize PhraseMatcher and define phrases to match----# 
    #a phrase matcher object allows spacy to group together multi-word phrases
    #nlp.vocab is essentially a dictionary of all words spacy knows about
    #attr="LOWER" makes the matcher case insensitive
    phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

    # Convert phrases into spaCy docs so phrase matcher is able to read them properly
    phrase_patterns = []
    for phrase in eng_keywords:
        phrase_patterns.append(nlp.make_doc(phrase))

    #Adds the phrase patterns to the matcher in order to identify them in the text, now phrase matcher knows which phrases to look for
    phrase_matcher.add("eng_keywords", phrase_patterns)

#----Use PhraseMatcher to find phrases in the text----#
    matches = phrase_matcher(doc)
    for match_id, start, end in matches:
        #finds the matched text in the original document
        match_span = doc[start:end]
        lemma = match_span.lemma_.lower()
        display_form = match_span.text.lower()
        if lemma not in important_words:
            idx = match_span.start_char
            snippet = text[max(0, idx-snippet_length):idx+snippet_length].strip()
            important_words[lemma] = {'count': 1, 'snippet': snippet,'form_count': {display_form: 1}, 'display_form': display_form}
        else:
            important_words[lemma]['count'] += 1
            #put the display form of the word into a dictionary to keep track of how many times each form appears
            forms = important_words[lemma]['form_count']
            forms[display_form] = forms.get(display_form, 0) + 1
            #return all form_items: {"engineer": 3, "engineering": 5}
            form_items = list(forms.items())
            #find the form item that has the highest count using lammbda to get the result from each tuple
            most_common_form = max(form_items, key=lambda x: x[1])[0]
            important_words[lemma]['display_form'] = most_common_form

    # Convert dictionary to list of dictionaries
    keywords_list = []
    for lemma, data in important_words.items():
        keywords_list.append({
            'lemma': lemma,
            'display_form': data['display_form'],
            'count': data['count'],
            'snippet': data['snippet'],
            'form_count': data['form_count']
        })
    
    return keywords_list

def extract_name(text: str) -> str:
    """
    Extract the candidate's name from resume text.
    Usually the first substantial line that looks like a name.
    """
    lines = text.splitlines()
    
    for line in lines:
        clean_line = line.strip()
        
        # Skip empty lines
        if not clean_line:
            continue
            
        # Skip lines that are clearly not names
        if (clean_line.startswith(('-', '*', '•', '•', 'o', '·', '◦', '▪', '▫')) or
            len(clean_line) > 50 or
            clean_line.lower() in ['resume', 'cv', 'curriculum vitae'] or
            '@' in clean_line or
            'http' in clean_line.lower() or
            any(char.isdigit() for char in clean_line)):
            continue
            
        # Check if line looks like a name (2-4 words, title case, no special chars)
        words = clean_line.split()
        if (2 <= len(words) <= 4 and 
            clean_line.istitle() and 
            all(word.isalpha() or word in ['-', "'", '.'] for word in words)): #makes sure all words in the line are either alphabetical or one of these punctuation marks
            return clean_line
    
    return "Name Not Found"

def extract_phone(text: str) -> str:
    """
    Extract phone number from resume text using regex patterns.
    """
    import re
    
    # Phone number patterns (US and international)
    phone_patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (555) 123-4567, 555-123-4567, 555.123.4567
        r'\+1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # +1 555 123 4567
        r'\+\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}',  # International
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # 555 123 4567
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Return the first valid phone number found
            phone = matches[0]
            # Clean up the phone number
            phone = re.sub(r'[^\d+]', '', phone) #replaces any character that is not a digit or a plus sign
            if len(phone) >= 10:  # Basic validation
                return phone
    
    return "Phone Not Found"

def extract_email(text: str) -> str:
    """
    Extract email address from resume text using regex.
    """
    import re
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    
    if matches:
        return matches[0]  # Return first email found
    
    return "Email Not Found"

def extract_linkedin(text: str) -> str:
    """
    Extract LinkedIn profile URL from resume text.
    """
    
    linkedin_patterns = [
        # Standard LinkedIn profile URLs with /in/
        r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+/?',
        r'linkedin\.com/in/[a-zA-Z0-9-]+/?',
        r'www\.linkedin\.com/in/[a-zA-Z0-9-]+/?',
        # LinkedIn URLs without /in/ (direct profile URLs)
        r'https?://(?:www\.)?linkedin\.com/[a-zA-Z0-9-]+/?',
        r'linkedin\.com/[a-zA-Z0-9-]+/?',
        r'www\.linkedin\.com/[a-zA-Z0-9-]+/?'
    ]
    
    for pattern in linkedin_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            linkedin_url = matches[0]
            # Ensure it has proper protocol
            if not linkedin_url.startswith('http'):
                linkedin_url = 'https://' + linkedin_url
            return linkedin_url
    
    return "LinkedIn Not Found"

def extract_github(text: str) -> str:
    """
    Extract GitHub profile URL from resume text.
    Handles both GitHub profiles (github.com/username) and GitHub Pages (username.github.io).
    """
    
    github_patterns = [
        # GitHub profiles: github.com/username
        r'https?://(?:www\.)?github\.com/[a-zA-Z0-9-]+/?',
        r'github\.com/[a-zA-Z0-9-]+/?',
        r'www\.github\.com/[a-zA-Z0-9-]+/?',
    ]
    
    for pattern in github_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            github_url = matches[0]
            # Ensure it has proper protocol
            if not github_url.startswith('http'):
                github_url = 'https://' + github_url
            return github_url
    
    return "GitHub Not Found"

def extract_website(text: str) -> str:
    """
    Extract website URL from resume text.
    Filters out websites that are part of sentences or bullet points.
    """
    import re
    
    website_patterns = [
    # Full URLs with http/https and any subdomain
    r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[a-zA-Z0-9._~:/?#[\]@!$&\'()*+,;=-]*)?(?=\s|$)',
    # URLs starting explicitly with www.
    r'www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?',
    # Bare domains (no protocol, no www), including custom TLDs like github.io
    r'[a-zA-Z0-9.-]+\.(?:com|org|net|edu|gov|io|co|me|info|biz|github\.io)(?:/[^\s]*)?',
    # GitHub Pages: username.github.io
    r'https?://[a-zA-Z0-9-]+\.github\.io/?',
    r'[a-zA-Z0-9-]+\.github\.io/?'
]
    
    for pattern in website_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            website_url = matches[0]
            # Skip LinkedIn and GitHub URLs (handled separately)
            if any(service in website_url.lower() for service in ['linkedin.com', 'github.com']):
                continue

            # Skip email domains
            if any(mail_url in website_url.lower() for mail_url in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']):
                continue
                
            # Find the context around the website URL
            url_start = text.lower().find(website_url.lower())
            if url_start == -1:
                continue
                
            # Get context before and after the URL
            context_before = text[max(0, url_start-5):url_start].lower()
            context_after = text[url_start+len(website_url):url_start+len(website_url)+5].lower()

            
            # Filter out websites that are part of sentences/bullets
            # Look for common words that indicate the URL is part of a description
            sentence_indicators = [
                'founded', 'created', 'built', 'developed', 'launched', 'established',
                'gaining', 'achieving', 'reaching', 'serving', 'helping', 'providing',
                'leading to', 'resulting in', 'with', 'for', 'at', 'on', 'in',
                'members', 'users', 'customers', 'clients', 'visitors', 'traffic'
            ]
            
            # Check if context suggests this is part of a sentence
            is_in_sentence = any(indicator in context_before or indicator in context_after 
                               for indicator in sentence_indicators)
            
            # Also check if it's on its own line (more likely to be contact info)
            lines = text.splitlines()
            is_on_own_line = any(website_url.lower() in line.lower() and 
                               len(line.strip().split()) <= 3 for line in lines)
            
            # Skip if it's clearly part of a sentence and not on its own line
            if is_in_sentence and not is_on_own_line:
                continue
                
            # Ensure it has proper protocol
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url
            return website_url
    
    return "Website Not Found"

def extract_contact_info(resume: Resume):
    """
    Extract all contact information from resume text.
    Returns a dictionary with found contact details.
    """
    name = extract_name(resume.plaintext)
    phone = extract_phone(resume.plaintext)
    email = extract_email(resume.plaintext)
    linkedin = extract_linkedin(resume.plaintext)
    github = extract_github(resume.plaintext)
    website = extract_website(resume.plaintext)
    
    if name != "Name Not Found":
        resume.name = name
    if phone != "Phone Not Found":
        resume.contact_info['phone'] = phone
    if email != "Email Not Found":
        resume.contact_info['email'] = email
    if linkedin != "LinkedIn Not Found":
        resume.contact_info['linkedin'] = linkedin
    if github != "GitHub Not Found":
        resume.contact_info['github'] = github
    if website != "Website Not Found":
        resume.contact_info['website'] = website

async def extract_section_headers(resume: Resume):
    """
    Extract all section headers from resume text and populate resume.sections as list of dicts.
    """
    print('Extracting section headers...')
    headers_with_indices = []
    lines = resume.plaintext.splitlines()
    bullets = ['*', '•', '•', '·', '◦', '▪', '▫', '', '']
        
    for idx, line in enumerate(lines):
        clean = line.strip()

        if not clean:
            continue

        for bullet in bullets:
            if clean.startswith(bullet):
                continue

        # Skip lines that are too long (likely content, not headers)
        if len(clean) > 50:
            continue
        
        # Check if line matches known resume headers (case insensitive)
        clean_lower = clean.lower()
        for header in resume_headers:
            if clean_lower == header.lower() or clean_lower in header.lower():
                headers_with_indices.append((idx, clean))
                break
                    
        # Also check for common header patterns even if not in our list
        if (clean_lower.endswith('experience') or 
            clean_lower.endswith('education') or 
            clean_lower.endswith('skills') or
            clean_lower.endswith('projects') or
            clean_lower.endswith('certifications') or
            clean_lower.endswith('awards') or
            clean_lower.endswith('publications')):
            if not any(clean_lower == existing[1].lower() for existing in headers_with_indices):
                headers_with_indices.append((idx, clean))

        # Sort headers by their position in the document
        headers_with_indices.sort(key=lambda x: x[0])

    
    # Extract sections between headers
    # Fed to extract_sections to functions to extract various entries
    sections = {}


    for i, (idx, header) in enumerate(headers_with_indices):
         start_idx = idx + 1
         if i + 1 < len(headers_with_indices):
             end_idx = headers_with_indices[i+1][0]
         else:
             end_idx = len(lines)

         section_lines = lines[start_idx:end_idx]
         
         # Filter out empty lines and clean up content
         section_content = "\n".join([line.strip() for line in section_lines if line.strip()])

         if header not in sections:
             sections[header] = section_content
            

    return sections

async def extract_sections(sections: dict, resume: Resume):
    for header in sections:
        if header.lower() in education_headers:
            #parses education entries for degree, school, location, duration, and section content
            education_entries = await parse_education(sections[header])       
            # Create a proper section structure for education
            education_section = {
                "type": "education",
                "header": header,
                "entries": education_entries,  # This is a list of education entries
            }
         #   print(education_section[header])

            resume.sections.append(education_section)

        elif header.lower() in experience_headers:
            #parses experience entries for title, company, location, duration, and section content
            experience_entries = await parse_experience(sections[header])
            experience_section = {
                "type": "experience",
                "header": header,
                "entries": experience_entries #IF SATARTS WITH BULLET POINTS, THEN IT IS THE CONTENT
            }

            resume.sections.append(experience_section)

        elif header.lower() in projects_headers:
            #parses project entries for project, location, affiliation, duration, and section content
            print(f'=== parse_projects INPUT: {sections[header]} ===')
            projects_entries = await parse_projects(sections[header])
            projects_section = {
                "type": "projects",
                "header": header,
                "entries": projects_entries
            }
            resume.sections.append(projects_section)

        elif header.lower() in skills_headers:
            #no parsing function, minimal styling needed for skills section
            skills_content = await parse_skills(sections[header])
            skills_section = {
                "type": "skills",
                "header": header,
                "content": skills_content
            }

            resume.sections.append(skills_section)


        elif header.lower() in misc_headers:
            #no parsing function, minimal styling needed for misc section
            misc_section = {
                "type": "misc",
                "header": header,
                "content": sections[header]
            }
            resume.sections.append(misc_section)

        else:
            catch_all_section = {
                "type": "catch_all",
                "header": header,
                "content": sections[header]
            }
            resume.sections.append(catch_all_section)


def clean_content(content: str) -> str:
    """
    Clean the content of the section.
    """
    bullets = ['*', '•', '•', '·', '◦', '▪', '▫', '']

    for word in content:
        for bullet in bullets:
            word = word.replace(bullet, '•')
    
    return content

