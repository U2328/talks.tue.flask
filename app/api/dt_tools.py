from collections import defaultdict
from functools import reduce

from sqlalchemy import or_
from flask import request, jsonify, current_app


__all__ = (
    'DataTable',
)


class DataTable:
    def __init_subclass__(cls):
        model = getattr(cls, 'model', False)
        if not model:
            raise ValueError('Need to specify model to query.')
        cols = getattr(cls, 'cols', False)
        if not cols:
            raise ValueError('Need to specify column definitions in cols.')

    model = None
    cols = None

    @classmethod
    def generate_html(cls, class_=None, table_class=None, table_style=None):
        return "".join(_.strip() for _ in f"""
        <div class="{'container pt-2' if class_ is None else str(class_)}">
            <div class"row">
                <table id="{cls.model.__name__.lower()}Table" class="{'table table-striped table-bordered' if table_class is None else str(table_class)}" style="{'' if table_style is None else str(table_style)}">
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
    def generate_js(cls, table_url, **kwargs):
        return "".join(_.strip() for _ in f"""
        <script type="text/javascript">
        $(document).ready(function() {{
            $('#{cls.model.__name__.lower()}Table').DataTable({{
                "fixedHeader": {{"header": true,}},
                "processing": true,
                "serverSide": true,
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
                "columns": [{', '.join(f'{{ "data": "{col["field"]}"}}' for col in cls.cols)}],
                {",".join(f'"{name}": {value}' for name, value in kwargs.items())}
            }});
        }});
        </script>
        """.split('\n'))

    def __init__(self, pre_filter=None):
        self._pre_filter = pre_filter or or_()

    @classmethod
    def get_col_def(cls, col):
        for col_def in cls.cols:
            if col_def['col'] == col:
                return col_def
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
        ), key=lambda ordering: ordering["def"]["weight"])
        return sum((
            [getattr(
                getattr(self.model, ordering["def"]["field"]),
                ordering["dir"]
            )(),]
            if "custom_order" not in ordering["def"] else
            list(ordering["def"]["custom_order"](ordering["dir"]))
            for ordering in _ 
        ), [])

    def filter(self, value):
        return or_(
            *(
                getattr(self.model, col_def['field']).contains(value)
                if "custom_filter" not in col_def else
                col_def["custom_filter"](value)
                for col_def in self.cols
            )
        )

    def _parse_filtering(self):
        requested_filtering = request.args.get("search[value]")
        if requested_filtering:
            return self.filter(requested_filtering)
        else:
            return or_()

    def get_data(self):
        q = self.model.query.filter(self._pre_filter).filter(self._parse_filtering()).order_by(*self._parse_ordering())
        amount = q.count()
        return {
            "fields": list(self.model.__table__.columns.keys()),
            "recordsTotal": amount,
            "recordsFiltered": amount,
            "data": [_.serialize() for _ in q[int(request.args.get('start')):int(request.args.get('start'))+int(request.args.get('length'))]],
        }

    def get_response(self):
        return jsonify(self.get_data())
