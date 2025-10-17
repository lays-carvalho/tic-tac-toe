from bson import ObjectId

def convert_objectid(doc):
    if isinstance(doc, dict):
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                doc[key] = str(value)
            elif isinstance(value, list):
                doc[key] = [convert_objectid(item) for item in value]
            elif isinstance(value, dict):
                doc[key] = convert_objectid(value)
    elif isinstance(doc, list):
        doc = [convert_objectid(item) for item in doc]
    return doc