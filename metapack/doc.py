# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Extensions to the MetatabDoc, Resources and References, etc.
"""

EMPTY_SOURCE_HEADER = '_NONE_'  # Marker for a column that is in the destination table but not in the source


from metapack.terms import Resource, Reference
from metatab import MetatabDoc
from rowgenerators import Url
from .html import linkify
from .util import slugify


class MetapackDoc(MetatabDoc):



    def __init__(self, ref=None, decl=None, package_url=None, cache=None, resolver=None, clean_cache=False):

        self.register_term_class('root.resource', 'metapack.terms.Resource')
        self.register_term_class('root.reference', 'metapack.terms.Resource')

        super().__init__(ref, decl, package_url, cache, resolver, clean_cache)


    @property
    def name(self):
        """Return the name from the metatab document, or the identity, and as a last resort,
        the slugified file reference"""
        return self.get_value('root.name', self.get_value('root.identity',slugify(self._ref)))

    @property
    def env(self):
        """Return the module associated with a package's python library"""
        try:
            return self.get_lib_module_dict()
        except ImportError:
            return None

    def get_lib_module_dict(self):
        """Load the 'lib' directory as a python module, so it can be used to provide functions
        for rowpipe transforms. This only works filesystem packages"""

        from os.path import dirname, abspath, join, isdir
        from importlib import import_module
        import sys

        u = Url(self.ref)
        if u.proto == 'file':

            doc_dir = dirname(abspath(u.parts.path))

            # Add the dir with the metatab file to the system path
            sys.path.append(doc_dir)

            if not isdir(join(doc_dir, 'lib')):
                return {}

            try:
                m = import_module("lib")
                return {k: v for k, v in m.__dict__.items() if not k.startswith('__')}
            except ImportError as e:

                raise ImportError("Failed to import python module form 'lib' directory: ", str(e))

        else:
            return {}

    def resource(self, name=None, term='Root.Datafile', section='Resources'):

        return self.find_first(term=term, name=name, section=section)


    def _repr_html_(self, **kwargs):
        """Produce HTML for Jupyter Notebook"""

        def resource_repr(r, anchor=kwargs.get('anchors', False)):
            return "<p><strong>{name}</strong> - <a target=\"_blank\" href=\"{url}\">{url}</a> {description}</p>" \
                .format(name='<a href="#resource-{name}">{name}</a>'.format(name=r.name) if anchor else r.name,
                        description=r.get_value('description', ''),
                        url=r.resolved_url)

        def documentation():

            out = ''

            try:
                self['Documentation']
            except KeyError:
                return ''

            try:
                for t in self['Documentation']:

                    if t.get_value('url'):

                        out += ("\n<p><strong>{} </strong>{}</p>"
                                .format(linkify(t.get_value('url'), t.get_value('title')),
                                        t.get_value('description')
                                        ))

                    else:  # Mostly for notes
                        out += ("\n<p><strong>{}: </strong>{}</p>"
                                .format(t.record_term.title(), t.value))


            except KeyError:
                raise
                pass

            return out

        def contacts():

            out = ''

            try:
                self['Contacts']
            except KeyError:
                return ''

            try:

                for t in self['Contacts']:
                    name = t.get_value('name', 'Name')
                    email = "mailto:" + t.get_value('email') if t.get_value('email') else None

                    web = t.get_value('url')
                    org = t.get_value('organization', web)

                    out += ("\n<p><strong>{}: </strong>{}</p>"
                            .format(t.record_term.title(),
                                    (linkify(email, name) or '') + " " + (linkify(web, org) or '')
                                    ))

            except KeyError:
                pass

            return out

        return """
<h1>{title}</h1>
<p>{name}</p>
<p>{description}</p>
<p>{ref}</p>
<h2>Documentation</h2>
{doc}
<h2>Contacts</h2>
{contact}
<h2>Resources</h2>
<ol>
{resources}
</ol>
""".format(
            title=self.find_first_value('Root.Title', section='Root'),
            name=self.find_first_value('Root.Name', section='Root'),
            ref=self.ref,
            description=self.find_first_value('Root.Description', section='Root'),
            doc=documentation(),
            contact=contacts(),
            resources='\n'.join(["<li>" + resource_repr(r) + "</li>" for r in self.resources()])
        )

    @property
    def html(self):
        from .html import html
        return html(self)

    @property
    def markdown(self):
        from .html import markdown
        return markdown(self)

