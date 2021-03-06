# -*- encoding: utf-8 -*-
import pylons.config as config
import nose.tools
import json
#import collections
#import copy
import mock
import pprint

import ckan.tests
import ckan.new_tests.factories as factories
import ckan.new_tests.helpers as helpers
import ckan.model as model
import ckan.logic as logic
import ckan.plugins as p

PAGE_STEP = int(config.get('ckanext.multilingual_datastore.resources.page_step', 100))

class TestController(ckan.tests.TestController):

    def __init__(self):
        self.user = factories.User()
        self.organization = factories.Organization(user=self.user)

    def get_context(self):
        print self.user
        return {
                'model':model,
                'session':model.Session,
                'user':self.user['name'],
                #'auth_user_obj': c.userobj,
                #'organization': self.organization['name'],
                'ignore_auth': True,
                'api_version':3,
                }

    ###
    ### Translate Resource Create Tests
    ###

    # If initialize_datastore or get_initial_datastore fail, all tests will fail
    @nose.tools.istest
    def test_a1_initialize_dataset_and_resource(self):
        self._initialize_datastore()

    @nose.tools.istest
    def test_a2_create_translation_resource_noauth(self):
        resource = self._get_initial_datastore(package_data.get('name'))
        context = self.get_context()
        context.update({'ignore_auth':False})

        nose.tools.assert_raises(logic.NotAuthorized, helpers.call_action, 'resource_translation_create', context=context)

    @nose.tools.istest
    def test_a3_create_translation_resource_invalid(self):
        resource = self._get_initial_datastore(package_data.get('name'))
        context = self.get_context()

        # Should raise validation error on all
        incomplete_or_wrong_trans_data = [{
                    'package_id': package_data.get('name'),
                    'resource_id': resource.get('id'),
                    },
                    #{
                    #'package_id': package_data.get('name'),
                    #'resource_id': resource.get('id'),
                    #'language': 1,
                    #},
                    {
                    'package_id': package_data.get('name'),
                    'language': 'gre',
                    },
                    {
                    'package_id': package_data.get('name'),
                    'language':'el',
                    },
                    {
                    'package_id': package_data.get('name'),
                    'resource_id': 'non-existing-resource-id',
                    'language': 'el',
                    },
                    {
                    'package_id': 'non-existing package name',
                    'resource_id': resource.get('id'),
                    'language': 'el',
                    }
                    ]

        for d in incomplete_or_wrong_trans_data:
            nose.tools.assert_raises(p.toolkit.ValidationError,
                                    helpers.call_action, 'resource_translation_create', context = context, **d)

    @nose.tools.istest
    def test_a4_create_translation_resource(self):
        resource = self._get_initial_datastore(package_data.get('name'))
        context = self.get_context()

        # Should create translation resource correctly
        trans_data = [{
                'package_id': package_data.get('name'),
                'resource_id': resource.get('id'),
                'language': 'en',
                },
                {
                'package_id': package_data.get('name'),
                'resource_id': resource.get('id'),
                'language': 'es',
                }]
        for d in trans_data:
            created_res = helpers.call_action('resource_translation_create', context=context, **d)
            assert created_res.get('id')
            assert created_res.get('translation_resource')
            assert created_res.get('translation_status')
            assert created_res.get('language')

    @nose.tools.istest
    def test_a5_create_same_translation_resource(self):
        resource = self._get_initial_datastore(package_data.get('name'))
        context = self.get_context()

        # Should raise validation error since translation resource already exists
        trans_data = {
                'package_id': package_data.get('name'),
                'resource_id': resource.get('id'),
                'language': 'en',
                }
        nose.tools.assert_raises(p.toolkit.ValidationError, helpers.call_action, 'resource_translation_create', context=context, **trans_data)

    ###
    ### Translate Resource Update Tests
    ###
    @nose.tools.istest
    def test_b1_update_translation_resource_invalid(self):
        context = self.get_context()
        resource = self._get_initial_datastore(package_data.get('name'))
        res_en = helpers.call_action('resource_show', context=context, id=json.loads(resource.get('has_translations')).get('en'))

        # Should raise validation error on all
        trans_data = [
                {
                # wrong resource id
                'resource_id': 'wrong-resource-id',
                'language': 'en',
                'mode':'manual',
                'column_name': 'address',
                },
                {
                'resource_id': resource.get('id'),
                # wrong lang code
                'language': 'gr',
                'mode':'manual',
                'column_name': 'wrong-column-name',
                },
                {
                # translation resource id (instead of parent)
                'resource_id': res_en.get('id'),
                'language': 'en',
                'mode':'manual',
                'column_name': 'address',
                },
                {
                'resource_id': resource.get('id'),
                'language': 'en',
                # wrong translation mode
                'mode':'no-such-mode',
                'column_name': 'address',
                },
                {
                'resource_id': resource.get('id'),
                'language': 'en',
                'mode':'manual',
                # wrong column name
                'column_name': 'wrong-column-name',
                }]

        for d in trans_data:
            nose.tools.assert_raises(p.toolkit.ValidationError, helpers.call_action, 'resource_translation_update', context=context, **d)
            #pprint.pprint(helpers.call_action ('resource_translation_update', context=context, **d))

    @nose.tools.istest
    def test_b2_update_translation_resource(self):
        resource = self._get_initial_datastore(package_data.get('name'))
        context = self.get_context()

        # Should create translation resource correctly
        res = helpers.call_action('resource_show', context=context, id=resource.get('id'))
        res_en = helpers.call_action('resource_show', context=context, id=json.loads(res.get('has_translations')).get('en'))
        assert res_en.get('id')
        assert res_en.get('translation_parent_id') == res.get('id')

        # Update same column twice to make sure no conflicts arise
        trans_data = [{
                'resource_id': resource.get('id'),
                'language': 'en',
                'mode':'manual',
                'column_name':'address',
                },
                {
                'resource_id': resource.get('id'),
                'language': 'en',
                'mode':'manual',
                'column_name':'address',
                }]

        for d in trans_data:
            helpers.call_action('resource_translation_update', context=context, **d)
            updated_ds = helpers.call_action('datastore_search', context=context, id=res_en.get('id'))
            assert updated_ds.get('resource_id') == res_en.get('id')
            assert updated_ds.get('total') == 3

    @nose.tools.istest
    def test_b3_update_translation_resource_transcription(self):
        resource = self._get_initial_datastore(package_data.get('name'))
        context = self.get_context()
        #context.update({'locale':'el'})
        # Should create translation resource correctly
        res = helpers.call_action('resource_show', context=context, id=resource.get('id'))
        res_en = helpers.call_action('resource_show', context=context, id=json.loads(res.get('has_translations')).get('en'))
        assert res_en.get('id')
        assert res_en.get('translation_parent_id') == res.get('id')

        trans_data = [{
                'resource_id': resource.get('id'),
                'language': 'en',
                'mode':'transcription',
                'column_name':'name',
                },
                {
                'resource_id': resource.get('id'),
                'language': 'en',
                'mode':'manual',
                'column_name':'name',
                },
                {
                'resource_id': resource.get('id'),
                'language': 'en',
                'mode':'transcription',
                'column_name':'address',
                }]

        for d in trans_data:
            helpers.call_action('resource_translation_update', context=context, **d)
            updated_ds = helpers.call_action('datastore_search', context=context, id=res_en.get('id'))
            pprint.pprint(updated_ds)

            assert updated_ds.get('resource_id') == res_en.get('id')
            assert updated_ds.get('total') == 3
            field_exists = False
            for field in updated_ds.get('fields'):
                if field.get('id') == d.get('column_name'):
                    field_exists = True
                    break
            assert field_exists

        res = helpers.call_action('datastore_search', context=context, id=res_en.get('id'))
        for rec in res.get('records'):
            print rec
            # manual translation so should be empty
            assert rec.get('name') == u''
            # transcription so should not be empty
            assert not rec.get('address') == u''
        pprint.pprint(res)
        assert rec.get('address')


    @nose.tools.istest
    def test_b4_update_translation_resource_transcription_pagination(self):
        resource = self._get_initial_datastore(package_data.get('name'))
        context = self.get_context()
        #context.update({'locale':'el'})
        # Should create translation resource correctly
        res = helpers.call_action('resource_show', context=context, id=resource.get('id'))
        res_en = helpers.call_action('resource_show', context=context, id=json.loads(res.get('has_translations')).get('en'))

        assert res_en.get('id')
        assert res_en.get('translation_parent_id') == res.get('id')

        original_ds = helpers.call_action('datastore_search', context=context, id=res.get('id'))
        # Update ds with 5000 dummy name entries
        p.toolkit.get_action('datastore_upsert')(context,
            {
                'resource_id': original_ds.get('resource_id'),
                'force':True,
                'method':'insert',
                'allow_update_with_id':True,
                'records': [{'name':'λαλαλα'} for i in range(1,4998)]
            })

        ds = helpers.call_action('datastore_search', context=context, id=res.get('id'))
        #pprint.pprint(ds)
        assert ds.get('resource_id') == res.get('id')
        assert ds.get('total') == 5000

        trans_data = [{
                'resource_id': resource.get('id'),
                'language': 'en',
                'mode':'transcription',
                'column_name':'name',
                },
                #{
                #'resource_id': res_el.get('id'),
                #'mode':'manual',
                #'column_name':'name',
                #},
                #{
                #'resource_id': res_el.get('id'),
                #'mode':'transcription',
                #'column_name':'address',
                #}
        ]

        for d in trans_data:
            helpers.call_action('resource_translation_update', context=context, **d)
            updated_ds = helpers.call_action('datastore_search', context=context, id=res_en.get('id'))
            #pprint.pprint(updated_ds)

            #assert updated_ds.get('resource_id') == res_el.get('id')
            #assert updated_ds.get('total') == 5000
            field_exists = False
            for field in updated_ds.get('fields'):
                if field.get('id') == d.get('column_name'):
                    field_exists = True
                    break
            assert field_exists
        res_first = helpers.call_action('datastore_search', context=context, id=res_en.get('id'), offset=0)
        assert len(res_first.get('records')) == PAGE_STEP
        assert res_first.get('records')[3].get('name') == 'lalala'
        pprint.pprint(res_first)

        res_last = helpers.call_action('datastore_search', context=context, id=res_en.get('id'), offset=50*PAGE_STEP-100, limit=PAGE_STEP)
        assert len(res_last.get('records')) == PAGE_STEP
        assert res_first.get('records')[PAGE_STEP-1].get('name') == 'lalala'
        pprint.pprint(res_last)

        res_none = helpers.call_action('datastore_search', context=context, id=res_en.get('id'), offset=50*PAGE_STEP, limit=PAGE_STEP)
        pprint.pprint(res_none)
        assert len(res_none.get('records')) == 0

    # TODO: Create tests in transcription, automatic translation modes

    ###
    ### Translate Resource Delete Tests
    ###

    @nose.tools.istest
    def test_c1_delete_translation_resource_column_invalid(self):
        resource = self._get_initial_datastore(package_data.get('name'))
        context = self.get_context()

        #resource_es_id = json.loads(resource.get('has_translations')).get('es')
        # Should raise validation error on all
        trans_data = [{
                'resource_id': resource.get('id'),
                'language': 'es',
                # wrong column name
                'column_name': 'invalid-column-name'
                },
                {
                'resource_id': resource.get('id'),
                # non existing language
                'language': 'de',
                'column_name': 'name'
                }]

        for d in trans_data:
            nose.tools.assert_raises(p.toolkit.ValidationError, helpers.call_action, 'resource_translation_delete', context=context, **d)

    @nose.tools.istest
    def test_c2_delete_translation_resource_column(self):
        resource = self._get_initial_datastore(package_data.get('name'))
        context = self.get_context()

        resource_en_id = json.loads(resource.get('has_translations')).get('en')
        #resource_el = p.toolkit.get_action('datastore_search')(context, {'id':resource_el_id})
        # Should delete translation resource correctly
        
        trans_data = [{
                'resource_id': resource.get('id'),
                'language': 'en',
                'column_name': 'name'
                },
                # should not change sth but not fail either
                {
                'resource_id': resource.get('id'),
                'language': 'en',
                'column_name': 'name'
                },

                ]

        for d in trans_data:
            pprint.pprint(helpers.call_action('resource_translation_delete', context=context, **d))
            res_en = helpers.call_action('datastore_search', context=context, resource_id=resource_en_id)
            print "RESULT"
            pprint.pprint(res_en)
            for fld in res_en.get('fields'):
                # assert deleted column does not exist in resource
                assert not fld.get('id') == 'name'

    @nose.tools.istest
    def test_c3_delete_translation_resource_invalid(self):
        resource = self._get_initial_datastore(package_data.get('name'))
        context = self.get_context()

        # Should raise validation error on all
        trans_data_wrong = [
                    {
                    'resource_id': resource.get('id'),
                    # non existing language
                    'language': 'de'
                    },
                    {
                    # non existing resource id
                    'resource_id': 'wrong-resource-id',
                    'language': 'en'
                    }]

        for d in trans_data_wrong:
            nose.tools.assert_raises(p.toolkit.ValidationError, helpers.call_action, 'resource_translation_delete', context=context, **d)


    @nose.tools.istest
    def test_c4_delete_translation_resource(self):
        resource = self._get_initial_datastore(package_data.get('name'))
        context = self.get_context()

        resource_es_id = json.loads(resource.get('has_translations')).get('es')
        # Should delete translation resource correctly
        trans_data = {
                'resource_id': resource.get('id'),
                'language': 'es'
                }

        helpers.call_action('resource_translation_delete', context=context, **trans_data)
        res = helpers.call_action('resource_show', context=context, id=resource_es_id)
        assert res.get('id')
        assert res.get('state') == 'deleted'
        orig_resource = helpers.call_action('resource_show', context=context, id=resource.get('id'))
        assert 'es' not in json.loads(orig_resource.get('has_translations'))
        #res_ds = helpers.call_action('datastore_search', context=context, resource_id=resource_es_id)
        nose.tools.assert_raises(p.toolkit.ObjectNotFound, helpers.call_action, 'datastore_search', context=context, resource_id=resource_es_id)

    # TODO: Move test after basic delete tests
    @nose.tools.istest
    def test_c5_delete_and_recreate_translation_resource(self):
        resource = self._get_initial_datastore(package_data.get('name'))
        context = self.get_context()

        resource_en_id = json.loads(resource.get('has_translations')).get('en')
        # Should delete translation resource correctly
        trans_data = {
                'resource_id': resource.get('id'),
                'language': 'en'
                }

        helpers.call_action('resource_translation_delete', context=context, **trans_data)
        # TODO: assert oringal metadata updates - has_translations and translation resource_deleted
        #deleted_resource = helpers.assert_raises('datastore_search', context=context, resource_id= resource_el_id)
        nose.tools.assert_raises(p.toolkit.ObjectNotFound, helpers.call_action, 'datastore_search', context=context, resource_id=resource_en_id)
        #print deleted_resource

        deleted_resource = helpers.call_action('resource_show', context=context, id=resource_en_id)
        assert deleted_resource.get('state') == 'deleted'

        original_updated_resource = helpers.call_action('resource_show', context=context, id=resource.get('id'))
        assert original_updated_resource.get('has_translations')
        assert 'en' not in json.loads(original_updated_resource.get('has_translations'))

        # Try to recreate translation in same language after it has been deleted
        trans_data = {
                'package_id': package_data.get('name'),
                'resource_id': resource.get('id'),
                'language': 'en',
                }

        created_res = helpers.call_action('resource_translation_create', context=context, **trans_data)
        assert created_res.get('id')
        assert created_res.get('translation_resource')

        original_resource = helpers.call_action('resource_show', context=context, id=resource.get('id'))
        assert original_resource.get('id') == created_res.get('translation_parent_id')
        assert original_resource.get('has_translations')
        assert 'en' in json.loads(original_resource.get('has_translations'))
        assert json.loads(original_resource.get('has_translations')).get('en') == created_res.get('id')

    # Helpers
    
    def _get_initial_datastore(self, name):
        context = self.get_context()
        res = helpers.call_action('package_show', context=context, id=name)
        # Assert resource exists and return it
        assert res.get('id')
        assert res.get('resources')[0]
        return res.get('resources')[0]

    def _initialize_datastore(self):
        context = self.get_context()
        # Step 1 - create package
        package = helpers.call_action('package_create', context=context, **package_data_no_datastore)
        created_package = helpers.call_action('package_show', context=context, id=package_data_no_datastore.get('name'))

        assert created_package
        assert created_package.get('id') == package.get('id')
        assert created_package.get('resources')
        assert created_package.get('resources')[0].get('id')

        #package_data.update({'owner_org' : self.organization['id']})
        print package_data
        print context
        package = helpers.call_action('package_create', context=context, **package_data)
        print package
        assert helpers.call_action('package_show', context=context, id=package.get('id')).get('id')
        # Step 2 - create the resource and table and fill it with sample data
        datastore = helpers.call_action('datastore_create', context=context, **datastore_data)
        # TODO: auth checks - not working
        #package = helpers.call_action('package_update', context=context, id=package['id'], name='changed')
        # Assert package created correctly
        created_package = helpers.call_action('package_show', context=context, id=package.get('id'))
        # Assert resource created
        assert helpers.call_action('resource_show', context=context, id=datastore.get('resource_id')).get('id')
        assert created_package.get('resources')
        assert created_package.get('resources')[0].get('id')

        # Assert datastore created
        res = helpers.call_action('datastore_search', context=context, resource_id=datastore.get('resource_id'))
        assert res.get('resource_id') == datastore.get('resource_id')

# Initial test data
package_data = {
            'name': 'hello-ckan-2',
            'title': u'Hello Ckan 2',
        }

package_data_no_datastore= {
            'name': 'hello-ckan-1',
            'title': u'Hello Ckan 1',
            'resources':[{'package_id': 'hello-ckan-1',
                        'url':'http://',
                        'url_type':'datastore',
                        'name':'hello-resource-1',
                        'format':'data_table'
                    }],
        }

datastore_data = {
                #'resource_id':package.get('resources')[0].get('id'),
                'force': True,
                'resource': {'package_id': 'hello-ckan-2',
                    },
                'fields':[{'id':'name',
                        'type':'text'},
                        {'id':'address',
                        'type':'text'},
                        {'id':'post_code',
                        'type':'text'}],
                'records':[{'name':u'Δημήτρης Γιαννακόπουλος',
                        'address':u'Αγ. Τράκη 56, Μαρούσι',
                        'post_code':'131313'},
                        {'name':u'Αχιλλέας Μπέος',
                        'address':u'Ιωαννίνων 5, Βόλος',
                        'post_code':'12345'},
                        {'name':u'Τάκης Τσουκαλάς',
                        'address':u'Κάδος Πατησίων 55, Πατήσια',
                        'post_code':'41235'}]
                }

