import os

if __name__ == '__main__':
    os.system('awe retrieve_images.py')
    os.system('python make_map.py')
    os.system('python write_json.py')
