class Frame:
    def __init__(self, data, width, height):
        self.data = data
        self.width = width
        self.height = height

    def get_data(self):
        return self.data

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height