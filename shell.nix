{ pkgs ? import ./nix {} }:
with pkgs.python38Packages;
let
  black = buildPythonPackage rec {
    pname = "black";
    version = "20.8b1";
    src = fetchPypi {
      inherit version pname;
      sha256 = "1c02557aa099101b9d21496f8a914e9ed2222ef70336404eeeac8edba836fbea";
    };
    buildInputs = [
      setuptools_scm
      regex
      click
      pathspec
      typed-ast
      toml
      mypy-extensions
      appdirs
      typing-extensions
    ];
    propagatedBuildInputs = [
      regex
      typing-extensions
      mypy-extensions
      toml
      typed-ast
      pathspec
      ];
    doCheck = false;
  };
in 
  pkgs.mkShell {
    buildInputs = with pkgs; [
      python38
      python38Packages.poetry
      black
      niv.niv
      yarn
      docker-compose
      openmpi
      python38Packages.tkinter
      ncurses
    ];
  }
