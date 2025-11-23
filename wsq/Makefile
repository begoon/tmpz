abc: build

VENDOR_PREFIX = vendor/python-wsq

INC = \
$(VENDOR_PREFIX)/csrc/commonnbis/include \
$(VENDOR_PREFIX)/csrc/imgtools/include \
$(VENDOR_PREFIX)/csrc

FLAGS = -D_POSIX_SOURCE -D__NBISLE__ -D__NBIS_PNG__ -O3

FLAGS_WASM = -D_POSIX_SOURCE -D__NBISLE__ -D__NBIS_PNG__ -O3

FILES = \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/ioutil/dataio.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/ioutil/filesize.c \
\
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/util/bres.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/util/bubble.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/util/computil.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/util/fatalerr.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/util/invbyte.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/util/invbytes.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/util/memalloc.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/util/ssxstats.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/util/syserr.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/util/ticks.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/util/time.c  \
\
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/fet/allocfet.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/fet/delfet.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/fet/extrfet.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/fet/freefet.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/fet/lkupfet.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/fet/nistcom.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/fet/printfet.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/fet/readfet.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/fet/strfet.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/fet/updatfet.c \
$(VENDOR_PREFIX)/csrc/commonnbis/src/lib/fet/writefet.c \
\
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/wsq/cropcoeff.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/wsq/decoder.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/wsq/encoder.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/wsq/globals.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/wsq/huff.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/wsq/ppi.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/wsq/sd14util.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/wsq/tableio.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/wsq/tree.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/wsq/util.c \
\
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/jpegl/decoder.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/jpegl/encoder.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/jpegl/huff.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/jpegl/huftable.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/jpegl/imgdat.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/jpegl/ppi.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/jpegl/sd4util.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/jpegl/tableio.c \
$(VENDOR_PREFIX)/csrc/imgtools/src/lib/jpegl/util.c \

build:
	 cc -o wsq $(FILES) main.c $(FLAGS) -m64 $(addprefix -I,$(INC))

wasm:
	emcc -o wsq.wasm \
  	-s EXPORTED_FUNCTIONS='["_wsq_decode","_malloc","_free"]' \
	-s STANDALONE_WASM=1 \
	-s ERROR_ON_UNDEFINED_SYMBOLS=0 \
  	 $(FILES) wqs_decode_wasm.c \
	 $(FLAGS) \
	 $(addprefix -I,$(INC))

clean:
	rm -f wsq wsq.wasm
