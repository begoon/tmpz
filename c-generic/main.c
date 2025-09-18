#include <stdio.h>
const char *x_int() { return "INT"; }
const char *x_float() { return "FLOAT"; }
struct a_struct
{
    int x;
};
const char *x_struct() { return "STRUCT"; }
const char *x_fallback() { return "FALLBACK"; }

int main()
{
    auto f1 = 3;
    auto f2 = 3.14f;
    auto f3 = (struct a_struct){.x = 5};
    auto r = _Generic(
        (f1), // or (f2), (f3)
        int: x_int(),
        float: x_float(),
        struct a_struct: x_struct(),
        default: x_fallback());
    printf("%s\n", r);
    return 0;
}