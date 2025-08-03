from lxml import etree as ET

def extract_map_data(map_xml):
    tree = ET.parse(map_xml)
    root = tree.getroot()
    elements_root = root.find("Z")
    grounds_count = len(elements_root.xpath("S/S"))
    objects_count = len(elements_root.xpath("O/O"))
    joints_count = len(elements_root.xpath("L/*"))

    return (grounds_count, objects_count, joints_count)