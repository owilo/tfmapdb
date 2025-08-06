from lxml import etree as ET

def extract_map_data(map_xml):
    root = ET.fromstring(map_xml)
    elements_root = root.find("Z")
    grounds_count = len(elements_root.xpath("S/S"))
    objects_count = len(elements_root.xpath("O/O"))
    joints_count = len(elements_root.xpath("L/*"))

    return (grounds_count, objects_count, joints_count)