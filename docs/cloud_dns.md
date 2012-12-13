# Cloud DNS

## Basic Concepts
The Cloud DNS API allows you to programmatically associate domain names with your devices, and add/edit/remove DNS records for those domains.


## About Domain Names
Rackspace does not handle domain name registration. You will have to go to any one of the many existing registrars if you need to register a domain name. Once your domain name is registered, you can then use it with your Rackspace Cloud account.

For the purposes of this document, the domain **example.edu** will be used. This is not a real domain; it is a domain name reserved for use in documentation. See this [Wikipedia](http://en.wikipedia.org/wiki/Example.com) article for more information about the use of this name.

**Subdomains** are domains within the parent domain, and are typically used to designate different functions within the domain. Examples of subdomains would be `mail.example.edu` (for handling email activity), `www.example.edu` (web traffic), and `ftp.example.edu` (FTP traffic). Subdomains can be further broken down into sub-subdomains, such as `main.ftp.example.edu` and `secondary.ftp.example.edu`, to suit the needs of the site.


## Cloud DNS in pyrax
Once you have authenticated and connected to the Cloud DNS service, you can reference the DNS module via `pyrax.cloud_dns`. This module provides methods for managing your DNS entries for the cloud.

All of the code samples in this document assume that you have already imported pyrax, authenticated, and created the name `dns` at the top of the script, like this:

    import pyrax
    pyrax.set_credential_file("my_cred_file")
    # or
    # pyrax.set_credentials("my_username", "my_api_key")
    dns = pyrax.cloud_dns


## Listing Domains
To get a list of all the domains that are manageable by your account, call the `list()` method:

    dns.list()

This will return a list of `CloudDNSDomain` objects, with which you can then interact. It is a flat list: there is no hierarchical nesting of subdomains within their parent domains. Assuming that you have just started, you will get back an empty list. The next step would be to add your domains.


### Paging
You could have hundreds of domains, and by default the `list()` method will only return the first hundred domains. You can optionally pass in `limit` and `offset` parameters which will control the results returned by `dns.list()`.

The `limit` parameter will determine how many records are returned, and must be a value between 1 and 100. If no `limit` is passed, a value of 100 will be used. The `offset` parameter determines where in the listing to begin when fetching. The value of `offset` defaults to 0 if not specified. Additionally, the value of `offset` must be either zero or a multiple of the limit. Together they enable paging across all of your domains.

To make things easier, pyrax offers two convenience methods: `list_previous_page()` and `list_next_page()` for traversing your domain records. After the initial call to `list()`, you can then navigate through the pages of results with these methods. Each will raise a `NoMoreResults` exception when there are no additional pages of results to fetch. For example, assume that there are 15 domain records, and you want to show them in pages of up to 4 at a time. This code will do that for you:

    domains = dns.list(limit=4)
    print domains
    while True:
        try:
            domains = dns.list_next_page()
            print domains
        except pyrax.exceptions.NoMoreResults:
            break

The same approach of using `offset` and `limit` will work with subdomains, records, and PTR records. The methods for the next and previous page of results have similar names, which are noted in their respective sections below.


### Iterators
To make working with large numbers of domains simpler, `pyrax` provides the `get_domain_iterator()` method. This will return an iterable object that will handle the paging requests for you, so you can treat them as a single request. For this example, assume that you have 250 domains named from 'example001.edu' to 'example250.edu'. Instead of the multiple commands you would need to use as in the example above, you can iterate through them in a single command:

    for domain in dns.get_domain_iterator():
        print domain.name

This would print out:

    example001.edu
    example002.edu
    ...
    example249.edu
    example250.edu

There will be a slight delay when the end of a page of domains is reached and the next page is fetched, but it is no different than when you manually page through your domains.


## Adding Domains
To create a domain, you would call the `dns.create()` method, supplying some or all of the following parameters:

Parameter | Description | Required?---- | ---- | ----**name** | The fully-qualified domain name (FQDN) | yes**emailAddress** | The email address of the domain administrator | yes**ttl** | The Time To Live (in seconds) for the domain. Default=3600. Minimum=300. | no**comment** | A brief description of the domain. Maximum length=160 characters | no**subdomains** | One or more dicts that represent subdomains of this new domain. The dicts have the same structure as the main domain, with each of these parameters being keys in the subdomain dicts. Including subdomains in the `create()` command is equivalent to creating them separately, but requires only one API call instead of many. | no**records** | You can optionally add DNS records for the domain, such as `MX`, `A`, and `CNAME`. The records are dicts with the same structure as for the `add_records()` method, and adding them in the `create()` command is equivalent to adding them separately afterward, but requires only one API call. | no

So the simplest form of the call would be:

    dom = dns.create(name="example.edu", emailAddress="sample@example.edu")

You could also add a TTL setting and a comment:

    dom = dns.create(name="example.edu", emailAddress="sample@example.edu",
            ttl=600, comment="Primary domain for this documentation.")

The `create()` command returns an instance of a `CloudDNSDomain` object:

    <CloudDNSDomain accountId=000000, comment=Primary domain for this documentation., created=2012-12-06T20:45:10.000+0000, emailAddress=sample@example.edu, id=3534921, name=example.edu, nameservers=[{u'name': u'dns1.stabletransit.com'}, {u'name': u'dns2.stabletransit.com'}], ttl=600, updated=2012-12-06T20:45:10.000+0000>


## Subdomains
Subdomains are conceptually the same as primary domains, but are a useful way of addressing multiple related devices without requiring each to have its own domain name. You create a subdomain just like creating a primary domain: by calling `dns.create()`, but with the `name` parameter replaced with the **FQDN** (Fully-Qualified Domain Name) of the subdomain.

Subdomains in DNS are managed in separate zone files, so this means that there isn't an explicit linkage between a subdomain and the primary domain. Instead, the relationship is only implied, and is the result of the naming: `a.example.edu` is by definition a subdomain of `example.edu`; likewise, `b.a.example.edu` is a subdomain of `a.example.edu`.

## Listing Subdomains
To get a listing of all the subdomains for a given domain 'dom', call the `list_subdomains()` method:

    subs = dom.list_subdomains()
    # or
    subs = dns.list_subdomains(dom)

Both of the above will return the same information. 


## DNS Records
Records specify information about the domain to which they belong. Rackspace Cloud DNS supports the following record types:

* A
* CNAME
* MX
* AAAA
* NS
* TXT
* SRV
* PTR


## Listing DNS Records
To get a listing of all the records for a given domain 'dom', call the `list_records()` method:

    recs = dom.list_records()
    # or
    recs = dns.list_records(dom)

Both of the above will return the same information. 


### Paging Subdomains and Records
Both the subdomain and record listing calls are subject to the same paging parameters as those for domain listing: 100 maximum per request. You can optionally specify the `limit` and `offset` parameters to get different blocks of subdomains, just as with domains. There are also the convenience methods for moving back and forth through the pages of results: 

    * list_subdomains_previous_page()
    * list_subdomains_next_page()
    * list_records_previous_page()
    * list_records_next_page()

It should be noted that these methods work with a single domain at a time, so if you were to list subdomains or records of a different domain, the new paging information would override the old.

To avoid that limitation, you can use the iterator:

    sub_iter = dns.get_subdomain_iterator(dom)
    # and
    rec_iter = dns.get_record_iterator(dom)

These will return objects you can iterate on to get all the subdomains or records for the specified domain 'dom'. Since each iterator is domain-specific, you don't have to be concerned about requests for different domains resetting the paging information.



## Adding DNS Records
DNS records are associated with a particular domain, so to add records you call the `add_records()` method of the CloudDNSDomain object for that domain. Alternatively, you can call the module's `add_records()` method, passing in the domain reference as well as the record information.

The record information should be a dict whose keys are the relevant record attributes; which keys are needed depend on the record type. To create multiple records in a single call, pass in a list of these record dicts.

Name | Description | Required--- | --- | ---**type** | Specifies the record type to add. | Yes**name** | Specifies the name for the domain or subdomain. Must be a valid domain name. | Yes**data** | The data field for PTR, A, and AAAA records must be a valid IPv4 or IPv6 IP address. For MX records it must be the FQDN for the mail server. | Yes**priority** | Required for MX and SRV records, but forbidden for other record types. If specified, must be an integer from 0 to 65535. | For MX and SRV records only**ttl** | If specified, must be greater than 300. Defaults to the domain TTL if available, or 3600 if no TTL is specified. | No**comment** | If included, its length must be less than or equal to 160 characters. | No

Here is an example of adding an **A** and an **MX** record to a `CloudDNSDomain` object 'dom':

    recs = [{
            "type": "A",
            "name": "example.edu",
            "data": "192.168.0.42",
            "ttl": 6000,
            }, {
            "type": "MX",
            "name": "example.edu",
            "data": "mail.example.edu",
            "priority": 50,
            "comment": "Backup mail server"
            }]
    dom.add_records(recs)
    # or
    dns.add_records(dom, recs)


## Adding Subdomains
Since a subdomain is really not any different than a primary domain, the command to add  a subdomain is exactly the same

    subdom1 = dns.create(name="north.example.edu", comment="1st sample subdomain",            emailAddress="sample@rackspace.edu")

Note that there is no reference to the primary domain. Instead, the relation is simply implied via the FQDN.


## Combining Mutliple Actions
The `create()` method allows you to specify subdomains and records to be added to the domain you are creating. The end result is identical, but by combining the actions into one, only one API call is made, making it much more efficient.

To illustrate, consider a situation where we need to create the `example.edu` domain, along with an `A` and an `MX` record, as well as four subdomains: `north.example.edu`, `west.example.edu`, `southeast.example.edu`, and `southby.southeast.example.edu`. The simplest approach would be to call `create()` and `add_record()` for each one separately:

    dom = dns.create(name="example.edu", comment="Primary domain",
            emailAddress="sample@rackspace.edu")    rec1 = dom.add_records({"type": "A", "name": "example.edu",
            "data": "192.168.0.42", "ttl": 6000})    rec2 = dom.add_records({"type": "MX", "name": "example.edu",
            "data": "mail.example.edu", "priority": 50, "comment":
            "Backup mail server"})    subdom1 = dns.create(name="north.example.edu", comment="1st sample subdomain",            emailAddress="sample@rackspace.edu")    subdom2 = dns.create(name="west.example.edu", comment="2nd sample subdomain",
            emailAddress="sample@rackspace.edu")    subdom3 = dns.create(name="southeast.example.edu",            emailAddress="sample@rackspace.edu")    subdom4 = dns.create(name="southby.southeast.example.edu",            comment="Final sample subdomain", emailAddress="sample@rackspace.edu")

That's a total of 7 separate calls to the server. Actually, some of these calls are done asynchronously, and require several callbacks to determine if the calls succeeded, so the total number of API calls is actually much higher.

By preparing the record and subdomain information ahead of time, the process can be made to be much more efficient, by requiring only a single `create()` call:

    subs = [        {"name" : "north.example.edu",            "comment" : "1st sample subdomain",            "emailAddress" : "sample@rackspace.edu"},        {"name" : "west.example.edu",            "comment" : "2nd sample subdomain",            "emailAddress" : "sample@rackspace.edu"},        {"name" : "southeast.example.edu",            "emailAddress" : "sample@rackspace.edu"},        {"name" : "southby.southeast.example.edu",            "comment" : "Final sample subdomain",            "emailAddress" : "sample@rackspace.edu"}        ]
    recs = [{
            "type": "A",
            "name": "example.edu",
            "data": "192.168.0.42",
            "ttl": 6000,
            }, {
            "type": "MX",
            "name": "example.edu",
            "data": "mail.example.edu",
            "priority": 50,
            "comment": "Backup mail server"
            }]
    dom = dns.create(name="example.edu", comment="Primary domain",
            emailAddress="sample@rackspace.edu", subdomains=subs,
            records=recs)

This will have the exact same result as the 7 separate calls, but much more efficiently. A recent test running this code showed 11.4 seconds for the separate calls, but only 4.6 for the combined call.


## Updating a Domain
You can modify any of the following attributes on an existing domain:

- Contact email address
- TTL
- Comment

To do that, call the domain's `update()` method, or the `dns.update_domain()` method. Given a `CloudDNSDomain` object 'dom', these two commands are equivalent:

    dom.update(ttl=1200)
    # or
    dns.update_domain(dom, ttl=1200)


## Deleting a Domain
If you have a `CloudDNSDomain` object 'dom' that you want to delete, you can use either the object-level or module-level command to do so:

    dom.delete()
    # or
    dns.delete(dom)


## Import / Export a Domain
If you have a BIND 9 formatted domain configuration file (for an example, see [this page](http://www.centos.org/docs/2/rhl-rg-en-7.2/s1-bind-configuration.html#BIND-EXAMPLE-ZONE-WHOLE) from the CentOS site) that describes the domain and its information, you can import that directly instead of creating the separate commands that would be needed to create and configure the domain from scratch.

    with file("/path/to/bindfile.txt") as bindfile:
        data = bindfile.read()
        dom = dns.import_domain(data)

Similarly, you can export a domain by calling its export() method, or the module's export_domain() method. The following two calls are equivalent:

    exp = dom.export
    # or
    exp = dns.export_domain(dom)

Both will create the same output:

    example.edu.        3600    IN    SOA    ns.rackspace.com. sample.rackspace.edu. 1354918038 21600 3600 1814400 500    example.edu.        6000    IN    A    192.168.0.42    example.edu.        3600    IN    NS    dns1.stabletransit.com.    example.edu.        3600    IN    NS    dns2.stabletransit.com.    example.edu.        3600    IN    MX    50 mail.example.edu.



## PTR Records








