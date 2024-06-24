import os
import json

def load_topics_from_json(file_path):
    base_path = os.path.dirname(__file__)
    full_path = os.path.join(base_path, file_path)
    
    with open(full_path, 'r') as file:
        data = json.load(file)
    
    interface_name = data["interface_name"]
    major_version = data["major_version"]
    manufacturer = data["manufacturer"]
    serial_numbers = data["serial_numbers"]
    topic_types = data["topics"]

    topics = []
    for topic_type in topic_types:
        for serial_number in serial_numbers:
            topic = f"{interface_name}/{major_version}/{manufacturer}/{serial_number}/{topic_type}"
            topics.append(topic)
    
    return topics

subscribe_topics = load_topics_from_json('topics/subscribe.json')
publish_topics = load_topics_from_json('topics/publish.json')