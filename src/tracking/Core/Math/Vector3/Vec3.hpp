#pragma once

class Vec3
{
    public:
        float x;
        float y;
        float z;

        Vec3();
        Vec3(float x, float y, float z);

        Vec3 operator+(const Vec3& other) const;
        Vec3 operator-(const Vec3& other) const;

        Vec3 operator*(float scalar) const;
        Vec3 operator/(float scalar) const;

        float dot(const Vec3& other) const;
        Vec3 cross(const Vec3& other) const;

        float magnitude() const;
        float magnitudeSquared() const;

        Vec3 normalize() const;

        bool equals(const Vec3& other) const;
};