import os, json, six
from abc import ABCMeta
from utils import make_pair, get_indentor, RecursiveDict, nest_dict, pandas_to_dict
from ..config import mp_level01_titles
from recparse import RecursiveParser
from monty.io import zopen
from pandas import DataFrame

class MPFile(six.with_metaclass(ABCMeta)):
    """Object for representing a MP Contribution File.

    Args:
        parser (RecursiveParser): recursive parser object, init empty RecursiveDict() if None
    """
    def __init__(self, parser=None):
        self.document = RecursiveDict() if parser is None else parser.document

    @staticmethod
    def from_file(filename):
        """Reads a MPFile from a file.

        Args:
            filename (str): name of file containing contribution data.

        Returns:
            MPFile object.
        """
        with zopen(filename, "rt") as f:
            return MPFile.from_string(f.read())

    @staticmethod
    def from_string(data):
        """Reads a MPFile from a string.

        Args:
            data (str): String containing contribution data.

        Returns:
            MPFile object.
        """
        data = '\n'.join([ # remove all comment lines first
            line for line in data.splitlines()
            if not line.lstrip().startswith("#")
        ])
        parser = RecursiveParser()
        parser.parse(data)
        return MPFile(parser)

    def get_string(self):
        """Returns a string to be written as a file"""
        lines = []
        min_indentor = get_indentor()
        for key,value in self.document.iterate():
            if key is None and isinstance(value, DataFrame):
                lines.append(value.to_csv(index=False, float_format='%g')[:-1])
            else:
                sep = '' if min_indentor in key else ':'
                if key == min_indentor: lines.append('')
                lines.append(make_pair(key, value, sep=sep))
        return '\n'.join(lines).decode('utf-8')

    def __repr__(self):
        return self.get_string()

    def __str__(self):
        """String representation of MPFile file."""
        return self.get_string()

    def write_file(self, filename, **kwargs):
        """Writes MPFile to a file. The supported kwargs are the same as those
        for the MPFile.get_string method and are passed through directly."""
        with zopen(filename, "wt") as f:
            f.write(self.get_string(**kwargs))

    def add_data_table(self, identifier, dataframe, name):
        """add a data table/frame to the root-level section for identifier"""
        # TODO: optional table name, required if multiple tables per root-level section
        self.document.rec_update(nest_dict(
            pandas_to_dict(dataframe), [identifier, name]
        ))

    def get_identifiers(self):
        """list of identifiers (i.e. all root-level headers excl. GENERAL"""
        return [ k for k in self.document if k.lower() != mp_level01_titles[0] ]
