import os.path
import xmlschema
import struct
import xml.etree.ElementTree as ET
import json
import jsonschema

DEFAULT_ISO_SCHEMA='schemas/ISO11783_TaskFile_V2-1.xsd'
LOG_JSON_SCHEMA_PATH='schemas/ISOBUS_CONVERTER-Log-schemaV1.0.json'
PMAP_JSON_SCHEMA_PATH='schemas/ISOBUS_CONVERTER-PrescriptionMap-schemaV2.3.json'

def validate_json(jsondoc, schema_path=PMAP_JSON_SCHEMA_PATH):
	assert schema_path in [LOG_JSON_SCHEMA_PATH, PMAP_JSON_SCHEMA_PATH] or os.path.isfile(schema_path), "%s not a file"%schema_path
	
	schema_doc = json.load(open(schema_path, 'r'))
	json_doc = json.load(open(jsondoc, 'r')) if not isinstance(jsondoc, dict) else jsondoc

	try:
		jsonschema.validate(json_doc, schema_doc)
	except Exception as e:
		return False, str(e)
	else:
		return True, json_doc

def to_dict(xml, path='.', vocabulary = True, xsd = DEFAULT_ISO_SCHEMA):
    try:
        schema = xmlschema.XMLSchema(xsd, validation='skip')
        res_dict = schema.to_dict('%s/'%path+xml, decimal_type=str, validation='skip')

        if vocabulary:
            xsd_vocabulary = make_vocabulary(xsd)
            res_dict = replace_keys(res_dict, '', xsd_vocabulary)

    except xmlschema.XMLSchemaValidationError as e:
        return False, str(e)
    return True, res_dict

def to_xml(data, xsd = DEFAULT_ISO_SCHEMA):
    try:
        schema = xmlschema.XMLSchema(xsd, validation='skip')
        xsd_vocabulary = make_vocabulary(xsd)
        xsd_vocabulary_map = {}
        for k, v in xsd_vocabulary.items():
            if '@' in k:
                tag, attr = k.split("@", 1)
                xsd_vocabulary_map[xsd_vocabulary[tag] + '@' + v] = '@' + attr
            else:
                xsd_vocabulary_map[v] = k
    except xmlschema.XMLSchemaValidationError as e:
        return False, str(e)

    # Replace Keys according to ISOBUS XML Schema notation
    # Any mapping/alteration between json schema and ISOXML should be done before this.
    # Anything not compliant to the vocabulary, will be omitted
    data_named = replace_keys({xsd_vocabulary['ISO11783_TaskData']: data}, '', xsd_vocabulary_map)

    return True, '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'+ET.tostring(schema.encode(data_named['ISO11783_TaskData'], path='ISO11783_TaskData', validation='skip'), encoding='unicode', method='xml')
    #return (ret is None, ret)

def replace_keys(document, key, vocabulary):
    """
    Replace XML tags and attributes names in document with relative descriptions from given vocabulary
    """
    document2 = document
    if isinstance(document, list):
        document2 = []
        for list_items in document:
            d = replace_keys(document=list_items, key=key, vocabulary=vocabulary)
            document2.append(d)

    elif isinstance(document, dict):
        document2 = {}
        for dict_key, dict_value in iter(document.items()):

            d = replace_keys(document=dict_value, key=dict_key, vocabulary=vocabulary)

            actual_key = key + dict_key if dict_key[0] == '@' else dict_key
            if actual_key in vocabulary:
                document2[vocabulary[actual_key]] = d
            elif key + '@' + dict_key in vocabulary:
                document2[vocabulary[key + '@' + dict_key]] = d
            else:
                actual_key = dict_key[1:] if dict_key[0] == '@' else dict_key
                document2[actual_key] = d
    return document2

def make_vocabulary(xmlxsd):
    schema = xmlschema.XMLSchema(xmlxsd, validation='skip')
    xsd = schema.to_dict(xmlxsd)
    _items = {}
    for elem in xsd['xs:element']:
        # Tag name and description in vocabulary
        try:
            _items[elem['@name']] = elem['xs:annotation']['xs:documentation'][0]['$']
        except KeyError:
            pass

        try:
            attributes = elem['xs:complexType']['xs:attribute']
        except KeyError:
            attributes = None

        # single attribute are not in a list
        if isinstance(attributes, list):
            attlist = attributes
        elif isinstance(attributes, dict):
            attlist = [attributes]

        for attribute in attlist:
            if isinstance(attribute, dict):
                try:
                    if 'xs:annotation' in attribute:
                        description = attribute['xs:annotation']['xs:documentation'][0]['$']
                    else:
                        description = attribute['@name']
                    _items[elem['@name'] + '@' + attribute['@name']] = description
                except KeyError:
                    pass

    return _items

#test unit
if __name__ == '__main__':
	#print(validate_xml('test/TASKDATA-PMAP/TASKDATA.XML'))
    import repo
    with open ('C:/Users/casel/workspace/Este/DssFertilizer/UsrFile/Oncino_4_presa_1_shapefile.json', 'r') as json_file:
        json_file = json.load(json_file)
        res, body_json= validate_json(json_file, PMAP_JSON_SCHEMA_PATH)
        assert res, body_json
        repo.path='C:/Users/casel/workspace/Este/DssFertilizer/UsrFile'
        res, body_xml = to_xml({k:repo.Factory.parse_recursive(k,v) for k,v in body_json.items()})
        assert res, body_xml
	    #print(validate_json('/home/tony/Progetti/ISOBUSConverter-tony/test/ISOBUS_CONVERTER-PrescriptionMap-examplev2.0.json',PMAP_JSON_SCHEMA_PATH))
