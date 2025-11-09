from typing import Any

class Resume():
    def __init__(self):
        self.plaintext: str = ""
        
        self.name: str = ""
        self.contact_info: dict = {}

        self.keywords: list[str] = []
        self.sections: list[dict[str, Any]] = []
      #this is just passing in the gpt output as of right now
        #self.sections = [{'type': 'education', 'header': 'EDUCATION', 'entries': [{'degree': 'B.S.E. Chemical Engineering & B.S. Chemistry', 'school': 'University of Michigan', 'location': 'Ann Arbor, MI', 'duration': 'Aug 2021 – May 2025', 'content': 'GPA: 3.90 / 4.00 | Capstone: Production of Light Olefins from Methanol'}]}, {'type': 'experience', 'header': 'EXPERIENCE', 'entries': [{'title': 'Oil Movements (OM) Process Contact Engineer', 'company': 'ExxonMobil', 'location': 'Channahon, IL', 'duration': 'Aug 2025 – Present', 'content': '• Responsible for ~60 on-site storage tanks, performed daily monitoring of key parameters to ensure safe operation of equipment<br>• Designed and executed temporary pump and hose system to meet H2S specification on exported virgin gas oil during unit shutdown'}, {'title': 'Process Engineering Intern', 'company': 'Eli Lilly & Company', 'location': 'Indianapolis, IN', 'duration': 'May 2024 – Aug 2024', 'content': '• Eliminated ergonomic concerns of raw material unloading by scoping out equipment and authoring change control to Quality and HSE standards, saving up to 60 minutes of hazardous operator per batch<br>• Investigated foam-out events to identify issues with current overfill protection equipment and specified new instrumentation to identify foam and enhance foam detection capabilities<br>• Collaborated with another intern to identify critical equipment for inclusion in an automated area shutdown procedure within a GIPSM area of the process<br>• Updated lock-out tag-out (LOTO) procedures to maintain sampling access for purified water lines during tank lockouts'}, {'title': 'Summer Professional Enrichment (SPE) Technical Intern', 'company': 'Evonik Industries', 'location': 'Weston, MI', 'duration': 'May 2023 – Aug 2023', 'content': '• Created a new piping and instrumentation diagram (P&ID) as-built for pump house supplying fire and cooling water to site using BricsCAD software<br>• Established a protocol for tank level strapping and updated several tank level calculations to ensure consistency of level switch activation with level high-high alarm from level transmitter<br>• Investigated two metal grinders on-site through amperage trending and particle size sampling to construct a database to identify when to shorten grind time, preventing unnecessary equipment wear and addressing inefficiencies in procedure'}]}, {'type': 'projects', 'header': 'PROJECTS', 'entries': [{'project': 'Production of Light Olefins from Methanol', 'location': 'Ann Arbor, MI', 'affiliation': 'University of Michigan College of Engineering', 'duration': 'Jan 2025 – Apr 2025', 'content': '• Designed 0.5 MMTPA methanol to olefins (MTO) facility, with 4-stage distillation train achieving 99.5%+ purity separation<br>• Performed class 5 economic analysis to assess economic feasibility, implementing spider diagrams to visualize key economic inputs and sensitivity analysis'}, {'project': 'Stock Dashboard Application', 'location': 'Naperville, IL', 'affiliation': 'Software Development', 'duration': 'Aug 2025', 'content': '• Developed GUI application tracking NYSE stocks with live data feeds, price visualizations, and automated summaries'}, {'project': 'Portfolio Website (ryanshafi.com)', 'location': 'Naperville, IL', 'affiliation': 'Web Development', 'duration': 'Aug 2025', 'content': '• Developed responsive personal website with HTML5/CSS3 showcasing technical projects and experience'}]}, {'type': 'skills', 'header': 'SKILLS', 'content': '• Engineering Software: APEN Plus, AutoCAD, BricsCAD, SolidWorks, Siemens NX, MS 365, Seeq, GMARS<br>• Technical: Bulk material storage, process monitoring, process design, distillation systems, heat integration<br>• Programming: Python, HTML/CSS, JavaScript (learning) | PyQt5, matplotlib | APIs (yfinance, OpenAI) | Git/GitHub'}]
       
class Job():
  def __init__(self):
    self.plaintext: str = ""
    self.keywords: list(dict) = []
    self.html: str = ""

    #self.keywords = [{
    #        'lemma': lemma,
    #       'display_form': data['display_form'],
    #        'count': data['count'],
    #        'snippet': data['snippet'],
    #        'form_count': data['form_count']
    #    }]
        # self.sections = [
        #     {
        #         "type": "education",
        #         "header": str,
        #         "entries": [
        #             {
        #                 "degree": str,
        #                 "school": str,
        #                 "location": str,
        #                 "duration": str,
        #                 "content": str
        #             }
        #         ]
        #     },

        #     {
        #         "type": "experience",
        #         "header": str,
        #         "entries": [
        #             {
        #                 "title": str,
        #                 "company": str,
        #                 "location": str,
        #                 "duration": str,
        #                 "content": str
        #             }
        #         ]
        #     },

        #     {
        #         "type": "projects",
        #         "header": str,
        #         "entries": [
        #             {
        #                 "project": str,
        #                 "location": str,
        #                 "affiliation": str,
        #                 "duration": str,
        #                 "content": str
        #             }
        #         ]
        #     },

        #     {
        #         "type": "skills",
        #         "header": str,
        #         "entries": [
        #             {
        #                 "description": str
        #             }
        #         ]
        #     },

        #     {
        #         "type": "other",
        #         "header": str,
        #         "entries": [
        #             {
        #                 "description": str
        #             }
        #         ]
        #     }
        # ]

