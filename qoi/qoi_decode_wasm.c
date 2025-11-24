#define QOI_IMPLEMENTATION
#include "qoi.h"

__attribute__((import_module("env"), import_name("render"))) extern void render(const unsigned char *buffer, int cols, int rows, int depth);

int qoi_render(unsigned char *qoi_buffer, int qoi_size)
{
    qoi_desc desc;

    void *out_buffer = qoi_decode(qoi_buffer, qoi_size, &desc, 4);
    if (!out_buffer)
    {
        return -1;
    }

    render(out_buffer, desc.width, desc.height, desc.channels);
    free(out_buffer);

    return 0;
}
