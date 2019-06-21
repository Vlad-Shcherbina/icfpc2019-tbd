with import <nixpkgs> {};
with python37Packages;

stdenv.mkDerivation {
  name = "icfpc2019-tbd";

  buildInputs = [
    python
    virtualenv
    pip
    nodejs
    chromium
  ];

  shellHook = ''
    export SOURCE_DATE_EPOCH=$(date +%s)
    virtualenv --no-setuptools virtualenv

    export PATH=$PWD/virtualenv/bin:$PATH
    pip install -r requirements.txt
  '';

  PUPPETEER_SKIP_CHROMIUM_DOWNLOAD = "1";
  PUPPETEER_EXECUTABLE_PATH = "${chromium}/bin/chromium";
}
