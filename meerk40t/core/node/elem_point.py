from copy import copy

from meerk40t.core.node.node import Node
from meerk40t.svgelements import Matrix, Point


class PointNode(Node):
    """
    PointNode is the bootstrapped node type for the 'elem path' type.
    """

    def __init__(
        self,
        point=None,
        matrix=None,
        fill=None,
        stroke=None,
        stroke_width=None,
        settings=None,
        **kwargs,
    ):
        if settings is None:
            settings = dict()
        settings.update(kwargs)
        super(PointNode, self).__init__(type="elem point", **settings)
        self._formatter = "{element_type} {id} {stroke}"
        self.point = point
        self.matrix = matrix
        self.settings = settings
        self.fill = fill
        self.stroke = stroke
        self.stroke_width = stroke_width
        self.lock = False

    def __copy__(self):
        return PointNode(
            point=copy(self.point),
            matrix=copy(self.matrix),
            fill=copy(self.fill),
            stroke=copy(self.stroke),
            stroke_width=self.stroke_width,
            settings=self.settings,
        )

    def validate(self):
        if self.matrix is None:
            self.matrix = Matrix()
        if self.point is None:
            x = float(self.settings.get("x", 0))
            y = float(self.settings.get("y", 0))
            self.matrix.pre_translate(x, y)
            self.point = Point(0, 0)

    def preprocess(self, context, matrix, commands):
        self.matrix *= matrix
        self._bounds_dirty = True

    @property
    def bounds(self):
        if self._bounds_dirty:
            p = self.matrix.transform_point(self.point)
            self._bounds = (
                p[0],
                p[1],
                p[0],
                p[1],
            )
            self._bounds_dirty = False
        return self._bounds

    def default_map(self, default_map=None):
        default_map = super(PointNode, self).default_map(default_map=default_map)
        default_map["element_type"] = "Point"
        if self.point is not None:
            default_map["x"] = self.point[0]
            default_map["y"] = self.point[1]
        else:
            default_map["x"] = 0
            default_map["y"] = 0
        default_map.update(self.settings)
        default_map["stroke"] = self.stroke
        default_map["fill"] = self.fill
        default_map["stroke-width"] = self.stroke_width
        default_map["matrix"] = self.matrix
        return default_map

    def drop(self, drag_node, modify=True):
        # Dragging element into element.
        if drag_node.type.startswith("elem"):
            if modify:
                self.insert_sibling(drag_node)
            return True
        return False

    def revalidate_points(self):
        bounds = self.bounds
        if bounds is None:
            return
        if len(self._points) < 9:
            self._points.extend([None] * (9 - len(self._points)))
        self._points[0] = [bounds[0], bounds[1], "bounds top_left"]
        self._points[1] = [bounds[2], bounds[1], "bounds top_right"]
        self._points[2] = [bounds[0], bounds[3], "bounds bottom_left"]
        self._points[3] = [bounds[2], bounds[3], "bounds bottom_right"]
        cx = (bounds[0] + bounds[2]) / 2
        cy = (bounds[1] + bounds[3]) / 2
        self._points[4] = [cx, cy, "bounds center_center"]
        self._points[5] = [cx, bounds[1], "bounds top_center"]
        self._points[6] = [cx, bounds[3], "bounds bottom_center"]
        self._points[7] = [bounds[0], cy, "bounds center_left"]
        self._points[8] = [bounds[2], cy, "bounds center_right"]
        self._points.append([self.point.x, self.point.y, "point"])

    def update_point(self, index, point):
        return False

    def add_point(self, point, index=None):
        return False
