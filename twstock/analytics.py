# -*- coding: utf-8 -*-


class Analytics(object):
    @property
    def price(self):
        return [d.close for d in self.data]

    @property
    def capacity(self):
        return [d.capacity for d in self.data]

