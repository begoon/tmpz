#include <wsq.h>
#include <stdio.h>
#include <stdlib.h>

int debug = 0;

int main(int argc, char *argv[])
{
    unsigned char *wsq_buffer = NULL;
    int wsq_size = 0;

    int out_cols, out_rows;
    int out_depth, out_ppi;
    int out_lossy_flag;
    unsigned char *out_buffer = NULL;
    int ret_code;

    FILE *fin = NULL;
    FILE *fout = NULL;

    if (argc != 3)
    {
        fprintf(stderr, "usage: %s input.wsq output.ppm\n", argv[0]);
        return 1;
    }

    const char *input_filename = argv[1];
    const char *output_filename = argv[2];

    /* --- Read WSQ file into memory --- */
    fin = fopen(input_filename, "rb");
    if (!fin)
    {
        perror("Error opening input WSQ file");
        return 1;
    }

    if (fseek(fin, 0, SEEK_END) != 0)
    {
        perror("fseek failed");
        fclose(fin);
        return 1;
    }

    long fsize = ftell(fin);
    if (fsize < 0)
    {
        perror("ftell failed");
        fclose(fin);
        return 1;
    }
    rewind(fin);

    wsq_size = (int)fsize; /* assuming file fits in int */
    wsq_buffer = (unsigned char *)malloc(wsq_size);
    if (!wsq_buffer)
    {
        fprintf(stderr, "Memory allocation failed\n");
        fclose(fin);
        return 1;
    }

    if (fread(wsq_buffer, 1, wsq_size, fin) != (size_t)wsq_size)
    {
        fprintf(stderr, "Failed to read entire WSQ file\n");
        free(wsq_buffer);
        fclose(fin);
        return 1;
    }
    fclose(fin);
    fin = NULL;

    /* --- Decode WSQ to raw image --- */
    ret_code = wsq_decode_mem(&out_buffer,
                              &out_cols,
                              &out_rows,
                              &out_depth,
                              &out_ppi,
                              &out_lossy_flag,
                              wsq_buffer,
                              wsq_size);
    free(wsq_buffer);
    wsq_buffer = NULL;

    if (ret_code != 0)
    {
        fprintf(stderr, "wsq_decode_mem failed with code %d\n", ret_code);
        if (out_buffer)
        {
            free(out_buffer);
        }
        return 1;
    }

    if (out_depth != 8)
    {
        fprintf(stderr, "Unexpected depth %d (expected 8-bit grayscale)\n", out_depth);
        free(out_buffer);
        return 1;
    }

    /* --- Write PPM P3 (ASCII) --- */
    fout = fopen(output_filename, "w");
    if (!fout)
    {
        perror("Error opening output PPM file");
        free(out_buffer);
        return 1;
    }

    /* PPM P3 header */
    fprintf(fout, "P3\n");
    fprintf(fout, "%d %d\n", out_cols, out_rows);
    fprintf(fout, "255\n");

    /*
     * out_buffer is grayscale (one byte per pixel).
     * PPM expects RGB, so write v v v for each pixel.
     */
    int num_pixels = out_cols * out_rows;
    for (int i = 0; i < num_pixels; i++)
    {
        unsigned char v = out_buffer[i];
        /* One pixel per line, keeps it simple */
        fprintf(fout, "%d %d %d\n", v, v, v);
    }

    fclose(fout);
    free(out_buffer);

    return 0;
}
