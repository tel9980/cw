
import uuid
import logging

class MockDataStore:
    # Global store for mock data
    tables = [] 

    @classmethod
    def reset(cls):
        cls.tables = []

    @classmethod
    def get_table(cls, table_id):
        for t in cls.tables:
            if t['table_id'] == table_id: return t
        return None
    
    @classmethod
    def get_table_by_name(cls, name):
        for t in cls.tables:
            if t['name'] == name: return t
        return None

    @classmethod
    def create_table(cls, name):
        # check duplicate
        exist = cls.get_table_by_name(name)
        if exist: return exist['table_id']
        
        tid = f"tbl_{uuid.uuid4().hex[:8]}"
        cls.tables.append({"table_id": tid, "name": name, "records": []})
        return tid

class MockResponse:
    def __init__(self, success=True, msg="success", data=None):
        self._success = success
        self.msg = msg
        self.data = data
    def success(self): return self._success

class MockObj:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def __getitem__(self, item):
        return getattr(self, item)
        
    def get(self, item, default=None):
        return getattr(self, item, default)

class MockClient:
    def __init__(self, *args, **kwargs):
        self.bitable = self._Bitable()

    class _Bitable:
        def __init__(self):
            self.v1 = self._V1()

        class _V1:
            def __init__(self):
                self.app_table = self._AppTable()
                self.app_table_record = self._AppTableRecord()

            class _AppTable:
                def list(self, req):
                    items = []
                    for t in MockDataStore.tables:
                        items.append(MockObj(table_id=t['table_id'], name=t['name']))
                    return MockResponse(data=MockObj(items=items, has_more=False, page_token=None))

                def create(self, req):
                    # Handle structure: req.request_body.table.name
                    # But verify if 'table' attribute exists, as sometimes it might be flat or different
                    # depending on SDK version or usage.
                    # CW.py uses .table(...)
                    try:
                        name = req.request_body.table.name
                    except AttributeError:
                        try:
                            name = req.request_body.name
                        except:
                            name = "Unknown Table"
                            
                    tid = MockDataStore.create_table(name)
                    return MockResponse(data=MockObj(table_id=tid))

            class _AppTableRecord:
                def list(self, req):
                    t = MockDataStore.get_table(req.table_id)
                    if not t: return MockResponse(False, "Table not found")
                    
                    items = []
                    for r in t['records']:
                        items.append(MockObj(record_id=r['record_id'], fields=r['fields']))
                    return MockResponse(data=MockObj(items=items, has_more=False, page_token=None))

                def batch_create(self, req):
                    t = MockDataStore.get_table(req.table_id)
                    if not t: return MockResponse(False, "Table not found")
                    
                    for r in req.request_body.records:
                        rid = f"rec_{uuid.uuid4().hex[:8]}"
                        t['records'].append({"record_id": rid, "fields": r.fields})
                    return MockResponse()

                def create(self, req):
                    t = MockDataStore.get_table(req.table_id)
                    if not t: return MockResponse(False, "Table not found")
                    rid = f"rec_{uuid.uuid4().hex[:8]}"
                    t['records'].append({"record_id": rid, "fields": req.request_body.fields})
                    return MockResponse(data=MockObj(record_id=rid))
                
                def batch_update(self, req):
                    t = MockDataStore.get_table(req.table_id)
                    if not t: return MockResponse(False, "Table not found")
                    for r in req.request_body.records:
                        for existing in t['records']:
                            if existing['record_id'] == r.record_id:
                                existing['fields'].update(r.fields)
                    return MockResponse()
                
                def delete(self, req):
                    t = MockDataStore.get_table(req.table_id)
                    if not t: return MockResponse(False, "Table not found")
                    t['records'] = [r for r in t['records'] if r['record_id'] != req.record_id]
                    return MockResponse()
