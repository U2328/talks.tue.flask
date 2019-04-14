from collections import defaultdict
import operator

from sqlalchemy import or_, cast, Text
from flask import request, jsonify


__all__ = (
    'DataTable',
    'ModelDataTable'
)


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
    return "".join(l.strip() for l in s.split('\n'))


class DataTable:
    def __init_subclass__(cls, new_base=False):
        if not new_base:
            if not hasattr(cls, 'cols'):
                raise ValueError('Need to specify column definitions in cols.')
            if not hasattr(cls, "table_id"):
                setattr(cls, 'table_id', f"{cls.__name__.lower()}Table")

    dom = "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>><'row'<'col-sm-12'tr>><'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>"
    js_kwargs = None
    search_delimiter = '|'

    @classmethod
    def generate_html(cls, css_class=None):
        return minify(f"""
        <div class="{'container pt-2' if css_class is None else str(css_class)}">
            <div class"row">
                <table id="{cls.table_id}" class="table table-striped table-bordered responsive responsive" style="width: 100%;">
                    <thead>
                        <tr>
                            {"".join(
                                f'<th>{col.get("name") or col["field"]}</th>'
                                for col in cls.cols
                            )}
                        </tr>
                    </thead>
                </table>
            </div>
        </div>
        """)

    @classmethod
    def generate_js(cls, table_url, row_class="", dom=None, **kwargs):
        kwargs = {**(cls.js_kwargs or {}), **kwargs}
        return minify(f"""
        $(document).ready(function() {{
            var {cls.table_id} = $('#{cls.table_id}').DataTable({{
                "dom": "{dom or cls.dom}",
                "processing": true,
                "serverSide": true,
                "responsive": true,
                "ajax": {{
                    "dataType": 'json',
                    "contentType": "application/json; charset=utf-8",
                    "type": "GET",
                    "url":"{table_url}",
                    "dataSrc": function(json) {{return json.data;}}
                }},
                "deferRender": true,
                "columns": [{
                    ', '.join(
                        f'{{ "data": "{col["field"]}", "orderable": {str(col.get("orderable", True)).lower()}, "render": {col.get("render", "undefined")}}}'
                        for col in cls.cols
                    )
                }],
                "createdRow" : function( row, data, index ) {{
                    $(row).addClass("{cls.model.__name__.lower()}-row {row_class}");
                    {kwargs.pop('createdRow', '')}
                }},
                {",".join(f'"{name}": {value}' for name, value in kwargs.items())}
            }});
            $('#{cls.table_id}_filter input').unbind();
            $('#{cls.table_id}_filter input').bind('keyup', function(e) {{
                if (e.keyCode == 13) {{
                    {cls.table_id}.search($(this).val()).draw();
                }}
            }});
        }});
        """)

    def _parse_filter_value(self):
        value = request.args.get("search[value]", None)
        return value.split(self.search_delimiter) if self.search_delimiter else value

    def filter_func(self, data, filter_values):
        if not filter_values:
            return data

        def f(obj):
            return all(
                any(
                    col.get(
                        'custom_filter',
                        lambda obj, value: (
                            as_callable(col['value'])(obj)
                            if 'value' in col else
                            value in getattr(obj, col['field'])
                        )
                    )(obj, value)
                    for col in self.cols
                )
                for value in filter_values
            )
        return filter(f, data)

    def _parse_ordering(self):
        ordering = defaultdict(dict)
        for name, val in request.args.items():
            if name.startswith('order'):
                _num, _target = name[5:].split('][')
                num = int(_num[1:])
                target = _target[:-1]
                ordering[num][target] = val
        ordering = (
            {
                "def": self.cols[int(order['column'])],
                "dir": order["dir"]
            }
            for order in ordering.values()
        )
        ordering = sorted((
            order for order in ordering
            if order["def"] is not None and order["def"].get("orderable", True)
        ), key=lambda order: order["def"].get("weight", float('inf')))
        return ordering

    def order_func(self, data, ordering):
        comparers = [
            (
                (
                    operator.attrgetter(order['def']['field'])
                    if 'value' not in order['def']['field'] else
                    as_callable(order['def']['field']['value'])
                ),
                -1 if order["dir"] == 'desc' else 1
            )
            for order in ordering
        ]
        return sorted(data, key=lambda obj: [(fn(obj), mult) for fn, mult in comparers])

    def _parse_slicing(self):
        return (
            int(request.args.get('start')),
            int(request.args.get('length'))
        )

    def slice_func(self, data, start, length):
        return data[start:start + length]

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
            col['field']: (
                as_callable(col['value'])(obj)
                if 'value' in col else
                getattr(obj, col['field'])
                if hasattr(cls.model, col['field']) else
                None
            )
            for col in cls.cols
        }

    def get_response(self):
        return jsonify(self.get_requested_data())


class ModelDataTable(DataTable, new_base=True):
    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, 'model'):
            raise ValueError('Need to specify model to query.')
        if not hasattr(cls, "table_id"):
            setattr(cls, 'table_id', f"{cls.model.__name__.lower()}Table")
        super().__init_subclass__(**kwargs)
        setattr(cls, 'get_data', staticmethod(as_callable(getattr(cls, 'query', None) or (lambda: cls.model.query))))
        setattr(cls, 'db_cols', {
            column.name: column
            for column in cls.model.__table__.c
        })

    @classmethod
    def generate_js(cls, *args, createdRow=None, **kwargs):
        return super().generate_js(*args, createdRow=(createdRow or "") + 'if( data.hasOwnProperty("id") ) {row.id = data.id}', **kwargs)

    def filter_func(self, data, filter_values):
        if not filter_values:
            return data
        db_filters = [
            or_(
                cast(self.db_cols[col['field']], Text).contains(value)
                for col in self.cols
                if col['field'] in self.db_cols
            )
            for value in filter_values
        ]
        externally_filtered_ids = (
            [obj.id for obj in super().filter_func(data, filter_values)]
            if any(hasattr(col, 'custom_filter') or hasattr(col, 'value') for col in self.cols) else
            []
        )
        if externally_filtered_ids:
            db_filters.append(self.model.id.in_(externally_filtered_ids))
        return data.filter(or_(*db_filters))

    def order_func(self, data, ordering):
        return data.order_by(*[
            getattr(
                self.db_cols[order["def"]['field']],
                order["dir"]
            )()
            for order in ordering
        ])

    def slice_func(self, data, start, length):
        return data.slice(start, length)

    def length_func(self, data):
        return data.count()

    @classmethod
    def serialize(cls, obj):
        return {
            **super().serialize(obj),
            "id": obj.id
        }
