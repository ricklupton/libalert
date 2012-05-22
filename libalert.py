import traceback
from datetime import date, timedelta

from libemail import Emailer
import handlers

class LibraryAlert(object):
  """
  Main LibraryAlert class.
  """
  def __init__(self, config):
    self.config = config
    
  def get_handler(self, library_name):
    "Return a handler for the library."
    library_config = self.config.libraries[library_name]
    handler = handlers.HANDLERS[library_config['type']]
    return handler(library_config['url'])

  def get_user_loans(self, username):
    "Return a list of loans for the user."
    user_details = self.config.users[username]
    library_name = user_details['library']
    handler = self.get_handler(library_name)
    loans = handler.get_user_loans(user_details['number'], user_details['pin'])
    return loans

  def next_returns_day(self, returns_days):
    """
    Returns date of next book returning day.
    returns_days is list of weekdays (numbers 1-7).
    """
    today = date.today()
    for d in range(7):
      day = today + timedelta(days=d)
      if day.isoweekday() in returns_days:
        return day
    return today # assume any day if didn't find a better answer

  def user_needs_notification(self, username, duedate):
    """Check if the user should be notified about a book due on duedate.
    
    Notify user if duedate is within days_notice days, but only if today is a
    day that the user can return books: e.g. if books are only returned at
    the weekend, don't notify about a book due on Monday until the Friday
    or Saturday before.
    
    If the book will be due back before the next returns day, notify anyway.
    """
    details = self.config.users[username]
    next_returns_day = self.next_returns_day(details['returns-days'])
    is_urgent = (duedate <= next_returns_day)
    today_is_returns_day = (next_returns_day == date.today())
    within_days_notice = (duedate - date.today()).days < details['days-notice']
    return is_urgent or (today_is_returns_day and within_days_notice)

  def check_loans(self, users=None, send_email=True, testing=False):
    """
    Check users' loans and send emails if books are nearly due.
    
    Arguments
    ---------
    users      : list of usernames to check, or None to check all active users
    send_email : whether to send emails when books are nearly due
    testing    : if True, email the administrator rather than the users
    
    Returns
    -------
    Returns (loans, errors)
    loans  : a dictionary of users and their list of loans
    errors : a list of error messages
    """
    if users is None:
      users = self.config.users.keys()
    today = date.today()
    emailer = Emailer(self.config)
    all_loans = {}
    errors = []
    for username in users:
        print "---- {} ----".format(username)
        try:
            all_loans[username] = loans = self.get_user_loans(username)
            
            any_notify = False
            for (duedate,desc) in loans:
                notify = self.user_needs_notification(username, duedate)
                print "{:2}{}  {}".format(
                    notify * '*', duedate.strftime('%d/%m/%Y'), desc )
                any_notify = any_notify or notify
    
            if send_email and any_notify:
                details = self.config.users[username]
                if testing:
                    to = (self.config.admin_name, self.config.admin_email)
                else:
                    to = (username, details['email'])
                library = self.config.libraries[ details['library'] ]
                emailer.send_loans_email(to, loans, library['url'])
            else:
                print "No reminders needed."
        except Exception as e:
            print "Error: %s" % e
            errors.append('Error checking loans for {}:\n{}'.format(
                                            username, traceback.format_exc()))
    
    if errors:
      emailer.send_failure_email('\n\n'.join(errors))
    
    return all_loans, errors