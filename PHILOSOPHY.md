PHILOSOPHY
==========

* Don't bother with Packages that can't be bothered to have a full cheeseshop record.
* Don't bother with complex version requirements in Cheesefile.
* Don't bother with getting stuff 100% right.
* Bother with an (internal) API.

Notes
=====

A note on binary distributions
------------------------------

While the initial version will probably not support them, we very likely want to allow this.


A note on cheeseshops
---------------------

The official PyPI is a beast: it has four different ways offering data access, none of them supporting the same set of features.

The initial version will probably only support cheeseshops with an XMLRPC interface. Depending on what else happens, we might need to expand on this support.

