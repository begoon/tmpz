#include <wsq.h>

int debug = 0;

__attribute__((import_module("env"), import_name("render"))) extern void render(const unsigned char *buffer, int cols, int rows, int depth);

int wsq_decode(unsigned char *wsq_buffer, int wsq_size)
{
    int out_cols, out_rows;
    int out_depth, out_ppi;
    int out_lossy_flag;
    unsigned char *out_buffer = NULL;
    int ret_code;

    ret_code = wsq_decode_mem(&out_buffer,
                              &out_cols,
                              &out_rows,
                              &out_depth,
                              &out_ppi,
                              &out_lossy_flag,
                              wsq_buffer,
                              wsq_size);
    if (ret_code != 0)
    {
        free(out_buffer);
        return ret_code;
    }
    render(out_buffer, out_cols, out_rows, out_depth);
    free(out_buffer);

    return 0;
}

int main() { return 0; }
