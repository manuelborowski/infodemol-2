from app.application import reservation as mreservation, settings as msettings, enter as menter, utils as mutils
import re, json


false = False
true = True
null = None


def prepare_registration_form(code):
    ret = mreservation.prepare_reservation(code)
    if ret.result == ret.Result.E_OK:
        available_timeslots = ret.ret['available_timeslots']
        template = ret.ret['template']
        update_available_timeslots(available_timeslots, template, 'radio-timeslot')
        update_template(template, new='new' == ret.ret['mode'] )
    return ret


def prepare_settings_form(form):
    component = search_component(form, 'div-load-guest-file')
    template = msettings.get_configuration_setting('div-load-guest-file')
    component['html'] = template


def update_template(template, new):
    new_header = search_component(template, 'header-new')
    new_header['hidden'] = not new
    update_header = search_component(template, 'header-update')
    update_header['hidden'] = new
    child_name = search_component(template, 'child_name')
    child_name['disabled'] = not new

    misc_config = json.loads(msettings.get_configuration_setting('import-misc-fields'))
    for c in misc_config:
        misc_field = search_component(template, c['veldnaam'])
        misc_field['disabled'] = not new
    email = search_component(template, 'email')
    email['disabled'] = not new
    show_phone = msettings.get_configuration_setting('import-phone-field') != ''
    phone = search_component(template, 'phone')
    phone['hidden'] = not show_phone and not new
    show_name = msettings.get_configuration_setting('import-parentname-field') != ''
    parent_name = search_component(template, 'full_name')
    parent_name['hidden'] = not show_name and not new


def update_available_timeslots(timeslots, form, key):
    components = form['components']
    for component in components:
        if 'key' in component and component['key'] == key:
            values = []
            # component['components'] = []
            for timeslot in timeslots:
                if timeslot['available'] <= 0:
                    continue
                new = {
                    'label': timeslot['label'],
                    'value': timeslot['value'],
                    'shortcut': '',
                }
                values.append(new)
                if timeslot['default']:
                    component['defaultValue'] = timeslot['value']
            component['values'] = values
            return
        if 'components' in component:
            update_available_timeslots(timeslots, component, key)
    return


def search_component(form, key):
    components = form['components']
    for component in components:
        if 'key' in component and component['key'] == key:
            return component
        if 'components' in component:
            found_component = search_component(component, key)
            if found_component: return found_component
    return None


def prepare_enter_form(code):
    #recursive
    def process_items(parent, items):
        for item in items:
            type = item['type']
            child = None
            if type == 'content':
                child = mutils.deepcopy(formio_component_templates['content'])
                child['html'] = item['text']
            elif type == 'embedded-video':
                child = mutils.deepcopy(formio_component_templates['content'])
                youtube_id = get_youtube_id_from_url(item['url'])
                url = f'https://www.youtube.com/embed/{youtube_id}'
                play_options = []
                if 'autostart' in item and item['autostart']:
                    play_options.append('autoplay=1&mute=1')
                if 'loop' in item and item['loop']:
                    play_options.append(f'playlist={youtube_id}&loop=1')
                if play_options:
                    url = f'{url}?{"&".join(play_options)}'
                title = item["title"] if 'title' in item else ''
                tooltip = get_tooltip_from_item(item)
                html = embedded_video_template.replace('{{URL-TAG}}', url)
                html = html.replace('{{TITLE-TAG}}', title)
                child['html'] = html.replace('{{TOOLTIP-TAG}}', tooltip)
            elif type == 'floating-video':
                child = mutils.deepcopy(formio_component_templates['content'])
                tooltip = get_tooltip_from_item(item)
                html = floating_video_template.replace('{{TITLE-TAG}}', item['title'])
                html = html.replace('{{TOOLTIP-TAG}}', tooltip)
                youtube_id = get_youtube_id_from_url(item['url'])
                html = html.replace('{{THUMB-URL-TAG}}', f'https://img.youtube.com/vi/{youtube_id}/sddefault.jpg')
                child['html'] = html.replace('{{URL-TAG}}', f'https://www.youtube.com/watch?v={youtube_id}')
            elif type == 'floating-document':
                child = mutils.deepcopy(formio_component_templates['content'])
                tooltip = get_tooltip_from_item(item)
                thumbnail_link = google_drive_link_to_thumbnail(item)
                html = floating_document_template.replace('{{TITLE-TAG}}', item['title'])
                html = html.replace('{{TOOLTIP-TAG}}', tooltip)
                html = html.replace('{{THUMB-URL-TAG}}', thumbnail_link)
                child['html'] = html.replace('{{URL-TAG}}', item['url'])
            elif type == 'link':
                child = mutils.deepcopy(formio_component_templates['content'])
                tooltip = get_tooltip_from_item(item)
                thumbnail_link = google_drive_link_to_thumbnail(item)
                html = link_template.replace('{{TITLE-TAG}}', item['title'])
                html = html.replace('{{TOOLTIP-TAG}}', tooltip)
                html = html.replace('{{THUMB-URL-TAG}}', thumbnail_link)
                child['html'] = html.replace('{{URL-TAG}}', item['url'])
            elif type == 'columns':
                child = mutils.deepcopy(formio_component_templates['columns'])
                for column in item['columns']:
                    column_template = mutils.deepcopy(formio_component_templates['columns-column'])
                    column_template['width'] = column['width']
                    process_items(column_template['components'], column['content'])
                    child['columns'].append(column_template)
            elif type == 'panel':
                child = mutils.deepcopy(formio_component_templates['panel'])
                child['title'] = item['title']
                child['key'] = f"key-{item['title'].replace(' ', '-')}"
                process_items(child['components'], item['components'])
            # elif type == 'wonder-url':
            #     child = mutils.deepcopy(formio_component_templates['panel'])
            #     child['collapsed'] = False
            #     child['collapsible'] = False
            #     child['title'] = item['title']
            #     wonder_links = menter.get_wonder_links(ret.ret['user'])
            #     for link in wonder_links:
            #         inner_child = mutils.deepcopy(formio_component_templates['content'])
            #         template = mutils.deepcopy(wonder_link_template)
            #         template = template.replace('{{URL-TAG}}', link['link']).replace('{{TIMESLOT-TAG}}', link['timeslot'])
            #         inner_child['html'] = template
            #         child['components'].append(inner_child)
            parent.append(child)
        return parent

    ret = menter.end_user_wants_to_enter(code)
    if ret.ret:
        embedded_video_template = msettings.get_embedded_video_template()
        floating_video_template = msettings.get_floating_video_template()
        floating_document_template = msettings.get_floating_document_template()
        link_template = msettings.get_link_template()
        template = ret.ret['template']
        for tab, items in ret.ret['tabpages'].items():
            tab_component = search_component(template, tab)
            if tab_component:
                process_items(tab_component['components'], items)
    return ret


formio_component_templates = {
    'panel': {
        "collapsible": true,
        "key": "panel2",
        "type": "panel",
        "label": "Dummy Label",
        "input": false,
        "tableView": false,
        "components": [],
        "collapsed": true
    },
    'content': {
        "html": "",
        "label": "Content",
        "refreshOnChange": false,
        "key": "content",
        "type": "content",
        "input": false,
        "tableView": false,
    },
    'columns': {
        "label": "Columns",
        "columns": [],
        "key": "columns",
        "type": "columns",
        "input": false,
        "tableView": false
    },
    'columns-column': {
            "components": [],
            "width": 3,
            "offset": 0,
            "push": 0,
            "pull": 0,
            "size": "md"
        },
}

# in: https://drive.google.com/file/d/1q219q5dDRym0v6IxiqtX-CV1ZelMerW3/view?usp=sharing
# out: https://drive.google.com/thumbnail?id=1q219q5dDRym0v6IxiqtX-CV1ZelMerW3
def google_drive_link_to_thumbnail(item):
    if 'thumb-url' in item:
        match = re.match('.+drive.google.com\/file\/d\/(.+)\/', item['thumb-url'])
        image_link = f'https://drive.google.com/thumbnail?id={match.group(1)}'
        return image_link
    return 'https://drive.google.com/thumbnail?id=1ExD-sGRE-7XVz3qkhwMd8lIMEcBoap4u'


def get_tooltip_from_item(item):
    tooltip = f'title="{item["tooltip"]}"' if 'tooltip' in item else f'title="{item["title"]}"' if 'title' in item else ''
    return tooltip


def get_youtube_id_from_url(url):
    try:
        youtube_id = url.split('v=')[1]
    except:
        youtube_id = url.split('be/')[1]
    return youtube_id

