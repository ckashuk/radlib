import yaml

with open('../../processors/total_segmentator_processor/docker_app/docker-compose.yaml') as y:
    data = yaml.safe_load(y)

print(data)

data['processors']['total_segmentator_processor']['volumes'] = [
    '/one:/one',
    '/two:/two',
    '/three:/three'
]
data['volumes'] = {
    'one': None,
    'two': None,
    'three': None
}

print(data)
