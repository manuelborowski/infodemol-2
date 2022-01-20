from app.data import settings as msettings, utils as mutils


def get_configuration_settings():
    return msettings.get_configuration_settings()


def get_configuration_setting(setting):
    return msettings.get_configuration_setting(setting)


def set_configuration_setting(setting, value):
    msettings.set_configuration_setting(setting, value)

def get_embedded_video_template():
    return msettings.get_configuration_setting('embedded-video-template')


def get_floating_video_template():
    return msettings.get_configuration_setting('floating-video-template')


def get_floating_pdf_template():
    return msettings.get_configuration_setting('floating-pdf-template')


def get_floating_document_template():
    return msettings.get_configuration_setting('floating-document-template')


def get_link_template():
    return msettings.get_configuration_setting('link-template')



def set_setting_topic(settings):
    try:
        for k, container in settings.items():
            if 'submit' in container and container['submit']:
                for key, value in container.items():
                    if key in handle_update_setting:
                        if handle_update_setting[key]['cb'](key, value, handle_update_setting[key]['opaque']):
                            msettings.set_configuration_setting(key, value)
                    else:
                        msettings.set_configuration_setting(key, value)
    except Exception as e:
        mutils.raise_error('Could not set settings topic', e)


handle_update_setting = {}


def subscribe_handle_update_setting(topic, cb, opaque):
    handle_update_setting[topic] = {
        'cb': cb,
        'opaque': opaque
    }

