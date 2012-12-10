#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax
from pyrax.manager import BaseManager
from pyrax.clouddns import assure_domain
from pyrax.clouddns import CloudDNSClient
from pyrax.clouddns import CloudDNSDomain
from pyrax.clouddns import CloudDNSManager
from pyrax.clouddns import CloudDNSRecord
import pyrax.exceptions as exc
import pyrax.utils as utils

from tests.unit import fakes

example_uri = "http://example.com"


class CloudDNSTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CloudDNSTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.client = fakes.FakeDNSClient()
        self.client._manager = fakes.FakeDNSManager(self.client)
        self.domain = fakes.FakeDNSDomain()
        self.domain.manager = self.client._manager

    def tearDown(self):
        self.client = None
        self.domain = None

    def test_assure_domain(self):
        @assure_domain
        def test(self, domain):
            return domain
        clt = self.client
        dom = self.domain
        clt._manager._get = Mock(return_value=dom)
        d1 = test(clt, dom)
        d2 = test(clt, dom.id)
        self.assertEqual(d1, d2)
        self.assertTrue(isinstance(d1, CloudDNSDomain))
        self.assertTrue(isinstance(d2, CloudDNSDomain))

    def test_manager_get(self):
        ret_body = {"recordsList": {
                "records": [{
                "accountId": "728829",
                "created": "2012-09-21T21:32:27.000+0000",
                "emailAddress": "me@example.com",
                "id": "3448214",
                "name": "example.com",
                "updated": "2012-09-21T21:35:45.000+0000"
                }]}}
        mgr = self.client._manager
        mgr.api.method_get = Mock(return_value=(None, ret_body))
        dom = mgr._get("fake")
        self.assertTrue(isinstance(dom, CloudDNSDomain))


    def test_manager_create(self):
        clt = self.client
        mgr = clt._manager
        ret_body = {"callbackUrl": example_uri,
                "status": "RUNNING"}
        mgr.api.method_post = Mock(return_value=(None, ret_body))
        stat_body = {"status": "complete",
                "response": {mgr.response_key: [{
                "accountId": "728829",
                "created": "2012-09-21T21:32:27.000+0000",
                "emailAddress": "me@example.com",
                "id": "3448214",
                "name": "example.com",
                "updated": "2012-09-21T21:35:45.000+0000"
                }]}}
        mgr.api.method_get = Mock(return_value=(None, stat_body))
        dom = mgr._create("fake", {})
        self.assertTrue(isinstance(dom, CloudDNSDomain))

    def test_manager_create_error(self):
        clt = self.client
        mgr = clt._manager
        ret_body = {"callbackUrl": example_uri,
                "status": "RUNNING"}
        mgr.api.method_post = Mock(return_value=(None, ret_body))
        stat_body = {"status": "ERROR",
                "error": {
                    "details": "fail",
                    "code": 666}}
        mgr.api.method_get = Mock(return_value=(None, stat_body))
        self.assertRaises(exc.DomainCreationFailed, mgr._create, "fake", {}) 

    def test_manager_findall(self):
        clt = self.client
        mgr = clt._manager
        mgr._list = Mock()
        mgr.findall(name="fake")
        mgr._list.assert_called_once_with("/domains?name=fake")

    def test_manager_findall_default(self):
        clt = self.client
        mgr = clt._manager
        sav = BaseManager.findall
        BaseManager.findall = Mock()
        mgr.findall(foo="bar")
        BaseManager.findall.assert_called_once_with(foo="bar")
        BaseManager.findall = sav

    def test_create_body(self):
        clt = self.client
        fake_name = utils.random_name()
        body = clt._create_body(fake_name, "fake@fake.com")
        self.assertEqual(body["domains"][0]["name"], fake_name)

    def test_async_call_body(self):
        clt = self.client
        mgr = clt._manager
        body = {"fake": "fake"}
        uri = "http://example.com"
        callback_uri = "https://fake.example.com/status/fake"
        massaged_uri = "/status/fake?showDetails=true"
        put_resp = {"callbackUrl": callback_uri,
                "status": "RUNNING"}
        get_resp = {"response": {"result": "fake"},
                "status": "COMPLETE"}
        method = "PUT"
        clt.method_put = Mock(return_value=({}, put_resp))
        clt.method_get = Mock(return_value=({}, get_resp))
        ret = mgr._async_call(uri, body=body, method=method)
        clt.method_put.assert_called_once_with(uri, body=body)
        clt.method_get.assert_called_once_with(massaged_uri)
        self.assertEqual(ret, ({}, get_resp["response"]))

    def test_async_call_no_body(self):
        clt = self.client
        mgr = clt._manager
        uri = "http://example.com"
        callback_uri = "https://fake.example.com/status/fake"
        massaged_uri = "/status/fake?showDetails=true"
        put_resp = {"callbackUrl": callback_uri,
                "status": "RUNNING"}
        get_resp = {"response": {"result": "fake"},
                "status": "COMPLETE"}
        method = "DELETE"
        clt.method_delete = Mock(return_value=({}, put_resp))
        clt.method_get = Mock(return_value=({}, get_resp))
        ret = mgr._async_call(uri, method=method)
        clt.method_delete.assert_called_once_with(uri)
        clt.method_get.assert_called_once_with(massaged_uri)
        self.assertEqual(ret, ({}, get_resp["response"]))

    def test_async_call_no_response(self):
        clt = self.client
        mgr = clt._manager
        uri = "http://example.com"
        callback_uri = "https://fake.example.com/status/fake"
        massaged_uri = "/status/fake?showDetails=true"
        put_resp = {"callbackUrl": callback_uri,
                "status": "RUNNING"}
        get_resp = {"status": "COMPLETE"}
        method = "DELETE"
        clt.method_delete = Mock(return_value=({}, put_resp))
        clt.method_get = Mock(return_value=({}, get_resp))
        ret = mgr._async_call(uri, method=method, has_response=False)
        clt.method_delete.assert_called_once_with(uri)
        clt.method_get.assert_called_once_with(massaged_uri)
        self.assertEqual(ret, ({}, get_resp))

    def test_async_call_error(self):
        clt = self.client
        mgr = clt._manager
        uri = "http://example.com"
        callback_uri = "https://fake.example.com/status/fake"
        massaged_uri = "/status/fake?showDetails=true"
        put_resp = {"callbackUrl": callback_uri,
                "status": "RUNNING"}
        get_resp = {"response": {"result": "fake"},
                "status": "ERROR"}
        method = "DELETE"
        clt.method_delete = Mock(return_value=({}, put_resp))
        clt.method_get = Mock(return_value=({}, get_resp))
        err_class = exc.DomainRecordDeletionFailed
        err = err_class("oops")
        mgr._process_async_error = Mock(side_effect=err)
        self.assertRaises(err_class,
                mgr._async_call, uri, method=method, error_class=err_class)
        clt.method_delete.assert_called_once_with(uri)
        clt.method_get.assert_called_once_with(massaged_uri)
        mgr._process_async_error.assert_called_once_with(get_resp, err_class)

    def test_process_async_error(self):
        clt = self.client
        mgr = clt._manager
        err = {"error": {"message": "fake", "details": "", "code": 400}}
        err_class = exc.DomainRecordDeletionFailed
        self.assertRaises(err_class, mgr._process_async_error, err, err_class)

    def test_process_async_error_nested(self):
        clt = self.client
        mgr = clt._manager
        err = {"error": {
                "failedItems": {"faults": [
                    {"message": "fake1", "details": "", "code": 400},
                    {"message": "fake2", "details": "", "code": 400},
                    ]}}}
        err_class = exc.DomainRecordDeletionFailed
        self.assertRaises(err_class, mgr._process_async_error, err, err_class)

    def test_changes_since(self):
        clt = self.client
        dom = self.domain
        clt.method_get = Mock(return_value=({}, {"changes": ["fake"]}))
        dt = "2012-01-01"
        ret = clt.changes_since(dom, dt)
        uri = "/domains/%s/changes?since=2012-01-01T00:00:00+0000" % dom.id
        clt.method_get.assert_called_once_with(uri)
        self.assertEqual(ret, ["fake"])

    def test_export_domain(self):
        clt = self.client
        dom = self.domain
        export = utils.random_name()
        clt._manager._async_call = Mock(return_value=({}, {"contents": export}))
        ret = clt.export_domain(dom)
        uri = "/domains/%s/export" % dom.id
        clt._manager._async_call.assert_called_once_with(uri, error_class=exc.NotFound, method="GET")
        self.assertEqual(ret, export)

    def test_import_domain(self):
        clt = self.client
        mgr = clt._manager
        data = utils.random_name()
        mgr._async_call = Mock(return_value=({}, "fake"))
        req_body = {"domains" : [{
                "contentType" : "BIND_9",
                "contents" : data,
                }]}
        ret = clt.import_domain(data)
        mgr._async_call.assert_called_once_with("/domains/import", method="POST",
                body=req_body, error_class=exc.DomainCreationFailed)

    def test_update_domain_empty(self):
        self.assertRaises(exc.MissingDNSSettings, self.client.update_domain,
                self.domain)

    def test_update_domain(self):
        clt = self.client
        dom = self.domain
        mgr = clt._manager
        emailAddress = None
        comment = utils.random_name()
        ttl = 666
        mgr._async_call = Mock(return_value=({}, "fake"))
        uri = "/domains/%s" % utils.get_id(dom)
        req_body = {"comment" : comment,
                "ttl" : ttl,
                }
        ret = clt.update_domain(dom, emailAddress, ttl, comment)
        mgr._async_call.assert_called_once_with(uri, method="PUT",
                body=req_body, error_class=exc.DomainUpdateFailed,
                has_response=False)

    def test_delete(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        mgr._async_call = Mock(return_value=({}, {}))
        uri = "/domains/%s" % utils.get_id(dom)
        clt.delete(dom)
        mgr._async_call.assert_called_once_with(uri, method="DELETE",
                error_class=exc.DomainDeletionFailed, has_response=False)

    def test_delete_subdomains(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        mgr._async_call = Mock(return_value=({}, {}))
        uri = "/domains/%s?deleteSubdomains=true" % utils.get_id(dom)
        clt.delete(dom, delete_subdomains=True)
        mgr._async_call.assert_called_once_with(uri, method="DELETE",
                error_class=exc.DomainDeletionFailed, has_response=False)

    def test_list_subdomains(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        clt.method_get = Mock(return_value=({}, {}))
#        uri = "/domains/%s/subdomains" % utils.get_id(dom)
        uri = "/domains?name=%s" % dom.name
        clt.list_subdomains(dom)
        clt.method_get.assert_called_once_with(uri)

    def test_list_records(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        clt.method_get = Mock(return_value=({}, {}))
        uri = "/domains/%s/records" % utils.get_id(dom)
        clt.list_records(dom)
        clt.method_get.assert_called_once_with(uri)

    def test_search_records(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        typ = "A"
        clt.method_get = Mock(return_value=({}, {}))
        uri = "/domains/%s/records?type=%s" % (utils.get_id(dom), typ)
        clt.search_records(dom, typ)
        clt.method_get.assert_called_once_with(uri)

    def test_search_records_params(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        typ = "A"
        nm = utils.random_name()
        data = "0.0.0.0"
        clt.method_get = Mock(return_value=({}, {}))
        uri = "/domains/%s/records?type=%s&name=%s&data=%s" % (utils.get_id(dom),
                typ, nm, data)
        clt.search_records(dom, typ, name=nm, data=data)
        clt.method_get.assert_called_once_with(uri)

    def test_add_records(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        rec = {"type": "A", "name": "example.com", "data": "0.0.0.0"}
        mgr._async_call = Mock(return_value=({}, {}))
        uri = "/domains/%s/records" % utils.get_id(dom)
        clt.add_records(dom, rec)
        mgr._async_call.assert_called_once_with(uri, method="POST",
                body={"records": [rec]}, error_class=exc.DomainRecordAdditionFailed,
                has_response=False)

    def test_update_record(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        rec = CloudDNSRecord(mgr, {"id": utils.random_name()})
        ttl = 9999
        data = "0.0.0.0"
        nm = "example.com"
        mgr._async_call = Mock(return_value=({}, {}))
        uri = "/domains/%s/records/%s" % (utils.get_id(dom), utils.get_id(rec))
        req_body = {"name": nm, "data": data, "ttl": ttl}
        clt.update_record(dom, rec, nm, data=data, ttl=ttl)
        mgr._async_call.assert_called_once_with(uri, method="PUT",
                body=req_body, error_class=exc.DomainRecordUpdateFailed,
                has_response=False)

    def test_delete_record(self):
        clt = self.client
        mgr = clt._manager
        dom = self.domain
        rec = CloudDNSRecord(mgr, {"id": utils.random_name()})
        mgr._async_call = Mock(return_value=({}, {}))
        uri = "/domains/%s/records/%s" % (utils.get_id(dom), utils.get_id(rec))
        clt.delete_record(dom, rec)
        mgr._async_call.assert_called_once_with(uri, method="DELETE",
                error_class=exc.DomainRecordDeletionFailed,
                has_response=False)

    def test_get_ptr_details_server(self):
        clt = self.client
        mgr = clt._manager
        dvc = fakes.FakeDNSDevice()
        dvc_type = "server"
        sav = pyrax._get_service_endpoint
        pyrax._get_service_endpoint = Mock(return_value=example_uri)
        expected_href = "%s/servers/%s" % (example_uri, dvc.id)
        href, svc_name = mgr._get_ptr_details(dvc, dvc_type)
        self.assertEqual(svc_name, "cloudServersOpenStack")
        self.assertEqual(href, expected_href)
        pyrax._get_service_endpoint = sav

    def test_get_ptr_details_lb(self):
        clt = self.client
        mgr = clt._manager
        dvc = fakes.FakeDNSDevice()
        dvc_type = "loadbalancer"
        sav = pyrax._get_service_endpoint
        pyrax._get_service_endpoint = Mock(return_value=example_uri)
        expected_href = "%s/loadbalancers/%s" % (example_uri, dvc.id)
        href, svc_name = mgr._get_ptr_details(dvc, dvc_type)
        self.assertEqual(svc_name, "cloudLoadBalancers")
        self.assertEqual(href, expected_href)
        pyrax._get_service_endpoint = sav

    def test_list_ptr_records(self):
        clt = self.client
        mgr = clt._manager
        dvc = fakes.FakeDNSDevice()
        href = "%s/%s" % (example_uri, dvc.id)
        svc_name = "cloudServersOpenStack"
        uri = "/rdns/%s?href=%s" % (svc_name, href)
        mgr._get_ptr_details = Mock(return_value=(href, svc_name))
        clt.method_get = Mock(return_value=({}, {"records": []}))
        ret = clt.list_ptr_records(dvc)
        clt.method_get.assert_called_once_with(uri)
        self.assertEqual(ret, [])

    def test_list_ptr_records_not_found(self):
        clt = self.client
        mgr = clt._manager
        dvc = fakes.FakeDNSDevice()
        href = "%s/%s" % (example_uri, dvc.id)
        svc_name = "cloudServersOpenStack"
        uri = "/rdns/%s?href=%s" % (svc_name, href)
        mgr._get_ptr_details = Mock(return_value=(href, svc_name))
        clt.method_get = Mock(side_effect=exc.NotFound(""))
        ret = clt.list_ptr_records(dvc)
        clt.method_get.assert_called_once_with(uri)
        self.assertEqual(ret, [])

    def test_add_ptr_records(self):
        clt = self.client
        mgr = clt._manager
        dvc = fakes.FakeDNSDevice()
        href = "%s/%s" % (example_uri, dvc.id)
        svc_name = "cloudServersOpenStack"
        rec = {"foo": "bar"}
        body = {"recordsList": {"records": [rec]},
                "link": {"content": "", "href": href, "rel": svc_name}}
        uri = "/rdns"
        mgr._get_ptr_details = Mock(return_value=(href, svc_name))
        clt.method_post = Mock(return_value=({}, {"records": []}))
        clt.add_ptr_records(rec, dvc)
        clt.method_post.assert_called_once_with(uri, body=body)

    def test_update_ptr_record(self):
        clt = self.client
        mgr = clt._manager
        dvc = fakes.FakeDNSDevice()
        href = "%s/%s" % (example_uri, dvc.id)
        svc_name = "cloudServersOpenStack"
        ptr_record = fakes.FakeEntity()
        ttl = 9999
        data = "0.0.0.0"
        long_comment = "x" * 200
        trim_comment = long_comment[:160]
        nm = "example.com"
        rec = {"name": nm, "id": ptr_record.id, "type": "PTR", "data": data,
                "ttl": ttl, "comment": trim_comment}
        uri = "/rdns"
        body = {"recordsList": {"records": [rec]}, "link": {"content": "", "href": href, "rel": svc_name}}
        mgr._get_ptr_details = Mock(return_value=(href, svc_name))
        clt.method_put = Mock(return_value=({}, {"records": []}))
        clt.update_ptr_record(ptr_record, dvc, domain_name=nm, data=data, ttl=ttl,
                comment=long_comment)
        clt.method_put.assert_called_once_with(uri, body=body)

    def test_delete_ptr_records(self):
        clt = self.client
        mgr = clt._manager
        dvc = fakes.FakeDNSDevice()
        href = "%s/%s" % (example_uri, dvc.id)
        svc_name = "cloudServersOpenStack"
        ip_address = "0.0.0.0"
        uri = "/rdns/%s?href=%s&ip=%s" % (svc_name, href, ip_address)
        mgr._get_ptr_details = Mock(return_value=(href, svc_name))
        clt.method_delete = Mock(return_value=({}, {"records": []}))
        ret = clt.delete_ptr_records(dvc, ip_address=ip_address)
        clt.method_delete.assert_called_once_with(uri)

    def test_get_absolute_limits(self):
        clt = self.client
        rand_limit = utils.random_name()
        resp = {"limits": {"absolute": rand_limit}}
        clt.method_get = Mock(return_value=({}, resp))
        ret = clt.get_absolute_limits()
        self.assertEqual(ret, rand_limit)

    def test_get_rate_limits(self):
        clt = self.client
        limits = [{"uri": "fake1", "limit": 1},
                {"uri": "fake2", "limit": 2}]
        resp = {"limits": {"rate": limits}}
        resp_limits = [{"uri": "fake1", "limits": 1},
                {"uri": "fake2", "limits": 2}]
        clt.method_get = Mock(return_value=({}, resp))
        ret = clt.get_rate_limits()
        self.assertEqual(ret, resp_limits)


if __name__ == "__main__":
    unittest.main()
