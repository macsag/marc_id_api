from pymarc import *
import logging
from tqdm import tqdm
import requests
from permissive import PermissiveMARCReader
from datetime import datetime
from datetime import timedelta


# constants for index configuration

# bibliographic record fields to check for authority identifiers
# tuples (string (marc field), list of strings (marc subfields}]

FIELDS_TO_CHECK = [('100', ['a', 'b', 'c', 'd']),
                   ('110', ['a', 'b', 'c', 'd', 'n']),
                   ('111', ['a', 'b', 'c', 'd', 'n']),
                   ('130', ['a', 'b', 'c', 'd', 'n', 'p']),
                   ('380', ['a', 'b', 'c', 'd', 'n', 'p']),
                   ('388', ['a']),
                   ('385', ['a']),
                   ('386', ['a']),
                   ('600', ['a', 'b', 'c', 'd', 'n', 'p', 't', 'x', 'y', 'z']),
                   ('610', ['a', 'b', 'c', 'd', 'n', 'p', 't', 'x', 'y', 'z']),
                   ('611', ['a', 'b', 'c', 'd', 'n', 'p', 't', 'x', 'y', 'z']),
                   ('630', ['a', 'b', 'c', 'd', 'n', 'p', 't', 'x', 'y', 'z']),
                   ('648', ['a']),
                   ('650', ['a', 'b', 'c', 'd', 'x', 'y', 'z']),
                   ('651', ['a', 'b', 'c', 'd', 'x', 'y', 'z']),
                   ('655', ['a', 'b', 'c', 'd', 'x', 'y', 'z']),
                   ('658', ['a']),
                   ('700', ['a', 'b', 'c', 'd', 'n', 'p', 't', 'x', 'y', 'z']),
                   ('710', ['a', 'b', 'c', 'd', 'n', 'p', 't', 'x', 'y', 'z']),
                   ('711', ['a', 'b', 'c', 'd', 'n', 'p', 't', 'x', 'y', 'z']),
                   ('730', ['a', 'b', 'c', 'd', 'n', 'p', 't', 'x', 'y', 'z']),
                   ('830', ['a', 'b', 'c', 'd', 'n', 'p', 't', 'x', 'y', 'z'])]

# authority record fields to index

AUTHORITY_INDEX_FIELDS = ['100', '110', '111', '130', '148', '150', '151', '155']


def create_authority_index(data):
    """
    Creates authority records index in form of dictionary.
    Structure:
    record id (string): heading (string)
    and
    heading (string): record ids (list).

    Available requests by authority id and authority heading.
    """
    authority_index = {}

    with open(data, 'rb') as fp:
        rdr = PermissiveMARCReader(fp, to_unicode=True, force_utf8=True, utf8_handling='ignore')
        for rcd in tqdm(rdr):
            try:
                record_id = rcd.get_fields('001')[0].value()
                #logging.debug('Indeksuję: {}'.format(record_id))
            except IndexError:
                continue
            for fld in AUTHORITY_INDEX_FIELDS:
                if fld in rcd:
                    fld_value = get_rid_of_punctuation(rcd.get_fields(fld)[0].value())
                    authority_index.setdefault(fld_value, []).append(record_id)
                    authority_index[record_id] = fld_value
                    #logging.debug('Indexing: {} - {}'.format(fld_value, authority_index[fld_value]))

    return authority_index

def create_local_bib_index(data):
    l_b_index = {}

    with open(data, 'rb') as fp:
        rdr = PermissiveMARCReader(fp, to_unicode=True, force_utf8=True, utf8_handling='ignore')
        for rcd in tqdm(rdr):
            try:
                record_id = rcd.get_fields('001')[0].value()
                #logging.debug('Indeksuję: {}'.format(record_id))
            except IndexError:
                continue
            l_b_index[record_id] = rcd.as_marc()

    return l_b_index


def get_rid_of_punctuation(string):
    return ''.join(char.replace(',', '').replace('.', '') for char in string)


def read_marc_from_binary(data_chunk):
    marc_rdr = MARCReader(data_chunk, to_unicode=True, force_utf8=True, utf8_handling='ignore')
    for rcd in marc_rdr:
        return rcd


def process_record(marc_record, auth_index):
    """
    Main processing loop for adding authority identifiers to bibliographic record.
    """

    for marc_field_and_subfields in FIELDS_TO_CHECK:
        fld, subflds = marc_field_and_subfields[0], marc_field_and_subfields[1]

        if fld in marc_record:
            raw_objects_flds_list = marc_record.get_fields(fld)

            for raw_fld in raw_objects_flds_list:
                term_to_search = get_rid_of_punctuation(' '.join(subfld for subfld in raw_fld.get_subfields(*subflds)))

                if term_to_search in auth_index:
                    identifier_001 = auth_index[term_to_search][0]
                    marc_record.remove_field(raw_fld)
                    raw_fld.add_subfield('0', identifier_001)
                    marc_record.add_ordered_field(raw_fld)

    return marc_record

def calculate_check_digit(record_id):
    char_sum = 0
    i = 2
    for character in record_id[::-1]:
        char_sum += int(character) * i
        i += 1
    remainder = char_sum % 11
    check_digit = str(remainder) if remainder != 10 else 'x'
    return record_id + check_digit

class UpdaterStatus(object):
    def __init__(self, date_now):
        self.update_in_progress = False

        self.last_bib_update = date_now
        self.last_auth_update = date_now

class Updater(object):
    def __init__(self):
        pass

    def update_bibliographic_index(self, bib_index, updater_status):
        # set update status
        updater_status.update_in_progress = True
        logging.debug("Status: {}".format(updater_status.update_in_progress))

        # create dates for queries
        date_from = updater_status.last_bib_update - timedelta(days=2)
        date_from_in_iso_with_z = date_from.isoformat(timespec='seconds') + 'Z'
        date_to = datetime.utcnow()
        date_to_in_iso_with_z = date_to.isoformat(timespec='seconds') + 'Z'

        # get deleted bib records ids from data.bn.org.pl
        deleted_query = 'http://data.bn.org.pl/api/bibs.json?updatedDate={}%2C{}&deleted=true&limit=100'.format(
            date_from_in_iso_with_z, date_to_in_iso_with_z)

        deleted_records_ids = self.get_records_ids_from_data_bn_for_bibliographic_index_update(deleted_query)
        logging.debug("Rekordów usuniętych: {}".format(len(deleted_records_ids)))

        # get updated bib records ids from data.bn.org.pl
        updated_query = 'http://data.bn.org.pl/api/bibs.json?updatedDate={}%2C{}&limit=100'.format(
            date_from_in_iso_with_z, date_to_in_iso_with_z)

        updated_records_ids = self.get_records_ids_from_data_bn_for_bibliographic_index_update(updated_query)
        logging.debug("Rekordów zmodyfikowanych: {}".format(len(updated_records_ids)))

        # delete authority records from authority index by record id (deletes entries by record id and heading)
        self.remove_deleted_records_from_bibliographic_index(deleted_records_ids, bib_index)

        # update authority records in authority index by record id (updates entries by record id and heading)
        self.update_updated_records_in_bibliographic_index(updated_records_ids, bib_index)

        # set update status
        updater_status.update_in_progress = False
        updater_status.last_bib_update = date_to
        logging.debug("Status: {}".format(updater_status.update_in_progress))

    def update_authority_index(self, authority_index, updater_status):
        # set update status
        updater_status.update_in_progress = True
        logging.debug("Status: {}".format(updater_status.update_in_progress))

        # create dates for queries
        date_from = updater_status.last_auth_update - timedelta(days=3)
        date_from_in_iso_with_z = date_from.isoformat(timespec='seconds') + 'Z'
        date_to = datetime.utcnow()
        date_to_in_iso_with_z = date_to.isoformat(timespec='seconds') + 'Z'

        # get deleted authority records ids from data.bn.org.pl
        deleted_query = 'http://data.bn.org.pl/api/authorities.json?updatedDate={}%2C{}&deleted=true&limit=100'.format(
                                                                        date_from_in_iso_with_z, date_to_in_iso_with_z)

        deleted_records_ids = self.get_records_ids_from_data_bn_for_authority_index_update(deleted_query)
        logging.debug("Rekordów usuniętych: {}".format(len(deleted_records_ids)))

        # get updated authority records ids from data.bn.org.pl
        updated_query = 'http://data.bn.org.pl/api/authorities.json?updatedDate={}%2C{}&limit=100'.format(
                                                            date_from_in_iso_with_z, date_to_in_iso_with_z)
        updated_records_ids = self.get_records_ids_from_data_bn_for_authority_index_update(updated_query)
        logging.debug("Rekordów zmodyfikowanych: {}".format(len(updated_records_ids)))

        # delete authority records from authority index by record id (deletes entries by record id and heading)
        self.remove_deleted_records_from_authority_index(deleted_records_ids, authority_index)

        # update authority records in authority index by record id (updates entries by record id and heading)
        self.update_updated_records_in_authority_index(updated_records_ids, authority_index)

        # set update status
        updater_status.update_in_progress = False
        updater_status.last_auth_update = date_to
        logging.debug("Status: {}".format(updater_status.update_in_progress))

    @staticmethod
    def update_updated_records_in_authority_index(updated_records_ids, authority_index):
        chunk_max_size = 100
        chunks = [updated_records_ids[i:i + chunk_max_size] for i in range(0, len(updated_records_ids), chunk_max_size)]

        for chunk in chunks:
            data = get_marc_data_from_data_bn(chunk)

            rdr = PermissiveMARCReader(data, to_unicode=True, force_utf8=True, utf8_handling='ignore')

            for rcd in rdr:
                try:
                    record_id = rcd.get_fields('001')[0].value()
                    print(record_id)
                except IndexError:
                    continue
                for fld in AUTHORITY_INDEX_FIELDS:
                    if fld in rcd:
                        heading = get_rid_of_punctuation(rcd.get_fields(fld)[0].value())
                        if record_id in authority_index:
                            old_heading = authority_index[record_id]
                            if old_heading == heading:
                                break
                            else:
                                authority_index[record_id] = heading
                                old_heading_ids = authority_index[old_heading]
                                if len(old_heading_ids) > 1:
                                    authority_index[old_heading] = old_heading_ids.remove(record_id)
                                    authority_index.setdefault(heading, []).append(record_id)
                                    break
                                else:
                                    del authority_index[old_heading]
                                    authority_index.setdefault(heading, []).append(record_id)
                                    break
                        else:
                            authority_index[record_id] = heading
                            authority_index.setdefault(heading, []).append(record_id)
                            break

    @staticmethod
    def update_updated_records_in_bibliographic_index(updated_records_ids, bib_index):
        chunk_max_size = 100
        chunks = [updated_records_ids[i:i + chunk_max_size] for i in range(0, len(updated_records_ids), chunk_max_size)]

        for chunk in chunks:
            data = get_marc_data_from_data_bn(chunk)

            rdr = PermissiveMARCReader(data, to_unicode=True, force_utf8=True, utf8_handling='ignore')

            for rcd in rdr:
                try:
                    record_id = rcd.get_fields('001')[0].value()
                    print(record_id)
                except IndexError:
                    continue
                bib_index[record_id] = rcd.as_marc()

    @staticmethod
    def remove_deleted_records_from_authority_index(records_ids, authority_index):
        for record_id in records_ids:
            if record_id in authority_index:
                heading = authority_index.pop(record_id)
                heading_ids = authority_index[heading]
                if len(heading_ids) > 1:
                    authority_index[heading] = heading_ids.remove(record_id)
                else:
                    del authority_index[heading]

    @staticmethod
    def remove_deleted_records_from_bibliographic_index(records_ids, bib_index):
        for record_id in records_ids:
            if record_id in bib_index:
                del bib_index[record_id]

    @staticmethod
    def get_records_ids_from_data_bn_for_authority_index_update(query):
        records_ids = []

        while query:
            r = requests.get(query)
            logging.debug("Pobieram: {}".format(query))
            json_chunk = r.json()

            for rcd in json_chunk['authorities']:
                try:
                    record_id = rcd['marc']['fields'][0]['001']
                except TypeError:
                    record_id = 'a' + calculate_check_digit(str(rcd['id']))
                records_ids.append(record_id)
                logging.debug("Dołączam rekord nr: {}".format(record_id))

            query = json_chunk['nextPage'] if json_chunk['nextPage'] else None

        return records_ids

    @staticmethod
    def get_records_ids_from_data_bn_for_bibliographic_index_update(query):
        records_ids = []

        while query:
            r = requests.get(query)
            logging.debug("Pobieram: {}".format(query))
            json_chunk = r.json()

            for rcd in json_chunk['bibs']:
                try:
                    record_id = rcd['marc']['fields'][0]['001']
                except TypeError:
                    record_id = 'a' + calculate_check_digit(str(rcd['id']))
                records_ids.append(record_id)
                logging.debug("Dołączam rekord nr: {}".format(record_id))

            query = json_chunk['nextPage'] if json_chunk['nextPage'] else None

        return records_ids


def get_marc_data_from_data_bn(records_ids):
    records_ids_length = len(records_ids)

    if records_ids_length <= 100:
        ids_for_query = '%2C'.join(record_id for record_id in records_ids)
        query = 'http://data.bn.org.pl/api/authorities.marc?id={}&limit=100'.format(ids_for_query)

        result = bytearray(requests.get(query).content)
        logging.debug("Pobieram: {}".format(query))
        return result


class BibliographicRecordsChunk(object):
    def __init__(self, query, auth_index, bib_index):
        self.query = query
        self.json_response = self.get_json_response()

        self.next_page_for_data_bn = self.get_next_page_for_data_bn()
        self.next_page_for_user = self.create_next_page_for_user()
        self.records_ids = self.get_bibliographic_records_ids_from_data_bn()
        self.marc_chunk = self.get_bibliographic_records_in_marc_from_local_bib_index(bib_index)
        self.marc_objects_chunk = self.read_marc_from_binary_in_chunks()
        self.marc_processed_objects_chunk = self.batch_process_records(auth_index)
        self.xml_processed_chunk = self.produce_output_xml()

    def get_json_response(self):
        if 'http://data.bn.org.pl/api/bibs.json?{}' not in self.query:
            processed_query = 'http://data.bn.org.pl/api/bibs.json?{}'.format(self.query)
        else:
            processed_query = self.query

        r = requests.get(processed_query)
        #logging.debug("Pobieram: {}".format(processed_query))
        json_chunk = r.json()
        return json_chunk

    def get_bibliographic_records_ids_from_data_bn(self):
        records_ids = []

        for rcd in self.json_response['bibs']:
            record_id = rcd['marc']['fields'][0]['001']
            records_ids.append(record_id)
            #logging.debug("Dołączam rekord nr: {}".format(record_id))

        return records_ids

    def get_next_page_for_data_bn(self):
        return self.json_response['nextPage']

    def create_next_page_for_user(self):
        base_url = 'http://127.0.0.1:5000/get_bibs/'
        query = self.next_page_for_data_bn[36:]

        next_page_for_user = base_url + query

        return next_page_for_user

    def get_bibliographic_records_in_marc_from_data_bn(self):
        """
        Currently not used. Requires additional query to data.bn.org.pl.
        Uses get_bibliographic_records_in_marc_from_local_bib_index instead.
        """

        records_ids_length = len(self.records_ids)

        if records_ids_length <= 100:
            ids_for_query = '%2C'.join(record_id for record_id in self.records_ids)
            query = 'http://data.bn.org.pl/api/bibs.marc?id={}&amp;limit=100'.format(ids_for_query)

            marc_data_chunk = bytearray(requests.get(query).content)
            #logging.debug("Pobieram: {}".format(query))

            return marc_data_chunk

    def get_bibliographic_records_in_marc_from_local_bib_index(self, bib_index):
        marc_data_chunk_list = []

        for record_id in self.records_ids:
            if record_id in bib_index:
                marc_data_chunk_list.append(bib_index[record_id])

        marc_data_chunk_joined_to_one_bytearray = bytearray().join(marc_data_chunk_list)

        return marc_data_chunk_joined_to_one_bytearray

    def read_marc_from_binary_in_chunks(self):
        marc_objects_chunk = []

        marc_rdr = MARCReader(self.marc_chunk, to_unicode=True, force_utf8=True, utf8_handling='ignore')
        for rcd in marc_rdr:
            marc_objects_chunk.append(rcd)

        return marc_objects_chunk

    def batch_process_records(self, auth_index):
        processed_records = [process_record(rcd, auth_index) for rcd in self.marc_objects_chunk]
        return processed_records

    def produce_output_xml(self):
        wrapped_processed_records_in_xml = []

        for rcd in self.marc_processed_objects_chunk:
            xmlized_rcd = marcxml.record_to_xml(rcd, namespace=True)
            wrapped_rcd = '<bib>' + str(xmlized_rcd)[2:-1] + '</bib>'
            wrapped_processed_records_in_xml.append(wrapped_rcd)
            print(wrapped_rcd)

        joined_to_str = ''.join(rcd for rcd in wrapped_processed_records_in_xml)
        print(joined_to_str)

        out_xml = '<resp><nextPage>{}</nextPage><bibs>{}</bibs></resp>'.format(self.next_page_for_user, joined_to_str)

        return out_xml


class BibliographicRecordsChunksCache(object):
    def __init__(self, max_chunks):
        self.max_chunks = max_chunks

        self.chunks_in_cache_count = 0
        self.cache = {}

    def add_to_cache(self, bib_chunk):
        self.cache[bib_chunk.query] = bib_chunk
        self.chunks_in_cache_count += 1
        logging.debug('Cache count: {}'.format(self.chunks_in_cache_count))

    def flush_cache(self):
        if self.chunks_in_cache_count == self.max_chunks:
            self.cache.clear()
            self.chunks_in_cache_count = 0


class MarcRecordWrapper(object):
    def __init__(self, marc_record, authority_index):
        self.marc_record = marc_record
        self.marc_record_as_dict = self.marc_record.as_dict()
        self.marc_record_processed = process_record(self.marc_record, authority_index)
        self.marc_record_processed_as_dict = self.marc_record_processed.as_dict()
        self.marc_record_processed_ax_xml = marcxml.record_to_xml(self.marc_record, namespace=True)


class Authority(object):
    def __init__(self, query, authority_index):
        self.query = query
        self.value_from_dict = authority_index[self.query]
        self.authority_heading = self.get_heading()
        self.authority_ids = self.get_ids()

    def get_heading(self):
        if isinstance(self.value_from_dict, str):
            return self.value_from_dict
        else:
            return self.query

    def get_ids(self):
        if isinstance(self.value_from_dict, list):
            return self.value_from_dict
        else:
            return self.query
