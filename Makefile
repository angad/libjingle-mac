SCONS_DIR = scons-2.2.0/
export

default: build
talk/third_party/expat-2.1.0/Makefile:
	cd talk/third_party/expat-2.1.0 && ./configure
talk/third_party/srtp/Makefile:
	cd talk/third_party/srtp && ./configure

build: talk/third_party/expat-2.1.0/Makefile talk/third_party/srtp/Makefile
	cd talk && third_party/swtoolkit/hammer.sh

verbose: talk/third_party/expat-2.0.1/Makefile talk/third_party/srtp/Makefile
	cd talk && third_party/swtoolkit/hammer.sh --verbose

clean:
	cd talk && third_party/swtoolkit/hammer.sh --clean
