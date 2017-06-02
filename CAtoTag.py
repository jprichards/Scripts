#!/usr/bin/python

# PoC script to get devices with a given Custom Attribute and
# Value and update each device with a Tag for Reporting purposes.
#
# Written by John Richards
# 1/31/17
#
# ./CAtoTag.py <Group-id> <CA-name> <CA-value> <Tag-name>

import json
import requests
import sys
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import tostring

url = ""

headers = {
    'Authorization': "",
    'aw-tenant-code': "",
    'accept': "application/json",
}

grp_id = sys.argv[1]
CA_name = sys.argv[2]
CA_value = sys.argv[3]
tag_name = sys.argv[4]

xmlnamespace = ' xmlns:xsd="http://www.w3.org/2001/XMLSchema" \
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
                 xmlns="http://www.air-watch.com/servicemodel/resources"'


def get_CAdevices(headers, caname, cavalue):
    endpoint = url + "/api/mdm/devices/customattribute/search?"
    query = {"customattributename": caname}
    try:
        response = requests.request("GET", endpoint, headers=headers,
                                    params=query)
        data = json.loads(response.text)
        s = []
        for x in data['Devices']:
            for y in x.get('CustomAttributes'):
                if y.get('Name') == caname:
                    if y.get('Value') == cavalue:
                        s.append(x.get('SerialNumber'))
        return s
    except KeyError, error:
        return 'Unknown'


def get_maxTagID(headers):
    endpoint = url + "/api/mdm/tags/search?organizationgroupid=7"
    try:
        response = requests.request("GET", endpoint, headers=headers)
        data = json.loads(response.text)
        i = []
        for t in data['Tags']:
            i.append(t['Id']['Value'])
        try:
            return max(i)
        except ValueError, e:
            return 1000
    except KeyError, error:
        return 'Unknown'


def createTag(headers, tagxml):
    endpoint = url + "/api/mdm/tags/addtag"
    try:
        response = requests.request("POST", endpoint, headers=headers,
                                    data=tagxml)
        data = json.loads(response.text)
        return data
    except KeyError, error:
        return 'Unknown'


def set_deviceTag(headers, tagid, tagbody):
    endpoint = url + "/api/mdm/tags/%s/adddevices" % tagid
    try:
        response = requests.request("POST", endpoint, headers=headers,
                                    data=tagbody)
        data = json.loads(response.text)
        return data
    except KeyError, error:
        return 'Unknown'


def get_deviceID(headers, serial):
    endpoint = url + "/api/mdm/devices"
    query = {"searchby": "Serialnumber", "id": serial}
    try:
        response = requests.request("GET", endpoint, headers=headers,
                                    params=query)
        data = json.loads(response.text)
        return data["Id"]["Value"]
    except KeyError, error:
        return 'Unknown'


def get_ogid(headers, groupid):
    endpoint = url + "/api/system/groups/search?groupid=" + groupid
    try:
        response = requests.request("GET", endpoint, headers=headers)
        data = json.loads(response.text)
        return data['LocationGroups'][0]['Id']['Value']
    except KeyError, error:
        return 'Unknown'


def main():
    # get current highest Tag ID
    maxTagID = get_maxTagID(headers)
    # increase by 1 for the new tag
    nextTagID = maxTagID + 1

    # get OG ID with Group ID
    ogid = get_ogid(headers, grp_id)

    # build XML for creating the new tag
    rootTag = ET.Element("Tag")
    ET.SubElement(rootTag, "Id").text = str(nextTagID)
    ET.SubElement(rootTag, "TagName").text = tag_name
    ET.SubElement(rootTag, "TagType").text = "Device"
    ET.SubElement(rootTag, "LocationGroupId").text = str(ogid)

    tagXML = tostring(rootTag)
    # create tag
    tagID = createTag(headers, tagXML)
    tid = tagID['Value']

    # get list of serials of devices with supplied CA+Value
    serials = get_CAdevices(headers, CA_name, CA_value)

    # get the Device ID's of the serials
    id_list = []
    for i in serials:
        x = get_deviceID(headers, i)
        id_list.append(x)

    # build XML to add tag to each Device ID
    bulkinput = ET.Element("BulkInput")
    bulkvalues = ET.SubElement(bulkinput, "BulkValues")

    for n in id_list:
        x = ET.SubElement(bulkvalues, "Value")
        x.text = str(n)

    xmlstr = ET.tostring(bulkinput, method='xml')

    # add this XML namespace crap for this particular endpoint
    bs_xml = xmlstr[:10] + xmlnamespace + xmlstr[10:]

    # set device tag for device id's
    set_deviceTag(headers, tid, bs_xml)


if __name__ == '__main__':
    main()
