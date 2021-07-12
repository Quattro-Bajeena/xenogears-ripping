import json


def generate():
    descriptions = {}
    for i in range(1, 730):
        descriptions[i] = {"description": ""}

    with open('Maps/descriptions.json', 'w+') as file:
        json.dump(descriptions, file, indent=4)

def add_tags():
    with open('Maps/descriptions.json', 'r') as file:
        descriptions = json.load(file)

    for  room_id in descriptions:
        descriptions[room_id]["tags"] = []

    with open('Maps/descriptions.json', 'w') as file:
        json.dump(descriptions, file, indent=4)
    

