from fastapi.responses import HTMLResponse
from models import Resume
from parse.parse_plaintext import extract_contact_info, extract_section_headers, extract_sections


async def format_resume(text: str, resume: Resume) -> HTMLResponse:
    """
    Format resume text into a structured HTML layout with editable sections.
    Clean version with contact information extraction.
    """
    try:
        #extract contact information
        extract_contact_info(resume)

        #extract section headers
        sections = await extract_section_headers(resume)

        #use section headers and content to populate resume sections dictionary with information
        #COMMENTED OUT FOR FORMAT TESTING FOR NOW
        #REMEMBER
        #TO
        #PUT THIS BACK IN AHHHHHH!!!!!
        await extract_sections(sections, resume)



        # Generate HTML content
        html_content = "<div class='resume'>"
        
        #Put name in html_content
        html_content += f"""<div class='name'>
                            <h1 class='name'>{resume.name}</h1>
                        </div>"""
        
        if resume.contact_info:
            html_content += f"""<div class='contact-info'>
                            <ul class='contact-info'>"""

            for value in resume.contact_info.values():
                html_content += f"""<li class='contact-info'><a href='{value}'>{value}</a></li>"""
                
            html_content += f"""</ul></div>"""

        if resume.sections:
            html_content += f"""<div class='resume-sections'>"""

            for section in resume.sections:
                if section['type']:
                    html_content += f"""<div class='section-header'>{section['header']}</div>
                                        """

                if section['type'] == "education":
                    for i in range(0, len(section['entries'])):
                        html_content += f"""<div class='first-line'><ul class='first-line-ul'><li>{section['entries'][i]['school']}</li>
                                                                        <li>{section['entries'][i]['location']}</li></ul></div>
                                            <div class='second-line'><ul class='second-line-ul'><li>{section['entries'][i]['degree']}</li>
                                                                        <li>{section['entries'][i]['duration']}</li></ul></div>
                                            <div class='section-content'>{section['entries'][i]['content']}</div>"""

                elif section['type'] == "experience":
                    for i in range(0, len(section['entries'])):
                        html_content += f"""<div class='first-line'><ul class='first-line-ul'><li>{section['entries'][i]['company']}</li>
                                                                        <li>{section['entries'][i]['location']}</li></ul></div>
                                            <div class='second-line'><ul class='second-line-ul'><li>{section['entries'][i]['title']}</li>
                                                                        <li>{section['entries'][i]['duration']}</li></ul></div>
                                            <div class='section-content'>{section['entries'][i]['content']}</div>"""
                
                elif section['type'] == "skills":
                    html_content += f"""<div class='section-content'>{section['content']}</div>
                                    """

                elif section['type'] == "projects":
                    for i in range(0, len(section['entries'])):
                        html_content += f"""<div class='first-line'><ul class='first-line-ul'><li>{section['entries'][i]['project']}</li>
                                                                        <li>{section['entries'][i]['location']}</li></ul></div>
                                            <div class='second-line'><ul class='second-line-ul'><li>{section['entries'][i]['affiliation']}</li>
                                                                        <li>{section['entries'][i]['duration']}</li></ul></div>
                                            <div class='section-content'>{section['entries'][i]['content']}</div>"""

                elif section['type'] == "skills":
                    pass

                elif section['type'] == "other":
                    pass

        html_content += """
            </div>
            </div>
            <script>
                document.getElementById('get-job-description').style.display = 'block';
                document.getElementById('export-button').style.display = 'block';
                document.getElementbyClass('resume').style.display = 'block';
            </script>
        """


        return HTMLResponse(html_content)
        
    except Exception as e:
        print(f"Error in format_resume: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse("<h1>Error processing resume</h1><p>Check console for details.</p>")

