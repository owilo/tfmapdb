from lxml import etree
from PIL import Image, ImageDraw
import math
import numpy as np

def extract_map_data(map_xml):
    root = etree.fromstring(map_xml)
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

def get_spawn_point(map_xml):
    root = etree.fromstring(map_xml)

    decorations = root.xpath("Z/D")

    spawns = []
    holes = []
    for deco in decorations:
        spawns.extend(deco.xpath("DS"))
        holes.extend(deco.xpath("T"))

    if spawns:
        return np.array([float(spawns[0].get("X")), float(spawns[0].get("Y"))])
    elif holes:
        return np.array([float(holes[0].get("X")), float(holes[0].get("Y"))])
    else:
        return None


def is_autowin(map_xml):
    spawn_point = get_spawn_point(map_xml)
    if spawn_point is None:
        return False
    root = etree.fromstring(map_xml)

    decorations = root.xpath("Z/D")

    holes = []
    cheeses = []
    for deco in decorations:
        holes.extend(deco.xpath("T"))
        cheeses.extend(deco.xpath("F"))

    for cheese in cheeses:
        cheese_coordinates = np.array([float(cheese.get("X")), float(cheese.get("Y"))])
        if np.linalg.norm(cheese_coordinates - spawn_point) <= 30:
            for hole in holes:
                hole_coordinates = np.array([float(hole.get("X")), float(hole.get("Y"))])
                if np.linalg.norm(hole_coordinates - spawn_point) <= 30:
                    return True
            return False
    return False

# TODO rework
from PIL import Image, ImageDraw
import xml.etree.ElementTree as ET
import math
from typing import Optional, Tuple, List

def xml_to_image(xml_str, size=(400, 200), scale=1.0, bgcolor=(106, 116, 149, 255)):
    """
    Render the XML structure to a PIL RGBA image.
    """

    palette = [
        "a87f56", "89a5b8", "5a3879", "ad2a00", "5b240b", "563018", "8ba417", "f3d45f",
        "dddddd", "51a0a5", "797568", "e6eff0", "324650", "324650", "000000", "c4c8d1",
        "a87f56", "c69e1b", "c99fb3", "59c012", "fbd310", "2c0054"
    ]

    def hex_to_rgba(hexstr: Optional[str], alpha: float = 1.0) -> Tuple[int, int, int, int]:
        if not hexstr:
            hexstr = "000000"
        hs = hexstr.strip().lstrip("#")
        if len(hs) == 3:
            hs = ''.join(2 * c for c in hs)
        hs = (hs + "000000")[:6]
        try:
            r = int(hs[0:2], 16)
            g = int(hs[2:4], 16)
            b = int(hs[4:6], 16)
        except Exception:
            r, g, b = 0, 0, 0
        a = int(round(max(0.0, min(1.0, float(alpha))) * 255))
        return (r, g, b, a)

    def parse_float_attr(elem, name, default=0.0):
        v = elem.get(name)
        if v is None or v == "":
            return default
        try:
            return float(v)
        except Exception:
            return default

    def safe_alpha_composite(base: Image.Image, overlay: Image.Image, xy: Tuple[int, int]):
        ox, oy = int(xy[0]), int(xy[1])
        if overlay.width == 0 or overlay.height == 0:
            return
        left_crop = max(0, -ox)
        top_crop = max(0, -oy)
        right_overflow = max(0, ox + overlay.width - base.width)
        bottom_overflow = max(0, oy + overlay.height - base.height)
        crop_left = left_crop
        crop_top = top_crop
        crop_right = overlay.width - right_overflow
        crop_bottom = overlay.height - bottom_overflow

        if crop_right <= crop_left or crop_bottom <= crop_top:
            return

        if crop_left != 0 or crop_top != 0 or right_overflow != 0 or bottom_overflow != 0:
            overlay = overlay.crop((crop_left, crop_top, crop_right, crop_bottom))
            ox = max(0, ox)
            oy = max(0, oy)

        base.alpha_composite(overlay, dest=(ox, oy))

    if isinstance(xml_str, str):
        xml_bytes = xml_str.encode("utf-8")
    else:
        xml_bytes = xml_str
    root = ET.fromstring(xml_bytes)

    z_nodes = root.findall('Z')
    if not z_nodes:
        if root.tag == 'Z':
            z = root
        else:
            raise ValueError("Cannot find Z element in XML")
    else:
        z = z_nodes[0]

    scaled_size = (int(round(size[0] * scale)), int(round(size[1] * scale)))
    img = Image.new("RGBA", scaled_size, bgcolor)

    tf_items = []
    ds_items = []
    for d in z.findall('D'):
        for child in list(d):
            tag = child.tag
            if tag in ("T", "F"):
                x = parse_float_attr(child, "X", 0.0) * scale
                y = parse_float_attr(child, "Y", 0.0) * scale
                tf_items.append((tag, x, y))
            elif tag == "DS":
                x = parse_float_attr(child, "X", 0.0) * scale
                y = parse_float_attr(child, "Y", 0.0) * scale
                ds_items.append((tag, x, y))

    def draw_marker_circle(image: Image.Image, cx: float, cy: float, diam: float, color_hex: str):
        d = max(1, int(round(diam)))
        temp = Image.new("RGBA", (d, d), (0, 0, 0, 0))
        draw = ImageDraw.Draw(temp)
        draw.ellipse([0, 0, d - 1, d - 1], fill=hex_to_rgba(color_hex, alpha=1.0))
        paste_x = int(round(cx - d / 2.0))
        paste_y = int(round(cy - d / 2.0))
        safe_alpha_composite(image, temp, (paste_x, paste_y))

    for tag, x, y in tf_items:
        if tag == "T":
            draw_marker_circle(img, x, y, 30 * scale, "332117")
        else:  # F
            draw_marker_circle(img, x, y, 24 * scale, "E8B95B")

    for _tag, x, y in ds_items:
        draw_marker_circle(img, x, y, 24 * scale, "503B24")

    s_container = z.find('S')
    s_elems_all = s_container.findall('S') if s_container is not None else z.findall('S')

    s_positions: List[Tuple[float, float]] = []
    for s in s_elems_all:
        Xf = parse_float_attr(s, "X", 0.0)
        Yf = parse_float_attr(s, "Y", 0.0)
        s_positions.append((Xf, Yf))

    def parse_joint_c_attr(c_attr: Optional[str]):
        if not c_attr:
            return None
        parts = [p.strip() for p in c_attr.split(",")]
        if len(parts) < 3:
            return None
        color_hex, thickness_str, opacity_str = parts[0], parts[1], parts[2]
        foreground_str = parts[3] if len(parts) > 3 else "0"
        if not (color_hex or thickness_str or opacity_str):
            return None
        try:
            thickness = float(thickness_str)
            opacity = float(opacity_str)
        except Exception:
            return None
        if thickness <= 0 or opacity <= 0:
            return None
        try:
            fg = int(foreground_str or "0")
        except Exception:
            fg = 0
        return (color_hex.lstrip('#'), thickness, opacity, bool(fg))

    jd_container = z.find('L')
    jds = []
    if jd_container is not None:
        for jd in jd_container.findall('JD'):
            parsed = parse_joint_c_attr(jd.get("c"))
            if not parsed:
                continue
            color_hex, thickness, opacity, fg = parsed
            jds.append({
                'elem': jd,
                'color_hex': color_hex,
                'thickness': thickness,
                'opacity': opacity,
                'foreground': fg,
                'P1': jd.get('P1'),
                'P2': jd.get('P2'),
                'M1': jd.get('M1'),
                'M2': jd.get('M2'),
            })

    grounds = []
    for idx, s in enumerate(s_elems_all):
        skip_due_to_m = (s.get('m') is not None)
        Lf = parse_float_attr(s, 'L', 0.0)
        Hf = parse_float_attr(s, 'H', 0.0)
        Xf = parse_float_attr(s, 'X', 0.0)
        Yf = parse_float_attr(s, 'Y', 0.0)
        try:
            t_index = int(s.get('T')) if s.get('T') is not None else 0
        except Exception:
            t_index = 0

        draw_flag = True
        if t_index == 14 or skip_due_to_m:
            draw_flag = False

        if t_index in (8, 9):
            opacity = 0.7
        elif t_index == 15:
            opacity = 0.9
        else:
            opacity = 1.0

        color_hex = palette[t_index] if (0 <= t_index < len(palette)) else palette[0]
        if t_index in (12, 13):
            o_attr = s.get('o')
            if o_attr and o_attr.strip():
                color_hex = o_attr.strip().lstrip('#')
            else:
                draw_flag = False

        color_rgba = hex_to_rgba(color_hex, alpha=opacity)

        angle = 0.0
        P = s.get('P', '')
        if P:
            parts = [p.strip() for p in P.split(",") if p.strip() != ""]
            if len(parts) >= 5:
                try:
                    angle = float(parts[4])
                except Exception:
                    angle = 0.0

        foreground = ('N' in s.attrib)

        grounds.append({
            'elem': s,
            'index': idx,
            'L': Lf,
            'H': Hf,
            'X': Xf,
            'Y': Yf,
            'T': t_index,
            'angle': angle,
            'color_hex': color_hex,
            'color_rgba': color_rgba,
            'opacity': opacity,
            'draw': bool(draw_flag),
            'foreground': bool(foreground),
        })

    def resolve_jd_point(P_attr: Optional[str], M_attr: Optional[str]):
        if P_attr:
            try:
                px_txt = P_attr.strip()
                parts = [c.strip() for c in px_txt.split(",") if c.strip() != ""]
                if len(parts) < 2:
                    return None
                px, py = float(parts[0]), float(parts[1])
                return (px * scale, py * scale)
            except Exception:
                return None
        if M_attr is not None:
            try:
                mi = int(M_attr)
                if 0 <= mi < len(s_positions):
                    x_raw, y_raw = s_positions[mi]
                    return (x_raw * scale, y_raw * scale)
            except Exception:
                return None
        return None

    def draw_capsule(main_img: Image.Image, p1, p2, thickness, color_rgba):
        if main_img.mode != "RGBA":
            raise ValueError("main_img must be RGBA")

        t = float(thickness)
        r = t / 2.0

        x1, y1 = p1
        x2, y2 = p2
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)

        if length <= 1e-6:
            diameter = max(1, int(math.ceil(t)))
            temp = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
            draw = ImageDraw.Draw(temp)
            draw.ellipse([0, 0, diameter - 1, diameter - 1], fill=color_rgba)
            paste_x = int(round(x1 - diameter / 2.0))
            paste_y = int(round(y1 - diameter / 2.0))
            safe_alpha_composite(main_img, temp, (paste_x, paste_y))
            return

        ux = dx / length
        uy = dy / length
        px = -uy
        py = ux
        ox = px * r
        oy = py * r

        pA = (x1 + ox, y1 + oy)
        pB = (x2 + ox, y2 + oy)
        pC = (x2 - ox, y2 - oy)
        pD = (x1 - ox, y1 - oy)

        xs = [pA[0], pB[0], pC[0], pD[0], x1 - r, x1 + r, x2 - r, x2 + r]
        ys = [pA[1], pB[1], pC[1], pD[1], y1 - r, y1 + r, y2 - r, y2 + r]

        x0 = min(xs) - 1.0
        y0 = min(ys) - 1.0
        x1b = max(xs) + 1.0
        y1b = max(ys) + 1.0

        bx0 = int(math.floor(x0))
        by0 = int(math.floor(y0))
        bx1 = int(math.ceil(x1b))
        by1 = int(math.ceil(y1b))

        tw = bx1 - bx0
        th = by1 - by0
        if tw <= 0 or th <= 0:
            return

        temp = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        draw = ImageDraw.Draw(temp)

        rA = (pA[0] - bx0, pA[1] - by0)
        rB = (pB[0] - bx0, pB[1] - by0)
        rC = (pC[0] - bx0, pC[1] - by0)
        rD = (pD[0] - bx0, pD[1] - by0)
        rp1 = (x1 - bx0, y1 - by0)
        rp2 = (x2 - bx0, y2 - by0)

        draw.polygon([rA, rB, rC, rD], fill=color_rgba)
        draw.ellipse([rp1[0] - r, rp1[1] - r, rp1[0] + r, rp1[1] + r], fill=color_rgba)
        draw.ellipse([rp2[0] - r, rp2[1] - r, rp2[0] + r, rp2[1] + r], fill=color_rgba)

        safe_alpha_composite(main_img, temp, (bx0, by0))

    joints_bg = []
    joints_fg = []
    for jd in jds:
        p1 = resolve_jd_point(jd['P1'], jd['M1'])
        p2 = resolve_jd_point(jd['P2'], jd['M2'])
        if p1 is None or p2 is None:
            continue
        color_rgba = hex_to_rgba(jd['color_hex'], alpha=jd['opacity'])
        thickness_scaled = jd['thickness'] * scale
        target = joints_fg if jd['foreground'] else joints_bg
        target.append({
            'p1': p1,
            'p2': p2,
            'thickness': thickness_scaled,
            'color_rgba': color_rgba
        })

    grounds_bg = [s for s in grounds if (not s['foreground']) and s['draw']]
    grounds_fg = [s for s in grounds if s['foreground'] and s['draw']]

    # ---- draw layers ----
    # Layer 1: joints (background)
    for cap in joints_bg:
        draw_capsule(img, cap['p1'], cap['p2'], cap['thickness'], cap['color_rgba'])

    # Layer 2: grounds (background)
    def draw_ground_item(image: Image.Image, s):
        t_index = s['T']
        color_rgba = s['color_rgba']
        Xs = s['X'] * scale
        Ys = s['Y'] * scale

        if t_index == 13:
            radius = s['L'] * scale
            if radius <= 0:
                return
            diameter = max(1, int(math.ceil(radius * 2.0)))
            temp = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
            draw = ImageDraw.Draw(temp)
            draw.ellipse([0, 0, diameter - 1, diameter - 1], fill=color_rgba)
            paste_x = int(round(Xs - diameter / 2.0))
            paste_y = int(round(Ys - diameter / 2.0))
            safe_alpha_composite(image, temp, (paste_x, paste_y))
            return

        Ls = s['L'] * scale
        Hs = s['H'] * scale
        w = max(1, int(math.ceil(Ls)))
        h = max(1, int(math.ceil(Hs)))
        if w <= 0 or h <= 0:
            return

        rect = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(rect)
        draw.rectangle([0, 0, w - 1, h - 1], fill=color_rgba)

        rot = rect.rotate(-s['angle'], expand=True)
        rw, rh = rot.size
        paste_x = int(round(Xs - rw / 2.0))
        paste_y = int(round(Ys - rh / 2.0))
        safe_alpha_composite(image, rot, (paste_x, paste_y))

    for s in grounds_bg:
        draw_ground_item(img, s)

    # Layer 3: joints (foreground)
    for cap in joints_fg:
        draw_capsule(img, cap['p1'], cap['p2'], cap['thickness'], cap['color_rgba'])

    # Layer 4: grounds (foreground)
    for s in grounds_fg:
        draw_ground_item(img, s)

    return img
