#!/usr/bin/env python
"""
Library handler for Sirsi online library catalogues
"""

import re 
import mechanize
from bs4 import BeautifulSoup, Comment
from datetime import date, datetime

def delete_comments(el):
    for comment in el.find_all(text=lambda el: isinstance(el, Comment)):
        comment.extract() # remove comments

class SirsiHandler(object):
    def __init__(self, url):
        self.url = url

    def _get_loans_page(self, number, pin):
        br = mechanize.Browser()
        br.set_handle_robots(False) # robots.txt says we're not allowed
        print 'Loading login page...'
        br.open(self.url)
        br.select_form(name="accessform") # Login form
        br['user_id'] = number
        br['password'] = pin
        print 'Loading loads list...'
        response = br.submit()
        return response.get_data()

    def _get_loans_list(self, page):
        # First check if no items
        if "User has no charges" in page:
            return []
    
        # Otherwise look for list of loans
        soup = BeautifulSoup(page)
        loans = []
        for row in soup.find_all('tr'):
            cls = row.td.get('class', [])
            if 'itemlisting' in cls or 'itemlisting2' in cls:
                delete_comments(row)
                label = row.find('label')
                description = " - ".join(label.stripped_strings)
                duedate = row.find('strong').string
                duedate = datetime.strptime(duedate, "%d/%m/%Y,%H:%M").date()
                loans.append((duedate, description))
        
        if not loans:
            # Didn't see "User has no charges" so should have found some
            raise Exception("Expected loans list but couldn't find one")
        return loans
    
    def get_user_loans(self, number, pin):
        page = self._get_loans_page(number, pin)
        loans = self._get_loans_list(page)
        return loans
        
class SpydusHandler(object):
    def __init__(self, url):
        self.url = url

    def _get_loans_page(self, number, pin):
        br = mechanize.Browser()
        br.set_handle_robots(False) # robots.txt says we're not allowed
        # Refreshes are needed to log in, but page uses refresh to timeout
        # after 20min, and mechanize would wait - so limit time
        br.set_handle_refresh(True, max_time=1)
        
        print 'Loading login page...'
        br.open(self.url)
        br.select_form(nr=0) # Login form - first one - page sets id not name
        br['BRWLID'] = number
        br['BRWLPWD'] = pin
        
        print 'Loading account page...'
        br.submit()
        
        print 'Loading loads list...'
        try:
            response = br.follow_link(text="Current loans")
            return response.get_data()
        except mechanize.LinkNotFoundError:
            # If use has no loans, there is no link
            return None

    def _get_loans_list(self, page):
        # Look for list of loans
        soup = BeautifulSoup(page)
        loans = []
        for row in soup.find_all('tr'):
            tds = row.find_all('td')
            if not tds: continue # e.g. header row
            
            description = " ".join(tds[1].stripped_strings)
            duedate = list(tds[2].stripped_strings)[0]
            duedate = datetime.strptime(duedate, "%d %b %Y").date()
            loans.append((duedate, description))        
        if not loans:
            # If there was a page, should have some items on it
            raise Exception("Expected loans list but couldn't find one")
        return loans
    
    def get_user_loans(self, number, pin):
        page = self._get_loans_page(number, pin)
        if page is not None:
            loans = self._get_loans_list(page)
        else:
            loans = []
        return loans


HANDLERS = {
    'Sirsi': SirsiHandler,
    'Spydus': SpydusHandler,
}