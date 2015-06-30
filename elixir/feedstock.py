import requests
import json
import re
import os
import sys
import re
import logging
import codecs
from html import unescape

from lxml import etree
from xylose import scielodocument
from elixir import utils

html_regex = re.compile(r'<body[^>]*>(.*)</body>', re.DOTALL | re.IGNORECASE)
midias_regex = re.compile(r'href=["\'](.*)["\']', re.IGNORECASE)
images_regex = re.compile(r'["\'](/img.*|\\img.*)["\']', re.IGNORECASE)

logger = logging.getLogger(__name__)

def _config_logging(logging_level='INFO', logging_file=None):

    allowed_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    
    logger.setLevel(allowed_levels.get(logging_level, 'INFO'))

    if logging_file:
        hl = logging.FileHandler(logging_file, mode='a')
    else:
        hl = logging.StreamHandler()

    hl.setFormatter(formatter)
    hl.setLevel(allowed_levels.get(logging_level, 'INFO'))

    logger.addHandler(hl)


def html_decode(string):

    try:
        string = unescape(string)
        logger.info('HTML entities replaced')
    except:
        logger.info('Unable to replace the HTML entities')
        return string

    return string


def loadXML(pid):
    url = 'http://192.168.1.162:7000/api/v1/article?code=%s&format=xmlrsps' % pid
    try:
        xml = requests.get(
            url,
            timeout=10
        ).text.strip()
        logger.info('XML retrieved from (%s)' % url)
    except:
        raise
        logger.error('Timeout opening (%s)' % url)

    return xml


def load_rawdata(pid):
    url = 'http://192.168.1.162:7000/api/v1/article?code=%s' % pid
    try:
        json_data = json.loads(
            requests.get(
                url,
                timeout=10
            ).text.strip()
        )
        logger.info('JSON data retrieved from (%s)' % url)
    except:
        logger.error('Timeout opening (%s)' % 'http://192.168.1.162:7000/api/v1/article?code=%s&format=xmlwos' % pid)

    try:
        rawdata = scielodocument.Article(json_data)
        logger.info('JSON data parsed')
    except:
        logger.error('Unable to parse json retrieved by (%s)' % url)

    return rawdata


def is_valid_pid(pid):
    pid_regex = re.compile("^S[0-9]{4}-[0-9]{3}[0-9xX][0-2][0-9]{3}[0-9]{4}[0-9]{5}$", re.IGNORECASE)

    if pid_regex.search(pid) is None:
        logger.error('Invalid PID (%s)' % pid)
        return False

    logger.info('Valid PID (%s)' % pid)

    return True


def read_file(fl, replace_entities=False, encoding='utf-8', version='sps'):
    """
    This method retrieve the HTML string of a given HTML file.

    Keyword arguments:
    fl -- complete path to the HTML file.
    replace_entities -- a boolean to set if the HTML will be retrived replacing the entities or not, default is False.
    encoding -- document encoding
    """

    try:
        content = codecs.open(fl, 'r', encoding=encoding).read()
        logger.debug('Local file readed (%s)' % fl)
    except FileNotFoundError:
        logger.error('Unable to read file (%s)' % fl)
        raise FileNotFoundError(
            u'File does not exists: %s' % fl
        )

    if not replace_entities or version == 'sps':
        return content

    content = html_decode(content).replace('\n', '')

    return html_regex.findall(content)[0]


def get_document_images(document):
    """
    This method retrieve a list of images paths founded into a HTML.

    Keyword arguments:
    document -- could be a valid file path to a HTML document or a string withing an HTML.
    """

    try:
        html = read_file(document, encoding='iso-8859-1')
    except FileNotFoundError:
        html = document

    images = images_regex.findall(html)

    fixed_slashs = [x.replace('\\', '/').lower() for x in images]

    return fixed_slashs


def get_document_midias(document):
    """
    This method retrieve a list of midia files founded into a HTML.

    Keyword arguments:
    document -- could be a valid file path to a HTML document or a string withing an HTML.
    """
    allowed_midias = ['mp4', 'doc', 'mp3', 'pdf', 'avi', 'mov', 'mpeg', 'ppt', 'xls']

    try:
        html = read_file(document, encoding='iso-8859-1')
    except FileNotFoundError:
        html = document

    midias = midias_regex.findall(html)

    fltr_allowed = [x.replace('\\', '/').lower() for x in midias if x.split('.')[-1].lower() in allowed_midias]

    return fltr_allowed


def get_xml_document_images(document):

    try:
        xml = etree.parse(document)
        logger.debug('XML file parsed')
    except:
        logger.error('XML file could not be parsed')
        raise

    graphics = xml.findall('//graphic')+xml.findall('//inline-graphic')

    files = []
    for fname in [x.get('{http://www.w3.org/1999/xlink}href') for x in graphics]:
        if not '.' in fname:
            files.append('%s.jpg' % fname)
        else:
            files.append(fname)

    return files


def get_xml_document_midias(document):

    try:
        xml = etree.parse(document)
        logger.debug('XML file parsed')
    except:
        logger.error('XML file could not be parsed')
        raise

    midias = xml.findall('//midia')

    files = []
    for fname in [x.get('{http://www.w3.org/1999/xlink}href') for x in midias]:
        files.append(fname)

    return files


def check_images_availability(available_images, document_images):

    if isinstance(document_images, list):
        html_images = document_images
    elif isinstance(document_images, str):
        html_images = get_document_images(document_images)
    elif isinstance(document_images, etree):
        html_images = get_xml_document_images(document_images)
    else:
        raise ValueError('Expected a list of images or a string with an html document, given: %s' % source)

    images_availability = []

    html_images = {x.split('/')[-1]:x for x in html_images}
    av_images = {x.split('/')[-1]:x for x in available_images}

    for image_name, image_path in html_images.items():
        if image_name in av_images:
            logger.info('Image available in the file system (%s)' % image_path)
            images_availability.append((av_images[image_name], True))
        else:
            logger.warning('Image not available in the file system (%s)' % image_path)
            images_availability.append((image_path, False))

    return images_availability


def list_path(path):

    try:
        files = os.listdir(path)
        logger.debug('Source directory found (%s)' % path)
    except FileNotFoundError:
        logger.error('Source directory not found (%s)' % path)
        raise FileNotFoundError(
            u'Source directory does not exists: %s' % path
        )

    return [x.lower() for x in files]


def fix_images_paths(content):
    """
    This method remove all the relative paths from a given source ['img', 'pdf'].

    Ex:
        From: <img src="/img/revistas/rsp/v12n1/fig1.gif">
        To: <img src="fig1.gif">
    """

    def get_file_name(matchobj):
        fullpath = matchobj.group()
        return '"%s"' % fullpath.replace('\\', '/').split('/')[-1][0:-1]

    return images_regex.sub(get_file_name, content)


class Article(object):

    def __init__(self, pid, xml, raw_data, source_dir, deposit_dir):

        if not is_valid_pid(pid):
            raise ValueError(u'Invalid PID: %s' % pid)

        try:
            os.listdir(source_dir)
            logger.debug('Source directory found (%s)' % source_dir)
        except FileNotFoundError:
            logger.error('Source directory not found (%s)' % source_dir)
            raise FileNotFoundError(u'Invalid source directory: %s' % source_dir)

        self.deposit_dir = deposit_dir or '.'

        if self.deposit_dir[-1] in ['/', '\\']:
            self.deposit_dir = deposit_dir[0:-1]

        self.source_dir = source_dir or '.'
        self.xml = xml
        self.xylose = raw_data
        self.pid = pid
        self.journal_issn = self._journal_issn()
        self.issue_label = self._issue_label()
        self.journal_acronym = self._journal_acronym()
        self.content_version = self._content_version()
        self.file_code = self._file_code()

    def _journal_issn(self):
        issn = self.xylose.scielo_issn

        logger.info('Journal ISSN for source files is (%s)' % issn)

        return issn

    def _journal_acronym(self):
        ja = self.xylose.journal_acronym

        logger.info('Journal acronym for source files is (%s)' % ja)

        return ja

    def _file_code(self):

        logger.info('File code is (%s)' % self.xylose.file_code())

        return self.xylose.file_code()

    def _content_version(self):
        """
        This method retrieve the version of the document. If the file with
        the document content is an XML SPS, the method will retrieve 'sps',
        otherwise, if the file is an html the method will retrieve 'legacy'.
        This is checked using the file extension of do path stored into the
        field v702.
        """

        extension = self.xylose.data['article']['v702'][0]['_'].split('.')[-1]

        version = 'legacy'

        if extension == 'xml':
            version = 'sps'

        logger.info('Content version (%s)' % version)

        return version

    def _issue_label(self):
        """
        This method retrieve the name of the directory, where the article
        store the static files. The name is returned in compliance with
        the SciELO patterns. Once this pattern is controlled manually in
        the file system, this method maybe not find a related static
        directory for some articles.
        """

        issue_dir = ''

        if self.xylose.issue == 'ahead':
            issue_dir += self.xylose.publication_date[0:4]

        if self.xylose.volume:
            issue_dir += 'v%s' % self.xylose.volume

        if self.xylose.supplement_volume:
            issue_dir += 's%s' % self.xylose.supplement_volume

        if self.xylose.issue:
            issue_dir += 'n%s' % self.xylose.issue

        if self.xylose.supplement_issue:
            issue_dir += 's%s' % self.xylose.supplement_issue

        if self.xylose.document_type == 'press-release':
            issue_dir += 'pr'

        issue_label = issue_dir.lower()

        logger.info('Issue label for source files is (%s)' % issue_label)

        return issue_label

    @property
    def _get_body_from_files(self):

        htmls = {}
        for doc in self.list_documents:
            filename = doc.split('/')[-1]
            x = htmls.setdefault(filename.replace('_b', '_'), {'files': []})
            htmls[filename.replace('_b', '_')]['files'].append(doc)

        for html, filenames in htmls.items():
            docs = []
            for doc in filenames['files']:
                docs.append(
                    read_file(
                        doc,
                        replace_entities=True,
                        encoding='iso-8859-1',
                        version=self.content_version
                    )
                )

            content = ''.join(docs).strip()

            htmls[html]['content'] = content

        return htmls

    @property
    def list_source_images(self):

        path = '/'.join(
            [self.source_dir, 'img', self.journal_acronym, self.issue_label]
        )

        images = ['/'.join([path, x]) for x in list_path(path)]

        if len(images) == 0:
            logger.debug('No source images available for the issue (%s)' % self.issue_label)

        for image in images:
            logger.debug('Image (%s) available in source for the issue (%s)' % (image, self.issue_label))

        return images

    @property
    def list_document_images(self):

        doc_images = []

        for document in self.list_documents:
            if self.content_version == 'sps':
                doc_images += get_xml_document_images(document)
            else:
                doc_images += get_document_images(document)

        if len(doc_images) == 0:
            logger.info('Images not required for (%s)' % (self.pid))

        for image in doc_images:
            logger.info('Image (%s) required for (%s)' % (image, self.pid))

        return doc_images

    @property
    def list_document_midia(self):

        doc_midias = []

        for document in self.list_documents:
            if self.content_version == 'sps':
                doc_midias += get_xml_document_midias(document)
            else:
                doc_midias += get_document_midias(document)

        if len(doc_midias) == 0:
            logger.info('Midia not required for (%s)' % (self.pid))

        for midia in doc_midias:
            logger.info('Midia (%s) required for (%s)' % (midia, self.pid))

        return doc_midias

    @property
    def list_pdfs(self):

        path = '/'.join(
            [self.source_dir, 'pdf', self.journal_acronym, self.issue_label]
        )

        pdfs = ['/'.join([path, x]) for x in list_path(path) if self.file_code in x]

        if len(pdfs) == 0:
            logger.warning('PDF not found for (%s)' % self.pid)

        for pdf in pdfs:
            logger.info('PDF (%s) found for (%s)' % (pdf, self.pid))

        return pdfs

    @property
    def list_htmls(self):

        path1 = '/'.join(
            [self.source_dir, 'html', self.journal_acronym, self.issue_label]
        )

        htmls = ['/'.join([path1, x]) for x in list_path(path1) if self.file_code in x]

        if len(htmls) == 0:
            logger.warning('HTML not found for (%s)' % self.pid)

        for html in htmls:
            logger.info('HTML (%s) found for (%s)' % (html, self.pid))

        return htmls

    @property
    def list_xmls(self):

        path = '/'.join(
            [self.source_dir, 'xml', self.journal_acronym, self.issue_label]
        )

        xmls = ['/'.join([path, x]) for x in list_path(path) if self.file_code in x]

        if len(xmls) == 0:
            logger.warning('XML not found for (%s)' % self.pid)

        for xml in xmls:
            logger.info('XML (%s) found for (%s)' % (xml, self.pid))

        return xmls

    @property
    def xml_files(self):
        documents = self.list_documents()

    @property
    def list_documents(self):
        """
        This method retrieve the html's or xml's according to the vesion of the
        given document.
        """

        if self.content_version == 'sps':
            return self.list_xmls
        else:
            return self.list_htmls

    @property
    def xml_sps_with_legacy_data(self):

        xml = self.xml

        try:
            xml = etree.fromstring(xml)
            logger.debug('XML file parsed')
        except:
            logger.error('XML file could not be parsed')
            raise

        nsmap = xml.nsmap

        x = 0
        for html, data in self._get_body_from_files.items():
            if not data['content']:
                continue
            x += 1
            lang = html[0:2]

            paragraphy = etree.Element('p')
            paragraphy.text = etree.CDATA(fix_images_paths(data['content']))

            body = etree.Element('body')
            body.append(paragraphy)

            sa = etree.Element('sub-article')
            sa.set('{http://www.w3.org/XML/1998/namespace}lang', lang)
            sa.set('article-type', 'translated')
            sa.set('id', 'S%s' % x)
            sa.append(etree.Element('front-stub'))
            sa.append(body)

            xml.append(sa)

        return xml

    @property
    def rsps_xml(self):

        docs = []

        if self.content_version == 'sps':

            xml = read_file(
                self.list_documents[0],
                replace_entities=False,
                encoding='utf-8',
                version=self.content_version
            )
            return utils.MemoryFileLike('%s.xml' % self.file_code, xml)
        else:
            return utils.MemoryFileLike(
                '%s.xml' % self.file_code,
                etree.tostring(
                    self.xml_sps_with_legacy_data,
                    encoding='unicode',
                    pretty_print=True
                )
            )

    @property
    def images_status(self):
        return check_images_availability(
            self.list_source_images,
            self.list_document_images
        )

    def wrap_document(self, file_name=None):
        images = [x[0] for x in self.images_status if x[1]]
        pdfs = self.list_pdfs
        xml = self.rsps_xml
        files = images+pdfs
        files.append(xml)

        zipf = utils.WrapFiles(*files)

        if not file_name:
            file_name = '%s.zip' % self.pid

        fn = '/'.join([self.deposit_dir, file_name])

        with codecs.open(fn, 'wb') as f:
            f.write(zipf.read())

        logger.info('ZIP file writen at (%s)' % fn)
