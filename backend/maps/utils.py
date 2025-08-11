from lxml import etree as ET

def extract_map_data(map_xml):
    root = ET.fromstring(map_xml)
    elements_root = root.find("Z")
    grounds_count = len(elements_root.xpath("S/S"))
    decorations_count = len(elements_root.xpath("D/*"))
    objects_count = len(elements_root.xpath("O/O"))
    joints_count = len(elements_root.xpath("L/*"))
    properties = root.find("P")
    length = int(properties.get("L", 800))
    height = int(properties.get("H", 400))

    return {
        "grounds_count": grounds_count,
        "decorations_count": decorations_count,
        "objects_count": objects_count,
        "joints_count": joints_count,
        "length": length,
        "height": height
    }