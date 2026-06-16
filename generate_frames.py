#!/usr/bin/env python3
import os
import math
import subprocess
import copy
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFilter

def ease_out_cubic(t):
    return 1.0 - (1.0 - t) ** 3

def ease_in_out_quad(t):
    if t < 0.5:
        return 2.0 * t * t
    else:
        return 1.0 - (-2.0 * t + 2.0) ** 2 / 2.0

def ease_out_quad(t):
    return 1.0 - (1.0 - t) * (1.0 - t)

def ease_out_back(t, overshoot=1.70158):
    s = overshoot
    t = t - 1.0
    return t * t * ((s + 1.0) * t + s) + 1.0

# Polygon Resampling for morphing
def resample_polygon(vertices, n):
    num_v = len(vertices)
    edges = []
    total_len = 0.0
    cum_len = [0.0]
    for i in range(num_v):
        p1 = vertices[i]
        p2 = vertices[(i + 1) % num_v]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.sqrt(dx*dx + dy*dy)
        total_len += length
        cum_len.append(total_len)
        edges.append((p1, p2, length))
        
    points = []
    for step in range(n):
        target_d = (step / float(n)) * total_len
        edge_idx = 0
        for i in range(num_v):
            if cum_len[i] <= target_d <= cum_len[i+1]:
                edge_idx = i
                break
        else:
            edge_idx = num_v - 1
            
        p1, p2, edge_len = edges[edge_idx]
        if edge_len > 0:
            t = (target_d - cum_len[edge_idx]) / edge_len
        else:
            t = 0.0
        x = p1[0] + (p2[0] - p1[0]) * t
        y = p1[1] + (p2[1] - p1[1]) * t
        points.append((x, y))
    return points

def get_circle_points(r=32, n=180):
    points = []
    for i in range(n):
        theta = i * (2 * math.pi / n)
        points.append((r * math.cos(theta), r * math.sin(theta)))
    return points

def get_star_points(num_points, r_outer, r_inner, n=180, rotation=0.0):
    vertices = []
    for i in range(num_points * 2):
        theta = i * (math.pi / num_points) - math.pi / 2.0 + rotation
        r = r_outer if (i % 2 == 0) else r_inner
        vertices.append((r * math.cos(theta), r * math.sin(theta)))
    return resample_polygon(vertices, n)

def get_pentagon_points(r=32, n=180):
    vertices = []
    for i in range(5):
        theta = i * (2 * math.pi / 5.0) - math.pi / 2.0
        vertices.append((r * math.cos(theta), r * math.sin(theta)))
    return resample_polygon(vertices, n)

def get_pill_points(w=64, h=32, n=180):
    r = h / 2.0
    cx = (w - h) / 2.0
    vertices = []
    # Right semi-circle
    for i in range(20):
        theta = -math.pi / 2.0 + i * (math.pi / 19.0)
        vertices.append((cx + r * math.cos(theta), r * math.sin(theta)))
    # Left semi-circle
    for i in range(20):
        theta = math.pi / 2.0 + i * (math.pi / 19.0)
        vertices.append((-cx + r * math.cos(theta), r * math.sin(theta)))
    return resample_polygon(vertices, n)

def get_oval_points(a=32, b=20, n=180):
    points = []
    for i in range(n):
        theta = i * (2 * math.pi / n)
        x = a * math.cos(theta)
        y = b * math.sin(theta)
        rot_x = x * math.cos(-math.pi/4) - y * math.sin(-math.pi/4)
        rot_y = x * math.sin(-math.pi/4) + y * math.cos(-math.pi/4)
        points.append((rot_x, rot_y))
    return points

def spring_simulation(df_local):
    stiffness = 180.0
    damping_ratio = 0.6
    morph_scale = 0.14
    
    wn = math.sqrt(stiffness)
    za = damping_ratio * wn
    wd = wn * math.sqrt(1.0 - damping_ratio * damping_ratio)
    r = za / wd
    
    spring_max_velocity = 6.69
    
    t = df_local / 60.0
    pos = 1.0 - math.exp(-za * t) * (math.cos(wd * t) + r * math.sin(wd * t))
    vel = math.exp(-za * t) * (wn * wn / wd) * math.sin(wd * t)
    
    p = min(1.0, pos)
    scale = 1.0 + vel * (morph_scale / spring_max_velocity)
    rot_morph = pos * 120.0
    
    return p, scale, rot_morph

def main():
    workspace = os.path.dirname(os.path.abspath(__file__))
    svg_path = os.path.join(workspace, "image.svg")
    output_dir = os.path.join(workspace, "caelestia-plymouth")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Parse and extract paths from image.svg
    print("Parsing SVG...")
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    tree = ET.parse(svg_path)
    root_node = tree.getroot()
    
    g_node = None
    for elem in root_node.iter():
        if elem.tag.endswith('g') and elem.get('id') == 'light-4':
            g_node = elem
            break
            
    if g_node is None:
        raise ValueError("Could not find group with id='light-4' in SVG.")
        
    paths = list(g_node)
    
    # Identify components by start of 'd' attribute
    logo_body_paths = []
    star1_path = None
    star2_path = None
    star3_path = None
    
    for p in paths:
        d = p.get('d', '')
        if d.startswith("m475.79") or d.startswith("m1151.76") or d.startswith("m625.03"):
            logo_body_paths.append(p)
        elif d.startswith("m1096.96"):
            star1_path = p
        elif d.startswith("m1267.37"):
            star2_path = p
        elif d.startswith("m1259.85"):
            star3_path = p
            
    # Function to write a subset of SVG paths to a file (Vibrant color mapping)
    def write_svg_subset(keep_paths, out_path, is_star=False):
        new_tree = copy.deepcopy(tree)
        new_g = None
        for elem in new_tree.getroot().iter():
            if elem.tag.endswith('g') and elem.get('id') == 'light-4':
                new_g = elem
                break
        
        keep_d_set = {p.get('d') for p in keep_paths}
        for child in list(new_g):
            if child.get('d') not in keep_d_set:
                new_g.remove(child)
                
        # Apply color mappings
        svg_str = ET.tostring(new_tree.getroot(), encoding='utf-8').decode('utf-8')
        if is_star:
            # Stars are bright white
            svg_str = svg_str.replace("#fff", "#ffffff")
            svg_str = svg_str.replace("#FFF", "#ffffff")
            svg_str = svg_str.replace("#6ae5e1", "#ffffff")
            svg_str = svg_str.replace("#6AE5E1", "#ffffff")
            svg_str = svg_str.replace("#ebf4ff", "#ffffff")
            svg_str = svg_str.replace("#EBF4FF", "#ffffff")
        else:
            # Body is white & vibrant neon teal
            svg_str = svg_str.replace("#fff", "#ffffff")
            svg_str = svg_str.replace("#FFF", "#ffffff")
            svg_str = svg_str.replace("#6ae5e1", "#9feee7") # vibrant neon teal
            svg_str = svg_str.replace("#6AE5E1", "#9feee7")
            svg_str = svg_str.replace("#ebf4ff", "#ffffff") # pure white
            svg_str = svg_str.replace("#EBF4FF", "#ffffff")
        
        with open(out_path, "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + svg_str)
            
    # Write components to SVG
    temp_body_svg = os.path.join(workspace, "temp_body.svg")
    temp_star1_svg = os.path.join(workspace, "temp_star1.svg")
    temp_star2_svg = os.path.join(workspace, "temp_star2.svg")
    temp_star3_svg = os.path.join(workspace, "temp_star3.svg")
    
    write_svg_subset(logo_body_paths, temp_body_svg, is_star=False)
    write_svg_subset([star1_path], temp_star1_svg, is_star=True)
    write_svg_subset([star2_path], temp_star2_svg, is_star=True)
    write_svg_subset([star3_path], temp_star3_svg, is_star=True)
    
    # Render component SVGs to PNG (width 1024 - full size for crisp high-resolution transforms)
    print("Rendering component SVGs to PNG...")
    components = ['body', 'star1', 'star2', 'star3']
    svgs = [temp_body_svg, temp_star1_svg, temp_star2_svg, temp_star3_svg]
    pngs = [os.path.join(workspace, f"temp_{c}.png") for c in components]
    
    for svg, png in zip(svgs, pngs):
        subprocess.run([
            "rsvg-convert",
            "-w", "1024",
            "-f", "png",
            "-o", png,
            svg
        ], check=True)
        # Clean up SVG
        if os.path.exists(svg):
            os.remove(svg)
            
    # Load PNG assets into Pillow and place them in 2048x2048 canvases centered
    canvas_w, canvas_h = 2048, 2048
    
    def make_canvas(png_path):
        img = Image.open(png_path).convert("RGBA")
        c = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        w, h = img.size
        paste_x = (canvas_w - w) // 2
        paste_y = (canvas_h - h) // 2
        c.paste(img, (paste_x, paste_y), img)
        return c
        
    body_canvas = make_canvas(pngs[0])
    star1_canvas = make_canvas(pngs[1])
    star2_canvas = make_canvas(pngs[2])
    star3_canvas = make_canvas(pngs[3])
    
    # Clean up temp PNGs
    for png in pngs:
        if os.path.exists(png):
            os.remove(png)
            
    # Vibrant Planet Colors
    dot_colors = [
        (87, 205, 218, 255),  # Vibrant Blue
        (250, 116, 111, 255),  # Vibrant Red
        (211, 250, 232, 255),  # Bright Yellow-Green
        (141, 241, 223, 255)   # Vibrant Green
    ]
    
    merge_target_color = (255, 255, 255, 255) # pure white merge target
    
    # Global Layout (2048x2048 space)
    final_canvas_size = 2048
    logo_center_x, logo_center_y = 1024, 800
    progress_bar_y = 1680
    
    # Concentric Orbits
    R = [24.0 * 4.0, 48.0 * 4.0, 72.0 * 4.0, 96.0 * 4.0]
    planet_radii = [4.0 * 4.0, 5.0 * 4.0, 6.0 * 4.0, 7.0 * 4.0]
    speeds = [3.0, 2.0, 1.0, -1.0] # Orbit cycles per 150 frames (negative is retrograde)
    omega = [s * 2.0 * math.pi / 150.0 for s in speeds]
    init_angles = [0.0, math.pi / 2.0, math.pi, 3.0 * math.pi / 2.0]
    
    # Helper to calculate planet loop position at frame f (at 4x)
    def get_loop_pos(f, i):
        f_local = f - 90
        theta_i = init_angles[i] + f_local * omega[i]
        d_i = R[i]
        x = logo_center_x + d_i * math.cos(theta_i)
        y = logo_center_y + d_i * math.sin(theta_i)
        return x, y
        
    # Helper to transform a 2048x2048 canvas (scale, rotate, opacity, blur)
    def transform_canvas(canvas, scale, rotation, opacity, blur=0):
        w = int(canvas_w * scale)
        h = int(canvas_h * scale)
        if w <= 0 or h <= 0:
            return Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            
        scaled = canvas.resize((w, h), Image.Resampling.LANCZOS)
        
        placed = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        paste_x = (canvas_w - w) // 2
        paste_y = (canvas_h - h) // 2
        placed.paste(scaled, (paste_x, paste_y), scaled)
        
        rotated = placed.rotate(-rotation, resample=Image.Resampling.BICUBIC)
        
        if opacity < 1.0:
            r_ch, g_ch, b_ch, a_ch = rotated.split()
            a_ch = a_ch.point(lambda p: int(p * opacity))
            rotated = Image.merge("RGBA", (r_ch, g_ch, b_ch, a_ch))
            
        if blur > 0:
            rotated = rotated.filter(ImageFilter.GaussianBlur(blur))
            
        return rotated

    # V6 M3 Loading Shapes (SoftBurst, Sunny, Pill) resampled to 180 points
    print("Generating M3 shapes...")
    shape0_points = get_star_points(10, 32.0, 22.0, 180) # SoftBurst
    shape1_points = get_star_points(8, 32.0, 25.0, 180)  # Sunny
    shape2_points = get_pill_points(64.0, 32.0, 180)     # Pill
    shapes_list = [shape0_points, shape1_points, shape2_points]

    print("Generating 360 frames...")
    
    for f in range(360):
        # Create transparent canvas (2048x2048)
        frame = Image.new("RGBA", (final_canvas_size, final_canvas_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)
        
        if f < 90:
            # --- PHASE 1: INTRO (0-89) ---
            # Central Star Sun fades in (Material Design "Sunny" 8-pointed shape)
            sun_t = min(1.0, f / 30.0)
            sun_scale = ease_out_cubic(sun_t)
            sun_alpha = int(255 * sun_scale)
            if sun_alpha > 0:
                sun_rot = f * (2.0 * math.pi / 360.0)
                sun_pts = get_star_points(8, 32.0 * sun_scale, 25.0 * sun_scale, n=32, rotation=sun_rot)
                sun_pts_placed = [(pt[0] + logo_center_x, pt[1] + logo_center_y) for pt in sun_pts]
                draw.polygon(sun_pts_placed, fill=(255, 213, 79, sun_alpha))
                
            for i in range(4):
                f_start = i * 10
                if f >= f_start:
                    t = min(1.0, (f - f_start) / 30.0)
                    ease = ease_out_cubic(t)
                    r = planet_radii[i] * ease
                    
                    target_x, target_y = get_loop_pos(f, i)
                    x = logo_center_x + (target_x - logo_center_x) * ease
                    y = logo_center_y + (target_y - logo_center_y) * ease
                    draw.ellipse([x - r, y - r, x + r, y + r], fill=dot_colors[i])
                    
        elif f < 120:
            # --- PHASE 2: KEPLERIAN DANCE LOOP (90-119) ---
            # Central Star Sun (Material Design "Sunny" shape)
            sun_rot = f * (2.0 * math.pi / 360.0)
            sun_pts = get_star_points(8, 32.0, 25.0, n=32, rotation=sun_rot)
            sun_pts_placed = [(pt[0] + logo_center_x, pt[1] + logo_center_y) for pt in sun_pts]
            draw.polygon(sun_pts_placed, fill=(255, 213, 79, 255))
            
            for i in range(4):
                x, y = get_loop_pos(f, i)
                r = planet_radii[i]
                draw.ellipse([x - r, y - r, x + r, y + r], fill=dot_colors[i])
                
        elif f < 150:
            # --- PHASE 3: MERGE (120-149) ---
            f_merge = f - 120
            t = f_merge / 30.0
            factor = 1.0 - t
            
            # Central Star Sun fades out
            sun_alpha = int(255 * factor)
            if sun_alpha > 0:
                sun_rot = f * (2.0 * math.pi / 360.0)
                sun_pts = get_star_points(8, 32.0 * factor, 25.0 * factor, n=32, rotation=sun_rot)
                sun_pts_placed = [(pt[0] + logo_center_x, pt[1] + logo_center_y) for pt in sun_pts]
                draw.polygon(sun_pts_placed, fill=(255, 213, 79, sun_alpha))
                
            for i in range(4):
                theta_i = init_angles[i] + (30 + f_merge) * omega[i]
                d_i = R[i] * factor
                x = logo_center_x + d_i * math.cos(theta_i)
                y = logo_center_y + d_i * math.sin(theta_i)
                
                if t >= 0.7:
                    c_t = (t - 0.7) / 0.3
                    orig_color = dot_colors[i]
                    r_col = int(orig_color[0] + (merge_target_color[0] - orig_color[0]) * c_t)
                    g_col = int(orig_color[1] + (merge_target_color[1] - orig_color[1]) * c_t)
                    b_col = int(orig_color[2] + (merge_target_color[2] - orig_color[2]) * c_t)
                    color = (r_col, g_col, b_col, 255)
                else:
                    color = dot_colors[i]
                    
                r = planet_radii[i] * factor if factor > 0 else 0
                if r > 0:
                    draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
                    
        elif f < 240:
            # --- PHASE 4: MORPH / LOGO INTRO (150-239) ---
            f_morph = f - 150
            
            # Central dot expands and fades out
            if f_morph < 30:
                t_dot = f_morph / 30.0
                ease_dot = 1.0 - (1.0 - t_dot) ** 2
                circle_r = (16.0 + 32.0 * ease_dot) * 4.0
                circle_opacity = max(0.0, 1.0 - t_dot)
                circle_color = (
                    merge_target_color[0],
                    merge_target_color[1],
                    merge_target_color[2],
                    int(255 * circle_opacity)
                )
                
                if circle_opacity > 0:
                    circle_layer = Image.new("RGBA", (final_canvas_size, final_canvas_size), (0, 0, 0, 0))
                    circle_draw = ImageDraw.Draw(circle_layer)
                    circle_draw.ellipse(
                        [logo_center_x - circle_r, logo_center_y - circle_r, logo_center_x + circle_r, logo_center_y + circle_r],
                        fill=circle_color
                    )
                    frame = Image.alpha_composite(frame, circle_layer)
                    draw = ImageDraw.Draw(frame)
                    
            # Compute logo body transform properties
            # Rotation
            if f_morph < 36:
                rot = 750.0 * ease_out_cubic(f_morph / 36.0)
            elif f_morph < 46:
                rot = 750.0 + (710.0 - 750.0) * ease_in_out_quad((f_morph - 36) / 10.0)
            elif f_morph < 58:
                rot = 710.0 + (725.0 - 710.0) * ease_in_out_quad((f_morph - 46) / 12.0)
            elif f_morph < 68:
                rot = 725.0 + (720.0 - 725.0) * ease_out_quad((f_morph - 58) / 10.0)
            else:
                rot = 720.0
                
            # Scale
            if f_morph < 36:
                sc = 1.08 * ease_out_cubic(f_morph / 36.0)
            elif f_morph < 44:
                sc = 1.08 + (0.96 - 1.08) * ease_in_out_quad((f_morph - 36) / 8.0)
            elif f_morph < 54:
                sc = 0.96 + (1.00 - 0.96) * ease_out_back((f_morph - 44) / 10.0, 1.05)
            else:
                sc = 1.0
                
            # Opacity
            if f_morph < 22:
                op = ease_in_out_quad(f_morph / 22.0)
            else:
                op = 1.0
                
            # Blur (scaled by 4.0)
            if f_morph < 32:
                bl = 240.0 * (1.0 - ease_out_cubic(f_morph / 32.0))
            else:
                bl = 0.0
                
            # Compute star transform properties
            star_delays = [40, 46, 50]
            star_opacities = [0.0, 0.0, 0.0]
            star_scales = [0.0, 0.0, 0.0]
            
            for j in range(3):
                f_star = f_morph - star_delays[j]
                if f_star >= 0:
                    # Opacity
                    if f_star < 26:
                        star_opacities[j] = ease_in_out_quad(f_star / 26.0)
                    else:
                        star_opacities[j] = 1.0
                    # Scale
                    if f_star < 18:
                        star_scales[j] = 1.08 * ease_out_quad(f_star / 18.0)
                    elif f_star < 32:
                        star_scales[j] = 1.08 + (1.0 - 1.08) * ease_in_out_quad((f_star - 18) / 14.0)
                    else:
                        star_scales[j] = 1.0
                        
            # Build combined logo (2048x2048 canvas size)
            combined = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            combined.paste(body_canvas, (0, 0), body_canvas)
            
            # Composite stars
            star_canvases = [star1_canvas, star2_canvas, star3_canvas]
            for j in range(3):
                if star_opacities[j] > 0 and star_scales[j] > 0:
                    star_trans = transform_canvas(star_canvases[j], star_scales[j], 0, star_opacities[j])
                    combined = Image.alpha_composite(combined, star_trans)
                    
            # Apply overall transforms to combined logo and paste centered (offset -224)
            logo_transformed = transform_canvas(combined, sc, rot, op, bl)
            paste_x = 0
            paste_y = -224
            frame.paste(logo_transformed, (paste_x, paste_y), logo_transformed)
            
        else:
            # --- PHASE 5: LOGO & M3 LOADER LOOP (240-359) ---
            f_loop = f - 240
            
            # Stars float and scale breathing offsets (synchronized to 120-frame loop)
            s1_dy = -2.5 * math.sin(f_loop * (2 * math.pi / 120.0))
            s1_sc = 1.0 + 0.04 * math.sin(f_loop * (2 * math.pi / 120.0))
            
            s2_dy = 2.5 * math.sin(f_loop * (2 * math.pi / 120.0))
            s2_sc = 1.0 + 0.06 * math.sin(f_loop * (2 * math.pi / 120.0))
            
            s3_dy = -2.5 * math.sin(f_loop * (4 * math.pi / 120.0))
            s3_sc = 1.0 + 0.04 * math.sin(f_loop * (4 * math.pi / 120.0))
            
            # Composite stars on top of body (2048x2048)
            combined = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            combined.paste(body_canvas, (0, 0), body_canvas)
            
            # Transform star 1
            star1_trans = transform_canvas(star1_canvas, s1_sc, 0, 1.0)
            star1_placed = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            star1_placed.paste(star1_trans, (0, int(s1_dy * 4.0)), star1_trans)
            combined = Image.alpha_composite(combined, star1_placed)
            
            # Transform star 2
            star2_trans = transform_canvas(star2_canvas, s2_sc, 0, 1.0)
            star2_placed = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            star2_placed.paste(star2_trans, (0, int(s2_dy * 4.0)), star2_trans)
            combined = Image.alpha_composite(combined, star2_placed)
            
            # Transform star 3
            star3_trans = transform_canvas(star3_canvas, s3_sc, 0, 1.0)
            star3_placed = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            star3_placed.paste(star3_trans, (0, int(s3_dy * 4.0)), star3_trans)
            combined = Image.alpha_composite(combined, star3_placed)
            
            paste_x = 0
            paste_y = -224
            frame.paste(combined, (paste_x, paste_y), combined)
            
            # --- M3 SQUIGGLY LOADING CIRCLE ---
            cycle_idx = f_loop // 40
            df_local = f_loop % 40
            
            from_idx = cycle_idx
            to_idx = (cycle_idx + 1) % 3
            
            # Run Spring Simulation
            p, s_spring, rot_morph = spring_simulation(df_local)
            
            # Interpolate points:
            shape_from = shapes_list[from_idx]
            shape_to = shapes_list[to_idx]
            morphed_points = [
                ((1.0 - p) * p1[0] + p * p2[0], (1.0 - p) * p1[1] + p * p2[1])
                for p1, p2 in zip(shape_from, shape_to)
            ]
            
            # Render morphed shape at 4x resolution (512x512 canvas) for anti-aliasing
            highres_size = 512
            highres_img = Image.new("RGBA", (highres_size, highres_size), (0, 0, 0, 0))
            highres_draw = ImageDraw.Draw(highres_img)
            scaled_points = [(pt[0] * 4.0 + 256.0, pt[1] * 4.0 + 256.0) for pt in morphed_points]
            highres_draw.polygon(scaled_points, fill=(159, 238, 231, 255)) # vibrant neon teal #9feee7
            
            # Rotate loader on high resolution canvas to keep edges perfectly sharp
            cRot = f_loop * 3.0
            lRot = cycle_idx * 120.0
            rot = cRot + lRot + rot_morph
            highres_rotated = highres_img.rotate(-rot, resample=Image.Resampling.BICUBIC)
            
            # Downscale & scale by spring bounce directly at the final step
            loader_size = 512
            w = int(loader_size * s_spring)
            h = int(loader_size * s_spring)
            if w > 0 and h > 0:
                shape_scaled = highres_rotated.resize((w, h), Image.Resampling.LANCZOS)
                paste_loader_x = logo_center_x - w // 2
                paste_loader_y = progress_bar_y - h // 2
                frame.paste(shape_scaled, (paste_loader_x, paste_loader_y), shape_scaled)
            
        # Downsample 4x highres canvas to 512x512 for perfect antialiasing
        final_frame = frame.resize((512, 512), Image.Resampling.LANCZOS)
        
        # Save frame
        frame_name = f"frame_{f:03d}.png"
        frame_path = os.path.join(output_dir, frame_name)
        final_frame.save(frame_path, "PNG")
        
    print("Done generating V6 frames!")

if __name__ == "__main__":
    main()
