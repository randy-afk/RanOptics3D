"""
ranoptics3d._aperture
~~~~~~~~~~~~~~~~~~~~~
Parse aperture definition files and match them to lattice elements.

File format (space or comma separated, # comments):

    # name       shape      outer_x   outer_y
    MQA*         cylinder   10.0      10.0
    MQB*         block      8.0       12.0
    QF           block      8.0            # outer_y defaults to outer_x
    QD                                     # all defaults

Columns:
    name     — element name pattern, wildcards * and ? supported (required)
    shape    — 'cylinder' or 'block', default 'block'
    outer_x  — outer half-width/radius in cm, default = element_half_width * 100
    outer_y  — outer half-height in cm, default = outer_x

For cylinder shape, outer_x is used as radius (outer_y ignored).
"""
import re
import fnmatch


def parse_aperture_file(path):
    """Parse an aperture definition file.

    Returns a list of dicts:
        [{'pattern': str, 'shape': str,
          'outer_x': float|None, 'outer_y': float|None}, ...]
    outer_x/outer_y are in cm, or None if not specified (use default).
    """
    entries = []
    with open(path, 'r') as f:
        for line in f:
            # Strip comments
            line = line.split('#')[0].strip()
            if not line:
                continue
            # Split on whitespace or comma
            parts = re.split(r'[\s,]+', line)
            if not parts or not parts[0]:
                continue

            name    = parts[0]
            shape   = 'block'
            outer_x = None
            outer_y = None

            if len(parts) >= 2:
                p1 = parts[1].lower()
                if p1 in ('cylinder', 'block'):
                    shape = p1
                    if len(parts) >= 3:
                        try: outer_x = float(parts[2])
                        except ValueError: pass
                    if len(parts) >= 4:
                        try: outer_y = float(parts[3])
                        except ValueError: pass
                else:
                    # No shape specified — treat as outer_x
                    try: outer_x = float(parts[1])
                    except ValueError: pass
                    if len(parts) >= 3:
                        try: outer_y = float(parts[2])
                        except ValueError: pass

            # outer_y defaults to outer_x
            if outer_x is not None and outer_y is None:
                outer_y = outer_x
            if outer_y is not None and outer_x is None:
                outer_x = outer_y

            entries.append({
                'pattern': name,
                'shape':   shape,
                'outer_x': outer_x,
                'outer_y': outer_y,
            })

    return entries


def match_apertures(elements, entries, default_hw=0.2):
    """Match aperture entries to elements using wildcard patterns.

    Returns a list of dicts, one per matched element:
        {'element': elem_dict, 'shape': str,
         'outer_x': float, 'outer_y': float}   (outer in metres)

    Only elements explicitly matched by an entry are returned.
    default_hw is element_half_width in metres (used when outer not specified).
    """
    default_cm = default_hw * 100.0
    matched = []

    for e in elements:
        name = e['name'].split('\\')[-1].upper()
        for entry in entries:
            pat = entry['pattern'].upper()
            if fnmatch.fnmatch(name, pat):
                ox_cm = entry['outer_x'] if entry['outer_x'] is not None else default_cm
                oy_cm = entry['outer_y'] if entry['outer_y'] is not None else ox_cm
                matched.append({
                    'element': e,
                    'shape':   entry['shape'],
                    'outer_x': ox_cm / 100.0,   # convert to metres
                    'outer_y': oy_cm / 100.0,
                })
                break  # first matching pattern wins

    return matched
