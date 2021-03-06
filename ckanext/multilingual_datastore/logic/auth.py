import ckan.plugins as p


def translate_resource_auth(context, data_dict, privilege='resource_update'):
    if not 'id' in data_dict:
        data_dict['id'] = data_dict.get('resource_id')
    user = context.get('user')

    authorized = p.toolkit.check_access(privilege, context, data_dict)

    if not authorized:
        return {
            'success': False,
            'msg': p.toolkit._('User {0} not authorized to update resource {1}'
                    .format(str(user), data_dict['id']))
        }
    else:
        return {'success': True}


def translate_resource_create(context, data_dict):
    return translate_resource_auth(context, data_dict)


def translate_resource_update(context, data_dict):
    return translate_resource_auth(context, data_dict)


def translate_resource_delete(context, data_dict):
    return translate_resource_auth(context, data_dict, privilege='resource_delete')

def translate_resource_publish(context, data_dict):
    return translate_resource_auth(context, data_dict)


def translate_resource_search(context, data_dict, privilege='resource_show'):
    return translate_resource_auth(context, data_dict)
