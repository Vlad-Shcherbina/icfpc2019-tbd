with import <nixpkgs> {};

stdenvNoCC.mkDerivation {
  name = "coin-in-a-jar";
  nativeBuildInputs = [
    elixir

    erlang

    rustc
    cargo

    nodejs
    chromium
  ];
  PUPPETEER_SKIP_CHROMIUM_DOWNLOAD = "1";
  PUPPETEER_EXECUTABLE_PATH = "${chromium}/bin/chromium";
}
