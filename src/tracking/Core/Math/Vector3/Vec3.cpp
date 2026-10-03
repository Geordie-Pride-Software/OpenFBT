#include "Vec3.hpp"

#include <cmath>


Vec3::Vec3()
    : x(0.0f), y(0.0f), z(0.0f)
{
}


Vec3::Vec3(float x, float y, float z)
    : x(x), y(y), z(z)
{
}


Vec3 Vec3::operator+(const Vec3& other) const
{
    return Vec3(
        x + other.x,
        y + other.y,
        z + other.z
    );
}


Vec3 Vec3::operator-(const Vec3& other) const
{
    return Vec3(
        x - other.x,
        y - other.y,
        z - other.z
    );
}


Vec3 Vec3::operator*(float scalar) const
{
    return Vec3(
        x * scalar,
        y * scalar,
        z * scalar
    );
}


Vec3 Vec3::operator/(float scalar) const
{
    return Vec3(
        x / scalar,
        y / scalar,
        z / scalar
    );
}


float Vec3::dot(const Vec3& other) const
{
    return (x * other.x) +
           (y * other.y) +
           (z * other.z);
}


Vec3 Vec3::cross(const Vec3& other) const
{
    return Vec3(
        (y * other.z) - (z * other.y),
        (z * other.x) - (x * other.z),
        (x * other.y) - (y * other.x)
    );
}


float Vec3::magnitude() const
{
    return std::sqrt(
        (x * x) +
        (y * y) +
        (z * z)
    );
}


float Vec3::magnitudeSquared() const
{
    return (x * x) +
           (y * y) +
           (z * z);
}


Vec3 Vec3::normalize() const
{
    float length = magnitude();

    if (length == 0.0f)
        return Vec3();

    return *this / length;
}


bool Vec3::equals(const Vec3& other) const
{
    return x == other.x &&
           y == other.y &&
           z == other.z;
}