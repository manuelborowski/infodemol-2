from app.application.utils import datetime_to_dutch_datetime_string, formiodate_to_datetime, datetime_to_formiodate
from app.data import settings as msettings, guest as mguest
from app import email, log, email_scheduler, flask_app
import datetime, time, re, sys
from flask_mail import Message


def send_email(to, subject, content):
    sender = flask_app.config['MAIL_USERNAME']
    msg = Message(sender=sender, recipients=[to], subject=subject, html=content)
    try:
        email.send(msg)
        return True
    except Exception as e:
        log.error(f'send_email: ERROR, could not send email: {e}')
    return False


def send_register_ack(**kwargs):
    try:
        if not msettings.get_configuration_setting('enable-send-ack-email'):
            return False
        guest = mguest.get_first_not_sent_ack()
        if not guest:
            return False
        email_send_max_retries = msettings.get_configuration_setting('email-send-max-retries')
        if guest.email_send_retry >= email_send_max_retries:
            guest.set_enabled(False)
            return False
        guest.set_email_send_retry(guest.email_send_retry + 1)

        email_subject = msettings.get_configuration_setting('register-mail-ack-subject-template')
        email_content = msettings.get_configuration_setting('register-mail-ack-content-template')

        timeslot = datetime_to_dutch_datetime_string(guest.timeslot)
        physical_date = datetime.datetime(2022, 2, 8, 23, 59)

        email_subject = email_subject.replace('{{TAG_TIMESLOT}}', timeslot)

        if guest.timeslot <= physical_date:
            email_content = re.sub('{{TAG_1_START}}', '', email_content)
            email_content = re.sub('{{TAG_1_STOP}}', '', email_content)
            email_content = email_content.replace('{{TAG_TIMESLOT}}', timeslot)
        else:
            email_content = re.sub('{{TAG_1_START}}.*{{TAG_1_STOP}}', '', email_content)

        url_tag = re.search('{{[^}]*\|TAG_UPDATE_URL}}', email_content)
        url_text = url_tag.group(0).split('|')[0].split('{{')[1]
        url = f'{msettings.get_configuration_setting("base-url")}/register?code={guest.code}'
        url_template = f'<a href={url}>{url_text}</a>'
        email_content = re.sub('{{[^}]*\|TAG_UPDATE_URL}}', url_template, email_content)

        url_tag = re.search('{{[^}]*\|TAG_ENTER_URL}}', email_content)
        url_text = url_tag.group(0).split('|')[0].split('{{')[1]
        url = f'{msettings.get_configuration_setting("base-url")}/enter'
        url_template = f'<a href={url}>{url_text}</a>'
        email_content = re.sub('{{[^}]*\|TAG_ENTER_URL}}', url_template, email_content)

        log.info(f'"{email_subject}" to {guest.email}')
        ret = send_email(guest.email, email_subject, email_content)
        if ret:
            guest.set_ack_email_sent(True)
            guest.set_nbr_ack_sent(guest.nbr_ack_sent + 1)
            return ret
        return False
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return False


def send_invite(**kwargs):
    try:
        if not msettings.get_configuration_setting('enable-send-invite-email'):
            return False
        guest = mguest.get_first_not_sent_invite()
        if not guest:
            return False
        email_send_max_retries = msettings.get_configuration_setting('email-send-max-retries')
        if guest.email_send_retry >= email_send_max_retries:
            guest.set_enabled(False)
            return False
        guest.set_email_send_retry(guest.email_send_retry + 1)

        email_subject = msettings.get_configuration_setting('invite-mail-subject-template')
        email_content = msettings.get_configuration_setting('invite-mail-content-template')

        if guest.nbr_invite_sent > 0:
            email_reminder_subject_prefix = msettings.get_configuration_setting('invite-mail-subject-reminder-template')
            email_subject = f'{email_reminder_subject_prefix}{email_subject}'
        url_tag = re.search('{{.*\|TAG_URL}}', email_content)
        url_text = url_tag.group(0).split('|')[0].split('{{')[1]
        url = f'{msettings.get_configuration_setting("base-url")}/register?code={guest.code}'
        url_template = f'<a href={url}>{url_text}</a>'
        email_content = re.sub('{{.*\|TAG_URL}}', url_template, email_content)
        log.info(f'"{email_subject}" to {guest.email}')
        ret = send_email(guest.email, email_subject, email_content)
        if ret:
            guest.set_invite_email_sent(True)
            guest.set_nbr_invite_sent(guest.nbr_invite_sent + 1)
            return ret
        return False
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return False




send_email_config = [
    {'function': send_register_ack, 'args': {}},
    {'function': send_invite, 'args': {}},
]


run_email_task = True
def send_email_task():
    nbr_sent_per_minute = 0
    while run_email_task:
        with flask_app.app_context():
            at_least_one_email_sent = True
            start_time = datetime.datetime.now()
            job_interval = msettings.get_configuration_setting('email-task-interval')
            emails_per_minute = msettings.get_configuration_setting('emails-per-minute')
            while at_least_one_email_sent:
                at_least_one_email_sent = False
                for send_email in send_email_config:
                    if run_email_task and msettings.get_configuration_setting('enable-send-email'):
                        ret = send_email['function'](**send_email['args'])
                        if ret:
                            nbr_sent_per_minute += 1
                            now = datetime.datetime.now()
                            delta = now - start_time
                            if (nbr_sent_per_minute >= emails_per_minute) and (delta < datetime.timedelta(seconds=60)):
                                time_to_wait = 60 - delta.seconds + 1
                                log.info(f'send_email_task: have to wait for {time_to_wait} seconds')
                                time.sleep(time_to_wait)
                                nbr_sent_per_minute = 0
                                start_time = datetime.datetime.now()
                            at_least_one_email_sent = True
        if run_email_task:
                now = datetime.datetime.now()
                delta = now - start_time
                if delta < datetime.timedelta(seconds=job_interval):
                    time_to_wait = job_interval - delta.seconds
                    time.sleep(time_to_wait)


def set_base_url(url):
    msettings.set_configuration_setting('base-url', url)


def stop_send_email_task():
    global run_email_task
    run_email_task = False


def start_send_email_task():
    running_job = email_scheduler.get_job('send_email_task')
    if running_job:
        email_scheduler.remove_job('send_email_task')
    email_scheduler.add_job('send_email_task', send_email_task)

start_send_email_task()

