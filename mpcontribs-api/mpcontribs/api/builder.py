# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os, re, bson
from mpcontribs.config import mp_id_pattern
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert import HTMLExporter
from bs4 import BeautifulSoup

def export_notebook(nb, cid, separate_script=False):
    html_exporter = HTMLExporter()
    html_exporter.template_file = 'basic'
    # TODO pop first code cell here
    body = html_exporter.from_notebook_node(nb)[0]
    body = body.replace("var element = $('#", "var element = document.getElementById('")
    soup = BeautifulSoup(body, 'html.parser')
    soup.div.extract() # remove first code cell (loads mpfile)
    for t in soup.find_all('a', 'anchor-link'):
        t.extract() # rm anchors
    # mark cells with special name for toggling, and
    # make element id's unique by appending cid
    # NOTE every cell has only one tag with id
    div_name = None
    for div in soup.find_all('div', 'cell')[1:]:
        tag = div.find('h3', id=True)
        if tag is not None:
            tag['id'] = '-'.join([tag['id'], str(cid)])
            div_name = tag['id'].split('-')[0]
        if div_name is not None:
            div['name'] = div_name
    # name divs for toggling code_cells
    for div in soup.find_all('div', 'input'):
        div['name'] = 'Input'
    if separate_script:
        script = []
        for s in soup.find_all('script'):
            script.append(s.text)
            s.extract() # remove javascript
        return soup.prettify(), '\n'.join(script)
    return soup.prettify()

class MPContributionsBuilder(object):
    """build user contributions from `mpcontribs.contributions`"""
    def __init__(self, db):
        from mpcontribs.io.core.recdict import RecursiveDict
        self.db = db
        self.nbdir = os.path.dirname(os.path.abspath(__file__))
        self.ep = ExecutePreprocessor(timeout=600, allow_errors=False)
        if isinstance(self.db, dict):
            self.notebooks = RecursiveDict()
        else:
            opts = bson.CodecOptions(document_class=RecursiveDict)
            self.contributions = self.db.contributions.with_options(codec_options=opts)
            self.notebooks = self.db.compositions.with_options(codec_options=opts)

    def delete(self, project, cids):
        for contrib in self.contributions.find({'_id': {'$in': cids}}):
            mp_cat_id, cid = contrib['mp_cat_id'], contrib['_id']
            is_mp_id = mp_id_pattern.match(mp_cat_id)
            coll = self.materials if is_mp_id else self.compositions
            key = '.'.join([project, str(cid)])
            coll.update({}, {'$unset': {key: 1}}, multi=True)
        # remove `project` field when no contributions remaining
        for coll in [self.materials, self.compositions]:
            for doc in coll.find({project: {'$exists': 1}}):
                for d in doc.itervalues():
                    if not d:
                        coll.update({'_id': doc['_id']}, {'$unset': {project: 1}})

    def find_contribution(self, cid):
        return self.db if isinstance(self.db, dict) else \
                self.contributions.find_one({'_id': cid})

    def build(self, cid, api_key=None, endpoint=None):
        """update materials/compositions collections with contributed data"""
        from mpcontribs.io.core.utils import get_short_object_id
        from nbformat import v4 as nbf
        from mpcontribs.io.core.mpfile import MPFileCore
        cid_short, cid_str = get_short_object_id(cid), str(cid)
        contrib = self.find_contribution(cid)
        if not contrib:
            raise Exception('Contribution {} not found!'.format(cid))
        mpfile = MPFileCore.from_contribution(contrib)
        mp_cat_id = mpfile.ids[0]
        is_mp_id = mp_id_pattern.match(mp_cat_id)
        self.curr_coll = self.materials if is_mp_id else self.compositions
        project = contrib.get('project')

        nb = nbf.new_notebook()
        if isinstance(self.db, dict):
            contrib.pop('_id')
            if 'cid' in contrib['content']:
                contrib['content'].pop('cid')
            nb['cells'].append(nbf.new_code_cell(
                "from __future__ import unicode_literals\n"
                "from mpcontribs.io.core.mpfile import MPFileCore\n"
                "from mpcontribs.io.core.recdict import RecursiveDict\n"
                "mpfile = MPFileCore.from_contribution({})\n"
                "identifier = '{}'"
                .format(contrib, mp_cat_id)
            ))
        else:
            nb['cells'].append(nbf.new_code_cell(
                "from __future__ import unicode_literals\n"
                "from mpcontribs.rest.rester import MPContribsRester"
            ))
            os.environ['PMG_MAPI_KEY'] = api_key
            os.environ['PMG_MAPI_ENDPOINT'] = endpoint
            nb['cells'].append(nbf.new_code_cell(
                "with MPContribsRester() as mpr:\n"
                "    mpfile = mpr.find_contribution('{}')\n"
                "    identifier = mpfile.ids[0]"
                .format(cid)
            ))
        nb['cells'].append(nbf.new_markdown_cell(
            "## Contribution #{} for {}".format(cid_short, mp_cat_id)
        ))
        nb['cells'].append(nbf.new_markdown_cell(
            "### Hierarchical Data"
        ))
        nb['cells'].append(nbf.new_code_cell("mpfile.hdata[identifier]"))
        if mpfile.tdata.get(mp_cat_id):
            nb['cells'].append(nbf.new_markdown_cell("### Tabular Data"))
            for table_name in mpfile.tdata[mp_cat_id].keys():
                nb['cells'].append(nbf.new_markdown_cell(
                    "#### {}".format(table_name)
                ))
                nb['cells'].append(nbf.new_code_cell(
                    "mpfile.tdata[identifier]['{}']".format(table_name)
                ))
        if mpfile.gdata.get(mp_cat_id):
            nb['cells'].append(nbf.new_markdown_cell("### Graphical Data"))
            for plot_name in mpfile.gdata[mp_cat_id].keys():
                nb['cells'].append(nbf.new_markdown_cell(
                    "#### {}".format(plot_name)
                ))
                nb['cells'].append(nbf.new_code_cell(
                    "mpfile.gdata[identifier]['{}']".format(plot_name)
                ))

        if mpfile.sdata.get(mp_cat_id):
            nb['cells'].append(nbf.new_markdown_cell("### Structural Data"))
            for structure_name in mpfile.sdata[mp_cat_id].keys():
                nb['cells'].append(nbf.new_markdown_cell(
                    "#### {}".format(structure_name)
                ))
                nb['cells'].append(nbf.new_code_cell(
                    "mpfile.sdata[identifier]['{}']".format(structure_name)
                ))

        self.ep.preprocess(nb, {'metadata': {'path': self.nbdir}})

        if isinstance(self.db, dict):
            return [mp_cat_id, project, cid_short, export_notebook(nb, cid)]
        else:
            build_doc = RecursiveDict()
            build_doc['mp_cat_id'] = mp_cat_id
            build_doc['project'] = project
            build_doc['nb'] = nb
            self.curr_coll.update({'_id': cid}, {'$set': build_doc}, upsert=True)
            return '{}/{}'.format( # return URL for contribution page
                ('materials' if is_mp_id else 'compositions'), cid_str)