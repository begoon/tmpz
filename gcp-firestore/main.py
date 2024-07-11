from google.cloud import firestore

db = firestore.Client()

collection = db.collection("a collection")
document = collection.document("a document")

data = {
    "title": "title",
    "body": "message",
}
document.set(data)

read = document.get()
if read.exists:
    print("read:", read.to_dict())
else:
    print("document not found")

# document.delete() 
