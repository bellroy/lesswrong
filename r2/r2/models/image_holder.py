class ImageHolder(object):
    def get_images(self):
        """
        Iterator over list of (name, image_num) pairs which have been
        uploaded for custom styling of this subreddit.
        """
        if self.images is None:
            self.images = {}
        for name, img_num in self.images.iteritems():
            if isinstance(img_num, int):
                yield (name, img_num)

    def add_image(self, name, max_num = None):
        """
        Adds an image to the image holder's image list.  The resulting
        number of the image is returned.  Note that image numbers are
        non-sequential insofar as unused numbers in an existing range
        will be populated before a number outside the range is
        returned.  Imaged deleted with del_image are pushed onto the
        "/empties/" stack in the images dict, and those values are
        pop'd until the stack is empty.

        raises ValueError if the resulting number is >= max_num.

        The ImageHolder will be _dirty if a new image has been added to
        its images list, and no _commit is called.
        """
        if self.images is None:
            self.images = {}

        if name in self.images:
            # we've seen the image before, so just return the existing num
            return self.images[name]
        # copy and blank out the images list to flag as _dirty
        l = self.images
        self.images = None
        # initialize the /empties/ list
        l.setdefault('/empties/', [])
        try:
            num = l['/empties/'].pop() # grab old number if we can
        except IndexError:
            num = len(l) - 1 # one less to account for /empties/ key
        if max_num is not None and num >= max_num:
            raise ValueError, "too many images"
        # update the dictionary and rewrite to images attr
        l[name] = num
        self.images = l
        return num

    def del_image(self, name):
        """
        Deletes an image from the images dictionary assuming an image
        of that name is in the current dictionary.  The freed up
        number is pushed onto the /empties/ stack for later recycling
        by add_image.

        The Subreddit will be _dirty if image has been removed from
        its images list, and no _commit is called.
        """
        if self.images is None or name not in self.images:
            return
        l = self.images
        self.images = None
        l.setdefault('/empties/', [])
        # push the number on the empties list
        l['/empties/'].append(l[name])
        del l[name]
        self.images = l

