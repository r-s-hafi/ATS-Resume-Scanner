from typing import Any

class Resume():
    def __init__(self):
        self.plaintext: str = ""
        
        self.name: str = ""
        self.contact_info: dict = {}

        self.keywords: list[str] = []
        self.sections: list[dict[str, Any]] = []
      
       
class Job():
  def __init__(self):
    self.plaintext: str = ""
    self.keywords: list(dict) = []
    self.html: str = ""

class User():
  def __init__(self):
    self.resume = Resume()
    self.job = Job()
    self.resume_html = ""
    self.resume_html_new = ""
    self.matched_keywords = {}
    self.unmatched_keywords = []
    self.current_keyword = ""

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

