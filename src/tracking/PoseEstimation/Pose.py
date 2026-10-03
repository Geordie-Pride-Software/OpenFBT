class Landmark:
    def __init__(
        self,
        name,
        image_x,
        image_y,
        world_x,
        world_y,
        world_z,
        visibility=1.0,
        presence=1.0
    ):
        self.name = name

        self.image_x = image_x
        self.image_y = image_y

        self.world_x = world_x
        self.world_y = world_y
        self.world_z = world_z

        self.visibility = visibility
        self.presence = presence

    def get_name(self):
        return self.name

    def get_image_x(self):
        return self.image_x

    def get_image_y(self):
        return self.image_y

    def get_world_x(self):
        return self.world_x

    def get_world_y(self):
        return self.world_y

    def get_world_z(self):
        return self.world_z

    def get_visibility(self):
        return self.visibility

    def get_presence(self):
        return self.presence


class Pose:
    def __init__(self, landmarks):
        self.landmarks = landmarks

    def get_landmarks(self):
        return self.landmarks

    def get_landmark(self, name):
        return self.landmarks.get(name)

    def has_landmark(self, name):
        return name in self.landmarks