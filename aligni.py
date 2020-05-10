import requests
import time
import xml.etree.ElementTree as ET

from collections import namedtuple

# Aligni rate limits to no more than 30 calls in 60 seconds.
RATE_LIMIT_SECS = 2.1

AligniPart = namedtuple('AligniPart', 'part_id revision_id')

class Aligni:
    def __init__(self, api_token, url_base):
        """
        Initialize the Aligni class with the API
        Token and URL.
        """
        self.api_token = api_token
        self.url_base = url_base

    def create_part(self,
                    partnumber,
                    manufacturer_pn,
                    manufacturer_name,
                    part_type,
                    units,
                    revision,
                    description,
                    comment,
                    alternate_part_ids=[]):
        """
        Public method to create an Aligni top level part.

        Returns the part ID of the created part.
        """
        # Look up manufacturer ID
        manufacturer_id = ""
        manufacturer_dict = self.get_manufacturer_list()
        if str(manufacturer_name) in manufacturer_dict:
            manufacturer_id = manufacturer_dict[str(manufacturer_name)]
        else:
            manufacturer_id =  self.create_manufacturer(str(manufacturer_name))

        # Get Type ID
        part_type_id = ""
        part_type_dict = self.get_part_types()
        if str(part_type) in part_type_dict:
            part_type_id = part_type_dict[str(part_type)]
        else:
            part_type_id = self.__api_create_parttype(part_type)

        # Look up units ID
        unit_id = ""
        units_dict = self.get_units()
        if str(units) in units_dict:
            unit_id = units_dict[str(units)]
        else:
            unit_id = self.create_unit(units)

        # Call API
        return self.__api_create_part(partnumber,
                                      manufacturer_pn,
                                      manufacturer_id,
                                      part_type_id,
                                      unit_id,
                                      revision,
                                      description,
                                      comment,
                                      alternate_part_ids)

    def __api_create_parttype(self,
                              type_name):
        """
        Creates a new parttype in Aligni.
        """
        # First contstruct the XML tree for the request.
        root = ET.Element('parttype')

        name_xml = ET.SubElement(root, "name")
        name_xml.text = str(type_name)

        material_xml = ET.SubElement(root, "is_non_material")
        material_xml.text = str('false')

        # Construct the HTTP request.
        headers = {'Content-Type': 'application/xml',
                'Accept': 'application/xml'}
        xml_string = ET.tostring(root, encoding='utf-8')

        # Send the HTTP request.
        try:
            response = requests.post(self.url_base + self.api_token + '/parttype/',
                                    data=xml_string, headers=headers)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        # Check if the request was successful and raise an exception if not.
        if response.status_code == 400:
            raise requests.ConnectionError(response.content)

        if response.status_code == 429:
            raise requests.ConnectionError('Aligni Rate Limit Exceeded')

        type_id = None
        tree = ET.fromstring(response.text)
        for child in tree:
            if child.tag == 'id':
                type_id  = child.text

        time.sleep(RATE_LIMIT_SECS)
        return type_id


    def __api_create_part(self,
                          partnumber,
                          manufacturer_pn,
                          manufacturer_id,
                          parttype_id,
                          unit_id,
                          rev_name,
                          description,
                          comment,
                          alternate_part_ids=[]):
        """
        Creates a part in Aligni by constructing the XML and sending an
        HTTP request.

        :param partnumber: The aligni part number.
        :param manufacturer_pn: The manufacturer part number.
        :param manufacturer_id: The manufacturer id number from aligni.
        :param parttype_id: The parttype ID for aligni.
        :param unit_id: The unit ID for aligni.
        :param rev_name: The revision name of this part.
        :param description: The item description.
        :param comment: Comment about the part.

        https://api.aligni.com/v2/part/create.html
        """

        # First contstruct the XML tree for the request.
        root = ET.Element('part')

        partnumber_xml = ET.SubElement(root, "partnumber")
        partnumber_xml.text = str(partnumber)

        manufacturer_pn_xml = ET.SubElement(root, "manufacturer_pn")
        manufacturer_pn_xml.text = str(manufacturer_pn)

        manufacturer_id_xml = ET.SubElement(root, "manufacturer_id")
        manufacturer_id_xml.text = str(manufacturer_id)

        parttype_id_xml = ET.SubElement(root, "parttype_id")
        parttype_id_xml.text = str(parttype_id)

        unit_id_xml = ET.SubElement(root, "unit_id")
        unit_id_xml.text = str(unit_id)

        # Add the revision info subtree.
        revision = ET.SubElement(root, "revision")
        
        revision_name_xml = ET.SubElement(revision, "revision_name")
        revision_name_xml.text = str(rev_name)

        description_xml = ET.SubElement(revision, "description")
        description_xml.text = str(description)

        comment_xml = ET.SubElement(revision, "comment")
        comment_xml.text = str(comment)

        for alternate_part in alternate_part_ids:
            # Add the revision info subtree.
            alternate_parts = ET.SubElement(root, "alternate_parts")

            for alternate_part_id in alternate_part_ids:
                alternate_part = ET.SubElement(alternate_parts, "alternate_part")

                alternate_part_id_xml = ET.SubElement(alternate_part, "part_id")
                alternate_part_id_xml.text = str(alternate_part_id)

                alternate_part_comment_xml = ET.SubElement(alternate_part, "comment")
                alternate_part_comment_xml.text = "testing"

                alternate_part_quality_xml = ET.SubElement(alternate_part, "quality")
                alternate_part_quality_xml.text = "100"

        # Construct the HTTP request.
        headers = {'Content-Type': 'application/xml',
                'Accept': 'application/xml'}
        xml_string = ET.tostring(root, encoding='utf-8')

        print(xml_string)

        time.sleep(RATE_LIMIT_SECS)

        # Send the HTTP request.
        try:
            response = requests.post(self.url_base + self.api_token + '/part/',
                                    data=xml_string, headers=headers)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        # Check if the request was successful and raise an exception if not.
        if response.status_code == 400:
            raise requests.ConnectionError(response.content)

        if response.status_code == 429:
            raise requests.ConnectionError('Aligni Rate Limit Exceeded')

        # Parse response and get part ID.
        part_id = None
        rev_id = None
        tree = ET.fromstring(response.text)
        for child in tree:
            if child.tag == 'id':
                    part_id = child.text
            
            if child.tag == 'revision':
                for rev_tags in child:
                    if rev_tags.tag == 'id':
                        rev_id = rev_tags.text

        return AligniPart(part_id, rev_id)


    def create_subpart(self,
                       parent_part_id,
                       parent_part_revision_id, 
                       subpart_revision_id,
                       manufacturer_pn,
                       partnumber,
                       quantity,
                       designator,
                       comment):
        """
        Creates a part in Aligni by constructing the XML and sending an
        HTTP request.

        :param parent_part_id: The Aligni ID of the parent part.
        :param parent_part_revision_id: The Aligni rev of the parent part.
        :param subpart_revision_id: The Aligni rev of the parent part.
        :param manufacturer_pn: The manufacturer part number.
        :param partnumber: The internal part number.
        :param quantity: How many of the sub part to include.
        :param designator: The schematic designator for the part.
        :param comment: Comment about the part.

        https://api.aligni.com/v2/part/create.html
        """

        # First contstruct the XML tree for the request.
        root = ET.Element('subpart')

        parent_part_id_xml = ET.SubElement(root, "part_id")
        parent_part_id_xml.text = str(parent_part_id)

        parent_part_rev_xml = ET.SubElement(root, "part_revision_id")
        parent_part_rev_xml.text = str(parent_part_revision_id)

        subpart_part_revision_id_xml = ET.SubElement(root, "subpart_part_revision_id")
        subpart_part_revision_id_xml.text = str(subpart_revision_id)

        manufacturer_pn_xml = ET.SubElement(root, "manufacturer_pn")
        manufacturer_pn_xml.text = str(manufacturer_pn)

        partnumber_xml = ET.SubElement(root, "partnumber")
        partnumber_xml.text = str(partnumber)

        quantity_xml = ET.SubElement(root, "quantity")
        quantity_xml.text = str(quantity)

        designator_xml = ET.SubElement(root, "designator")
        designator_xml.text = str(designator)

        comment_xml = ET.SubElement(root, "comment")
        comment_xml.text = str(comment)

        # Construct the HTTP request.
        headers = {'Content-Type': 'application/xml',
                'Accept': 'application/xml'}
        xml_string = ET.tostring(root, encoding='utf-8')

        print(xml_string)

        time.sleep(RATE_LIMIT_SECS)

        # Send the HTTP request.
        try:
            response = requests.post(self.url_base + self.api_token + '/subpart/',
                                    data=xml_string, headers=headers)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        # Check if the request was successful and raise an exception if not.
        if response.status_code == 400:
            raise requests.ConnectionError(response.content)

        if response.status_code == 429:
            raise requests.ConnectionError('Aligni Rate Limit Exceeded')


    def create_manufacturer(self, manufacturer_name):
        """
        Creates a manufacturer in the Aligni database.

        :param manufacturer_name: The name of the manufacturer.

        Returns ID of created manufacturer.
        """

        # First contstruct the XML tree for the request.
        root = ET.Element('manufacturer')

        manufacturer_name_xml = ET.SubElement(root, "name")
        manufacturer_name_xml.text = str(manufacturer_name)

        # Construct the HTTP request.
        headers = {'Content-Type': 'application/xml',
                'Accept': 'application/xml'}
        xml_string = ET.tostring(root, encoding='utf-8')

        time.sleep(RATE_LIMIT_SECS)

        # Send the HTTP request.
        try:
            response = requests.post(self.url_base + self.api_token + '/manufacturer/',
                                    data=xml_string, headers=headers)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        # Check if the request was successful and raise an exception if not.
        if response.status_code == 400:
            raise requests.ConnectionError(response.content)

        if response.status_code == 429:
            raise requests.ConnectionError('Aligni Rate Limit Exceeded')

        # Parse response and get manufacturer ID.
        manufacturer_id = None
        tree = ET.fromstring(response.text)
        for child in tree:
            for item in child:
                if item.tag == 'id':
                    manufacturer_id  = item.text

        return manufacturer_id


    def get_manufacturer_list(self):
        """
        Populates a dictiontary of the manufacturers in the ALigni database.
        """
        url = self.url_base + self.api_token + '/manufacturer'
        r=requests.get(url)

        tree = ET.fromstring(r.text)

        manu_dict = {}

        for child in tree:
            manufacturer_name = ''
            manufacturer_id = ''

            for item in child:
                if item.tag == 'name':
                    manufacturer_name = item.text
                
                if item.tag == 'id':
                    manufacturer_id = item.text
                
            if manufacturer_name != '':
                manu_dict[manufacturer_name] = manufacturer_id

        time.sleep(RATE_LIMIT_SECS)

        return manu_dict

    def get_parts_list(self):
        """
        Returns a dictiontary of the parts in the ALigni database.
        Keyed using manufacturer pn.
        """
        url = self.url_base + self.api_token + '/part'
        r=requests.get(url)

        tree = ET.fromstring(r.text)

        part_dict = {}

        for child in tree:
            part_name = ''
            part_id = ''
            
            for item in child:
                if item.tag == 'manufacturer_pn':
                    part_name = item.text
                
                if item.tag == 'id':
                    part_id = item.text
                
            if part_name != '':
                part_dict[part_name] = part_id

        return part_dict


    def get_part_types(self):
        """
        Returns a dictionary of parts types in the Aligni database.
        Keyed using the part type name.
        The dictionary contains the ID.
        """

        url = self.url_base + self.api_token + '/parttype'
        r=requests.get(url)
        time.sleep(RATE_LIMIT_SECS)

        tree = ET.fromstring(r.text)

        type_dict = {}

        for child in tree:
            type_name = ''
            type_id = ''
            
            for item in child:
                if item.tag == 'name':
                    type_name = item.text
                
                if item.tag == 'id':
                    type_id = item.text
                
            if type_name != '':
                type_dict[type_name] = type_id

        return type_dict

    def create_unit(self, unit_name):
        """
        Creates a unit type in the Aligni database.

        :param unit_name: The name of the unit.

        :return The ID of the created Unit.
        """

        # First contstruct the XML tree for the request.
        root = ET.Element('unit')

        unit_name_xml = ET.SubElement(root, "name")
        unit_name_xml.text = str(unit_name)

        # Construct the HTTP request.
        headers = {'Content-Type': 'application/xml',
                'Accept': 'application/xml'}
        xml_string = ET.tostring(root, encoding='utf-8')

        time.sleep(RATE_LIMIT_SECS)

        # Send the HTTP request.
        try:
            response = requests.post(self.url_base + self.api_token + '/unit/',
                                    data=xml_string, headers=headers)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        # Check if the request was successful and raise an exception if not.
        if response.status_code == 400:
            raise requests.ConnectionError(response.content)

        if response.status_code == 429:
            raise requests.ConnectionError('Aligni Rate Limit Exceeded')

        # Parse response and get part ID.
        unit_id = None
        print(response.text)
        tree = ET.fromstring(response.text)
        for child in tree:
            if child.tag == 'id':
                unit_id = child.text

        return unit_id

    def get_units(self):
        """
        Returns a dictionary of unit types in the Aligni database.
        Keyed using the unit name.
        The dictionary contains the ID.
        """

        url = self.url_base + self.api_token + '/unit'
        r=requests.get(url)

        time.sleep(RATE_LIMIT_SECS)

        tree = ET.fromstring(r.text)

        unit_dict = {}

        for child in tree:
            unit_name = ''
            unit_id = ''
            
            for item in child:
                if item.tag == 'name':
                    unit_name = item.text
                
                if item.tag == 'id':
                    unit_id = item.text
                
            if unit_name != '':
                unit_dict[unit_name] = unit_id

        return unit_dict
