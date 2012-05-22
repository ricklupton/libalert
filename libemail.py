# encoding: utf-8

from datetime import date
from email.mime.text import MIMEText
import smtplib, time

def format_duedate(d):
  duestr = d.strftime('%a, %d %b %Y') 
  days = (d - date.today()).days
  if days  < -1: relstr = " (%d days ago)" % -days
  if days  <  0: relstr = " (yesterday)"
  if days ==  0: relstr = " (today)"
  if days  <  0: relstr = " (tomorrow)"
  if days  <  7: relstr = " (in %d days)" % days
  else: relstr = ""
  return duestr + relstr

class Emailer(object):
  def __init__(self, config):
    self.config = config

  def send_loans_email(self, to, books, renewals_url=None): 
    rows = []
    for duedate,description in sorted(books, reverse=True):
      style = ' style="color: red;"' if (duedate <= date.today()) else ''
      rows.append('''
        <tr{style}>
          <td valign="top" align="left">{due}</td>
          <td valign="top" align="left">{desc}</td>
        </tr>
      '''.format(style=style, due=format_duedate(duedate), desc=description))

    # Use unicode message text
    text = u'''
    <center>
    <table bgcolor="#e0cee0" width="100%" cellspacing="0" cellpadding="2">
    <tr>
    <td width="30%" align="left"><b>Due Date</b></td>
    <td width="70%" align="left"><b>Book</b></td>
    </tr>
    {rows}
    </table>
    </center>
    '''.format(rows='\n'.join(rows))
    if renewals_url is not None:
      text += '<p><a href="%s">Click here for renewals.</a></p>' % renewals_url

    return self.send_message(to, text)
    
  def send_failure_email(self, errmsg):
    to = ('Libalert Admin', self.config.admin_email)
    text = u'<pre>\n%s\n</pre>\n' % errmsg
    return self.send_message(to, text, 'Library Alert: Failure')

  def send_message(self, to, text, subject='Library Alert'):
    msg = MIMEText(text, 'html', 'iso-8859-1')
    msg['Subject'] = subject
    msg['From'] = 'Library Alert <%s>' % self.config.admin_email
    msg['To'] = '%s <%s>' % to

    try:
      print "Sending email to %s <%s>" % to
      s = smtplib.SMTP(self.config.smtp_server)
      if self.config.debug_level >= 1:
        s.set_debuglevel(1)

      if self.config.smtp_password:
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(self.config.smtp_email, self.config.smtp_password)
      
      s.sendmail(msg['From'], to[1], msg.as_string())
      s.close()
      
    except smtplib.SMTPException as e:
      print "*** %s ***" % e
      return False
    return True

if __name__ == '__main__':
  from datetime import timedelta
  from libconfig import LibalertConfig
  config = LibalertConfig('config.ini')
  to = (config.admin_name, config.admin_email)
  books = [(date.today() + timedelta(days=2), 'A Novel - Fred Pearce')]
  emailer = Emailer(config)
  try:
    emailer.send_books_email(to, books)
  except Exception as e:
    import traceback
    error = "*** %s ***\n%s" % (e, traceback.format_exc())
    emailer.send_failure_email(error)