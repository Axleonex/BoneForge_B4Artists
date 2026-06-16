"""BoneForge BFA - landmark detection geometry kernel (Task 3, BF-GAP-01).

PURE geometry math over a point cloud (mesh vertices, world space). No bpy,
no model files. This is the deterministic fallback path of smart marker
detection: bounds, centroid, mirror-axis detection, extremity finding, and
heuristic body-landmark guesses with confidence.

The mesh-reading glue (sampling ``bpy`` vertices) lives in ``inference.py``.
This kernel owns the pure robustness pass: finite-point cleanup, loose
connected-component filtering for disconnected props/clothing, scale
normalization helpers, guarded symmetry-axis choice, and conservative
confidence on non-upright clouds.

Clean-room: first-principles geometry; no third-party detection code.
"""
import math

UP = 2  # Z-up world convention


def _as_point(p):
    return (float(p[0]), float(p[1]), float(p[2]))


def _finite_points(points):
    clean = []
    for p in points:
        if p is None or len(p) < 3:
            continue
        q = _as_point(p)
        if all(math.isfinite(v) for v in q):
            clean.append(q)
    return clean


def _require_points(points):
    pts = _finite_points(points)
    if not pts:
        raise ValueError("point cloud is empty")
    return pts


def _axis_vals(points, axis):
    return [p[axis] for p in points]


def bounds(points):
    points = _require_points(points)
    xs, ys, zs = (_axis_vals(points, 0), _axis_vals(points, 1),
                  _axis_vals(points, 2))
    return ((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))


def centroid(points):
    points = _require_points(points)
    n = float(len(points))
    return tuple(sum(_axis_vals(points, a)) / n for a in range(3))


def extent(points):
    lo, hi = bounds(points)
    return tuple(hi[a] - lo[a] for a in range(3))


def _percentile(sorted_vals, frac):
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = max(0.0, min(1.0, frac)) * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_vals[lo]
    t = pos - lo
    return sorted_vals[lo] * (1.0 - t) + sorted_vals[hi] * t


def _robust_extent(points):
    """5/95-percentile extents, resistant to small disconnected outliers."""
    pts = _require_points(points)
    out = []
    for axis in range(3):
        vals = sorted(_axis_vals(pts, axis))
        out.append(_percentile(vals, 0.95) - _percentile(vals, 0.05))
    return tuple(max(v, 0.0) for v in out)


def _largest_loose_component(points):
    """Keep the largest voxel-connected component.

    Mesh vertex clouds do not carry topology here, so this is deliberately
    loose: a cell size derived from robust body scale connects adjacent body
    parts while dropping far disconnected clothing, props, or scanner debris.
    """
    pts = _require_points(points)
    if len(pts) < 16:
        return pts

    rext = _robust_extent(pts)
    diag = math.sqrt(sum(v * v for v in rext))
    cell_size = max(diag * 0.16, max(rext) * 0.06, 1e-6)
    if cell_size <= 1e-6:
        return pts

    cells = {}
    for idx, p in enumerate(pts):
        key = tuple(int(math.floor(p[a] / cell_size)) for a in range(3))
        cells.setdefault(key, []).append(idx)

    seen = set()
    best = []
    offsets = [(dx, dy, dz)
               for dx in (-1, 0, 1)
               for dy in (-1, 0, 1)
               for dz in (-1, 0, 1)]
    for start in cells:
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        component = []
        while stack:
            key = stack.pop()
            component.extend(cells[key])
            for dx, dy, dz in offsets:
                nb = (key[0] + dx, key[1] + dy, key[2] + dz)
                if nb in cells and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        if len(component) > len(best):
            best = component

    if not best or len(best) == len(pts):
        return pts
    if len(best) < max(8, int(len(pts) * 0.40)):
        return pts
    return [pts[i] for i in sorted(best)]


def preprocess_points(points):
    """Clean and de-clutter a point cloud before landmark heuristics."""
    return _largest_loose_component(_require_points(points))


def normalize_points(points):
    """Return ``(normalized, center, scale)`` for a cleaned point cloud."""
    pts = preprocess_points(points)
    c = centroid(pts)
    scale = max((sum((p[a] - c[a]) ** 2 for a in range(3))) ** 0.5
                for p in pts) or 1.0
    norm = [tuple((p[a] - c[a]) / scale for a in range(3)) for p in pts]
    return norm, c, scale


def symmetry_score(points, axis, sample=300):
    """Reflection-overlap score across the centroid plane on ``axis``.

    Lower means more symmetric.
    """
    points = _require_points(points)
    if len(points) < 2:
        return 0.0
    c = centroid(points)
    pts = points[:sample] if len(points) > sample else points
    score = 0.0
    for p in pts:
        refl = list(p)
        refl[axis] = 2 * c[axis] - p[axis]
        score += min(sum((q[k] - refl[k]) ** 2 for k in range(3)) for q in pts)
    return score


def symmetry_axis(points):
    """Left-right mirror axis of an upright humanoid.

    Heuristic: the mirror axis is the widest horizontal axis (arm span /
    shoulder width). A thin, centred cloud is trivially symmetric across its
    thin axis, so extent leads; the overlap score only breaks ties when the
    two horizontal extents are close. Degenerate clouds fall back to X.
    """
    points = preprocess_points(points)
    ext = extent(points)
    horiz = sorted((a for a in range(3) if a != UP), key=lambda a: -ext[a])
    widest, other = horiz[0], horiz[1]
    if ext[widest] <= 1e-9:
        return 0
    if ext[other] > 0.75 * ext[widest]:
        return widest if symmetry_score(points, widest) <= \
            symmetry_score(points, other) else other
    return widest


def extremities(points, k=6):
    """Return the k points farthest from the centroid (hands/feet/head)."""
    points = preprocess_points(points)
    c = centroid(points)
    ranked = sorted(points,
                    key=lambda p: -sum((p[a] - c[a]) ** 2 for a in range(3)))
    return ranked[:k]


def guess_landmarks(points):
    """Heuristic body landmarks.

    Returns dict with axes + a list of ``{name, pos, confidence, source}``.
    Confidence is in [0, 1].
    """
    points = preprocess_points(points)
    lo, hi = bounds(points)
    c = centroid(points)
    ext = extent(points)
    height = ext[UP] or 1.0
    sym = symmetry_axis(points)
    other = [a for a in (0, 1, 2) if a not in (UP, sym)][0]
    out = []

    horizontal = max(ext[a] for a in range(3) if a != UP) or 1.0
    upright_scale = 1.0 if height >= 0.75 * horizontal else 0.65

    def conf(value):
        return max(0.0, min(1.0, value * upright_scale))

    def at_height(frac):
        return lo[UP] + frac * height

    def side_points(positive):
        return [p for p in points if (p[sym] - c[sym] > 0) == positive] or points

    top = max(points, key=lambda p: p[UP])
    out.append({"name": "head", "pos": tuple(top),
                "confidence": conf(0.8), "source": "geometry"})
    hips = list(c); hips[UP] = at_height(0.53)
    out.append({"name": "hips", "pos": tuple(hips),
                "confidence": conf(0.7), "source": "geometry"})
    for positive, tag in ((True, "L"), (False, "R")):
        sp = side_points(positive)
        hand = max(sp, key=lambda p: (p[sym] if positive else -p[sym]))
        out.append({"name": "hand-" + tag, "pos": tuple(hand),
                    "confidence": conf(0.6), "source": "geometry"})
        foot = min(sp, key=lambda p: p[UP])
        out.append({"name": "foot-" + tag, "pos": tuple(foot),
                    "confidence": conf(0.65), "source": "geometry"})
        sh = max(sp, key=lambda p: p[UP] + (p[sym] if positive else -p[sym]))
        shoulder = list(sh); shoulder[UP] = at_height(0.82)
        out.append({"name": "shoulder-" + tag, "pos": tuple(shoulder),
                    "confidence": conf(0.5), "source": "geometry"})
    return {"up_axis": UP, "symmetry_axis": sym, "front_axis": other,
            "height": height, "landmarks": out}


def confidence_category(score):
    """``'CONFIRMED'`` (>=0.85), ``'REVIEW'`` (>=0.6), else ``'ADJUST'``.

    Pure logic kept in the kernel so it is testable without ``bpy``; the
    detection layer re-exports it.
    """
    if score >= 0.85:
        return 'CONFIRMED'
    if score >= 0.6:
        return 'REVIEW'
    return 'ADJUST'


def _lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def body_marker_proposals(geo):
    """Map geometry landmarks onto the wizard's BODY_MARKERS.

    Intermediate joints (neck, elbows, hips, knees, toes, heels) are derived
    by interpolation. Pure: returns ``{MARKER_NAME: {"pos": (x,y,z),
    "confidence": float, "source": str}}``. Confidence stays modest for
    derived joints so they land in the REVIEW/ADJUST band and are never
    silently auto-confirmed.
    """
    lm = {d["name"]: (d["pos"], d["confidence"]) for d in geo["landmarks"]}
    up, sym, front = geo["up_axis"], geo["symmetry_axis"], geo["front_axis"]
    height = geo["height"]
    out = {}

    def put(name, pos, conf, source="geometry"):
        out[name] = {"pos": tuple(float(x) for x in pos),
                     "confidence": round(float(conf), 3), "source": source}

    if "head" in lm:
        put("HEAD_TOP", *lm["head"])
    if "hips" in lm:
        put("PELVIS", *lm["hips"])
    if "shoulder-L" in lm and "shoulder-R" in lm:
        put("NECK_BASE", _lerp(lm["shoulder-L"][0], lm["shoulder-R"][0], 0.5),
            0.5, "derived")
    elif "head" in lm and "hips" in lm:
        put("NECK_BASE", _lerp(lm["hips"][0], lm["head"][0], 0.78), 0.4,
            "derived")

    for tag, side in (("L", "LEFT"), ("R", "RIGHT")):
        sh = lm.get("shoulder-" + tag)
        wr = lm.get("hand-" + tag)
        ft = lm.get("foot-" + tag)
        if sh:
            put("SHOULDER_" + side, *sh)
        if wr:
            put("WRIST_" + side, *wr)
        if ft:
            put("ANKLE_" + side, *ft)
        if sh and wr:
            put("ELBOW_" + side, _lerp(sh[0], wr[0], 0.5), 0.4, "derived")
        if "hips" in lm and ft:
            hip = list(lm["hips"][0])
            hip[sym] = 0.5 * ft[0][sym] + 0.5 * lm["hips"][0][sym]
            put("HIP_" + side, hip, 0.45, "derived")
            put("KNEE_" + side, _lerp(hip, ft[0], 0.5), 0.4, "derived")
        if ft:
            toe = list(ft[0]); toe[front] += 0.08 * height; toe[up] -= 0.02 * height
            heel = list(ft[0]); heel[front] -= 0.05 * height; heel[up] -= 0.02 * height
            put("TOE_" + side, toe, 0.35, "derived")
            put("HEEL_" + side, heel, 0.35, "derived")
    return out
