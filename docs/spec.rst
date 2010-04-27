==========================================
 Feed Service
==========================================

Discussion
==========

*Tristan*:
::

    I would like the feed processing to be a separate service, so it's not
    running on Portal. This service would use Redis (ref batiste's email
    about superfeedr, who got the same problem as us and fixed it with Redis)
    to solve most of the performance issues [they had].
    As a bonus, it could be really cool to use Durian and have a push service
    (with Portal as a client). But keep in mind it's a "bonus".


I don't think accessing the feeds through such a service is useful for
Portal, as Portal uses most (if not all) of the feeds in the system
this would only result in feeds being stored twice.

But if some other service at Opera needs this, we could add a
`PubSubHubbub`_ interface on top of this, using the proposed signals
below.


.. _`PubSubHubbub`: http://en.wikipedia.org/wiki/PubSubHubbub


Support for storing posts in Redis
==================================

* post.save()

    Create/modify post.  **IMPLEMENTED**

* post.delete()

    Delete a post.  **IMPLEMENTED**

* post.objects.get(id)

    Get post by id.  **IMPLEMENTED**

* post.objects.get_by_guid(feed_url, guid)

    Get post by guid **IMPLEMENTED**

* post.objects.all_by_order(feed_url, limit=20)

    Get a list of a feeds posts, sorted by timestamp.  **IMPLEMENTED**

* post.objects.update_or_create(feed_url, \*\*fields)

    Update post by guid, or create new post if guid does not
    already exist.  **IMPLEMENTED**

* post.objects.expire(feed_url, limit=50)

    Expire old posts in a feed. *NOT IMPLEMENTED*

Data structure
==============

Ids
---

The key of a post is the term "Entry" followed by a unique id,
the unique id is created by incrementing the key "ids:Entry".

Example keys::

    Entry:1
    Entry:2
    Entry:3


Pseudocode for creating a new id::

    new_id = "Entry:%s" % (db.incr("ids:Entry"), )


Posts
-----

Posts must have the following required fields:

* feed_url (:class:`str`)

        Url of the parent feed. To be able to point back to which feed
        an entry belongs to.

* guid (:class:`str`)

        The unique id of the post. This is only unique per post, so can
        not be used as a primary key (see `Ids`_ above).

* timestamp (:class:`datetime.datetime`)

        The timestamp corresponding to the date and time this entry
        was last updated.

The rest of the fields are arbitrary, but usually includes:

``title``, ``link``, ``content``, ``author``, ``date_published``,
``date_updated``.

Indexes
-------

* $feed_url:sort -> SortedSet(entry_id, timestamp)

    A sorted set (:class:`redish.types.SortedSet`) that stores the
    ordering of posts in a feed.

    The members of the sets are entry ids, and the score of the members is the
    timestamp (as a 32-bit int, unix timestamp) the post was last updated.

    Used to retreive posts in order, and to easily find older items to expire.

* $feed_url:guidmap -> Hash(guid, id)

    A mapping of guids and their entry ids, used to check for the existence
    of a post by guid, and to update existing posts by guid.

Missing features
----------------

Redis posts will not support categories or enclosures,
as this is not strictly required by us and makes the implementation
a lot more complex. It may be supported in the future, if requirements change.


New signals
-----------

* feed_created(sender=feed_url)

    A new feed url has been introduced to the system.

* feed_modified(sender=feed_url, changed=diff)

    A feed has been modified (title, description)

* post_created(feed_url, post, guid)

    New post available in a feed.

* post_modified(sender=guid, feed_url, post, changed=diff)

    Previously existing post has been modified
