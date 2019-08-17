from collections import defaultdict
import operator

from sqlalchemy import or_, cast, Text
from flask import request, jsonify, render_template  # , current_app


__all__ = ("DataTable", "ModelDataTable")


def as_callable(x):
    if callable(x):
        return x
    elif isinstance(x, str):
        return operator.attrgetter(x)
    elif isinstance(x, int):
        return operator.itemgetter(x)
    else:
        raise TypeError(f"Can't generate callable for {x!r}")


def minify(s):
    return "".join(l.strip() for l in s.split("\n"))


class DataTable:
    def __init_subclass__(cls, new_base=False):
        if not new_base:
            if not hasattr(cls, "cols"):
                raise ValueError("Need to specify column definitions in cols.")
            if not hasattr(cls, "table_id"):
                setattr(cls, "table_id", f"{cls.__name__.lower()}Table")

    js_kwargs = None
    search_delimiter = "|"

    @classmethod
    def generate_html(cls, css_class=None, head_css_class=None):
        return minify(
            render_template(
                "api/dt_tools/table.html",
                table_id=cls.table_id,
                cols=cls.cols,
                css_class=css_class or "",
                head_css_class=head_css_class or "",
            )
        )

    @classmethod
    def generate_js(cls, table_url, dom=None, eager_search=False, **kwargs):
        return minify(
            render_template(
                "api/dt_tools/script.html",
                dom=dom,
                eager_search=eager_search,
                cols=cls.cols,
                table_id=cls.table_id,
                table_url=table_url,
                js_kwargs={**(cls.js_kwargs or {}), **kwargs.pop("js_kwargs", dict())},
                kwargs=kwargs,
            )
        )

    def _parse_filter_value(self):
        value = request.args.get("search[value]", None)
        return value.split(self.search_delimiter) if self.search_delimiter else value

    def filter_func(self, data, filter_values):
        if not filter_values:
            return data

        def f(obj):
            return all(
                any(
                    (
                        "custom_filter" in col
                        and col["custom_filter"](obj, value)
                        or "value" in col
                        and value in as_callable(col["value"])(obj)
                        or value in str(getattr(obj, col["field"]))
                    )
                    for col in self.cols
                    if col.get("filterable", True)
                )
                for value in filter_values
            )

        return filter(f, data)

    def _parse_ordering(self):
        ordering = defaultdict(dict)
        for name, val in request.args.items():
            if name.startswith("order"):
                _num, _target = name[5:].split("][")
                num = int(_num[1:])
                target = _target[:-1]
                ordering[num][target] = val
        ordering = (
            {"def": self.cols[int(order["column"])], "dir": order["dir"]}
            for order in ordering.values()
        )
        ordering = sorted(
            (
                order
                for order in ordering
                if order["def"] is not None and order["def"].get("orderable", True)
            ),
            key=lambda order: order["def"].get("weight", float("inf")),
        )
        return ordering

    def order_func(self, data, ordering):
        comparers = [
            (
                (
                    operator.attrgetter(order["def"]["field"])
                    if "value" not in order["def"]["field"]
                    else as_callable(order["def"]["field"]["value"])
                ),
                -1 if order["dir"] == "desc" else 1,
            )
            for order in ordering
        ]
        return sorted(data, key=lambda obj: [(fn(obj), mult) for fn, mult in comparers])

    def _parse_slicing(self):
        return (int(request.args.get("start")), int(request.args.get("length")))

    def slice_func(self, data, start, length):
        return data[start : start + length]

    def length_func(self, data):
        return len(data)

    def get_data(self):
        return self.data

    def get_requested_data(self):
        raw_data = self.get_data()
        filtered_data = self.filter_func(raw_data, self._parse_filter_value())
        ordered_data = self.order_func(filtered_data, self._parse_ordering())
        data = self.slice_func(ordered_data, *self._parse_slicing())
        amount = self.length_func(ordered_data)
        total_amount = self.length_func(raw_data)
        return {
            "fields": list(self.model.__table__.columns.keys()),
            "recordsTotal": total_amount,
            "recordsFiltered": amount,
            "data": [self.serialize(_) for _ in data],
        }

    @classmethod
    def serialize(cls, obj):
        return {
            col["field"]: (
                as_callable(col["value"])(obj)
                if "value" in col
                else getattr(obj, col["field"])
                if hasattr(cls.model, col["field"])
                else None
            )
            for col in cls.cols
        }

    def get_response(self):
        return jsonify(self.get_requested_data())


class ModelDataTable(DataTable, new_base=True):
    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, "model"):
            raise ValueError("Need to specify model to query.")
        if not hasattr(cls, "table_id"):
            setattr(cls, "table_id", f"{cls.model.__name__.lower()}Table")
        super().__init_subclass__(**kwargs)
        setattr(
            cls, "db_cols", {column.name: column for column in cls.model.__table__.c}
        )

    def __init__(self, *args, query=None, **kwargs):
        super().__init__(*args, **kwargs)
        if query is not None:
            self.query = query
        elif not hasattr(self, "query"):
            self.query = self.model.query

    def get_data(self):
        return self.query() if callable(self.query) else self.query

    @classmethod
    def generate_js(cls, *args, createdRow=None, **kwargs):
        return super().generate_js(
            *args,
            createdRow=(createdRow or "")
            + 'if( data.hasOwnProperty("id") ) {row.id = data.id}',
            **kwargs,
        )

    def filter_func(self, data, filter_values):
        if not filter_values:
            return data
        db_filters = [
            or_(
                cast(self.db_cols[col["field"]], Text).contains(value)
                for col in self.cols
                if col.get("filterable", True) and col["field"] in self.db_cols
            )
            for value in filter_values
        ]
        externally_filtered_ids = (
            [obj.id for obj in super().filter_func(data, filter_values)]
            if any("custom_filter" in col or "value" in col for col in self.cols)
            else []
        )
        if externally_filtered_ids:
            db_filters.append(self.model.id.in_(externally_filtered_ids))
        return data.filter(or_(*db_filters))

    def order_func(self, data, ordering):
        return data.order_by(
            *[
                getattr(self.db_cols[order["def"]["field"]], order["dir"])()
                for order in ordering
                if order["def"]["field"] in self.db_cols
            ]
        )

    def slice_func(self, data, start, length):
        return data.slice(start, length)

    def length_func(self, data):
        return data.count()

    @classmethod
    def serialize(cls, obj):
        return {**super().serialize(obj), "id": obj.id}
