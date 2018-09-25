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