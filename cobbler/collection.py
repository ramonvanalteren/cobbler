"""
Base class for any serializable list of things...

Copyright 2006, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import exceptions
import cexceptions
import serializable
import utils
import cobbler_msg

class Collection(serializable.Serializable):

    def __init__(self,config):
        """
	Constructor.
	"""
        self.config = config
        self.clear()

    def factory_produce(self,config,seed_data):
        """
        Must override in subclass.  Factory_produce returns an Item object
        from datastructure seed_data
        """
        raise exceptions.NotImplementedError

    def filename(self):
        """
        Must override in subclass.  See Serializable
        """
        raise exceptions.NotImplementedError

    def clear(self):
        """
        Forget about objects in the collection.
        """
        self.listing = {}

    def find(self,name):
        """
        Return anything named 'name' in the collection, else return None if
        no objects can be found.
        """
        if name in self.listing.keys():
            return self.listing[name]
        return None


    def to_datastruct(self):
        """
        Serialize the collection
        """
        datastruct = [x.to_datastruct() for x in self.listing.values()]
        return datastruct

    def from_datastruct(self,datastruct):
        if datastruct is None:
            return
        for seed_data in datastruct:
            item = self.factory_produce(self.config,seed_data)
            self.add(item)

    def add(self,ref):
        """
        Add an object to the collection, if it's valid.  Returns True
        if the object was added to the collection.  Returns False if the
        object specified by ref deems itself invalid (and therefore
        won't be added to the collection).
        """
        if ref is None or not ref.is_valid():
            raise cexceptions.CobblerException("bad_param")
        self.listing[ref.name] = ref
        return True


    def printable(self):
        """
        Creates a printable representation of the collection suitable
        for reading by humans or parsing from scripts.  Actually scripts
        would be better off reading the YAML in the config files directly.
        """
        values = sorted(self.listing.values())
        results = []
        for i,v in enumerate(values):
           results.append(v.printable(1+i))
        if len(values) > 0:
           return "\n\n".join(results)
        else:
           return cobbler_msg.lookup("empty_list" % cobbler_msg.lookup(self.collection_type()))

    def __iter__(self):
        """
	Iterator for the collection.  Allows list comprehensions, etc
	"""
        for a in self.listing.values():
	    yield a

    def __len__(self):
        """
	Returns size of the collection
	"""
        return len(self.listing.values())

    def collection_type(self):
        """
        Returns the string key for the name of the collection (for use in messages for humans)
        """
        return exceptions.NotImplementedError


