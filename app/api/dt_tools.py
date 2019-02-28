from collections import defaultdict

from sqlalchemy import or_
from flask import request, jsonify, current_app


__all__ = (
    'DataTable',
)

import operator

def as_callable(x):
    if callable(x):
        return x
    elif isinstance(x, str):
        return operator.attrgetter(x)
    elif isinstance(x, int):
        return operator.itemgetter(x)
    else:
        raise TypeError(f"Can't generate callable for {x!r}")


class DataTable:
    def __init_subclass__(cls):
        model = getattr(cls, 'model', False)
        if not model:
            raise ValueError('Need to specify model to query.')
        cols = getattr(cls, 'cols', False)
        if not cols:
            raise ValueError('Need to specify column definitions in cols.')

    model = None
    query = None
    cols = None
    dom = None
    row_controls = None
    js_kwargs = None

    @classmethod
    def generate_html(cls, class_=None):
        return "".join(_.strip() for _ in f"""
        <div class="{'container pt-2' if class_ is None else str(class_)}">
            <div class"row">
                <table id="{cls.model.__name__.lower()}Table" class="table table-striped table-bordered responsive responsive" style="width: 100%;">
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
        """.split('\n'))

    @classmethod
    def generate_js(cls, table_url, row_class="", dom=None, **kwargs):
        dom = dom or "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>><'row'<'col-sm-12'tr>><'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>"
        kwargs = {**(cls.js_kwargs or {}), **kwargs}
        return "".join(_.strip() for _ in f"""
        $(document).ready(function() {{
            $('#{cls.model.__name__.lower()}Table').DataTable({{
                "dom": "{dom}",
                "processing": true,
                "serverSide": true,
                "responsive": true,
                "ajax": {{
                    "dataType": 'json',
                    "contentType": "application/json; charset=utf-8",
                    "type": "GET",
                    "url":"{table_url}",
                    "dataSrc": function(json) {{
                        if (!("{cls.model.__name__.lower()}_fields" in sessionStorage)) {{
                            sessionStorage["{cls.model.__name__.lower()}_fields"] = JSON.stringify(json.fields);
                        }} else if (JSON.stringify(json.fields) !== sessionStorage["{cls.model.__name__.lower()}_fields"]) {{
                            sessionStorage.clear();
                            sessionStorage["{cls.model.__name__.lower()}_fields"] = JSON.stringify(json.fields);
                        }}
                        return json.data;
                    }}
                }},
                "deferRender": true,
                "columns": [{', '.join(f'{{ "data": "{col["field"]}", "orderable": {str(col.get("orderable", True)).lower()}, "render": {col.get("render", "undefined")}}}' for col in cls.cols)}],
                "createdRow" : function( row, data, index ) {{
                    sessionStorage["{cls.model.__name__.lower()}" + data.id] = JSON.stringify(data);
                    $(row).addClass("{cls.model.__name__.lower()}-row {row_class}");
                    if( data.hasOwnProperty("id") ) {{row.id = data.id}}
                    {kwargs.pop('createdRow', '')}
                }},
                {",".join(f'"{name}": {value}' for name, value in kwargs.items())}
            }});
        }});
        """.split('\n'))

    def __init__(self, pre_filter=None):
        self._pre_filter = pre_filter or or_()

    @classmethod
    def get_col_def(cls, col_idx):
        for col in cls.cols:
            if col['col'] == col_idx:
                return col
        return None

    def _parse_ordering(self):
        requested_ordering = defaultdict(dict)
        for name, val in request.args.items():
            if name.startswith('order'):
                _num, _target = name[5:].split('][')
                num = int(_num[1:])
                target = _target[:-1]
                requested_ordering[num][target] = val
        _ = (
            { "def": self.get_col_def(int(ordering['column'])), "dir": ordering["dir"] }
            for ordering in requested_ordering.values()
        )
        _ = sorted((
            ordering for ordering in _
            if ordering["def"] is not None and ordering["def"].get("orderable", True)
        ), key=lambda ordering: ordering["def"].get("weight", float('inf')))
        return sum((
            [getattr(
                getattr(self.model, ordering["def"]["field"]),
                ordering["dir"]
            )(),]
            if "custom_order" not in ordering["def"] else
            list(ordering["def"]["custom_order"](ordering["dir"]))
            for ordering in _ 
        ), [])

    def _parse_filtering(self):
        value = request.args.get("search[value]", None)
        def _filter_func(obj):
            values = value.split("|")
            current_app.logger.info(values)
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
                for value in values
            )
        return _filter_func if value is not None else lambda obj: True

    def get_data(self):
        data = list(filter(self._parse_filtering(), (as_callable(self.__class__.query)() if self.query is not None else self.model.query).filter(self._pre_filter).order_by(*self._parse_ordering())))
        amount = len(data)
        return {
            "fields": list(self.model.__table__.columns.keys()),
            "recordsTotal": amount,
            "recordsFiltered": amount,
            "data": [self._serialize(_) for _ in data[int(request.args.get('start')):int(request.args.get('start'))+int(request.args.get('length'))]],
        }

    @classmethod
    def _serialize(cls, obj):
        return {
            **(obj.serialize() if hasattr(obj, 'serialize') and callable(obj.serialize) else {}),
            **{
                col['field']: as_callable(col['value'])(obj)
                for col in cls.cols
                if 'value' in col
            }
        }

    def get_response(self):
        return jsonify(self.get_data())
