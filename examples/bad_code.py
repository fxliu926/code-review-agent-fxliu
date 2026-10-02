def divide(a, b):
    return a / b


def process_list(items):
    result = []
    for i in range(len(items)):
        if items[i] != None:
            result.append(items[i] * 2)
    return result


class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def is_adult(self):
        if self.age >= 18:
            return True
        else:
            return False