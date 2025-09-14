def explanations(path=None):
    if not path:
        path = 'src/data_dictionary/data_dictionary.txt'
    with open(path, 'r') as file:
        text = file.read()
    return text
    
if __name__ == '__main__':
    text = explanations()
    print(text )