import morepath
from api_core import *


# initialise app
class App(morepath.App):
    pass

# serve docs as root
@App.path(path='')
class Root(object):
    def __init__(self):
        pass

    @staticmethod
    def open_docs_from_file():
        with open('docs.html', 'r', encoding='utf8') as fp:
            docs = fp.read()
        return docs


@App.html(model=Root)
def get_static_html(self, request):
    return self.open_docs_from_file()


# single bib record

# available formats: marcxml / json
# marcxml: only processed bib record available
# json: original and processed records available

@App.path(model=MarcRecordWrapper, path='/get_single_bib_record/{marc_record_number}')
def get_record(marc_record_number):
    if local_bib_index[marc_record_number]:
        return MarcRecordWrapper(read_marc_from_binary(local_bib_index[marc_record_number]), local_auth_index)
    else:
        r = requests.get('http://data.bn.org.pl/api/bibs.marc?id={}'.format(marc_record_number)).content
        r = read_marc_from_binary(r)
        r = MarcRecordWrapper(r, local_auth_index)
        return r


@App.json(model=MarcRecordWrapper, name='json')
def render_json(self, request):
    return {'original_record': self.marc_record_as_dict, 'processed_record': self.marc_record_processed_as_dict}


@App.view(model=MarcRecordWrapper, name='xml')
def render_xml(self, request):
    return morepath.Response(body=self.marc_record_processed_ax_xml, content_type='application/xml')


# bib records chunk

# available formats: xml
# xml: only processed bib records available

@App.path(model=BibliographicRecordsChunk, path='/get_bibs/{query_for_data_bn}')
def get_bib_records(query_for_data_bn):
    if query_for_data_bn in local_next_page_cache.cache:
        chunk_to_return = local_next_page_cache.cache[query_for_data_bn]
        return chunk_to_return
    else:
        chunk_to_return = BibliographicRecordsChunk(query_for_data_bn, local_auth_index, local_bib_index)
        local_next_page_cache.add_to_cache(chunk_to_return)
        local_next_page_cache.flush_cache()
        return chunk_to_return


@App.view(model=BibliographicRecordsChunk)
def render_bib_records(self, request):
    return morepath.Response(body=self.xml_processed_chunk, content_type='application/xml')


# single authority record

@App.path(model=Authority, path='/get_authority/{id_or_name}')
def get_authority(id_or_name):
    return Authority(id_or_name, local_auth_index)

@App.view(model=Authority)
def authority_info(self, request):
    return "Authority: {} - {}".format(str(self.authority_ids), self.authority_heading)

# index status

@App.path(model='UpdaterStatus', path='/get_update_status')
def get_update_status():
    return updater_status

@App.json(model=UpdaterStatus)
def render_update_status(self, request):
        return {"update_in_progress": self.update_in_progress, "last_bib_update": self.last_bib_update.isoformat(timespec='seconds') + 'Z', "last_auth_update": self.last_auth_update.isoformat(timespec='seconds') + 'Z'}


# bibliographic and authority records index updater

@App.path(model='Updater', path='/update/{index}')
def update_index(index):
    if updater_status.update_in_progress:
        return updater
    else:
        if index == 'authorities':
            updater.update_authority_index(local_auth_index, updater_status)
        if index == 'bibs':
            updater.update_bibliographic_index(local_bib_index, updater_status)

@App.json(model=Updater)
def render_after_update(self, request):
    return {"update_in_progress": updater_status.update_in_progress, "last_bib_update": updater_status.last_bib_update.isoformat(timespec='seconds') + 'Z', "last_auth_update": updater_status.last_auth_update.isoformat(timespec='seconds') + 'Z'}


# set index source files
bib_marc = 'bibs-all.marc'
auth_marc = 'authorities-all.marc'

# create indexes
local_bib_index = create_local_bib_index(bib_marc)
local_auth_index = create_authority_index(auth_marc)

# create updater and updater_status
updater = Updater()
updater_status = UpdaterStatus(datetime.utcnow())

# set max bibs cache size
local_next_page_cache = BibliographicRecordsChunksCache(20)

if __name__ == '__main__':
    logging.root.addHandler(logging.StreamHandler(sys.stdout))
    logging.root.setLevel(level=logging.DEBUG)

    morepath.run(App())