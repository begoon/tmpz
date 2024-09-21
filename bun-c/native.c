#include <stdio.h>
#include <string.h>
#include <ctype.h>

int native(char* s) {
    int sz = strlen(s);
    printf(" C: %d, %s\n", sz, s);
    for(; *s; ++s) *s = isalpha(*s) ? *s ^ 0x20 : *s;
    return sz;
}
